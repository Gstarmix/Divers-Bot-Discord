import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
from constants import *
import time

class PseudoModal(Modal):
    def __init__(self, bot, user_id, thread):
        super().__init__(title="Entrez votre pseudo")
        self.bot = bot
        self.user_id = user_id
        self.thread = thread
        self.add_item(TextInput(label="Pseudo", placeholder="Ton pseudo ici", min_length=4, max_length=32))

    async def on_submit(self, interaction: discord.Interaction):
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

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if thread.parent_id != PRESENTATION_CHANNEL_ID:
            return
        embed = discord.Embed(title="Quel est ton pseudo de joueur ?", color=0x5865f2)
        view = View()
        button = Button(label="Définir le pseudo", style=discord.ButtonStyle.primary, custom_id="set_nickname")
        button.callback = lambda interaction: interaction.response.send_modal(PseudoModal(self.bot, interaction.user.id, thread))
        view.add_item(button)
        await thread.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.guild or not message.author or message.author.bot:
            return
        if message.channel.type == discord.ChannelType.private:
            return
        if isinstance(message.channel, discord.Thread):
            thread_id = message.channel.id
            parent_id = message.channel.parent_id
        else:
            return
        if parent_id != PRESENTATION_CHANNEL_ID:
            return
        if thread_id not in self.first_author_message:
            self.first_author_message[thread_id] = message.id
        allowed_roles = [CHEF_SINGE_ROLE_ID, GARDIEN_YERTI_ROLE_ID, GARDIEN_GANG_ROLE_ID]
        is_author_first_message = message.id == self.first_author_message[thread_id]
        has_allowed_role = any(role.id in allowed_roles for role in message.author.roles)
        if not (is_author_first_message or has_allowed_role):
            await message.delete()
            await message.author.send("Vous n'êtes pas autorisé à écrire dans ce fil.")

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data.get('custom_id')
            if custom_id in ["yertirand", "gang"]:
                if "yertirand_gang_used" not in self.used_buttons:
                    self.used_buttons.add("yertirand_gang_used")
                    role_id = "<@&1036402538620129351>" if custom_id == "yertirand" else "<@&923190695190233138>"
                    await interaction.response.send_message(role_id, ephemeral=False)
                    for component in interaction.message.components:
                        for item in component.children:
                            if item.custom_id in ["yertirand", "gang"]:
                                item.disabled = True
                    await interaction.message.edit(view=View.from_message(interaction.message))

    @commands.command(name="c")
    async def change_channel_message(self, ctx, canal_number: int):
        user_mention = ctx.author.mention
        embed = discord.Embed(
            title="Instructions pour rejoindre une famille",
            description=(
                f":one: — Rejoins le Canal {canal_number}.\n"
                ":two: — Lance un <:hautparleur:1044376345456677005> `Haut-parleur` pour annoncer le nom de la famille que tu souhaites rejoindre.\n"
                f":three: — Après avoir annoncé le nom de la famille, clique sur le bouton ci-dessous pour mentionner {user_mention}.\n"
                ":four: — Si tu n'as pas reçu d'invitation après un certain temps, mentionne à nouveau le rôle gardien dans ta présentation."
            ),
            color=0x5865f2
        )
        view = View()
        view.add_item(Button(label="Mentionner pour invitation", style=discord.ButtonStyle.primary, custom_id="mention_for_invite"))
        await ctx.send(embed=embed, view=view)

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