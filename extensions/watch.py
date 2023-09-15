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
            for cmd in TRADE_WATCHED_COMMANDS:
                if message.content.startswith(cmd):
                    await self.notify_and_warn(message, "échanges et dons de kakeras")
                    break

        # Surveiller l'ajout d'images
        if message.channel.id in [MUDAE_WISH_CHANNEL_ID, MUDAE_SETTINGS_CHANNEL_2_ID]:
            for cmd in IMAGE_WATCHED_COMMANDS:
                if message.content.startswith(cmd):
                    await self.notify_and_warn(message, "ajouts d'images customisées")
                    break

    async def notify_and_warn(self, message, action_type):
        notify_user = await self.bot.fetch_user(NOTIFY_GSTAR)
        await notify_user.send(
            f"{message.author.mention} envoie le message suivant dans {message.channel.mention}: `{message.content}`. "
            f"Lien du message: {message.jump_url}"
        )

        additional_msg = ""
        if message.channel.id == MUDAE_SETTINGS_CHANNEL_2_ID:
            if action_type == "échanges et ventes de prêt":
                additional_msg = "\nNote : Dans cette instance, les commandes `$trade` et `$givek` sont limitées au tutoriel. Vous pouvez seulement échanger et donner un kakera. Utilisez `$trade @User 1 ka` et `$givek @User 1 ka`."
            else:
                additional_msg = "\nNote : Les commandes sont limitées selon le contexte du canal."

        await message.channel.send(
            f"`<@{NOTIFY_GSTAR}>` a été informé par MP de votre message et surveille vos {action_type}. "
            f"Des mesures sévères seront prises en cas d'abus, allant d'un mute jusqu'à un ban. {additional_msg}"
        )

async def setup(bot):
    await bot.add_cog(Watch(bot))
