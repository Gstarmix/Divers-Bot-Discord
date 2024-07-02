import logging
import discord
from discord.ext import commands
import aiohttp
import json
import os

from constants import QUESTION_CHANNEL_ID, ESTIMATION_CHANNEL_ID, ACTIVITES_ID

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

DATA_PATH = "extensions/auto_repost_on_delete_data.json"

class AutoRepostOnDelete(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.forum_channel_ids = {QUESTION_CHANNEL_ID, ESTIMATION_CHANNEL_ID, ACTIVITES_ID}
        self.thread_to_message = {}
        self.saved_attachments = self.load_thread_data()

    def load_thread_data(self):
        if os.path.exists(DATA_PATH):
            with open(DATA_PATH, 'r') as file:
                return json.load(file)
        return {}

    def save_thread_data(self):
        with open(DATA_PATH, 'w') as file:
            json.dump(self.saved_attachments, file)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        logger.debug(f"Message received: {message.content} in thread {message.channel.id}")
        if isinstance(message.channel, discord.Thread) and message.channel.parent_id in self.forum_channel_ids:
            logger.debug(f"Message is in a tracked forum channel and is a thread")
            thread_id = message.channel.id
            if thread_id not in self.thread_to_message:
                self.thread_to_message[thread_id] = message.id
                self.saved_attachments[message.id] = await self.download_and_save_attachments(message.attachments, thread_id)
                self.save_thread_data()
                logger.debug(f"First message in thread {thread_id} registered with ID {message.id}")
                logger.debug(f"Attachments saved: {self.saved_attachments[message.id]}")

    async def download_and_save_attachments(self, attachments, thread_id):
        attachment_paths = []
        for attachment in attachments:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(attachment.url) as response:
                        if response.status == 200:
                            data = await response.read()
                            filename = attachment.filename
                            folder_path = os.path.join("attachments", str(thread_id))
                            os.makedirs(folder_path, exist_ok=True)
                            file_path = os.path.join(folder_path, filename)
                            with open(file_path, 'wb') as f:
                                f.write(data)
                            attachment_paths.append(file_path)
                            logger.debug(f"Downloaded and saved attachment: {filename}")
                        else:
                            logger.error(f"Failed to download attachment: {attachment.url}, status code: {response.status}")
            except Exception as e:
                logger.error(f"Error downloading attachment: {attachment.url}, error: {e}")
        return attachment_paths

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        logger.debug(f"Message deleted: {message.id} in thread {message.channel.id}")
        if isinstance(message.channel, discord.Thread):
            thread = message.channel
            if thread.id in self.thread_to_message and self.thread_to_message[thread.id] == message.id:
                logger.debug(f"Deleted message is the first message of the thread {thread.id}")
                await self.repost_message(message, thread.id)
            else:
                logger.debug(f"Deleted message is not the first message or thread is not tracked")

    async def repost_message(self, message: discord.Message, thread_id: int):
        logger.debug(f"Reposting message {message.id} in thread {thread_id}")
        user = message.author
        content = message.content or "*No content*"
        attachment_paths = self.saved_attachments.get(message.id, [])

        files = [discord.File(path) for path in attachment_paths]

        logger.debug(f"Files to repost: {files}")

        thread = await self.bot.fetch_channel(thread_id)
        webhooks = await thread.parent.webhooks()
        webhook = discord.utils.find(lambda wh: wh.user == thread.guild.me, webhooks)
        if webhook is None:
            webhook = await thread.parent.create_webhook(name="AutoReposter", reason="Repost deleted first messages")
            logger.debug(f"Created new webhook for {thread.parent.id}")

        kwargs = {
            "content": f"{user.mention} a supprimé ce message : {content}",
            "username": user.display_name,
            "avatar_url": user.display_avatar.url,
            "wait": True,
            "thread": thread,
            "files": files,
        }

        logger.debug(f"Sending webhook with kwargs: {kwargs}")
        await webhook.send(**kwargs)
        logger.debug(f"Message reposted in thread {thread_id}")

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoRepostOnDelete(bot))
    logger.info("AutoRepostOnDelete cog loaded")
