import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
from constants import *
import json
import time
import asyncio

FAMILY_CHOICES_PATH = "extensions/family_choices.json"

def current_time():
    return time.time()

def create_button(label, style, custom_id, url=None):
    return Button(label=label, style=style, custom_id=custom_id, url=url)

def create_embed(title, description, color=0x5865f2):
    return discord.Embed(title=title, description=description, color=color)

def generate_message(author_name):
    return discord.Embed(
        title=f"Bienvenue, {author_name} !",
        description=(
            "- Tu as reçu le rôle <@&ROLE1_ID_FAFA>, te donnant accès à tous les salons.\n"
            "- Si tu as plusieurs personnages à LoL, modifie ton pseudo pour les inclure.\n"
            "- Première étape : Lis les règles dans le salon <#1031609454527000616>.\n"
            "- Deuxième étape : Choisis tes rôles dans le salon <#1056343806196318248>.\n"
            "- Troisième étape : Choisis ta famille en cliquant sur l'un des boutons ci-dessous."
        ),
        color=0x5865f2
    )

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
        if not (4 <= len(nickname) <= 32):
            await interaction.response.send_message("Pseudo invalide. Il doit contenir entre 4 et 32 caractères.", ephemeral=True)
            return
        if current_time() - self.player_setup.bot.last_pseudo_change.get(self.user_id, 0) < 300:
            await interaction.response.send_message("Vous ne pouvez changer votre pseudo qu'une fois toutes les 5 minutes.", ephemeral=True)
            return
        self.player_setup.bot.last_pseudo_change[self.user_id] = current_time()
        user_data = self.player_setup.author_family_choices.get(self.user_id, {
            "pseudo": None,
            "message_content": None,
            "family_choice": None
        })
        user_data['pseudo'] = nickname
        self.player_setup.author_family_choices[self.user_id] = user_data
        self.player_setup.save_family_choices()
        member = self.thread.guild.get_member(interaction.user.id)
        if member:
            await member.edit(nick=nickname)
            role = member.guild.get_role(ROLE1_ID_FAFA)
            if role:
                await member.add_roles(role)
        author_name = member.display_name if member else nickname
        embed = generate_message(author_name)
        view = View()
        view.add_item(create_button("Yertirand", discord.ButtonStyle.primary, "yertirand"))
        view.add_item(create_button("-GANG-", discord.ButtonStyle.primary, "gang"))
        view.add_item(create_button("Tutoriel LoL", discord.ButtonStyle.secondary, "https://www.nostar.fr/lol"))
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
        if current_time() - self.last_author_interaction.get(thread_id, 0) > 600:
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
        if not message.guild or message.author.bot:
            return
        if isinstance(message.channel, discord.Thread) and message.channel.parent_id == PRESENTATION_CHANNEL_ID:
            author_id = str(message.author.id)
            user_data = self.author_family_choices.get(author_id, {
                "pseudo": None,
                "message_content": None,
                "family_choice": None
            })
            user_data['message_content'] = message.content
            self.author_family_choices[author_id] = user_data
            self.save_family_choices()
            self.last_author_interaction[message.channel.id] = current_time()

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get('custom_id')
        thread_id = interaction.channel_id
        author_id = str(interaction.user.id)
        if custom_id in ["yertirand", "gang"]:
            last_time = self.last_interaction_time.get(author_id, 0)
            if current_time() - last_time < 300:
                await interaction.response.send_message("Veuillez attendre 5 minutes avant de réessayer.", ephemeral=True)
                return
            self.author_family_choices[author_id]['family_choice'] = custom_id.capitalize()
            self.save_family_choices()
            self.last_interaction_time[author_id] = current_time()
        elif custom_id == "mention_for_invite":
            command_initiator_id = self.command_initiators.get(thread_id)
            if command_initiator_id:
                await interaction.response.send_message(f"<@{command_initiator_id}>", ephemeral=False)
        self.last_author_interaction[interaction.channel.id] = current_time()

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
            family_choice = self.author_family_choices.get(ctx.author.id, {}).get("family_choice", "Yertirand")
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

async def setup(bot):
    await bot.add_cog(PlayerSetup(bot))