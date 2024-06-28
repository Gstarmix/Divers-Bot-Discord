import json
import logging
import os
from datetime import datetime
from difflib import SequenceMatcher

import discord
from discord.ext import commands
from constants import QUESTION_CHANNEL_ID
from threading import Lock

DATA_PATH = "extensions/threads"
THREADS_DATA_PATH = f"{DATA_PATH}/threads.json"
PENDING_THREADS_PATH = f"{DATA_PATH}/pending_threads.json"
PAGINATION_STATE_PATH = f"{DATA_PATH}/pagination_state.json"

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

INTERROGATIVE_WORDS = ["qui", "que", "quoi", "qu'", "où", "quand", "pourquoi", "comment", "est-ce", "combien", "quel", "quelle", "quels", "quelles", "lequel", "laquelle", "lesquels", "lesquelles"]
INTERROGATIVE_EXPRESSIONS = ["-t-", "-on", "-je", "-tu", "-il", "-elle", "-nous", "-vous", "-ils", "-elles"]

active_threads = {}
thread_locks = {}

def load_active_threads():
    try:
        if os.path.exists(THREADS_DATA_PATH):
            with open(THREADS_DATA_PATH, "r") as f:
                content = f.read().strip()
                if content:
                    threads_data = json.loads(content)
                    for thread in threads_data:
                        active_threads[thread["id"]] = thread
        logger.info("👍 Active threads loaded from the data file.")
    except Exception as e:
        logger.error(f"❗ Error loading active threads: {e}")

def save_active_threads():
    try:
        with open(THREADS_DATA_PATH, "w") as f:
            json.dump(list(active_threads.values()), f, indent=4)
        logger.info("👍 Active threads saved to the data file.")
    except Exception as e:
        logger.error(f"❗ Error saving active threads: {e}")

def get_thread_lock(thread_id):
    if thread_id not in thread_locks:
        thread_locks[thread_id] = Lock()
    return thread_locks[thread_id]

class ThreadManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.threads_data = []
        self.existing_thread_ids = set()
        self.pending_threads = {}
        self.pagination_state = self.load_pagination_state()
        self.load_threads_data()
        self.load_pending_threads_data()

        for thread_id, thread_data in active_threads.items():
            similar_threads = self.find_similar_threads(thread_data["name"], thread_id)
            current_page = self.pagination_state.get(thread_id, 0)
            self.bot.add_view(SimilarThreadsView(similar_threads, thread_id, self.bot, current_page), message_id=thread_data['message_id'])

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
                thread_with_similarity["link"] = thread_with_similarity.get(
                    "link",
                    f"https://discord.com/channels/{thread['guild_id']}/{thread['id']}/{thread['id']}"
                )
                thread_with_similarity["message_count"] = thread_with_similarity.get("message_count", 0)
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
        save_active_threads()

    async def delete_thread_info(self, thread_id):
        self.threads_data = [thread for thread in self.threads_data if thread["id"] != thread_id]
        self.existing_thread_ids.discard(thread_id)
        if thread_id in active_threads:
            del active_threads[thread_id]
        self.save_threads_data()
        save_active_threads()

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
        load_active_threads()
        self.bot.add_view(SimilarThreadsView([], "default_thread_id", self.bot))

    def save_pagination_state(self, thread_id, current_page):
        pagination_state_path = PAGINATION_STATE_PATH
        try:
            if os.path.exists(pagination_state_path):
                with open(pagination_state_path, "r") as f:
                    pagination_state = json.loads(f.read().strip() or "{}")
            else:
                pagination_state = {}

            pagination_state[thread_id] = current_page

            with open(pagination_state_path, "w") as f:
                json.dump(pagination_state, f, indent=4)
        except Exception as e:
            logger.error(f"❗ Error saving pagination state: {e}")

    def load_pagination_state(self):
        pagination_state_path = PAGINATION_STATE_PATH
        try:
            if os.path.exists(pagination_state_path):
                with open(pagination_state_path, "r") as f:
                    return json.loads(f.read().strip() or "{}")
            return {}
        except Exception as e:
            logger.error(f"❗ Error loading pagination state: {e}")
            return {}

    async def send_paginated_similar_threads(self, thread, similar_threads, current_page=0):
        view = SimilarThreadsView(similar_threads, thread.id, self.bot, current_page)
        embed = view.create_embed(similar_threads[:15], current_page + 1, len(view.pages))
        await thread.send(embed=embed, view=view)
        self.save_pagination_state(thread.id, current_page)

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
            "created_at": str(thread.created_at),
            "message_id": thread.last_message_id
        }
        active_threads[thread.id] = self.pending_threads[thread.id]
        self.save_pending_threads_data()
        self.save_threads_data()
        save_active_threads()

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
                save_active_threads()
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
        save_active_threads()

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
        if thread.id in active_threads:
            del active_threads[thread.id]
        self.save_threads_data()
        save_active_threads()

class SimilarThreadsView(discord.ui.View):
    def __init__(self, threads, thread_id, bot, current_page=0):
        super().__init__(timeout=None)
        self.threads = threads
        self.pages = [threads[i:i + 15] for i in range(0, len(threads), 15)]
        self.current_page = current_page
        self.thread_id = thread_id
        self.bot = bot

        self.update_buttons()

    def update_buttons(self):
        self.clear_items()
        if self.current_page > 0:
            self.add_item(PreviousPageButton(custom_id=f'persistent_view:previous_page:{self.thread_id}:{self.current_page}'))
        if self.current_page < len(self.pages) - 1:
            self.add_item(NextPageButton(custom_id=f'persistent_view:next_page:{self.thread_id}:{self.current_page}'))

    def format_date_french(self, date_str):
        date = datetime.fromisoformat(date_str)
        return date.strftime('%d/%m/%Y')

    def create_embed(self, threads, current_page, max_page):
        description = "\n".join([
            f"- `{self.format_date_french(t['created_at'])}` : [{t['name']}]({t.get('link', '#')}) ({t.get('message_count', 0)} msg)"
            for t in threads
        ])
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
            view.current_page = max(view.current_page - 1, 0)
            view.update_buttons()
            embed = view.create_embed(view.pages[view.current_page], view.current_page + 1, len(view.pages))
            await interaction.response.edit_message(embed=embed, view=view)
            view.bot.get_cog("ThreadManager").save_pagination_state(view.thread_id, view.current_page)
            print(f"Previous page button clicked. New current page: {view.current_page}")

class NextPageButton(discord.ui.Button):
    def __init__(self, custom_id: str):
        super().__init__(label="Page suivante ▶️", style=discord.ButtonStyle.secondary, custom_id=custom_id)

    async def callback(self, interaction: discord.Interaction):
        view = self.view
        if view:
            view.current_page = min(view.current_page + 1, len(view.pages) - 1)
            view.update_buttons()
            embed = view.create_embed(view.pages[view.current_page], view.current_page + 1, len(view.pages))
            await interaction.response.edit_message(embed=embed, view=view)
            view.bot.get_cog("ThreadManager").save_pagination_state(view.thread_id, view.current_page)
            print(f"Next page button clicked. New current page: {view.current_page}")

async def setup(bot):
    await bot.add_cog(ThreadManager(bot))
