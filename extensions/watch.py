import discord
from discord.ext import commands
from constants import *

# Commandes à surveiller pour les échanges et les dons
TRADE_WATCHED_COMMANDS = {"$trade", "$marryexchange", "$give", "$givek", "$givekakera"}

# Commandes à surveiller pour l'ajout d'images
IMAGE_WATCHED_COMMANDS = {"$ai", "$addimg"}


class Watch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user.name} has connected to Discord!")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignorer les messages du bot lui-même
        if message.author == self.bot.user:
            return

        # Surveiller les échanges et les dons
        if message.channel.id in [MUDAE_TRADE_CHANNEL_ID, MUDAE_KAKERA_CHANNEL_ID, MUDAE_SETTINGS_CHANNEL_2_ID]:
            await self.check_watched_commands(message, TRADE_WATCHED_COMMANDS, "échanges et dons de kakeras")

        # Surveiller l'ajout d'images
        if message.channel.id in [MUDAE_WISH_CHANNEL_ID, MUDAE_SETTINGS_CHANNEL_2_ID]:
            await self.check_watched_commands(message, IMAGE_WATCHED_COMMANDS, "ajouts d'images customisées")

    async def check_watched_commands(self, message, watched_commands, action_type):
        for cmd in watched_commands:
            if message.content.startswith(cmd):
                await self.notify_admin_and_warn_user(message, action_type)
                break

    async def notify_admin_and_warn_user(self, message, action_type):
        notify_user = await self.bot.fetch_user(NOTIFY_GSTAR)
        await notify_user.send(
            f"{message.author.mention} envoie le message suivant dans {message.channel.mention}: `{message.content}`. "
            f"Lien du message: {message.jump_url}"
        )

        additional_msg = ""
        if message.channel.id == MUDAE_SETTINGS_CHANNEL_2_ID:
            additional_msg = "\nNote : Les commandes sont limitées selon le contexte du canal."

        await message.channel.send(
            f"Gstar a été informé par MP de votre message et surveille vos {action_type}. "
            f"Des mesures sévères seront prises en cas d'abus, allant d'un mute jusqu'à un ban. {additional_msg}"
        )


async def setup(bot):
    await bot.add_cog(Watch(bot))