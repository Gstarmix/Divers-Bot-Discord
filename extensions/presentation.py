import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
from constants import *
import json
import time
import asyncio

FAMILY_CHOICES_PATH = "extensions/family_choices.json"

class PseudoModal(Modal):
    def __init__(self, player_setup, user_id, thread):
        super().__init__(title="Entrez votre pseudo")
        self.player_setup = player_setup
        self.user_id = user_id
        self.thread = thread
        self.add_item(TextInput(label="Pseudo", placeholder="Ton pseudo ici", min_length=4, max_length=32))

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Vous n'êtes pas autorisé à changer ce pseudo.", ephemeral=True)
            return
        nickname = self.children[0].value.strip()
        current_time = time.time()
        last_changed = self.player_setup.bot.last_pseudo_change.get(self.user_id, 0)
        if current_time - last_changed < 300:
            await interaction.response.send_message("Vous ne pouvez changer votre pseudo qu'une fois toutes les 5 minutes.", ephemeral=True)
            return
        if not (4 <= len(nickname) <= 32):
            await interaction.response.send_message("Pseudo invalide. Il doit contenir entre 4 et 32 caractères.", ephemeral=True)
            return
        self.player_setup.bot.last_pseudo_change[self.user_id] = current_time
        member = self.thread.guild.get_member(interaction.user.id)
        if member:
            await member.edit(nick=nickname)
            role = member.guild.get_role(ROLE1_ID_FAFA)
            if role:
                await member.add_roles(role)
        self.player_setup.author_family_choices[self.user_id]['pseudo'] = nickname
        self.player_setup.save_family_choices()
        author_name = member.display_name if member else nickname
        embed = generate_message(author_name)
        view = View()
        view.add_item(Button(label="Yertirand", style=discord.ButtonStyle.primary, custom_id="yertirand"))
        view.add_item(Button(label="-GANG-", style=discord.ButtonStyle.primary, custom_id="gang"))
        view.add_item(Button(label="Tutoriel LoL", style=discord.ButtonStyle.secondary, url="https://www.nostar.fr/lol"))
        await interaction.response.send_message(embed=embed, view=view)

class PlayerSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.last_pseudo_change = {}
        self.first_author_message = {}
        self.used_buttons = set()
        self.last_interaction_time = {}
        self.last_nickname_change_time = {}
        self.thread_initial_message_pending = set()
        self.family_selections = {}
        self.thread_authors = {}
        self.command_initiators = {}
        self.last_author_interaction = {}
        self.active_threads = set()
        self.author_family_choices = self.load_family_choices()
        print(f"author_family_choices loaded: {self.author_family_choices}")

    def load_family_choices(self):
        try:
            with open(FAMILY_CHOICES_PATH, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_family_choices(self):
        with open(FAMILY_CHOICES_PATH, 'w') as f:
            json.dump(self.author_family_choices, f)

    async def check_thread_activity(self, thread_id):
        await asyncio.sleep(600)
        if thread_id in self.active_threads:
            return
        current_time = time.time()
        if current_time - self.last_author_interaction.get(thread_id, 0) > 600:
            thread = self.bot.get_channel(thread_id)
            if thread:
                author = thread.guild.get_member(self.thread_authors.get(thread_id))
                if author:
                    try:
                        await author.send("Votre thread a été supprimé en raison de l'inactivité.")
                    except discord.errors.Forbidden:
                        pass
                await thread.delete()

    async def set_nickname_callback(self, interaction):
        thread_id = interaction.channel_id
        if interaction.user.id != self.thread_authors.get(thread_id):
            await interaction.response.send_message("Vous n'êtes pas autorisé à utiliser ce bouton.", ephemeral=True)
            return
        thread = self.bot.get_channel(thread_id)
        await interaction.response.send_modal(PseudoModal(self, interaction.user.id, thread))

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if thread.parent_id != PRESENTATION_CHANNEL_ID:
            return
        author_id = thread.owner_id
        self.thread_authors[thread.id] = author_id
        if author_id not in self.author_family_choices:
            self.author_family_choices[author_id] = {
                "pseudo": None,
                "message_content": None,
                "family_choice": None
            }
            self.save_family_choices()
        embed = discord.Embed(title="Quel est ton pseudo de joueur ?", color=0x5865f2)
        view = View()
        button = Button(label="Définir le pseudo", style=discord.ButtonStyle.primary, custom_id="set_nickname")
        button.callback = self.set_nickname_callback
        view.add_item(button)
        await thread.send(embed=embed, view=view)
        self.last_author_interaction[thread.id] = time.time()
        asyncio.create_task(self.check_thread_activity(thread.id))

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or not message.author or message.author.bot:
            return
        if isinstance(message.channel, discord.Thread):
            thread_id = message.channel.id
            if message.channel.parent_id == PRESENTATION_CHANNEL_ID:
                if thread_id not in self.first_author_message:
                    self.first_author_message[thread_id] = message.id
                allowed_roles = [CHEF_SINGE_ROLE_ID, GARDIEN_YERTI_ROLE_ID, GARDIEN_GANG_ROLE_ID]
                if message.id != self.first_author_message[thread_id] and not any(role.id in allowed_roles for role in message.author.roles):
                    await message.delete()
                    await message.author.send("Vous n'êtes pas autorisé à écrire dans ce fil.")
                if thread_id in self.thread_initial_message_pending and not self.first_author_message.get(thread_id):
                    self.thread_initial_message_pending.remove(thread_id)
                    self.first_author_message[thread_id] = message.id
                author_id = self.thread_authors.get(thread_id)
                if author_id and message.author.id == author_id:
                    if 'message_content' not in self.author_family_choices[author_id] or not self.author_family_choices[author_id]['message_content']:
                        self.author_family_choices[author_id]['message_content'] = message.content
                        self.save_family_choices()
                self.last_author_interaction[message.channel.id] = time.time()

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data.get('custom_id')
            thread_id = interaction.channel_id
            author_id = str(interaction.user.id)

            print(f"Interaction received: {custom_id}, Thread ID: {thread_id}, Author ID: {author_id}")
            print(f"Checking author in author_family_choices: {self.author_family_choices.get(author_id)}")

            if not author_id or author_id not in self.author_family_choices:
                print(f"Author not found or not in author_family_choices: Author ID: {author_id}")
                return
            current_time = time.time()
            if custom_id in ["yertirand", "gang"]:
                print(f"Processing family choice: {custom_id}")
                self.active_threads.add(thread_id)
                last_time = self.last_interaction_time.get(author_id, 0)
                if current_time - last_time < 300:
                    print("Less than 5 minutes since the last interaction.")
                    response_message = "Veuillez attendre 5 minutes avant de réessayer."
                    await (interaction.followup.send(response_message, ephemeral=True) if interaction.response.is_done() else interaction.response.send_message(response_message, ephemeral=True))
                    return
                self.last_interaction_time[author_id] = current_time
                family_choice = custom_id.capitalize()
                self.author_family_choices[author_id]['family_choice'] = family_choice
                self.save_family_choices()
                print(f"Family choice recorded for {author_id}: {family_choice}")
                role_id = GARDIEN_YERTI_ROLE_ID if custom_id == "yertirand" else GARDIEN_GANG_ROLE_ID
                role_mention = f"<@&{role_id}>"
                await (interaction.followup.send(role_mention, allowed_mentions=discord.AllowedMentions.all(), ephemeral=False) if interaction.response.is_done() else interaction.response.send_message(role_mention, allowed_mentions=discord.AllowedMentions.all(), ephemeral=False))

            elif custom_id == "mention_for_invite":
                command_initiator_id = self.command_initiators.get(thread_id)
                if command_initiator_id:
                    user_mention = f"<@{command_initiator_id}>"
                    if interaction.response.is_done():
                        await interaction.followup.send(user_mention, ephemeral=False)
                    else:
                        await interaction.response.send_message(user_mention, ephemeral=False)
            self.last_author_interaction[interaction.channel.id] = time.time()

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if isinstance(message.channel, discord.Thread) and message.channel.parent_id == PRESENTATION_CHANNEL_ID:
            thread_id = str(message.channel.id)
            if message.id == self.first_author_message.get(thread_id):
                author_id = str(self.thread_authors.get(thread_id))
                member = message.guild.get_member(int(author_id))
                if member:
                    role = member.guild.get_role(ROLE1_ID_FAFA)
                    if role:
                        await member.remove_roles(role)
                    try:
                        await member.send("Votre message initial dans le thread a été supprimé. Vous avez été retiré du rôle membre.")
                    except discord.errors.Forbidden:
                        pass

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if isinstance(after.channel, discord.Thread) and after.channel.parent_id == PRESENTATION_CHANNEL_ID:
            thread_id = str(after.channel.id)
            if after.id == self.first_author_message.get(thread_id):
                author_id = str(self.thread_authors.get(thread_id))
                if "lien vers la capture d'écran" not in after.content:
                    member = after.guild.get_member(int(author_id))
                    if member:
                        role = member.guild.get_role(ROLE1_ID_FAFA)
                        if role:
                            await member.remove_roles(role)
                        try:
                            await member.send("Vous avez modifié votre message initial et retiré la capture d'écran. Vous avez été retiré du rôle membre.")
                        except discord.errors.Forbidden:
                            pass
                self.author_family_choices[author_id]['message_content'] = after.content
                self.save_family_choices()

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        author_id = str(after.id)
        if author_id in self.author_family_choices:
            self.author_family_choices[author_id]['pseudo'] = after.display_name
            self.save_family_choices()

    @commands.command(name="c")
    async def change_channel_message(self, ctx):
        command_full = ctx.invoked_with
        if command_full == "c" or (command_full.startswith("c") and command_full[1:].isdigit()):
            canal_number = int(command_full[1:]) if command_full != "c" else 1
            user_mention = ctx.author.mention
            family_choice = self.author_family_choices.get(ctx.author.id, "Yertirand")
            if family_choice == "Yertirand":
                button_family = "Yertirand"
                role_gardien = f"<@&{GARDIEN_YERTI_ROLE_ID}>"
            elif family_choice == "-GANG-":
                button_family = "-GANG-"
                role_gardien = f"<@&{GARDIEN_GANG_ROLE_ID}>"
            else:
                button_family = "Yertirand"
                role_gardien = f"<@&{GARDIEN_YERTI_ROLE_ID}>"
            embed = discord.Embed(
                title="Instructions pour rejoindre une famille",
                description=(
                    f":one: — Rejoins le canal {canal_number}.\n"
                    ":two: — Lance un <:hautparleur:1044376345456677005> `Haut-parleur` pour annoncer le nom de la famille que tu souhaites rejoindre.\n"
                    f":three: — Après avoir annoncé le nom de la famille, clique sur le bouton ci-dessous pour mentionner {user_mention}.\n"
                    f":four: — Si tu n'as pas reçu d'invitation après un certain temps, clique à nouveau sur le bouton `{button_family}` pour mentionner le rôle {role_gardien}."
                ),
                color=0x5865f2
            )
            view = View()
            view.add_item(Button(label="Mentionner pour invitation", style=discord.ButtonStyle.primary, custom_id="mention_for_invite"))
            await ctx.send(embed=embed, view=view, allowed_mentions=discord.AllowedMentions.all())
        else:
            await ctx.send("Format de commande incorrect. Utilisez `!c<number>` (par exemple, `!c1`).")

    @commands.command(name="restart")
    async def start_bot(self, ctx, author: discord.Member = None):
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("Vous n'avez pas l'autorisation d'exécuter cette commande.")
            return
        if author is None:
            await ctx.send("Veuillez mentionner un utilisateur valide.")
            return
        self.bot.last_pseudo_change = {}
        self.first_author_message = {}
        self.used_buttons = set()
        self.last_interaction_time = {}
        self.last_nickname_change_time = {}
        self.thread_initial_message_pending = set()
        self.family_selections = {}
        self.command_initiators = {}
        self.thread_authors[ctx.channel.id] = author.id
        thread = ctx.channel
        if isinstance(thread, discord.Thread):
            async for message in thread.history(oldest_first=True, limit=None):
                if len(message.attachments) > 0:
                    continue
                try:
                    await message.delete()
                    await asyncio.sleep(0.5)
                except discord.Forbidden:
                    continue
        embed = discord.Embed(title="Quel est ton pseudo de joueur ?", color=0x5865f2)
        view = View()
        button = Button(label="Définir le pseudo", style=discord.ButtonStyle.primary, custom_id="set_nickname")
        button.callback = self.set_nickname_callback
        view.add_item(button)
        await thread.send(embed=embed, view=view)
        self.thread_initial_message_pending.add(thread.id)
        self.first_author_message[thread.id] = ctx.message.id
        await ctx.send(f"Le bot a été redémarré avec succès pour {author.mention}.")

def generate_message(author_name):
    embed = discord.Embed(
        title=f"Bienvenue, {author_name} !",
        description=(
            f"- Tu as reçu le rôle <@&{ROLE1_ID_FAFA}>, te donnant accès à tous les salons.\n"
            "- Si tu as plusieurs personnages à LoL, modifie ton pseudo pour les inclure.\n"
            "- __Première étape__ : Lis les règles dans le salon <#1031609454527000616>.\n"
            "- __Deuxième étape__ : Choisis tes rôles dans le salon <#1056343806196318248>.\n"
            "- __Troisième étape__ : Choisis ta famille en cliquant sur l'un des boutons ci-dessous."
        ),
        color=0x5865f2
    )
    return embed

async def setup(bot):
    await bot.add_cog(PlayerSetup(bot))