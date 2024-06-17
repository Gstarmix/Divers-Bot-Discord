import json
import logging
from datetime import datetime
from difflib import SequenceMatcher
import discord
from discord.ext import commands
from constants import QUESTION_CHANNEL_ID

DATA_PATH = "extensions/threads.json"

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ThreadManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.threads_data = []
        self.existing_thread_ids = set()
        self.load_threads_data()

    def load_threads_data(self):
        try:
            with open(DATA_PATH, "r") as f:
                content = f.read().strip()
                if content:
                    self.threads_data = json.loads(content)
                    self.existing_thread_ids = {thread["id"] for thread in self.threads_data}
                    logger.info(f"Loaded {len(self.threads_data)} threads from {DATA_PATH}")
                else:
                    logger.info(f"{DATA_PATH} is empty, starting with an empty list")
        except FileNotFoundError:
            logger.info(f"{DATA_PATH} not found, starting with an empty list")
            self.threads_data = []

    def save_threads_data(self):
        with open(DATA_PATH, "w") as f:
            json.dump(self.threads_data, f, indent=4)
            logger.info(f"Saved {len(self.threads_data)} threads to {DATA_PATH}")

    def find_similar_threads(self, thread_name, author_id):
        similar_threads = []
        for thread in self.threads_data:
            if thread["author_id"] == author_id:
                continue
            similarity = SequenceMatcher(None, thread_name, thread["name"]).ratio()
            if similarity > 0.5:
                thread_link = thread["link"]
                similar_threads.append(f"[{thread['name']}]({thread_link})")
        return similar_threads

    async def add_thread_info(self, thread):
        thread_info = {
            "id": thread.id,
            "name": thread.name,
            "author_id": thread.owner_id,
            "guild_id": thread.guild.id,
            "channel_id": thread.parent_id,
            "created_at": str(thread.created_at),
            "link": f"https://discord.com/channels/{thread.guild.id}/{thread.parent_id}/{thread.id}"
        }

        if thread_info not in self.threads_data:
            self.threads_data.append(thread_info)
            self.existing_thread_ids.add(thread.id)
            logger.info(f"Thread info added: {thread_info}")

    async def fetch_all_threads(self):
        guild = self.bot.get_guild(self.guild_id)
        if guild is None:
            logger.error(f"Could not find guild with id {self.guild_id}")
            return
        
        question_channel = guild.get_channel(QUESTION_CHANNEL_ID)
        if question_channel is None:
            logger.error(f"Could not find channel with id {QUESTION_CHANNEL_ID}")
            return
        
        async for thread in question_channel.threads:
            if thread.id not in self.existing_thread_ids:
                await self.add_thread_info(thread)
                try:
                    await thread.send("Collecting thread data for initialization.")
                    logger.info(f"Posted message in thread {thread.name} ({thread.id})")
                except discord.Forbidden:
                    logger.error(f"Bot does not have permission to post in thread {thread.name} ({thread.id})")
                except discord.HTTPException as e:
                    logger.error(f"Failed to post in thread {thread.name} ({thread.id}): {e}")

        async for thread in question_channel.archived_threads(limit=None):
            if thread.id not in self.existing_thread_ids:
                await self.add_thread_info(thread)
                try:
                    await thread.send("Collecting thread data for initialization.")
                    logger.info(f"Posted message in archived thread {thread.name} ({thread.id})")
                except discord.Forbidden:
                    logger.error(f"Bot does not have permission to post in archived thread {thread.name} ({thread.id})")
                except discord.HTTPException as e:
                    logger.error(f"Failed to post in archived thread {thread.name} ({thread.id}): {e}")

        self.save_threads_data()

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"{self.bot.user} has connected to Discord!")
        self.guild_id = self.bot.guilds[0].id
        await self.fetch_all_threads()

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if thread.parent_id == QUESTION_CHANNEL_ID and thread.id not in self.existing_thread_ids:
            await self.add_thread_info(thread)
            try:
                await thread.send("Collecting thread data for initialization.")
                logger.info(f"Posted message in new thread {thread.name} ({thread.id})")
            except discord.Forbidden:
                logger.error(f"Bot does not have permission to post in thread {thread.name} ({thread.id})")
            except discord.HTTPException as e:
                logger.error(f"Failed to post in thread {thread.name} ({thread.id}): {e}")
            self.save_threads_data()

    @commands.Cog.listener()
    async def on_message(self, message):
        if isinstance(message.channel, discord.Thread):
            await self.add_thread_info(message.channel)
            self.save_threads_data()

async def setup(bot):
    await bot.add_cog(ThreadManager(bot))
