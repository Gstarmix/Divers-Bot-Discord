import logging
import discord
from discord.ext import commands
import aiohttp
import json
import os
import asyncio

from constants import QUESTION_CHANNEL_ID, ESTIMATION_CHANNEL_ID, ACTIVITES_ID

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_PATH = "extensions/auto_repost_on_delete_data.json"

class AutoRepostOnDelete(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.forum_channel_ids = {QUESTION_CHANNEL_ID, ESTIMATION_CHANNEL_ID, ACTIVITES_ID}
        self.saved_attachments = self.load_thread_data()
        self.bot.loop.create_task(self.fetch_all_threads())

    def load_thread_data(self):
        if os.path.exists(DATA_PATH):
            with open(DATA_PATH, 'r') as file:
                content = file.read().strip()
                if content:
                    return json.loads(content)
                else:
                    return {}
        return {}

    def save_thread_data(self):
        with open(DATA_PATH, 'w') as file:
            json.dump(self.saved_attachments, file)

    async def get_first_message(self, thread):
        async for message in thread.history(limit=1, oldest_first=True):
            return message
        return None

    async def fetch_all_threads(self):
        await self.bot.wait_until_ready()  # Assure que le bot est prêt avant de commencer
        for channel_id in self.forum_channel_ids:
            channel = self.bot.get_channel(channel_id)
            if channel is None:
                continue

            try:
                for thread in channel.threads:
                    if str(thread.id) not in self.saved_attachments:
                        await self.add_thread_info(thread)

                async for thread in channel.archived_threads(limit=None):
                    if str(thread.id) not in self.saved_attachments:
                        await self.add_thread_info(thread)
            except Exception as e:
                await asyncio.sleep(5)
                await self.fetch_all_threads()

    async def add_thread_info(self, thread):
        first_message = await self.get_first_message(thread)
        if first_message:
            attachment_paths = await self.download_and_save_attachments(first_message.attachments, thread.id)
            self.saved_attachments[str(thread.id)] = {
                "content": first_message.content,
                "author_id": first_message.author.id,
                "attachments": attachment_paths
            }
            self.save_thread_data()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if isinstance(message.channel, discord.Thread) and message.channel.parent_id in self.forum_channel_ids:
            thread_id = str(message.channel.id)
            if thread_id not in self.saved_attachments:
                attachment_paths = await self.download_and_save_attachments(message.attachments, message.channel.id)
                self.saved_attachments[thread_id] = {
                    "content": message.content,
                    "author_id": message.author.id,
                    "attachments": attachment_paths
                }
                self.save_thread_data()

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
            except Exception as e:
                pass
        return attachment_paths

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if isinstance(message.channel, discord.Thread):
            thread_id = str(message.channel.id)
            if thread_id in self.saved_attachments and self.saved_attachments[thread_id]["content"] == message.content:
                await self.repost_message(message, thread_id)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if isinstance(after.channel, discord.Thread) and after.channel.parent_id in self.forum_channel_ids:
            thread_id = str(after.channel.id)
            if thread_id in self.saved_attachments:
                self.saved_attachments[thread_id]["content"] = after.content
                attachment_paths = await self.download_and_save_attachments(after.attachments, after.channel.id)
                self.saved_attachments[thread_id]["attachments"] = attachment_paths
                self.save_thread_data()

    @commands.Cog.listener()
    async def on_thread_delete(self, thread):
        if thread.parent_id in self.forum_channel_ids:
            self.saved_attachments.pop(str(thread.id), None)
            self.save_thread_data()

    async def repost_message(self, message: discord.Message, thread_id: str):
        user_id = self.saved_attachments[thread_id]["author_id"]
        user = await self.bot.fetch_user(user_id)
        content = self.saved_attachments[thread_id]["content"]
        attachment_paths = self.saved_attachments.get(thread_id, {}).get("attachments", [])

        thread = await self.bot.fetch_channel(int(thread_id))
        webhooks = await thread.parent.webhooks()
        webhook = discord.utils.find(lambda wh: wh.user == thread.guild.me, webhooks)
        if webhook is None:
            webhook = await thread.parent.create_webhook(name="AutoReposter")

        files = [(f"attachment://{os.path.basename(path)}", discord.File(path, filename=os.path.basename(path))) for path in attachment_paths]

        if files:
            image_urls, discord_files = zip(*files)
            view = ImageNavigator(list(image_urls), "Le premier message de ce fil a été supprimé", content, discord.Color.red(), list(discord_files))
            embed = view.update_embed(view.current_image)
            await webhook.send(
                username=user.display_name,
                avatar_url=user.display_avatar.url,
                thread=thread,
                embed=embed,
                view=view,
                file=discord_files[0]
            )
        else:
            embed = discord.Embed(
                title="Le premier message de ce fil a été supprimé",
                description=f"{content}",
                color=discord.Color.red()
            )
            await webhook.send(
                username=user.display_name,
                avatar_url=user.display_avatar.url,
                thread=thread,
                embed=embed
            )

class ImageNavigator(discord.ui.View):
    def __init__(self, images: list, title: str, description: str, color: discord.Color, files: list = None):
        super().__init__(timeout=None)
        self.images = images
        self.files = files
        self.current_image = 0
        self.title = title
        self.description = description
        self.color = color

    def update_embed(self, image_index):
        embed = discord.Embed(title=self.title, description=self.description, color=self.color)
        embed.set_image(url=self.images[image_index])
        embed.set_footer(text=f"{image_index + 1} / {len(self.images)}")
        return embed

    @discord.ui.button(label="◀️ Précédent", style=discord.ButtonStyle.grey, custom_id="previous_image")
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_image = (self.current_image - 1) % len(self.images)
        embed = self.update_embed(self.current_image)
        await interaction.response.edit_message(embed=embed, view=self, attachments=[self.files[self.current_image]] if self.files else None)

    @discord.ui.button(label="Suivant ▶️", style=discord.ButtonStyle.grey, custom_id="next_image")
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_image = (self.current_image + 1) % len(self.images)
        embed = self.update_embed(self.current_image)
        await interaction.response.edit_message(embed=embed, view=self, attachments=[self.files[self.current_image]] if self.files else None)

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoRepostOnDelete(bot))
