import discord
from discord.ext import commands
from constants import *

# Commandes à surveiller
WATCHED_COMMANDS = {"$trade", "$marryexchange", "$give", "$givek", "$givekakera"}

class TradeWatch(commands.Cog):
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

        if message.channel.id not in [MUDAE_TRADE_CHANNEL_ID, MUDAE_SETTINGS_CHANNEL_2_ID]:
            return

        command_used = None
        for cmd in WATCHED_COMMANDS:
            if message.content.startswith(cmd):
                command_used = cmd
                break

        if command_used:
            notify_user = await self.bot.fetch_user(NOTIFY_GSTAR)
            await notify_user.send(
                f"{message.author.mention} utilise la commande `{command_used}` dans {message.channel.mention}.\n"
                f"Lien du message: {message.jump_url}"
            )

            additional_msg = ""
            if message.channel.id == MUDAE_SETTINGS_CHANNEL_2_ID:
                additional_msg = "\nNote: Les commandes `$trade` et `$givek` sont limitées au tutoriel. Vous pouvez seulement échanger et donner un kakera. Utilisez `$trade @User 1 ka` et `$givek 1 ka`."

            await message.channel.send(
                f"<@{message.author.id}>\n<a:tention:1095042549384757299> <@{NOTIFY_GSTAR}> a été informé par MP que vous utilisez la commande `{command_used}` et surveille vos échanges et ventes de prêt. "
                f"Des mesures sévères seront prises en cas d'abus, allant d'un mute jusqu'à un ban. <a:tention:1095042549384757299>{additional_msg}"
            )

async def setup(bot):
    await bot.add_cog(TradeWatch(bot))
