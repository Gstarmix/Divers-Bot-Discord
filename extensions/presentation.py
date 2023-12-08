import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
from constants import *
import time
import asyncio

class PseudoModal(Modal):
    def __init__(self, bot, user_id, thread):
        super().__init__(title="Entrez votre pseudo")
        self.bot = bot
        self.user_id = user_id
        self.thread = thread
        self.add_item(TextInput(label="Pseudo", placeholder="Ton pseudo ici", min_length=4, max_length=32))

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Vous n'êtes pas autorisé à changer ce pseudo.", ephemeral=True)
            return
        nickname = self.children[0].value.strip()
        current_time = time.time()
        last_changed = self.bot.last_pseudo_change.get(self.user_id, 0)
        if current_time - last_changed < 60:
            await interaction.response.send_message("Vous ne pouvez changer votre pseudo qu'une fois par minute.", ephemeral=True)
            return
        self.bot.last_pseudo_change[self.user_id] = current_time
        if not (4 <= len(nickname) <= 32):
            await interaction.response.send_message("Pseudo invalide. Il doit contenir entre 4 et 32 caractères.", ephemeral=True)
            return
        await self.thread.edit(name=f"Présentation de {nickname}")
        member = self.thread.guild.get_member(interaction.user.id)
        if member:
            await member.edit(nick=nickname)
            role = member.guild.get_role(ROLE1_ID_FAFA)
            if role:
                await member.add_roles(role)
        author_name = member.display_name if member else nickname
        embed = generate_message(author_name)
        view = View()
        view.add_item(Button(label="Yertirand", style=discord.ButtonStyle.primary, custom_id="yertirand"))
        view.add_item(Button(label="-GANG-", style=discord.ButtonStyle.primary, custom_id="gang"))
        view.add_item(Button(label="Visite Tutoriel LoL", style=discord.ButtonStyle.secondary, url="https://www.nostar.fr/lol"))
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

    async def set_nickname_callback(self, interaction):
        thread_id = interaction.channel_id
        if interaction.user.id != self.thread_authors.get(thread_id):
            await interaction.response.send_message("Vous n'êtes pas autorisé à définir ce pseudo.", ephemeral=True)
        else:
            thread = self.bot.get_channel(thread_id)
            await interaction.response.send_modal(PseudoModal(self.bot, interaction.user.id, thread))

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if thread.parent_id != PRESENTATION_CHANNEL_ID:
            return
        self.thread_initial_message_pending.add(thread.id)
        self.thread_authors[thread.id] = thread.owner_id

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or not message.author or message.author.bot:
            return
        if isinstance(message.channel, discord.Thread):
            thread_id = message.channel.id
            parent_id = message.channel.parent_id
        else:
            return
        if parent_id != PRESENTATION_CHANNEL_ID:
            return
        if thread_id in self.thread_initial_message_pending and not self.first_author_message.get(thread_id):
            embed = discord.Embed(title="Quel est ton pseudo de joueur ?", color=0x5865f2)
            view = View()
            if message.author.id == self.thread_authors.get(thread_id):
                button = Button(label="Définir le pseudo", style=discord.ButtonStyle.primary, custom_id="set_nickname")
                button.callback = self.set_nickname_callback
                view.add_item(button)
            await message.channel.send(embed=embed, view=view)
            self.thread_initial_message_pending.remove(thread_id)
            self.first_author_message[thread_id] = message.id

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data.get('custom_id')
            thread_id = interaction.channel_id
            author_id = self.thread_authors.get(thread_id)
            current_time = time.time()

            if custom_id in ["yertirand", "gang", "mention_for_invite"]:
                if interaction.user.id != author_id:
                    if interaction.response.is_done():
                        await interaction.followup.send("Vous n'êtes pas autorisé à utiliser ce bouton.", ephemeral=True)
                    else:
                        await interaction.response.send_message("Vous n'êtes pas autorisé à utiliser ce bouton.", ephemeral=True)
                    return

            if custom_id in ["yertirand", "gang"]:
                last_time = self.last_interaction_time.get(author_id, 0)
                if current_time - last_time < 300:
                    if interaction.response.is_done():
                        await interaction.followup.send("Veuillez attendre 5 minutes avant de réessayer.", ephemeral=True)
                    else:
                        await interaction.response.send_message("Veuillez attendre 5 minutes avant de réessayer.", ephemeral=True)
                    return
                else:
                    self.last_interaction_time[author_id] = current_time
                    role_id = "<@&1036402538620129351>" if custom_id == "yertirand" else "<@&923190695190233138>"
                    if interaction.response.is_done():
                        await interaction.followup.send(role_id, allowed_mentions=discord.AllowedMentions.all(), ephemeral=False)
                    else:
                        await interaction.response.send_message(role_id, allowed_mentions=discord.AllowedMentions.all(), ephemeral=False)

            elif custom_id == "mention_for_invite":
                command_initiator_id = self.command_initiators.get(thread_id)
                if command_initiator_id:
                    user_mention = f"<@{command_initiator_id}>"
                    if interaction.response.is_done():
                        await interaction.followup.send(user_mention, ephemeral=False)
                    else:
                        await interaction.response.send_message(user_mention, ephemeral=False)

    @commands.command(name="c", aliases=["c1", "c2", "c3", "c4", "c5", "c6", "c7", "c8"])
    async def change_channel_message(self, ctx):
        command_full = ctx.invoked_with
        if command_full.startswith("c") and command_full[1:].isdigit():
            canal_number = int(command_full[1:])
            user_mention = ctx.author.mention
            family_choice = self.family_selections.get(ctx.author.id)
            button_family = "Yertirand" if family_choice == "yertirand" else "Gang"
            role_gardien = "<@&1036402538620129351>" if family_choice == "yertirand" else "<@&923190695190233138>"
            self.command_initiators[ctx.channel.id] = ctx.author.id
            embed = discord.Embed(
                title="Instructions pour rejoindre une famille",
                description=(
                    f":one: — Rejoins le canal {canal_number}.\n"
                    ":two: — Lance un <:hautparleur:1044376345456677005> `Haut-parleur` pour annoncer le nom de la famille que tu souhaites rejoindre.\n"
                    f":three: — Après avoir annoncé le nom de la famille, clique sur le bouton ci-dessous pour mentionner {user_mention}.\n"
                    f":four: — Si tu n'as pas reçu d'invitation après un certain temps, clique à nouveau sur le bouton {button_family} pour mentionner le rôle {role_gardien}."
                ),
                color=0x5865f2
            )
            view = View()
            view.add_item(Button(label="Mentionner pour invitation", style=discord.ButtonStyle.primary, custom_id="mention_for_invite"))
            await ctx.send(embed=embed, view=view, allowed_mentions=discord.AllowedMentions.all())
        else:
            await ctx.send("Format de commande incorrect. Utilisez `!c<number>` (par exemple, `!c1`).")

    @commands.command(name="start")
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
            "- Tu as maintenant le rôle <@&923002565602467840>, qui te donne accès à tous nos salons.\n"
            "- Ton pseudo Discord a été mis à jour pour correspondre à celui de ta présentation.\n"
            "- Choisis ta famille en cliquant sur l'un des boutons ci-dessous."
        ),
        color=0x5865f2
    )
    return embed

async def setup(bot):
    await bot.add_cog(PlayerSetup(bot))
