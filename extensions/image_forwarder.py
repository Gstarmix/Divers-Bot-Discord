from datetime import datetime, timedelta
import json
import discord
from discord.ext import commands
from discord.ui import Modal, TextInput
from constants import VENTES_ORGA_ID, VENTES_DESOR_ID, SIGNALEMENT_VENTES_ID

DATA_PATH = "datas/image_forwarder"

class ImageForwarder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.first_post_time_path = f"{DATA_PATH}/first_post_time.json"
        self.first_post_time = self.load_first_post_time()

    def load_first_post_time(self):
        try:
            with open(self.first_post_time_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_first_post_time(self):
        with open(self.first_post_time_path, "w") as f:
            json.dump(self.first_post_time, f)

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if thread.parent_id == VENTES_ORGA_ID:
            self.first_post_time[str(thread.id)] = datetime.utcnow().timestamp()
            self.save_first_post_time()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == VENTES_DESOR_ID and not message.author.bot:
            await message.delete()
            await message.author.send(f"Vous ne pouvez pas poster dans ce salon. Veuillez vous diriger vers le salon approprié <#{VENTES_ORGA_ID}> et cliquer sur le bouton \"Nouveau post\".\n https://www.zupimages.net/up/24/11/siro.png")
            return

        if message.author.bot or message.channel.type != discord.ChannelType.public_thread:
            return

        thread_id = str(message.channel.id)
        if message.channel.parent_id == VENTES_ORGA_ID:
            await self.handle_post_logic(message, thread_id)

    async def handle_post_logic(self, message, thread_id):
        message_count = 0
        async for _ in message.channel.history(limit=None):
            message_count += 1

        is_initial_post = message_count == 1

        current_time = datetime.utcnow().timestamp()
        last_post_time = self.first_post_time.get(thread_id, 0)
        elapsed_time = current_time - last_post_time

        if message.author == message.channel.owner:
            if is_initial_post or elapsed_time >= timedelta(hours=48).total_seconds():
                self.first_post_time[thread_id] = current_time
                self.save_first_post_time()
                await self.repost_message(message.channel, is_initial_post=is_initial_post)
            else:
                remaining_time = timedelta(seconds=timedelta(hours=48).total_seconds() - elapsed_time)
                await message.reply(f"🕒 Il reste {self.format_remaining_time(remaining_time)} avant la prochaine actualisation possible de votre vente dans <#{VENTES_DESOR_ID}>.", mention_author=True)

    async def repost_message(self, thread, is_initial_post):
        target_channel = self.bot.get_channel(VENTES_DESOR_ID)
        if not target_channel:
            return

        async for first_message in thread.history(oldest_first=True, limit=1):
            action = "🆕 Nouvelle vente" if is_initial_post else "♻️ Vente republiée"
            header = f"{action} par {first_message.author.mention} dans <#{thread.id}>\n"
            
            content = first_message.content.strip()
            tags_string = self.get_tags_string(first_message)
            title = f"**Titre :** {thread.name}"
            content_formatted = f"**Contenu :**\n> {content}" if content else ""
            
            message_parts = [header, title, tags_string, content_formatted]
            message_to_send = "\n".join(filter(None, message_parts))
            
            sent_message = await target_channel.send(message_to_send, files=[await att.to_file() for att in first_message.attachments if 'image' in att.content_type], view=ReportButton(message_id=first_message.id, channel_id=thread.id))
            break

    def get_tags_string(self, message):
        tags_list = message.channel.applied_tags
        tags_names = ", ".join([f"{tag.emoji} `{tag.name}`" for tag in tags_list]) if tags_list else ""
        return f"**Tags :** {tags_names}" if tags_names else ""

    def format_remaining_time(self, remaining_time):
        days, remainder = divmod(remaining_time.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(days)}j {int(hours)}h {int(minutes)}min"

class ReportModal(discord.ui.Modal):
    def __init__(self, message_id, channel_id, *args, **kwargs):
        super().__init__(title="Signaler un Message", *args, **kwargs)
        self.message_id = message_id
        self.channel_id = channel_id
        self.add_item(discord.ui.TextInput(label="Raison du signalement", style=discord.TextStyle.paragraph, placeholder="Expliquez pourquoi vous signalez ce message.", custom_id="report_reason", max_length=1024))

    async def on_submit(self, interaction: discord.Interaction):
        report_reason = self.children[0].value
        report_channel = interaction.client.get_channel(SIGNALEMENT_VENTES_ID)
        message_url = f"https://discord.com/channels/{interaction.guild_id}/{VENTES_DESOR_ID}/{self.message_id}"
        await report_channel.send(f"{interaction.user.mention} a signalé ce [message]({message_url}) pour la raison suivante : {report_reason}")
        await interaction.response.send_message("Votre signalement a été envoyé avec succès.", ephemeral=True)

class ReportButton(discord.ui.View):
    def __init__(self, message_id, channel_id):
        super().__init__()
        self.message_id = message_id
        self.channel_id = channel_id

    @discord.ui.button(label="Signaler", style=discord.ButtonStyle.danger, custom_id="report_button")
    async def report(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ReportModal(message_id=self.message_id, channel_id=self.channel_id)
        await interaction.response.send_modal(modal)

async def setup(bot):
    await bot.add_cog(ImageForwarder(bot))
