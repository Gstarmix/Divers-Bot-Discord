import json
import logging
import os
from datetime import datetime
from difflib import SequenceMatcher
import asyncio

import discord
from discord.ext import commands
from discord.errors import DiscordServerError
from constants import QUESTION_CHANNEL_ID

DATA_PATH = "extensions/threads.json"
KEYWORDS_PATH = "extensions/nostale_keywords.json"

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

INTERROGATIVE_WORDS = ["qui", "que", "quoi", "qu'", "où", "quand", "pourquoi", "comment", "est-ce", "combien", "quel", "quelle", "quels", "quelles", "lequel", "laquelle", "lesquels", "lesquelles"]
INTERROGATIVE_EXPRESSIONS = ["-t-", "-on", "-je", "-tu", "-il", "-elle", "-nous", "-vous", "-ils", "-elles"]

class ThreadManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.threads_data = []
        self.existing_thread_ids = set()
        self.nostale_keywords = self.load_keywords()
        self.load_threads_data()
        self.pending_threads = {}

    def load_keywords(self):
        try:
            if os.path.exists(KEYWORDS_PATH):
                with open(KEYWORDS_PATH, "r") as f:
                    keywords = json.load(f)
                    # logger.info(f"Loaded {len(keywords)} keywords from {KEYWORDS_PATH}")
                    return keywords
            else:
                # logger.warning(f"{KEYWORDS_PATH} not found")
                pass
        except FileNotFoundError:
            # logger.warning(f"{KEYWORDS_PATH} not found")
            pass
        return []

    def is_nostale_related(self, text):
        for keyword in self.nostale_keywords:
            if keyword.lower() in text.lower():
                # logger.debug(f"Keyword match found: {keyword} in text: {text}")
                return True
        return False

    def load_threads_data(self):
        try:
            if os.path.exists(DATA_PATH):
                with open(DATA_PATH, "r") as f:
                    content = f.read().strip()
                    if content:
                        self.threads_data = json.loads(content)
                        self.existing_thread_ids = {thread["id"] for thread in self.threads_data}
                        # logger.info(f"Loaded {len(self.threads_data)} threads from {DATA_PATH}")
                    else:
                        # logger.info(f"{DATA_PATH} is empty, starting with an empty list")
                        pass
        except FileNotFoundError:
            # logger.info(f"{DATA_PATH} not found, starting with an empty list")
            self.threads_data = []

    def save_threads_data(self):
        with open(DATA_PATH, "w") as f:
            json.dump(self.threads_data, f, indent=4)
            # logger.info(f"Saved {len(self.threads_data)} threads to {DATA_PATH}")

    def clean_title(self, title):
        words = title.lower().split()
        cleaned_words = [word for word in words if word not in INTERROGATIVE_WORDS]
        cleaned_title = ' '.join(cleaned_words)
        
        for expr in INTERROGATIVE_EXPRESSIONS:
            cleaned_title = cleaned_title.replace(expr, '')
        
        return cleaned_title.strip()

    def find_similar_threads(self, thread_name, thread_content, current_thread_id):
        clean_thread_name = self.clean_title(thread_name)
        clean_thread_content = self.clean_title(thread_content)
        similar_threads = []
        for thread in self.threads_data:
            if thread["id"] == current_thread_id:
                continue
            clean_existing_name = self.clean_title(thread["name"])
            clean_existing_content = self.clean_title(thread.get("first_message_content", ""))
            title_similarity = SequenceMatcher(None, clean_thread_name, clean_existing_name).ratio()
            content_similarity = SequenceMatcher(None, clean_thread_content, clean_existing_content).ratio()
            combined_similarity = (title_similarity + content_similarity) / 2
            if combined_similarity > 0.5 or self.is_nostale_related(clean_thread_name) or self.is_nostale_related(clean_thread_content):
                thread_with_similarity = thread.copy()
                thread_with_similarity["similarity"] = combined_similarity
                similar_threads.append(thread_with_similarity)
        similar_threads.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_threads

    async def get_first_message(self, thread):
        try:
            async for message in thread.history(limit=1, oldest_first=True):
                return message
        except DiscordServerError as e:
            # logger.error(f"DiscordServerError while fetching first message: {e}")
            await asyncio.sleep(5)  # wait before retrying
            return await self.get_first_message(thread)
        return None

    async def add_thread_info(self, thread):
        first_message = await self.get_first_message(thread)
        thread_info = {
            "id": thread.id,
            "name": thread.name,
            "author_id": thread.owner_id,
            "guild_id": thread.guild.id,
            "channel_id": thread.parent_id,
            "created_at": str(thread.created_at),
            "message_count": thread.message_count,
            "first_message_content": first_message.content if first_message else "",
            "link": f"https://discord.com/channels/{thread.guild.id}/{thread.id}/{thread.id}"
        }

        if thread.id not in self.existing_thread_ids:
            self.threads_data.append(thread_info)
            self.existing_thread_ids.add(thread.id)
            # logger.info(f"Thread info added: {thread_info}")
        else:
            for existing_thread in self.threads_data:
                if existing_thread["id"] == thread.id:
                    existing_thread.update(thread_info)
                    # logger.info(f"Thread info updated: {thread_info}")
                    break
        self.save_threads_data()

    async def delete_thread_info(self, thread_id):
        self.threads_data = [thread for thread in self.threads_data if thread["id"] != thread_id]
        self.existing_thread_ids.discard(thread_id)
        # logger.info(f"Thread info deleted: {thread_id}")
        self.save_threads_data()

    async def fetch_all_threads(self):
        question_channel = self.bot.get_channel(QUESTION_CHANNEL_ID)
        if question_channel is None:
            # logger.error(f"Could not find channel with id {QUESTION_CHANNEL_ID}")
            return
        
        try:
            for thread in question_channel.threads:
                if thread.id not in self.existing_thread_ids:
                    await self.add_thread_info(thread)

            async for thread in question_channel.archived_threads(limit=None):
                if thread.id not in self.existing_thread_ids:
                    await self.add_thread_info(thread)
        except DiscordServerError as e:
            # logger.error(f"DiscordServerError while fetching threads: {e}")
            await asyncio.sleep(5)  # wait before retrying
            await self.fetch_all_threads()

        self.save_threads_data()

    async def cog_load(self):
        # logger.info("Cog loaded successfully")
        await self.fetch_all_threads()

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if thread.parent_id != QUESTION_CHANNEL_ID:
            return

        try:
            await self.add_thread_info(thread)
            self.pending_threads[thread.id] = thread
            self.save_threads_data()
        except DiscordServerError as e:
            # logger.error(f"DiscordServerError on thread create: {e}")
            await asyncio.sleep(5)  # wait before retrying
            await self.on_thread_create(thread)

    @commands.Cog.listener()
    async def on_message(self, message):
        if isinstance(message.channel, discord.Thread):
            if message.channel.parent_id != QUESTION_CHANNEL_ID:
                return
            try:
                if message.channel.id in self.pending_threads and message.author.id == self.pending_threads[message.channel.id].owner_id:
                    await self.add_thread_info(message.channel)
                    self.save_threads_data()
                if message.embeds:
                    for embed in message.embeds:
                        if embed.title == "Titre validé":
                            thread = message.channel
                            async for msg in thread.history(limit=100):
                                if msg.author == self.bot.user and any(embed.title == "Questions similaires triées par pertinence :" for embed in msg.embeds):
                                    return
                            first_message_content = (await self.get_first_message(thread)).content
                            similar_threads = self.find_similar_threads(thread.name, first_message_content, thread.id)
                            if similar_threads:
                                await self.send_paginated_similar_threads(thread, similar_threads)
                                return
            except DiscordServerError as e:
                # logger.error(f"DiscordServerError on message: {e}")
                await asyncio.sleep(5)  # wait before retrying
                await self.on_message(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if isinstance(after.channel, discord.Thread):
            if after.channel.parent_id != QUESTION_CHANNEL_ID:
                return
            try:
                if after.embeds:
                    for embed in after.embeds:
                        if embed.title == "Titre validé":
                            thread = after.channel
                            async for msg in thread.history(limit=100):
                                if msg.author == self.bot.user and any(embed.title == "Questions similaires triées par pertinence :" for embed in msg.embeds):
                                    return
                            first_message_content = (await self.get_first_message(thread)).content
                            similar_threads = self.find_similar_threads(thread.name, first_message_content, thread.id)
                            if similar_threads:
                                await self.send_paginated_similar_threads(thread, similar_threads)
                                return
            except DiscordServerError as e:
                # logger.error(f"DiscordServerError on message edit: {e}")
                await asyncio.sleep(5)  # wait before retrying
                await self.on_message_edit(before, after)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        if thread.parent_id != QUESTION_CHANNEL_ID:
            return
        try:
            await self.delete_thread_info(thread.id)
            self.save_threads_data()
        except DiscordServerError as e:
            # logger.error(f"DiscordServerError on thread delete: {e}")
            await asyncio.sleep(5)  # wait before retrying
            await self.on_thread_delete(thread)

    async def send_paginated_similar_threads(self, thread, similar_threads):
        try:
            # Vérifier si l'embed "Questions similaires triées par pertinence :" existe déjà
            async for msg in thread.history(limit=100):
                if msg.author == self.bot.user and any(embed.title == "Questions similaires triées par pertinence :" for embed in msg.embeds):
                    # logger.info("Embed already exists, not sending a new one")
                    return

            view = SimilarThreadsView(similar_threads)
            embed = view.create_embed(similar_threads[:15], 1, len(view.pages))
            await thread.send(embed=embed, view=view)
        except DiscordServerError as e:
            # logger.error(f"DiscordServerError while sending paginated similar threads: {e}")
            await asyncio.sleep(5)  # wait before retrying
            await self.send_paginated_similar_threads(thread, similar_threads)

class SimilarThreadsView(discord.ui.View):
    def __init__(self, threads):
        super().__init__(timeout=None)
        self.threads = threads
        self.pages = [threads[i:i + 15] for i in range(0, len(threads), 15)]
        self.current_page = 0

        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        if self.current_page > 0:
            self.add_item(PreviousPageButton())
        if self.current_page < len(self.pages) - 1:
            self.add_item(NextPageButton())

    def format_date_french(self, date_str):
        date = datetime.fromisoformat(date_str)
        return date.strftime('%d/%m/%Y')

    def create_embed(self, threads, current_page, max_page):
        description = "\n".join([f"- `{self.format_date_french(t['created_at'])}` : [{t['name']}]({t['link']}) ({t['message_count']} msg)" for t in threads])
        embed = discord.Embed(
            title="Questions similaires triées par pertinence :",
            description=description,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Page {current_page} sur {max_page}")
        return embed

class PreviousPageButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="◀️ Page précédente", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if view:
            view.current_page -= 1
            view.update_buttons()
            embed = view.create_embed(view.pages[view.current_page], view.current_page + 1, len(view.pages))
            await interaction.response.edit_message(embed=embed, view=view)

class NextPageButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Page suivante ▶️", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if view:
            view.current_page += 1
            view.update_buttons()
            embed = view.create_embed(view.pages[view.current_page], view.current_page + 1, len(view.pages))
            await interaction.response.edit_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(ThreadManager(bot))