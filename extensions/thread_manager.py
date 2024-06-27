import json
import logging
import os
from datetime import datetime
from difflib import SequenceMatcher

import discord
from discord.ext import commands
from constants import QUESTION_CHANNEL_ID

DATA_PATH = "extensions/threads"
THREADS_DATA_PATH = f"{DATA_PATH}/threads.json"
PENDING_THREADS_PATH = f"{DATA_PATH}/pending_threads.json"

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

INTERROGATIVE_WORDS = ["qui", "que", "quoi", "qu'", "où", "quand", "pourquoi", "comment", "est-ce", "combien", "quel", "quelle", "quels", "quelles", "lequel", "laquelle", "lesquels", "lesquelles"]
INTERROGATIVE_EXPRESSIONS = ["-t-", "-on", "-je", "-tu", "-il", "-elle", "-nous", "-vous", "-ils", "-elles"]

class ThreadManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.threads_data = []
        self.existing_thread_ids = set()
        self.pending_threads = {}
        self.load_threads_data()
        self.load_pending_threads_data()

    def load_threads_data(self):
        try:
            if os.path.exists(THREADS_DATA_PATH):
                with open(THREADS_DATA_PATH, "r") as f:
                    content = f.read().strip()
                    if content:
                        self.threads_data = json.loads(content)
                        self.existing_thread_ids = {thread["id"] for thread in self.threads_data}
        except FileNotFoundError:
            self.threads_data = []

    def save_threads_data(self):
        os.makedirs(DATA_PATH, exist_ok=True)
        with open(THREADS_DATA_PATH, "w") as f:
            json.dump(self.threads_data, f, indent=4)

    def load_pending_threads_data(self):
        try:
            if os.path.exists(PENDING_THREADS_PATH):
                with open(PENDING_THREADS_PATH, "r") as f:
                    content = f.read().strip()
                    if content:
                        self.pending_threads = json.loads(content)
        except FileNotFoundError:
            self.pending_threads = {}

    def save_pending_threads_data(self):
        os.makedirs(DATA_PATH, exist_ok=True)
        with open(PENDING_THREADS_PATH, "w") as f:
            json.dump(self.pending_threads, f, indent=4)

    def clean_title(self, title):
        words = title.lower().split()
        cleaned_words = [word for word in words if word not in INTERROGATIVE_WORDS]
        cleaned_title = ' '.join(cleaned_words)
        
        for expr in INTERROGATIVE_EXPRESSIONS:
            cleaned_title = cleaned_title.replace(expr, '')
        
        return cleaned_title.strip()

    def find_similar_threads(self, thread_name, current_thread_id):
        clean_thread_name = self.clean_title(thread_name)
        similar_threads = []
        for thread in self.threads_data:
            if thread["id"] == current_thread_id:
                continue
            clean_existing_name = self.clean_title(thread["name"])
            similarity = SequenceMatcher(None, clean_thread_name, clean_existing_name).ratio()
            if similarity > 0.5:
                thread_with_similarity = thread.copy()
                thread_with_similarity["similarity"] = similarity
                similar_threads.append(thread_with_similarity)
        similar_threads.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_threads

    async def add_thread_info(self, thread):
        thread_info = {
            "id": thread.id,
            "name": thread.name,
            "author_id": thread.owner_id,
            "guild_id": thread.guild.id,
            "channel_id": thread.parent_id,
            "created_at": str(thread.created_at),
            "message_count": thread.message_count,
            "link": f"https://discord.com/channels/{thread.guild.id}/{thread.id}/{thread.id}"
        }

        if thread.id not in self.existing_thread_ids:
            self.threads_data.append(thread_info)
            self.existing_thread_ids.add(thread.id)
        else:
            for existing_thread in self.threads_data:
                if existing_thread["id"] == thread.id:
                    existing_thread.update(thread_info)
                    break
        self.save_threads_data()

    async def delete_thread_info(self, thread_id):
        self.threads_data = [thread for thread in self.threads_data if thread["id"] != thread_id]
        self.existing_thread_ids.discard(thread_id)
        self.save_threads_data()

    async def fetch_all_threads(self):
        question_channel = self.bot.get_channel(QUESTION_CHANNEL_ID)
        if question_channel is None:
            return
        
        for thread in question_channel.threads:
            if thread.id not in self.existing_thread_ids:
                await self.add_thread_info(thread)

        async for thread in question_channel.archived_threads(limit=None):
            if thread.id not in self.existing_thread_ids:
                await self.add_thread_info(thread)

        self.save_threads_data()

    async def cog_load(self):
        await self.fetch_all_threads()
        self.bot.add_view(SimilarThreadsView([]))

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if thread.parent_id != QUESTION_CHANNEL_ID:
            return

        await self.add_thread_info(thread)
        self.pending_threads[thread.id] = {
            "id": thread.id,
            "name": thread.name,
            "author_id": thread.owner_id,
            "guild_id": thread.guild.id,
            "channel_id": thread.parent_id,
            "created_at": str(thread.created_at)
        }
        self.save_pending_threads_data()
        self.save_threads_data()

    @commands.Cog.listener()
    async def on_message(self, message):
        if isinstance(message.channel, discord.Thread):
            if message.channel.parent_id != QUESTION_CHANNEL_ID:
                return
            if message.channel.id in self.pending_threads and message.author.id == self.pending_threads[message.channel.id]["author_id"]:
                await self.add_thread_info(message.channel)
                del self.pending_threads[message.channel.id]
                self.save_pending_threads_data()
                self.save_threads_data()
            if message.embeds:
                for embed in message.embeds:
                    if embed.title == "Titre validé":
                        thread = message.channel
                        async for msg in thread.history(limit=100):
                            if msg.author == self.bot.user and any(embed.title == "Questions similaires triées par pertinence :" for embed in msg.embeds):
                                return
                        similar_threads = self.find_similar_threads(thread.name, thread.id)
                        if similar_threads:
                            await self.send_paginated_similar_threads(thread, similar_threads)
                            return

    @commands.Cog.listener()
    async def on_thread_update(self, before, after):
        if before.parent_id != QUESTION_CHANNEL_ID:
            return
        
        await self.add_thread_info(after)
        self.save_threads_data()

        similar_threads = self.find_similar_threads(after.name, after.id)
        if similar_threads:
            async for msg in after.history(limit=100):
                if msg.author == self.bot.user and any(embed.title == "Questions similaires triées par pertinence :" for embed in msg.embeds):
                    return
            await self.send_paginated_similar_threads(after, similar_threads)

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        if thread.parent_id != QUESTION_CHANNEL_ID:
            return
        await self.delete_thread_info(thread.id)
        self.save_threads_data()

    async def send_paginated_similar_threads(self, thread, similar_threads):
        view = SimilarThreadsView(similar_threads)
        embed = view.create_embed(similar_threads[:15], 1, len(view.pages))
        await thread.send(embed=embed, view=view)

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
            self.add_item(PreviousPageButton(custom_id=f'persistent_view:previous_page:{self.current_page}'))
        if self.current_page < len(self.pages) - 1:
            self.add_item(NextPageButton(custom_id=f'persistent_view:next_page:{self.current_page}'))

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
    def __init__(self, custom_id: str):
        super().__init__(label="◀️ Page précédente", style=discord.ButtonStyle.secondary, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if view:
            view.current_page -= 1
            view.update_buttons()
            embed = view.create_embed(view.pages[view.current_page], view.current_page + 1, len(view.pages))
            await interaction.response.edit_message(embed=embed, view=view)

class NextPageButton(discord.ui.Button):
    def __init__(self, custom_id: str):
        super().__init__(label="Page suivante ▶️", style=discord.ButtonStyle.secondary, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if view:
            view.current_page += 1
            view.update_buttons()
            embed = view.create_embed(view.pages[view.current_page], view.current_page + 1, len(view.pages))
            await interaction.response.edit_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(ThreadManager(bot))
