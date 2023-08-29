import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import asyncio
from constants import *  # Assurez-vous que ce fichier est dans le même répertoire et correctement configuré

# Durée de l'attente avant de réinitialiser les permissions du rôle et du canal (en secondes)
TIMEOUT_DURATION = 5

# Liste des commandes acceptées
SLASH_COMMANDS = ["wa", "ha", "ma", "wg", "hg", "mg"]
TEXT_COMMANDS = ["$wa", "$ha", "$ma", "$wg", "$hg", "$mg", "$rolls", "$bw", "$bk", "$tu", "$mu", "$ku", "$rt", "$vote", "$daily"]

class MudaeRoleManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_timeout = {}

    @commands.Cog.listener()
    async def on_ready(self):
        guild = self.bot.get_guild(GUILD_ID_TEST)
        if guild is None:
            print("Bot is not in the guild.")
            return
        print(f"{self.bot.user.name} has connected to Discord!")

    @commands.Cog.listener()
    async def on_message(self, message):
        guild = self.bot.get_guild(GUILD_ID_TEST)
        if guild is None:
            return

        if not message.author.bot and message.channel.id == GENERAL_CHANNEL_ID:
            if message.content in TEXT_COMMANDS:
                await self.manage_roles(message)

    @commands.Cog.listener()
    async def on_interaction(self, interaction):
        if interaction.type == discord.InteractionType.application_command:
            command = interaction.data["name"]
            if command in SLASH_COMMANDS:
                await self.manage_roles(interaction)

    async def manage_roles(self, event):
        guild = self.bot.get_guild(GUILD_ID_TEST)
        role_membre_test = guild.get_role(MEMBRE_TEST_ID)
        role_singe_mudae = guild.get_role(SINGE_MUDAE_ID)

        if role_membre_test is None or role_singe_mudae is None:
            print("Roles not found.")
            return
        
        channel = guild.get_channel(GENERAL_CHANNEL_ID)
        if channel is None:
            print("Channel not found.")
            return

        # Donne le rôle SINGE_MUDAE à l'utilisateur
        await event.author.add_roles(role_singe_mudae)

        # Met à jour les permissions du canal
        await channel.set_permissions(role_membre_test, send_messages=False)
        await channel.set_permissions(event.author, send_messages=True)

        # Met à jour ou définit le délai d'expiration pour l'utilisateur
        self.user_timeout[event.author.id] = datetime.now() + timedelta(seconds=TIMEOUT_DURATION)

        # Lance la tâche de réinitialisation du rôle
        self.reset_role_and_channel_permissions.start()

    @tasks.loop(seconds=1)
    async def reset_role_and_channel_permissions(self):
        current_time = datetime.now()
        guild = self.bot.get_guild(GUILD_ID_TEST)
        
        role_membre_test = guild.get_role(MEMBRE_TEST_ID)
        role_singe_mudae = guild.get_role(SINGE_MUDAE_ID)

        if role_membre_test is None or role_singe_mudae is None:
            return

        channel = guild.get_channel(GENERAL_CHANNEL_ID)
        if channel is None:
            return

        for user_id, timeout in list(self.user_timeout.items()):
            user = guild.get_member(user_id)

            if current_time >= timeout:
                # Retire le rôle SINGE_MUDAE de l'utilisateur
                await user.remove_roles(role_singe_mudae)

                # Réinitialise les permissions du canal
                await channel.set_permissions(role_membre_test, send_messages=True)
                await channel.set_permissions(user, send_messages=None)

                # Retire l'utilisateur du dictionnaire de délai d'expiration
                del self.user_timeout[user_id]

async def setup(bot):
    await bot.add_cog(MudaeRoleManager(bot))
