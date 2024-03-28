import json
from datetime import datetime, timedelta
from typing import Callable, Awaitable, Literal
from functools import partial
import logging
import asyncio

import discord
from discord.ext import commands
from discord.ui import Modal, TextInput, View, Button

from constants import COMMERCES_ID, SIGNALEMENT_VENTES_ID, GSTAR_USER_ID, ACTIVITES_ID, ACTIVITY_CHANNELS, TRADE_CHANNELS, RAIDS_COSMOS_ID, RAIDS_NOSFIRE_ID, LOCKED_CHANNELS_1,  LOCKED_CHANNELS_2, RAIDS_LIST, RAID_ROLE_MAPPING, ACTIVITY_TYPES

DATA_PATH = "datas/image_forwarder"


# user_choices: dict[int, dict[str, str]] = {}

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
        await self.target_interaction.edit_original_response(content="Annonce supprimée !", view=None)

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.secondary, custom_id="cancel_delete")
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=False)
        await self.target_interaction.edit_original_response(content="Suppression annulée !", view=None)


class CommerceTypeView(discord.ui.View):
    def __init__(self, callback: Callable[[str], Awaitable[None]], author_id: int):
        super().__init__(timeout=None)
        self.callback = callback
        self.author_id = author_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Vous n'avez pas l'autorisation de faire cela.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Achat", style=discord.ButtonStyle.green, custom_id="buy")
    async def buy(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        await interaction.response.edit_message(view=self)
        new_callback = partial(self.callback, trade_type="achat")
        await interaction.followup.send("Veuillez choisir le serveur pour votre achat :", view=ServerChoiceView(new_callback, self.author_id))

    @discord.ui.button(label="Vente", style=discord.ButtonStyle.blurple, custom_id="sell")
    async def sell(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        await interaction.response.edit_message(view=self)
        new_callback = partial(self.callback, trade_type="vente")
        await interaction.followup.send("Veuillez choisir le serveur pour votre vente :", view=ServerChoiceView(new_callback, self.author_id))



class ServerChoiceView(discord.ui.View):
    def __init__(self, repost_message_func, author_id: int):
        super().__init__()
        # self.msg = msg
        # self.selected_raids = selected_raids
        self.repost_message_func = repost_message_func
        self.author_id = author_id

    # async def disable_buttons(self):
    #     for item in self.children:
    #         if isinstance(item, discord.ui.Button):
    #             item.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Vous n'avez pas l'autorisation de faire cela.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Cosmos", style=discord.ButtonStyle.green, custom_id="choose_cosmos")
    async def cosmos_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        target_channel_id = await self.repost_message_func(server="cosmos")
        # print("Result from repost_message_func:", target_channel_id)
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        await interaction.response.edit_message(content=f"Annonce postée sur <#{target_channel_id}>.", view=None)

    @discord.ui.button(label="NosFire", style=discord.ButtonStyle.blurple, custom_id="choose_nosfire")
    async def nosfire_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        target_channel_id = await self.repost_message_func(server="nosfire")
        print("Result from repost_message_func:", target_channel_id)
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        await interaction.response.edit_message(content=f"Annonce postée sur <#{target_channel_id}>.", view=None)

class RaidSelectView(discord.ui.View):
    def __init__(self, author_id, repost_message, *, page=0):
        super().__init__(timeout=None)
        self.author_id = author_id
        self.repost_message = repost_message
        self.page = page
        self.max_page = len(RAIDS_LIST) // 25 + (1 if len(RAIDS_LIST) % 25 > 0 else 0)
        self.add_item(RaidSelect(author_id, self.repost_message, page=page))
        if page > 0:
            self.add_item(PageButton(author_id, -1))
        if page < self.max_page - 1:
            self.add_item(PageButton(author_id, 1))


class RaidSelect(discord.ui.Select[RaidSelectView]):
    def __init__(self, author_id, repost_message, page=0):
        self.author_id = author_id
        self.repost_message = repost_message
        options = [
            discord.SelectOption(label=raid, value=raid)
            for raid in RAIDS_LIST[page * 25:min((page + 1) * 25, len(RAIDS_LIST))]
        ]
        super().__init__(placeholder='Choisissez les raids', min_values=1, max_values=min(len(options), 25), options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Vous n'avez pas l'autorisation de faire cela.", ephemeral=True)
            return
        new_callback = partial(self.repost_message, selected_raids=self.values)
        view = ServerChoiceView(repost_message_func=new_callback, author_id=self.author_id)
        await interaction.response.send_message("Sur quel serveur souhaitez-vous publier votre annonce de raid ?", view=view)


class PageButton(discord.ui.Button[RaidSelectView]):
    def __init__(self, author_id, page_to_add: Literal[-1, 1]):
        label = "Page précédente"
        if page_to_add == 1:
            label = "Page suivante"
        super().__init__(style=discord.ButtonStyle.secondary, label=label)
        self.author_id = author_id
        self.page_to_add = page_to_add

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Vous n'avez pas l'autorisation de faire cela.", ephemeral=True)
            return
        view = self.view
        view.clear_items()
        new_view = RaidSelectView(self.author_id, self.view.repost_message, page=view.page + self.page_to_add)
        await interaction.response.edit_message(view=new_view)


# class NextPageButton(discord.ui.Button):
#     def __init__(self, author_id):
#         super().__init__(style=discord.ButtonStyle.secondary, label="Page suivante")
#         self.author_id = author_id
#
#     async def callback(self, interaction: discord.Interaction):
#         if interaction.user.id != self.author_id:
#             await interaction.response.send_message("Vous n'avez pas l'autorisation de faire cela.", ephemeral=True)
#             return
#         view = self.view
#         view.clear_items()
#         new_view = RaidSelectView(self.author_id, page=view.page + 1)
#         await interaction.response.edit_message(view=new_view)


class ImageForwarder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.first_post_time_path = f"{DATA_PATH}/first_post_time.json"
        self.message_to_thread_path = f"{DATA_PATH}/message_to_thread.json"
        self.first_post_time, self.message_to_thread = self.load_datas()
        self.last_notification_time = {}

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
        # print("Données chargées : ", message_to_thread)
        return first_post_time, message_to_thread

    def save_datas(self):
        with open(self.first_post_time_path, "w") as f:
            json.dump(self.first_post_time, f)
        with open(self.message_to_thread_path, "w") as f:
            json.dump(self.message_to_thread, f)
        # print("Données sauvegardées : ", self.message_to_thread)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        print(f"Message reçu de {message.author.name}: {message.content}")
        if message.author.bot:
            return

        if message.channel.type == discord.ChannelType.public_thread and message.channel.parent_id == ACTIVITES_ID:
            print(f"Traitement du message dans un thread public dans ACTIVITES_ID : {message.channel.id}")
            thread = message.channel
            print(f"Tags appliqués : {[tag.name for tag in thread.applied_tags]}")

            num_tags = len(thread.applied_tags)

            if num_tags > 1:
                print(f"Suppression du thread {thread.id} pour cause de multiples tags.")
                warning_msg = f"{thread.owner.mention}, votre fil dans le salon des activités va être supprimé car il utilise plusieurs tags. Veuillez utiliser un seul tag par fil. Votre fil sera supprimé dans 5 minutes."
                await message.channel.send(warning_msg)

                await asyncio.sleep(300)

                try:
                    await thread.delete()
                    logging.info(f'Successfully deleted thread: {thread.id}')
                except Exception as e:
                    logging.error(f'Error deleting thread {thread.id}: {e}')
                    print(f"Erreur lors de la suppression du thread : {e}")

        if message.channel.id in LOCKED_CHANNELS_1:
            print(f"Message posté dans un canal verrouillé : {message.channel.id}")
            await message.delete()
            channel_mention = f"<#{COMMERCES_ID}>"
            inform_message = f"{message.author.mention}, vous ne pouvez pas poster directement dans ce salon. Veuillez vous diriger vers le salon approprié {channel_mention} et cliquer sur le bouton **\"Nouveau post\"**.\n https://www.zupimages.net/up/24/11/siro.png"
            bot_message = await message.channel.send(inform_message)
            await message.author.send(inform_message)
            await asyncio.sleep(300)
            await bot_message.delete()
        elif message.channel.id in LOCKED_CHANNELS_2 and message.channel.id not in [RAIDS_COSMOS_ID, RAIDS_NOSFIRE_ID]:
            await message.delete()
            channel_mention = f"<#{ACTIVITES_ID}>"
            inform_message = f"{message.author.mention}, vous ne pouvez pas poster directement dans ce salon. Veuillez vous diriger vers le salon approprié {channel_mention} et cliquer sur le bouton **\"Nouveau post\"**.\n https://www.zupimages.net/up/24/11/siro.png"
            bot_message = await message.channel.send(inform_message)
            await message.author.send(inform_message)
            await asyncio.sleep(300)
            await bot_message.delete()

        if message.channel.id in [RAIDS_COSMOS_ID, RAIDS_NOSFIRE_ID]:
            inform_message = f"{message.author.mention}, vous ne pouvez pas poster directement dans ce salon. Veuillez vous diriger vers le salon approprié pour les raids et cliquer sur le bouton **\"Nouveau post\"**. Les rôles sont disponibles afin d'être mentionné dans le salon <id:customize>.\n https://www.zupimages.net/up/24/11/siro.png"
            bot_message = await message.channel.send(inform_message)
            await asyncio.sleep(300)
            await bot_message.delete()

        if message.channel.type == discord.ChannelType.public_thread and message.channel.parent_id in {COMMERCES_ID, ACTIVITES_ID}:
            await self.handle_post_logic(message)
        logging.info('Finished processing on_message')

    async def repost_message(self, msg: discord.Message, is_initial_post: bool, msg_type: str, server: str = None, selected_raids: list | None = None, trade_type: str | None = None, activity_type: str | None = None, channel_id: int | None = None) -> int:
        target_channel_id = None
        print(f"Repost du message dans le canal {target_channel_id}")

        thread = msg.channel
        async for first_message in thread.history(oldest_first=True, limit=1):
            break
        else:
            first_message = msg

        if msg_type == "commerce":
            channel_info = TRADE_CHANNELS.get(f"{trade_type}_{server}")
            if channel_info:
                target_channel_id = channel_info["id"]
        elif msg_type == "raid":
            target_channel_id = RAIDS_COSMOS_ID if server == "cosmos" else RAIDS_NOSFIRE_ID
        elif msg_type == "activité":
            channel_info = ACTIVITY_CHANNELS.get(f"{activity_type}_{server}")
            if channel_info:
                target_channel_id = channel_info["id"]

        if target_channel_id is None:
            print("Aucun canal cible n'a été trouvé pour les paramètres donnés.")
            # Vous pourriez vouloir retourner ici ou gérer l'erreur différemment
            return

        target_channel = self.bot.get_channel(target_channel_id)
        if not target_channel:
            return {"id": target_channel_id}

        action = "🆕 Nouvelle annonce" if is_initial_post else "♻️ Annonce republiée"
        header = f"{action} par {first_message.author.mention} dans {thread.mention}."

        server_key = "Cosmos" if server.lower() == "cosmos" else "NosFire" if server.lower() == "nosfire" else None
        if server_key is None:
            print(f"Serveur invalide: {server}")
            return

        # title = f"**Titre :** {thread.name}"
        tags_string = self.get_tags_string(thread)

        raids_mentions = ""
        if selected_raids and msg_type == "raid":
            raids_mentions = " | **Raids :** " + ", ".join([f"<@&{RAID_ROLE_MAPPING[server_key].get(raid, '')}>" for raid in selected_raids])
        
        header_and_metadata = f"{header} [{tags_string}{raids_mentions}]".rstrip(" |")
        content_formatted = f"**Contenu :**\n" + "\n".join([f"{line}" for line in first_message.content.strip().split('\n')])
        final_msg_content = "\n".join([header_and_metadata, content_formatted])

        actions_view = ActionsView(thread.id)

        try:
            webhooks = await target_channel.webhooks()
            webhook = next((wh for wh in webhooks if wh.user == self.bot.user), None)
            if webhook is None:
                webhook = await target_channel.create_webhook(name="MonWebhook", reason="Pour reposter les messages")

            if not webhook.is_partial():
                await webhook.send(
                    content=final_msg_content,
                    username=msg.author.display_name,
                    avatar_url=msg.author.avatar.url if msg.author.avatar else None,
                    files=[await attachment.to_file() for attachment in first_message.attachments if 'image' in attachment.content_type],
                    view=actions_view if not webhook.is_partial() else None
                )
            else:
                raise Exception("Webhook partiel. Passage à l'envoi standard.")
        except Exception as e:
            print(f"Utilisation de l'envoi standard en raison d'une erreur avec le webhook: {e}")
            await target_channel.send(
                content=final_msg_content,
                files=[await attachment.to_file() for attachment in first_message.attachments if 'image' in attachment.content_type],
                view=actions_view
            )

        # print(f"Enregistrement du channel_id {target_channel_id} pour le thread {thread.id}")
        self.message_to_thread[str(thread.id)] = {"channel_id": target_channel_id}
        self.save_datas()
        return target_channel_id

    async def handle_post_logic(self, message: discord.Message):
        print(f"Entrée dans handle_post_logic avec message : {message.content}")
        if message.author.bot or message.channel.type != discord.ChannelType.public_thread or message.channel.parent_id not in {COMMERCES_ID, ACTIVITES_ID}:
            print("Condition initiale non remplie (auteur bot, type de canal, parent_id)")
            return

        thread = message.channel
        print(f"thread.parent_id: {thread.parent_id}")
        
        is_initial_post = not bool(self.message_to_thread.get(str(thread.id)))
        print(f"is_initial_post: {is_initial_post}, thread.id: {thread.id}")

        current_time = datetime.utcnow().timestamp()
        last_post_time = self.first_post_time.get(str(thread.id), 0)
        elapsed_time = current_time - last_post_time

        timer_hours = None
        if thread.parent_id == COMMERCES_ID:
            trade_type = "achat" if "achat" in thread.name else "vente"
            server = "cosmos" if "cosmos" in thread.name else "nosfire"
            print(f"Commerce détecté: trade_type={trade_type}, server={server}")
            timer_hours = TRADE_CHANNELS.get(f"{trade_type}_{server}", {}).get("timer_hours", 24)
        elif thread.parent_id == ACTIVITES_ID:
            detected_tags = {tag.name for tag in thread.applied_tags}
            print(f"Tags détectés: {detected_tags}")
            for tag in detected_tags:
                if tag in ACTIVITY_TYPES:
                    server = "cosmos" if "cosmos" in detected_tags else "nosfire"
                    print(f"Activité détectée: tag={tag}, server={server}")
                    timer_hours = ACTIVITY_CHANNELS[f"{tag}_{server}"].get("timer_hours")
                    break

        print(f"timer_hours avant condition finale: {timer_hours}")
        if timer_hours is None:
            timer_hours = 24
            print("Aucun timer_hours spécifique trouvé, utilisation de la valeur par défaut.")

        remaining_time = (timer_hours * 3600) - elapsed_time
        if remaining_time > 0 and not is_initial_post:
            print(f"Temps restant avant la prochaine publication: {remaining_time}")
            notification_message = f"🕒 Il reste {self.format_remaining_time(timedelta(seconds=remaining_time))} avant la prochaine actualisation possible de votre annonce."
            try:
                await message.author.send(notification_message)
            except Exception as e:
                print(f"Erreur lors de l'envoi du MP : {e}")
            return

        if is_initial_post:
            self.first_post_time[str(thread.id)] = current_time
            self.save_datas()

        if thread.parent_id == COMMERCES_ID and message.author == thread.owner:
            print("Thread parent_id est COMMERCES_ID, prêt à répondre pour le type de commerce")
            if is_initial_post:
                await message.reply(
                    "Quel type de commerce souhaitez-vous réaliser ?",
                    view=CommerceTypeView(
                        partial(self.repost_message, message, True, "commerce"),
                        author_id=message.author.id
                    )
                )
            else:
                thread_info = self.message_to_thread.get(str(thread.id), {})
                channel_id = thread_info.get("channel_id") if isinstance(thread_info, dict) else None
                # print(f"Récupération du channel_id pour le thread {thread.id} : {channel_id}")
                if channel_id:
                    await self.repost_message(message, False, "commerce", server="cosmos", channel_id=channel_id)
                else:
                    print(f"Aucun channel_id trouvé pour le thread {thread.id}. Peut-être le premier post n'a-t-il pas été traité correctement ?")

        elif thread.parent_id == ACTIVITES_ID and message.author == thread.owner:
            print("Thread parent_id est ACTIVITES_ID, vérification des tags pour l'action suivante")
            detected_tags = {tag.name for tag in thread.applied_tags}
            if is_initial_post:
                if "recherche-raid" in detected_tags:
                    print("Création de RaidSelectView pour la recherche de raid")
                    select_view = RaidSelectView(author_id=message.author.id, repost_message=partial(self.repost_message, msg=message, is_initial_post=True, msg_type="raid"), page=0)
                    await message.reply("Sélectionnez les types de raids :", view=select_view)
                else:
                    await message.reply(
                        "Sur quel serveur souhaitez-vous poster votre activité ?",
                        view=ServerChoiceView(
                            repost_message_func=partial(self.repost_message, msg=message, is_initial_post=True, msg_type="activité", activity_type=detected_tags.pop()),
                            author_id=message.author.id
                        )
                    )
            else:
                channel_id = self.message_to_thread.get(str(thread.id), {}).get("channel_id")
                if channel_id:
                    await self.repost_message(message, False, "commerce", server="cosmos", channel_id=channel_id)



    def get_tags_string(self, thread: discord.Thread) -> str:
        tags_list = thread.applied_tags
        tags_names = ", ".join([f"{tag.emoji} `{tag.name}`" for tag in tags_list])
        return f"**Tags :** {tags_names}" if tags_names else ""

    def format_remaining_time(self, remaining_time: timedelta) -> str:
        total_seconds = remaining_time.total_seconds()
        days, remainder = divmod(total_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(days)}j {int(hours)}h {int(minutes)}min"

async def setup(bot: commands.Bot):
    await bot.add_cog(ImageForwarder(bot))