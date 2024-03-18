import json
from datetime import datetime, timedelta
import discord
from discord.ext import commands
from discord.ui import Modal, TextInput, View, Button

from constants import COMMERCES_ID, VENTES_COSMOS_ID, ACHATS_COSMOS_ID, VENTES_NOSFIRE_ID, ACHATS_NOSFIRE_ID, SIGNALEMENT_VENTES_ID, GSTAR_USER_ID

DATA_PATH = "datas/image_forwarder"
user_choices = {}

class ActionsView(discord.ui.View):
    def __init__(self, target_thread_id: int):
        super().__init__(timeout=None)
        self.target_thread_id = target_thread_id

    @discord.ui.button(label="Signaler", style=discord.ButtonStyle.danger, custom_id="report_button_v1")
    async def report(self, interaction: discord.Interaction, button: discord.ui.Button):
        print("Bouton Signaler cliqué")
        modal = ReportModal(message_id=interaction.message.id, channel_id=self.target_thread_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Supprimer", style=discord.ButtonStyle.danger, custom_id="delete_button_v1")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        print("Bouton Supprimer cliqué")
        thread = await interaction.client.fetch_channel(self.target_thread_id)
        if interaction.user.id not in {GSTAR_USER_ID, thread.owner.id}:
            await interaction.response.send_message("Vous n'êtes autorisé à effectuer cette action que dans votre propre vente.", ephemeral=True)
        else:
            await interaction.response.defer(ephemeral=True, thinking=True)
            await interaction.edit_original_response(view=DeleteView(self.target_thread_id, interaction))

class ReportModal(discord.ui.Modal):
    def __init__(self, message_id, channel_id):
        super().__init__(title="Signaler un Message")
        self.message_id = message_id
        self.channel_id = channel_id
        self.add_item(TextInput(label="Raison du signalement", style=discord.TextStyle.paragraph, placeholder="Expliquez pourquoi vous signalez ce message...", custom_id="report_reason", max_length=1024))

    async def on_submit(self, interaction: discord.Interaction):
        report_reason = self.children[0].value
        report_channel = interaction.client.get_channel(SIGNALEMENT_VENTES_ID)
        message_url = f"https://discord.com/channels/{interaction.guild_id}/{self.channel_id}/{self.message_id}"
        await report_channel.send(f"{interaction.user.mention} a signalé ce [message]({message_url}) pour la raison suivante : {report_reason}")
        await interaction.response.send_message("Votre signalement a été envoyé avec succès.", ephemeral=True)

class DeleteView(discord.ui.View):
    def __init__(self, target_thread_id: int, target_interaction: discord.Interaction):
        super().__init__(timeout=None)
        self.target_thread_id = target_thread_id
        self.target_interaction = target_interaction

    @discord.ui.button(label="Confirmer la suppression", style=discord.ButtonStyle.danger, custom_id="confirm_delete")
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=False)
        try:
            target = await interaction.guild.fetch_channel(self.target_thread_id)
            await target.delete()
        except discord.NotFound:
            pass
        await self.target_interaction.message.delete()
        await self.target_interaction.edit_original_response(content="Vente supprimée !", view=None)

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.secondary, custom_id="cancel_delete")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=False)
        await self.target_interaction.edit_original_response(content="Suppression annulée !", view=None)

