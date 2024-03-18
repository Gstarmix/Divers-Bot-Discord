import json
from datetime import datetime, timedelta
from typing import Callable, Awaitable
from functools import partial

import discord
from discord.ext import commands
from discord.ui import Modal, TextInput, View, Button

from constants import (
    COMMERCES_ID, VENTES_COSMOS_ID, ACHATS_COSMOS_ID, VENTES_NOSFIRE_ID, ACHATS_NOSFIRE_ID,
    SIGNALEMENT_VENTES_ID, GSTAR_USER_ID, ACTIVITES_ID, FAMILLES_COSMOS_ID, RAIDS_COSMOS_ID,
    LEVELING_COSMOS_ID, GROUPE_XP_COSMOS_ID, FAMILLES_NOSFIRE_ID, RAIDS_NOSFIRE_ID,
    LEVELING_NOSFIRE_ID, GROUPE_XP_NOSFIRE_ID
)

DATA_PATH = "datas/image_forwarder"
user_choices: dict[int, dict[str, str]] = {}


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
        self.add_item(TextInput(label="Raison du signalement", style=discord.TextStyle.paragraph, placeholder="Expliquez pourquoi vous signalez ce message...",
                                custom_id="report_reason", max_length=1024))

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
    def __init__(self, message: discord.Message, callback: Callable[[], Awaitable[None]]):
        super().__init__(timeout=None)
        self.message = message
        self.callback = callback

    @discord.ui.button(label="Achat", style=discord.ButtonStyle.green, custom_id="buy")
    async def buy(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_choices[self.message.id] = {"type": "achat"}
        await interaction.response.send_message("Veuillez choisir le serveur pour votre achat :", view=ServerChoiceView(self.message, self.callback),
                                                ephemeral=True)

    @discord.ui.button(label="Vente", style=discord.ButtonStyle.blurple, custom_id="sell")
    async def sell(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_choices[self.message.id] = {"type": "vente"}
        await interaction.response.send_message("Veuillez choisir le serveur pour votre vente :", view=ServerChoiceView(self.message, self.callback),
                                                ephemeral=True)


class ServerChoiceView(View):
    def __init__(self, message: discord.Message, callback: Callable[[], Awaitable[None]], context: str):
        super().__init__(timeout=None)
        self.message = message
        self.callback = callback
        self.context = context

    @discord.ui.button(label="Cosmos", style=discord.ButtonStyle.green, custom_id="cosmos")
    async def cosmos(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_choices[self.message.id] = {"server": "cosmos", "context": self.context}
        await self.callback()
        await interaction.response.send_message("Votre annonce a été correctement redirigée.", ephemeral=True)

    @discord.ui.button(label="NosFire", style=discord.ButtonStyle.blurple, custom_id="nosfire")
    async def nosfire(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_choices[self.message.id] = {"server": "nosfire", "context": self.context}
        await self.callback()
        await interaction.response.send_message("Votre annonce a été correctement redirigée.", ephemeral=True)

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
        if message.author.bot or not message.channel.type == discord.ChannelType.public_thread:
            return

        message_count = 0
        async for _ in message.channel.history(limit=None):
            message_count += 1
        is_initial_post = message_count == 1

        current_time = int(datetime.utcnow().timestamp())
        last_post_time = self.first_post_time.get(str(message.channel.id), 0)
        elapsed_time = current_time - last_post_time

        if message.channel.parent_id == COMMERCES_ID:
            if message.author == message.channel.owner:
                if is_initial_post or elapsed_time >= timedelta(hours=48).total_seconds():
                    self.first_post_time[str(message.channel.id)] = current_time
                    self.save_datas()
                    await message.reply("Quel type de transaction souhaitez-vous réaliser ?", view=ServerChoiceView(message, partial(self.repost_message, message, True), "commerce"))
                else:
                    remaining_time = timedelta(seconds=timedelta(hours=48).total_seconds() - elapsed_time)
                    time_message = f"🕒 Il reste {self.format_remaining_time(remaining_time)} avant la prochaine actualisation possible de votre annonce."
                    await message.reply(time_message, mention_author=True)
        elif message.channel.parent_id == ACTIVITES_ID:
            detected_tags = [tag.name for tag in message.tags]
            if any(tag in detected_tags for tag in ['présentation-famille', 'recherche-famille', 'recherche-raid', 'recherche-leveling', 'recherche-groupe-xp']):
                await message.reply("Sur quel serveur souhaitez-vous poster votre activité ?", view=ServerChoiceView(message, partial(self.repost_message, message, True), "activité"))
                await message.reply(time_message, mention_author=True)

    async def repost_message(self, msg: discord.Message, is_initial_post: bool):
        choice = user_choices.get(msg.id)
        if not choice:
            print("Erreur : choix non trouvé.")
            return

        commerce_channel_map = {
            "achat_cosmos": ACHATS_COSMOS_ID,
            "vente_cosmos": VENTES_COSMOS_ID,
            "achat_nosfire": ACHATS_NOSFIRE_ID,
            "vente_nosfire": VENTES_NOSFIRE_ID,
        }

        activite_channel_map = {
            "présentation-famille_cosmos": FAMILLES_COSMOS_ID,
            "recherche-famille_cosmos": FAMILLES_COSMOS_ID,
            "recherche-raid_cosmos": RAIDS_COSMOS_ID,
            "recherche-leveling_cosmos": LEVELING_COSMOS_ID,
            "recherche-groupe-xp_cosmos": GROUPE_XP_COSMOS_ID,
            "présentation-famille_nosfire": FAMILLES_NOSFIRE_ID,
            "recherche-famille_nosfire": FAMILLES_NOSFIRE_ID,
            "recherche-raid_nosfire": RAIDS_NOSFIRE_ID,
            "recherche-leveling_nosfire": LEVELING_NOSFIRE_ID,
            "recherche-groupe-xp_nosfire": GROUPE_XP_NOSFIRE_ID,
        }

        if choice["context"] == "commerce":
            target_channel_id = commerce_channel_map.get(f"{choice['type']}_{choice['server']}")
        elif choice["context"] == "activité":
            detected_tag = next((tag for tag in ['présentation-famille', 'recherche-famille', 'recherche-raid', 'recherche-leveling', 'recherche-groupe-xp'] if tag in msg.tags), None)
            if detected_tag:
                target_channel_id = activite_channel_map.get(f"{detected_tag}_{choice['server']}")
            else:
                print("Erreur : Aucun tag d'activité valide détecté.")
                return

        if not target_channel_id:
            print("Canal cible non trouvé.")
            return

        target_channel = self.bot.get_channel(target_channel_id)
        if not target_channel:
            print("Erreur : Le canal cible n'a pas pu être récupéré.")
            return

        action = "🆕 Nouvelle annonce" if is_initial_post else "♻️ Annonce republiée"
        header = f"{action} par {msg.author.mention} dans {msg.channel.mention}.\n"
        title = f"**Titre :** {msg.channel.name}"
        tags_string = self.get_tags_string(msg.channel)
        content_formatted = "\n".join([f"> {line}" for line in msg.content.strip().split('\n')])
        final_msg_content = "\n".join(part for part in [header, title, tags_string, content_formatted] if part)

        actions_view = ActionsView(msg.channel.id)

        try:
            await target_channel.send(
                content=final_msg_content,
                files=[await attachment.to_file() for attachment in msg.attachments if 'image' in attachment.content_type],
                view=actions_view
            )
            del user_choices[msg.id]
        except Exception as e:
            print(f"Erreur lors de l'envoi du message: {e}")

        self.message_to_thread[str(msg.id)] = msg.channel.id
        self.save_datas()

    def determine_target_channel(self, choices):
        channel_map = {
            "achat_cosmos": ACHATS_COSMOS_ID,
            "vente_cosmos": VENTES_COSMOS_ID,
            "achat_nosfire": ACHATS_NOSFIRE_ID,
            "vente_nosfire": VENTES_NOSFIRE_ID,
            "présentation-famille_cosmos": FAMILLES_COSMOS_ID,
            "recherche-famille_cosmos": FAMILLES_COSMOS_ID,
            "recherche-raid_cosmos": RAIDS_COSMOS_ID,
            "recherche-leveling_cosmos": LEVELING_COSMOS_ID,
            "recherche-groupe-xp_cosmos": GROUPE_XP_COSMOS_ID,
            "présentation-famille_nosfire": FAMILLES_NOSFIRE_ID,
            "recherche-famille_nosfire": FAMILLES_NOSFIRE_ID,
            "recherche-raid_nosfire": RAIDS_NOSFIRE_ID,
            "recherche-leveling_nosfire": LEVELING_NOSFIRE_ID,
            "recherche-groupe-xp_nosfire": GROUPE_XP_NOSFIRE_ID,
        }

        if choices.get("context") == "commerce":
            return channel_map.get(f"{choices.get('type')}_{choices.get('server')}")
        elif choices.get("context") == "activité":
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