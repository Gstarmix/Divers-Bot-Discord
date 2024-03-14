import json
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from discord.ui import Modal, TextInput

from constants import VENTES_ORGA_ID, VENTES_DESOR_ID, SIGNALEMENT_VENTES_ID, GSTAR_USER_ID

DATA_PATH = "datas/image_forwarder"


class ActionsView(discord.ui.View):
    def __init__(self, target_thread_id: int):
        super().__init__(timeout=None)
        self.target_thread_id = target_thread_id

    @discord.ui.button(label="Signaler", style=discord.ButtonStyle.danger, custom_id="report_button_v1")
    async def report(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = ReportModal(message_id=interaction.message.id, channel_id=self.target_thread_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Supprimer", style=discord.ButtonStyle.danger, custom_id="delete_button_v1")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        author = interaction.user
        thread_owner_id = interaction.guild.get_thread(self.target_thread_id).owner.id
        if author.id not in {GSTAR_USER_ID, thread_owner_id}:
            await interaction.response.defer(thinking=False)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        await interaction.edit_original_response(view=DeleteView(self.target_thread_id, interaction))


class ReportModal(discord.ui.Modal):
    def __init__(self, message_id, channel_id):
        super().__init__(title="Signaler un Message")
        self.message_id = message_id
        self.channel_id = channel_id
        self.add_item(discord.ui.TextInput(label="Raison du signalement", style=discord.TextStyle.paragraph, placeholder="Expliquez pourquoi vous signalez ce message...", custom_id="report_reason", max_length=1024))

    async def on_submit(self, interaction: discord.Interaction):
        report_reason = self.children[0].value
        report_channel = interaction.client.get_channel(SIGNALEMENT_VENTES_ID)
        message_url = f"https://discord.com/channels/{interaction.guild_id}/{VENTES_DESOR_ID}/{self.message_id}"
        await report_channel.send(f"{interaction.user.mention} a signalé ce [message]({message_url}) pour la raison suivante : {report_reason}")
        await interaction.response.send_message("Votre signalement a été envoyé avec succès.", ephemeral=True)


class DeleteView(discord.ui.View):
    def __init__(self, target_thread_id: int, target_interaction: discord.Interaction):
        super().__init__(timeout=None)
        self.target_thread_id = target_thread_id
        self.target_interaction = target_interaction

    @discord.ui.button(label="Supprimer", style=discord.ButtonStyle.success, custom_id="deletion_confirm")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=False)
        try:
            target = await interaction.guild.fetch_channel(self.target_thread_id)
            await target.delete()
        except discord.NotFound:
            pass
        await self.target_interaction.message.delete()
        await self.target_interaction.edit_original_response(content="Vente supprimée !", view=None)

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.danger, custom_id="deletion_cancel")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=False)
        await self.target_interaction.edit_original_response(content="Suppression annulée !", view=None)


class ImageForwarder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.first_post_time_path = f"{DATA_PATH}/first_post_time.json"
        self.message_to_thread_path = f"{DATA_PATH}/message_to_thread.json"
        self.first_post_time, self.message_to_thread = self.load_datas()

        for msg_id, thread_id in self.message_to_thread.items():
            self.bot.add_view(ActionsView(thread_id), message_id=int(msg_id))

    def load_datas(self):
        first_post_time: dict[str, int] = {}
        message_to_thread: dict[str, int] = {}
        try:
            with open(self.first_post_time_path, "r") as f:
                first_post_time = json.load(f)
        except FileNotFoundError:
            pass
        try:
            with open(self.message_to_thread_path, "r") as f:
                message_to_thread = json.load(f)
        except FileNotFoundError:
            pass
        return first_post_time, message_to_thread

    def save_datas(self):
        with open(self.first_post_time_path, "w") as f:
            json.dump(self.first_post_time, f)
        with open(self.message_to_thread_path, "w") as f:
            json.dump(self.message_to_thread, f)

    @commands.Cog.listener()
    async def on_thread_create(self, thread: discord.Thread):
        if thread.parent_id == VENTES_ORGA_ID:
            self.first_post_time[str(thread.id)] = int(datetime.utcnow().timestamp())
            self.save_datas()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id == VENTES_DESOR_ID and not message.author.bot:
            await message.delete()
            await message.author.send(f"Vous ne pouvez pas poster dans ce salon. Veuillez vous diriger vers le salon approprié <#{VENTES_ORGA_ID}> et cliquer sur le bouton \"Nouveau post\".\n https://www.zupimages.net/up/24/11/siro.png")
            return

        if message.author.bot or message.channel.type != discord.ChannelType.public_thread:
            return

        if message.channel.parent_id == VENTES_ORGA_ID:
            await self.handle_post_logic(message)

    async def handle_post_logic(self, message: discord.Message) -> None:
        message_count = 0
        async for _ in message.channel.history(limit=None):
            message_count += 1

        is_initial_post = message_count == 1

        thread = message.channel

        current_time = int(datetime.utcnow().timestamp())
        last_post_time = self.first_post_time.get(str(thread.id), 0)
        elapsed_time = current_time - last_post_time

        if message.author == message.channel.owner:
            if is_initial_post or elapsed_time >= timedelta(hours=48).total_seconds():
                self.first_post_time[str(thread.id)] = current_time
                self.save_datas()
                await self.repost_message(message, is_initial_post=is_initial_post)
            else:
                remaining_time = timedelta(seconds=timedelta(hours=48).total_seconds() - elapsed_time)
                await message.reply(f"🕒 Il reste {self.format_remaining_time(remaining_time)} avant la prochaine actualisation possible de votre vente dans <#{VENTES_DESOR_ID}>.", mention_author=True)

    async def repost_message(self, msg: discord.Message, is_initial_post):
        target_channel = self.bot.get_channel(VENTES_DESOR_ID)
        if not target_channel:
            return

        thread: discord.Thread = msg.channel

        try:
            first_message = await thread.fetch_message(thread.id)
        except discord.NotFound:
            return

        action = "🆕 Nouvelle vente" if is_initial_post else "♻️ Vente republiée"
        header = f"{action} par {first_message.author.mention} dans {thread.mention}.\n"
        content = first_message.content.strip()
        tags_string = self.get_tags_string(thread)
        title = f"**Titre :** {thread.name}"
        content_formatted = f"**Contenu :**\n> {content}" if content else ""
        message_parts = [header, title, tags_string, content_formatted]
        message_to_send = "\n".join(filter(None, message_parts))

        actions_view = ActionsView(thread.id)

        msg = await target_channel.send(
            message_to_send, 
            files=[await attachment.to_file() for attachment in first_message.attachments if 'image' in attachment.content_type],
            view=actions_view
        )

        self.first_post_time[str(thread.id)] = int(datetime.utcnow().timestamp())
        self.message_to_thread[str(msg.id)] = thread.id
        self.save_datas()

    def get_tags_string(self, thread: discord.Thread) -> str:
        tags_list = thread.applied_tags
        tags_names = ", ".join([f"{tag.emoji} `{tag.name}`" for tag in tags_list])
        return f"**Tags :** {tags_names}" if tags_names else ""

    def format_remaining_time(self, remaining_time: timedelta) -> str:
        days, remainder = divmod(remaining_time.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(days)}j {int(hours)}h {int(minutes)}min"


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ImageForwarder(bot))