class CommerceTypeView(View):
    def __init__(self, message: discord.Message, bot: commands.Bot):
        super().__init__(timeout=180)
        self.message = message
        self.bot = bot

    @discord.ui.button(label="Achat", style=discord.ButtonStyle.green, custom_id="buy")
    async def buy(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_choices[self.message.id] = {"type": "achat"}
        await interaction.response.send_message("Veuillez choisir le serveur pour votre achat :", view=ServerChoiceView(self.message.id, self.bot), ephemeral=True)

    @discord.ui.button(label="Vente", style=discord.ButtonStyle.blurple, custom_id="sell")
    async def sell(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_choices[self.message.id] = {"type": "vente"}
        await interaction.response.send_message("Veuillez choisir le serveur pour votre vente :", view=ServerChoiceView(self.message.id, self.bot), ephemeral=True)

class ServerChoiceView(View):
    def __init__(self, message_id: int, bot: commands.Bot):
        super().__init__(timeout=180)
        self.message_id = message_id
        self.bot = bot

    @discord.ui.button(label="Cosmos", style=discord.ButtonStyle.green, custom_id="cosmos")
    async def cosmos(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_choices[self.message_id]["server"] = "cosmos"
        await finalize_choice(interaction, self.message_id, self.bot)

    @discord.ui.button(label="NosFire", style=discord.ButtonStyle.blurple, custom_id="nosfire")
    async def nosfire(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_choices[self.message_id]["server"] = "nosfire"
        await finalize_choice(interaction, self.message_id, self.bot)

async def finalize_choice(interaction: discord.Interaction, message_id: int, bot: commands.Bot):
    choice = user_choices[message_id]
    channel_map = {
        "achat_cosmos": ACHATS_COSMOS_ID,
        "vente_cosmos": VENTES_COSMOS_ID,
        "achat_nosfire": ACHATS_NOSFIRE_ID,
        "vente_nosfire": VENTES_NOSFIRE_ID,
    }
    target_channel_id = channel_map[f"{choice['type']}_{choice['server']}"]
    original_message = await interaction.channel.fetch_message(message_id)

    target_channel = bot.get_channel(target_channel_id)
    if target_channel:
        await target_channel.send(content=original_message.content, files=[await att.to_file() for att in original_message.attachments])
        await interaction.response.send_message("Votre annonce a été correctement redirigée.", ephemeral=True)
        del user_choices[message_id]


class ImageForwarder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.first_post_time_path = f"{DATA_PATH}/first_post_time.json"
        self.message_to_thread_path = f"{DATA_PATH}/message_to_thread.json"
        self.first_post_time, self.message_to_thread = self.load_datas()

    def load_datas(self):
        first_post_time = {}
        message_to_thread = {}
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
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.channel.id in [COMMERCES_ID, VENTES_COSMOS_ID, ACHATS_COSMOS_ID, VENTES_NOSFIRE_ID, ACHATS_NOSFIRE_ID]:
            await message.delete()
            inform_message = f"Vous ne pouvez pas poster directement dans ce salon. Veuillez utiliser le forum approprié <#{COMMERCES_ID}> pour créer votre annonce.\n"
            await message.author.send(inform_message)
            return

        if message.channel.type == discord.ChannelType.public_thread and message.channel.parent_id == COMMERCES_ID:
            await self.handle_post_logic(message)

    async def handle_post_logic(self, message: discord.Message):
        message_count = 0
        async for _ in message.channel.history(limit=None):
            message_count += 1

        is_initial_post = message_count == 1

        current_time = int(datetime.utcnow().timestamp())
        last_post_time = self.first_post_time.get(str(message.channel.id), 0)
        elapsed_time = current_time - last_post_time

        if message.author == message.channel.owner:
            if is_initial_post or elapsed_time >= timedelta(hours=48).total_seconds():
                self.first_post_time[str(message.channel.id)] = current_time
                self.save_datas()
                await message.reply("Quel type de transaction souhaitez-vous réaliser ?", view=CommerceTypeView(message, self.bot))
            else:
                remaining_time = timedelta(seconds=timedelta(hours=48).total_seconds() - elapsed_time)
                time_message = f"🕒 Il reste {self.format_remaining_time(remaining_time)} avant la prochaine actualisation possible de votre annonce."
                await message.reply(time_message, mention_author=True)

    async def repost_message(self, msg: discord.Message, is_initial_post):
        target_channel = self.bot.get_channel(COMMERCES_ID)
        if not target_channel:
            print("Canal cible non trouvé.")
            return

        thread: discord.Thread = msg.channel

        first_message = None
        async for message in thread.history(oldest_first=True, limit=1):
            first_message = message
            break

        if not first_message:
            print("Aucun premier message trouvé.")
            return

        action = "🆕 Nouvelle annonce" if is_initial_post else "♻️ Annonce republiée"
        header = f"{action} par {first_message.author.mention}\n"
        title = f"**Titre :** {thread.name}"
        tags_string = self.get_tags_string(thread)
        content = first_message.content.strip()
        content_formatted = f"**Contenu :**\n> {content}" if content else ""
        
        message_parts = [header, title, tags_string, content_formatted]
        message_to_send = "\n".join(filter(None, message_parts))

        print("Header:", header)
        print("Title:", title)
        print("Tags:", tags_string)
        print("Content:", content_formatted)
        print("Message Complet:", message_to_send)
        print("ActionsView ID:", thread.id)

        actions_view = ActionsView(thread.id)

        try:
            await target_channel.send(
                content=message_to_send, 
                files=[await attachment.to_file() for attachment in first_message.attachments if 'image' in attachment.content_type],
                view=actions_view
            )
        except Exception as e:
            print(f"Erreur lors de l'envoi du message: {e}")

        self.message_to_thread[str(msg.id)] = thread.id
        self.save_datas()

    def determine_target_channel(self, choices):
        channel_map = {
            "achat_cosmos": ACHATS_COSMOS_ID,
            "vente_cosmos": VENTES_COSMOS_ID,
            "achat_nosfire": ACHATS_NOSFIRE_ID,
            "vente_nosfire": VENTES_NOSFIRE_ID,
        }
        return channel_map.get(f"{choices.get('type')}_{choices.get('server')}")

    def get_tags_string(self, thread: discord.Thread) -> str:
        tags_list = thread.applied_tags
        tags_names = ", ".join([f"{tag.emoji} `{tag.name}`" for tag in tags_list])
        return f"**Tags :** {tags_names}" if tags_names else ""

    def format_remaining_time(self, remaining_time: timedelta) -> str:
        days, remainder = divmod(remaining_time.total_seconds(), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(days)}j {int(hours)}h {int(minutes)}min"

async def setup(bot: commands.Bot):
    await bot.add_cog(ImageForwarder(bot))
