import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import asyncio
from constants import *

TIMEOUT_DURATION = 5

SLASH_COMMANDS = ["wa", "ha", "ma", "wg", "hg", "mg"]
TEXT_COMMANDS = ["$wa", "$ha", "$ma", "$wg", "$hg", "$mg", "$rolls", "$bw", "$bk", "$tu", "$mu", "$ku", "$rt", "$vote", "$daily"]

class MudaeRoleManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_timeout = {}

    @commands.Cog.listener()
    async def on_ready(self):
        guild = self.bot.get_guild(GUILD_ID_TEST)
        if not guild:
            return
        print(f"{self.bot.user.name} has connected to Discord!")

    @commands.Cog.listener()
    async def on_message(self, message):
        guild = message.guild
        if guild.id != GUILD_ID_TEST:
            return

        channel = message.channel
        if channel.id != GENERAL_CHANNEL_ID:
            return

        author = message.author
        if message.interaction:
            author = message.interaction.user

        if author.id in self.user_timeout:
            return

        if author.bot:
            return

        command_name = None

        if message.interaction:
            command_name = message.interaction.name
            if not message.embeds:
                return

        if message.content:
            command_name = message.content

        if command_name not in SLASH_COMMANDS and command_name not in TEXT_COMMANDS:
            return

        role_membre_test = guild.default_role

        await channel.set_permissions(role_membre_test, send_messages=False)
        await channel.set_permissions(author, send_messages=True)

        self.user_timeout[author.id] = datetime.now() + timedelta(seconds=TIMEOUT_DURATION)

        await asyncio.sleep(TIMEOUT_DURATION)

        await channel.set_permissions(role_membre_test, send_messages=True)
        await channel.set_permissions(author, send_messages=None)

        self.user_timeout.pop(author.id, None)

async def setup(bot):
    await bot.add_cog(MudaeRoleManager(bot))
