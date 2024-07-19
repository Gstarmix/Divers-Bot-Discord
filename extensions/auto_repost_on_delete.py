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
                data = json.load(file)
                self.thread_to_message = {int(thread_id): msg_id for thread_id, msg_id in data.get("thread_to_message", {}).items()}
                return data.get("saved_attachments", {})
        return {}

    def save_thread_data(self):
        data = {
            "thread_to_message": self.thread_to_message,
            "saved_attachments": self.saved_attachments
        }
        with open(DATA_PATH, 'w') as file:
            json.dump(data, file)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if isinstance(message.channel, discord.Thread) and message.channel.parent_id in self.forum_channel_ids:
            thread_id = message.channel.id
            if thread_id not in self.thread_to_message:
                self.thread_to_message[thread_id] = message.id
                self.saved_attachments[message.id] = await self.download_and_save_attachments(message.attachments, thread_id)
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
                        else:
                            logger.error(f"Failed to download attachment: {attachment.url}, status code: {response.status}")
            except Exception as e:
                logger.error(f"Error downloading attachment: {attachment.url}, error: {e}")
        return attachment_paths

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if isinstance(message.channel, discord.Thread):
            thread = message.channel
            if thread.id in self.thread_to_message and self.thread_to_message[thread.id] == message.id:
                await self.repost_message(message, thread.id)
            elif message.id in self.saved_attachments:
                await self.repost_message_from_data(thread.id, message.id)

    async def repost_message(self, message: discord.Message, thread_id: int):
        user = message.author
        content = message.content or "*No content*"
        attachment_paths = self.saved_attachments.get(message.id, [])

        thread = await self.bot.fetch_channel(thread_id)
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

    async def repost_message_from_data(self, thread_id: int, message_id: int):
        attachment_paths = self.saved_attachments.get(message_id, [])
        thread = await self.bot.fetch_channel(thread_id)
        webhooks = await thread.parent.webhooks()
        webhook = discord.utils.find(lambda wh: wh.user == thread.guild.me, webhooks)
        if webhook is None:
            webhook = await thread.parent.create_webhook(name="AutoReposter")

        files = [(f"attachment://{os.path.basename(path)}", discord.File(path, filename=os.path.basename(path))) for path in attachment_paths]
        
        if files:
            image_urls, discord_files = zip(*files)
            view = ImageNavigator(list(image_urls), "Le premier message de ce fil a été supprimé", "*Contenu non disponible*", discord.Color.red(), list(discord_files))
            embed = view.update_embed(view.current_image)
            await webhook.send(
                username="Deleted User",
                avatar_url="",
                thread=thread,
                embed=embed,
                view=view,
                file=discord_files[0]
            )
        else:
            embed = discord.Embed(
                title="Le premier message de ce fil a été supprimé",
                description="*Contenu non disponible*",
                color=discord.Color.red()
            )
            await webhook.send(
                username="Deleted User",
                avatar_url="",
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
