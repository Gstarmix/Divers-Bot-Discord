import json
from datetime import datetime, timedelta
from typing import Callable, Awaitable, Literal
from functools import partial
import asyncio

import discord
from discord.ext import commands
from discord.ui import Modal, TextInput, View, Button
import discord.utils
from dateutil import tz

from constants import DELETE_COOLDOWN_HOURS, RAIDS_EMOTES, COMMERCES_ID, SIGNALEMENT_VENTES_ID, GSTAR_USER_ID, ACTIVITES_ID, ACTIVITY_CHANNELS, TRADE_CHANNELS, RAIDS_COSMOS_ID, RAIDS_NOSFIRE_ID, LOCKED_CHANNELS_1,  LOCKED_CHANNELS_2, RAIDS_LIST, RAID_ROLE_MAPPING, ACTIVITY_TYPES

DATA_PATH = "datas/image_forwarder"

FRA = tz.gettz('Europe/Paris')
# user_choices: dict[int, dict[str, str]] = {}

class ActionsView(discord.ui.View):
    def __init__(self, thread_to_messages: dict[str, list[int]], delete_timestamps: dict[str, int]) -> None:
        super().__init__(timeout=None)
        # self.target_thread_id = target_thread_id
        self.thread_to_messages = thread_to_messages
        self.delete_timestamps = delete_timestamps

    @discord.ui.button(label="Signaler", style=discord.ButtonStyle.danger, custom_id="report_button_v2")
    async def report(self, interaction: discord.Interaction, _: discord.ui.Button):
        print("Bouton Signaler cliqué")
        # modal = ReportModal(message_id=interaction.message.id, channel_id=self.target_thread_id)
        modal = ReportModal(message_id=interaction.message.id, channel_id=interaction.channel_id)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Supprimer", style=discord.ButtonStyle.danger, custom_id="delete_button_v2")
    async def delete(self, interaction: discord.Interaction, _: discord.ui.Button):
        print("Bouton Supprimer cliqué")
        # thread = await interaction.client.fetch_channel(self.target_thread_id)
        thread: discord.Thread = interaction.channel
        author = interaction.user
        if author.id not in {GSTAR_USER_ID, thread.owner.id}:
            await interaction.response.send_message("Vous n'êtes autorisé à effectuer cette action que dans votre propre vente.", ephemeral=True)
            return
        now = datetime.now(tz=FRA)
        last_delete = datetime.fromtimestamp(self.delete_timestamps.get(str(author.id), 0), tz=FRA)
        if now - last_delete < timedelta(hours=DELETE_COOLDOWN_HOURS):
            await interaction.response.send_message(f"Vous devez attendre au moins {DELETE_COOLDOWN_HOURS}h entre chaque suppression.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True, thinking=True)
        await interaction.edit_original_response(view=DeleteView(interaction, self.thread_to_messages, self.delete_timestamps))


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
    def __init__(self, target_interaction: discord.Interaction, thread_to_messages: dict[str, list[int]], delete_timestamps: dict[str, int]):
        super().__init__(timeout=None)
        # self.target_thread_id = target_thread_id
        self.target_interaction = target_interaction
        self.thread_to_messages = thread_to_messages
        self.delete_timestamps = delete_timestamps

    @discord.ui.button(label="Confirmer la suppression", style=discord.ButtonStyle.danger, custom_id="confirm_delete")
    async def delete(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.defer(thinking=False)
        try:
            # target: discord.Thread = await interaction.guild.fetch_channel(self.target_thread_id)
            target: discord.Thread = interaction.channel
            # await target.delete()
            await target.edit(archived=True, locked=True)

            self.delete_timestamps[str(interaction.user.id)] = int(datetime.now(tz=FRA).timestamp())

            if str(target.id) not in self.thread_to_messages:
                return

            repost_channel_id = await get_target_channel_id_and_add_tags(target, None, None, None, None)
            repost_channel = interaction.guild.get_channel(repost_channel_id)
            if not repost_channel:
                raise Exception(f"channel introuvable {repost_channel_id=}")

            for msg_id in self.thread_to_messages[str(target.id)]:
                await repost_channel.get_partial_message(msg_id).delete()
            del self.thread_to_messages[str(target.id)]

        except discord.NotFound:
            pass
        # await self.target_interaction.message.delete()
        # await self.target_interaction.edit_original_response(content="Annonce supprimée !", view=None)

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.secondary, custom_id="cancel_delete")
    async def cancel(self, interaction: discord.Interaction, _: discord.ui.Button):
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
    async def buy(self, interaction: discord.Interaction, _: discord.ui.Button):
        new_callback = partial(self.callback, trade_type="Achat")
        await end_view_chain(interaction, new_callback)
        # await interaction.followup.send("Veuillez choisir le serveur pour votre achat :", view=ServerChoiceView(new_callback, self.author_id))

    @discord.ui.button(label="Vente", style=discord.ButtonStyle.blurple, custom_id="sell")
    async def sell(self, interaction: discord.Interaction, _: discord.ui.Button):
        new_callback = partial(self.callback, trade_type="Vente")
        await end_view_chain(interaction, new_callback)
        # await interaction.followup.send("Veuillez choisir le serveur pour votre vente :", view=ServerChoiceView(new_callback, self.author_id))


# class ServerChoiceView(discord.ui.View):
#     def __init__(self, repost_message_func, author_id: int):
#         super().__init__()
#         # self.msg = msg
#         # self.selected_raids = selected_raids
#         self.repost_message_func = repost_message_func
#         self.author_id = author_id
#
#     # async def disable_buttons(self):
#     #     for item in self.children:
#     #         if isinstance(item, discord.ui.Button):
#     #             item.disabled = True
#
#     async def interaction_check(self, interaction: discord.Interaction) -> bool:
#         if interaction.user.id != self.author_id:
#             await interaction.response.send_message("Vous n'avez pas l'autorisation de faire cela.", ephemeral=True)
#             return False
#         return True
#
#     @discord.ui.button(label="Cosmos", style=discord.ButtonStyle.green, custom_id="choose_cosmos")
#     async def cosmos_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
#         await end_view_chain(interaction, self.repost_message_func, "cosmos")
#
#     @discord.ui.button(label="NosFire", style=discord.ButtonStyle.blurple, custom_id="choose_nosfire")
#     async def nosfire_button_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
#         await end_view_chain(interaction, self.repost_message_func, "nosfire")

class RaidSelectView(discord.ui.View):
    def __init__(self, author_id: int, repost_message, *, page=0):
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
    def __init__(self, author_id: int, repost_message, page=0):
        self.author_id = author_id
        self.repost_message = repost_message
        options = [
            discord.SelectOption(label=raid, value=raid, emoji=RAIDS_EMOTES.get(raid))
            for raid in RAIDS_LIST[page * 25:min((page + 1) * 25, len(RAIDS_LIST))]
        ]
        super().__init__(placeholder='Choisissez les raids', min_values=1, max_values=min(len(options), 25), options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Vous n'avez pas l'autorisation de faire cela.", ephemeral=True)
            return
        new_callback = partial(self.repost_message, selected_raids=self.values)
        await end_view_chain(interaction, new_callback, is_raid_search=True)
        # view = ServerChoiceView(repost_message_func=new_callback, author_id=self.author_id)
        # await interaction.response.send_message("Sur quel serveur souhaitez-vous publier votre annonce de raid ?", view=view)


class PageButton(discord.ui.Button[RaidSelectView]):
    def __init__(self, author_id: int, page_to_add: Literal[-1, 1]):
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


async def end_view_chain(target: discord.Interaction | discord.Thread, callback, server="cosmos", is_raid_search=False):
    target_channel_id, thread_to_messages, delete_timestamps = await callback(server=server)
    base_message = f":white_check_mark: Annonce postée dans <#{target_channel_id}>.\n"
    raid_message = ":warning: Pour être mentionné par les rôles de raid, rendez-vous dans <id:customize>.\n:warning: La républication n'est pas disponible pour les annonces de raid. Vous devrez créer un nouveau post pour mettre à jour votre recherche." if is_raid_search else ""
    if isinstance(target, discord.Thread):
        actions_view = ActionsView(thread_to_messages, delete_timestamps)
        await target.send(content=base_message + raid_message, view=actions_view)
    else:
        actions_view = ActionsView(thread_to_messages, delete_timestamps)
        await target.response.edit_message(content=base_message + raid_message, view=actions_view)

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
        self.last_post_time_path = f"{DATA_PATH}/last_post_time.json"
        self.thread_to_messages_path = f"{DATA_PATH}/thread_to_messages.json"
        self.delete_timestamps_path = f"{DATA_PATH}/delete_timestamps.json"
        self.last_post_time, self.thread_to_messages, self.delete_timestamps = self.load_datas()
        self.last_notification_time = {}

        self.bot.add_view(ActionsView(self.thread_to_messages, self.delete_timestamps))

    def load_datas(self):
        last_post_time = {}
        thread_to_messages: dict[str, list[int]] = {}
        delete_timestamps: dict[str, int] = {}

        try:
            with open(self.last_post_time_path, "r") as f:
                last_post_time = json.load(f)
        except FileNotFoundError:
            pass

        try:
            with open(self.thread_to_messages_path, "r") as f:
                thread_to_messages = json.load(f)
        except FileNotFoundError:
            pass

        try:
            with open(self.delete_timestamps_path, "r") as f:
                delete_timestamps = json.load(f)
        except FileNotFoundError:
            pass
        # print("Données chargées : ", message_to_thread)
        return last_post_time, thread_to_messages, delete_timestamps

    def save_datas(self):
        with open(self.last_post_time_path, "w") as f:
            json.dump(self.last_post_time, f)
        with open(self.thread_to_messages_path, "w") as f:
            json.dump(self.thread_to_messages, f)
        with open(self.delete_timestamps_path, "w") as f:
            json.dump(self.delete_timestamps, f)
        # print("Données sauvegardées : ", self.message_to_thread)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        author = message.author
        channel = message.channel

        # print(f"Message reçu de {message.author.name}: {message.content}")
        if author.bot:
            return

        if channel.type == discord.ChannelType.public_thread:
            num_tags = len(channel.applied_tags)
            if channel.parent_id == ACTIVITES_ID:
                # print(f"Traitement du message dans un thread public dans ACTIVITES_ID : {message.channel.id}")
                # print(f"Tags appliqués : {[tag.name for tag in channel.applied_tags]}")

                if num_tags > 1:
                    # print(f"Suppression du thread {channel.id} pour cause de multiples tags.")
                    warning_msg = f"<:no_valide:1125533828602150972> {channel.owner.mention}, votre fil dans le salon des activités va être supprimé car il utilise plusieurs tags. Veuillez n'utiliser qu'un seul tag par fil. Votre fil sera supprimé dans 5 minutes."
                    await channel.send(warning_msg)

                    await asyncio.sleep(300)

                    try:
                        await channel.delete()
                    except Exception as e:
                        raise Exception(f"Erreur lors de la suppression du thread {channel=} : {e}")

            if channel.parent_id == COMMERCES_ID:
                if num_tags > 4:
                    warning_msg = f"<:no_valide:1125533828602150972> {channel.owner.mention}, votre fil va être supprimé car il utilise trop de tags. Veuillez n'utiliser qu'au maximum 4 tags. Votre fil sera supprimé dans 5 minutes."
                    await channel.send(warning_msg)

                    await asyncio.sleep(300)

                    try:
                        await channel.delete()
                    except Exception as e:
                        raise Exception(f"Erreur lors de la suppression du thread {channel=} : {e}")

        if channel.id in LOCKED_CHANNELS_1:
            await message.delete()
            channel_mention = f"<#{COMMERCES_ID}>"
            inform_message = f"<:no_valide:1125533828602150972> {author.mention}, vous ne pouvez pas poster directement dans ce salon. Veuillez vous diriger vers le salon approprié {channel_mention} et cliquer sur le bouton **\"Nouveau post\"**.\n https://www.zupimages.net/up/24/11/siro.png"
            bot_message = await channel.send(inform_message)
            await bot_message.delete(delay=300)

        if channel.id in LOCKED_CHANNELS_2 and channel.id not in {RAIDS_COSMOS_ID, RAIDS_NOSFIRE_ID}:
            await message.delete()
            channel_mention = f"<#{ACTIVITES_ID}>"
            inform_message = f"<:no_valide:1125533828602150972> {author.mention}, vous ne pouvez pas poster directement dans ce salon. Veuillez vous diriger vers le salon approprié {channel_mention} et cliquer sur le bouton **\"Nouveau post\"**.\n https://www.zupimages.net/up/24/11/siro.png"
            bot_message = await channel.send(inform_message)
            await bot_message.delete(delay=300)

        if channel.id in {RAIDS_COSMOS_ID, RAIDS_NOSFIRE_ID}:
            await message.delete()
            channel_mention = f"<#{ACTIVITES_ID}>"
            inform_message = f"<:no_valide:1125533828602150972> {author.mention}, vous ne pouvez pas poster directement dans ce salon. Veuillez vous diriger vers le salon approprié {channel_mention} et cliquer sur le bouton **\"Nouveau post\"**. Les rôles de raid sont disponibles afin d'être mentionné dans le salon <id:customize>.\n https://www.zupimages.net/up/24/11/siro.png"
            bot_message = await channel.send(inform_message)
            await bot_message.delete(delay=300)

        if channel.type == discord.ChannelType.public_thread and channel.parent_id in {COMMERCES_ID, ACTIVITES_ID}:
            await self.handle_post_logic(message)

    async def repost_message(self, msg: discord.Message, is_initial_post: bool, msg_type: str, server: str = None, selected_raids: list | None = None, trade_type: str | None = None, activity_type: str | None = None) -> tuple[int, dict[str, list[int]], dict[str, int]]:
        thread = msg.channel
        guild = msg.guild

        async for first_message in thread.history(oldest_first=True, limit=1):
            break
        else:
            first_message = msg

        target_channel_id = await get_target_channel_id_and_add_tags(thread, msg_type, server, trade_type, activity_type)
        trade_type = trade_type or get_trade_type({tag.name for tag in thread.applied_tags})

        if not target_channel_id:
            raise Exception(f"Aucun canal cible n'a été trouvé pour les paramètres donnés {msg_type=} {server=} {activity_type=} {trade_type=}")

        target_channel = guild.get_channel(target_channel_id)
        if not target_channel:
            raise Exception(f"Est-ce que le salon {target_channel_id=} existe bien sur {guild.name} ?")

        # action = "🆕 Nouvelle annonce" if is_initial_post else "♻️ Annonce republiée"
        # header = f"{action} par {first_message.author.mention} dans {thread.mention}."

        # # title = f"**Titre :** {thread.name}"
        # tags_string = get_tags_string(thread)

        # raids_mentions = ""
        # if selected_raids and msg_type == "raid":
        #     raids_mentions = " | **Raids :** " + ", ".join([f"<@&{RAID_ROLE_MAPPING[server].get(raid, '')}>" for raid in selected_raids])
        
        # header_and_metadata = f"{header} [{tags_string}{raids_mentions}]".rstrip(" |")
        # if first_message.content.strip():
        #     # S'il y a du texte, ajoutez '> ' au début de chaque ligne.
        #     content_formatted = f"\n".join([f"> {line}" for line in first_message.content.strip().split('\n')])
        # else:
        #     # S'il n'y a pas de texte (image uniquement), ne modifiez pas le contenu.
        #     content_formatted = first_message.content

        # final_msg_content = "\n".join([header_and_metadata, content_formatted])

        # # actions_view = ActionsView(thread.id) 
        # # Les membres n'aiment pas cette fonctionnalité

        # tags_string = get_tags_string(thread)
        # raids_mentions = "**Raids :** " + ", ".join([f"<@&{RAID_ROLE_MAPPING[server].get(raid, '')}>" for raid in selected_raids]) if selected_raids and msg_type == "raid" else ""

        action = "🆕" if is_initial_post else "♻️"

        message_content = ", ".join([f"<@&{RAID_ROLE_MAPPING[server].get(raid, '')}>" for raid in selected_raids]) if selected_raids and msg_type == "raid" else ""

        embed = None
        files = []

        if trade_type == "Vente":
            header_vente = f"{action} {thread.mention}"
            if first_message.content.strip():
                content_formatted_vente = "\n".join([f"> {line}" for line in first_message.content.strip().split('\n')])
            else:
                content_formatted_vente = ""
            files = [await attachment.to_file() for attachment in first_message.attachments if 'image' in attachment.content_type]
            message_content = f"{header_vente}\n{content_formatted_vente}"
        else:
            embed = discord.Embed(
                title=f"{action} {thread.mention}",
                description=first_message.content,
                color=discord.Color.blue() if is_initial_post else discord.Color.green(),
            )

        webhooks = await target_channel.webhooks()
        webhook = discord.utils.find(lambda wh: wh.user == guild.me, webhooks)
        if webhook is None:
            webhook = await target_channel.create_webhook(name=guild.me.name, reason="Pour reposter les messages")

        sent_msg = await webhook.send(
            content=message_content,
            username=msg.author.display_name,
            avatar_url=msg.author.display_avatar.url,
            files=files,
            embed=embed,
            wait=True
        )

        # if not is_initial_post:
        #     msg_ids, thread_ids = tuple(self.message_to_thread), tuple(self.message_to_thread.values())
        #     try:
        #         msg_index = thread_ids.index(thread.id)
        #         msg_id = msg_ids[msg_index]
        #         del self.message_to_thread[msg_id]
        #         # await target_channel.get_partial_message(msg_id).edit(view=None)
        #     except ValueError:
        #         pass
        #     except discord.NotFound as e:
        #         if e.code == 10008:
        #             pass
        #         else:
        #             raise e

        # if not is_initial_post:
        #     confirmation_message = await thread.send(f":white_check_mark: Annonce repostée dans <#{target_channel_id}>. Ce message sera supprimé dans 5 minutes.")
        #     await confirmation_message.delete(delay=300)

        if not is_initial_post:
            confirmation_message = await thread.send(
                content=f":white_check_mark: Annonce repostée dans <#{target_channel_id}>.\n:warning: Ce message sera supprimé dans 5 minutes.",
                reference=msg
            )
            await confirmation_message.delete(delay=300)

        self.thread_to_messages.setdefault(str(thread.id), []).append(sent_msg.id)
        self.save_datas()
        return target_channel_id, self.thread_to_messages, self.delete_timestamps

    async def handle_post_logic(self, message: discord.Message):
        thread = message.channel
        author = message.author

        if author.bot or thread.type != discord.ChannelType.public_thread or thread.parent_id not in {COMMERCES_ID, ACTIVITES_ID}:
            raise Exception("Condition initiale non remplie (auteur bot, type de canal, parent_id)")

        if author != thread.owner:
            return
        
        is_initial_post = message.id == thread.id

        current_time = datetime.now(tz=FRA)
        last_post_time = datetime.fromtimestamp(self.last_post_time.get(str(thread.id), 0), tz=FRA)

        timer_hours = None
        thread_tags = {tag.name for tag in thread.applied_tags}

        server = get_server(thread_tags)
        activity_type = get_activity_type(thread_tags)
        trade_type = get_trade_type(thread_tags)
        if thread.parent_id == COMMERCES_ID and trade_type:
            # trade_type = "achat" if "achat" in thread.name else "vente"
            # server = "nosfire" if "nosfire" in thread.name else "cosmos"
            timer_hours = TRADE_CHANNELS.get(f"{trade_type}_{server}", {}).get("timer_hours", 24)
        elif thread.parent_id == ACTIVITES_ID and activity_type:
            # for tag in thread_tags:
            #     if tag in ACTIVITY_TYPES:
            #         timer_hours = ACTIVITY_CHANNELS[f"{tag}_{server}"].get("timer_hours")
            #         break
            timer_hours = ACTIVITY_CHANNELS[f"{activity_type}_{server}"].get("timer_hours")

        if timer_hours is None:
            timer_hours = 24
            #print(f"Aucun timer_hours spécifique trouvé, utilisation de la valeur par défaut (24h). Faut verifier pourquoi {thread=}")

        if last_post_time + timedelta(hours=timer_hours) > current_time and not is_initial_post:
            user_thread_key = (author.id, thread.id)
            if user_thread_key not in self.last_notification_time or (datetime.now() - self.last_notification_time[user_thread_key]).total_seconds() > 300:
                notification_message = f"🕒 Tu ne pourras reposter ton annonce qu'à partir du {discord.utils.format_dt(last_post_time + timedelta(hours=timer_hours), 'f')}.\n:warning: Ce message sera supprimé dans 5 minutes."
                bot_message = await thread.send(content=notification_message, reference=message)
                await bot_message.delete(delay=300)
                self.last_notification_time[user_thread_key] = datetime.now()
            return

        if activity_type != "Recherche-raid":
            self.last_post_time[str(thread.id)] = int(current_time.timestamp())
            self.save_datas()

        if thread.parent_id == COMMERCES_ID:
            if is_initial_post:
                await message.reply(
                    "Quel type de commerce souhaitez-vous réaliser ?",
                    view=CommerceTypeView(
                        partial(self.repost_message, msg=message, is_initial_post=True, msg_type="commerce"),
                        author_id=author.id
                    )
                )
            else:
                await self.repost_message(message, False, "commerce")

        if thread.parent_id == ACTIVITES_ID:
            # detected_tags = {tag.name for tag in thread.applied_tags} & ACTIVITY_TYPES
            if not activity_type:
                raise Exception(f"Aucun tag d'activités pour {thread=}")
            if is_initial_post:
                if activity_type == "Recherche-raid":
                    select_view = RaidSelectView(author_id=author.id, repost_message=partial(self.repost_message, msg=message, is_initial_post=True, msg_type="raid"), page=0)
                    await message.reply("Sélectionnez les types de raids :", view=select_view)
                else:
                    # await message.reply(
                    #     "Sur quel serveur souhaitez-vous poster votre activité ?",
                    #     view=ServerChoiceView(
                    #         repost_message_func=partial(self.repost_message, msg=message, is_initial_post=True, msg_type="activité", activity_type=detected_tags.pop()),
                    #         author_id=author.id
                    #     )
                    # )
                    await end_view_chain(thread, partial(self.repost_message, msg=message, is_initial_post=True, msg_type="activité", activity_type=activity_type))
            else:
                if activity_type == "Recherche-raid":
                    #print("tentative d'up de raid, pour l'instant ça ignore juste le message")
                    return
                await self.repost_message(message, False, "activité")


# def get_tags_string(thread: discord.Thread) -> str:
#     tags_list = thread.applied_tags
#     tags_names = ", ".join([f"{tag.emoji} `{tag.name}`" for tag in tags_list])
#     return f"**Tags :** {tags_names}" if tags_names else ""


# def format_remaining_time(remaining_time: timedelta) -> str:
#     total_seconds = remaining_time.total_seconds()
#     days, remainder = divmod(total_seconds, 86400)
#     hours, remainder = divmod(remainder, 3600)
#     minutes, seconds = divmod(remainder, 60)
#     return f"{int(days)}j {int(hours)}h {int(minutes)}min"


async def add_tag_to_thread(thread: discord.Thread, tag_name: str):
    tag_to_add = discord.utils.find(lambda tag: tag.name == tag_name, thread.parent.available_tags)
    if not tag_to_add:
        print(f"{tag_name=} introuvable dans {thread.parent=}")
        return
    await thread.add_tags(tag_to_add)


def get_trade_type(thread_tags: set[str]):
    trade_tags = thread_tags & {"Vente", "Achat"}
    if trade_tags:
        return trade_tags.pop()
    return None


def get_server(thread_tags: set[str]):
    server_tags = thread_tags & {"cosmos", "nosfire"}
    if server_tags:
        return server_tags.pop()
    else:
        return "cosmos"


def get_activity_type(thread_tags: set[str]):
    activity_tags = thread_tags & ACTIVITY_TYPES
    if activity_tags:
        return activity_tags.pop()
    return None


async def get_target_channel_id_and_add_tags(thread: discord.Thread, msg_type: str | None, server: str | None, trade_type: str | None, activity_type: str | None) -> int | None:
    thread_tags = {tag.name for tag in thread.applied_tags}

    target_channel_id = None

    server = server or get_server(thread_tags)
    trade_type = trade_type or get_trade_type(thread_tags)
    activity_type = activity_type or get_activity_type(thread_tags)

    if trade_type:
        msg_type = msg_type or "commerce"

    if activity_type:
        msg_type = msg_type or "activité"

    msg_type = msg_type or "raid"

    if msg_type == "commerce":
        channel_info = TRADE_CHANNELS.get(f"{trade_type}_{server}")
        if channel_info:
            target_channel_id = channel_info["id"]
        await add_tag_to_thread(thread, trade_type)
    if msg_type == "raid":
        target_channel_id = RAIDS_COSMOS_ID if server == "cosmos" else RAIDS_NOSFIRE_ID
    if msg_type == "activité":
        channel_info = ACTIVITY_CHANNELS.get(f"{activity_type}_{server}")
        if channel_info:
            target_channel_id = channel_info["id"]
        await add_tag_to_thread(thread, activity_type)
    # await add_tag_to_thread(thread, server)
    return target_channel_id


async def setup(bot: commands.Bot):
    await bot.add_cog(ImageForwarder(bot))
