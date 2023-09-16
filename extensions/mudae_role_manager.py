import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio
from constants import *

TIMEOUT_DURATION = 5

SLASH_COMMANDS = {"wa", "ha", "ma", "wg", "hg", "mg"}
TEXT_COMMANDS = {"$w", "$h", "$m", "$wa", "$ha", "$ma", "$wg", "$hg", "$mg"}


class MudaeRoleManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_timeout = {}

    @commands.Cog.listener()
    async def on_ready(self):
        guild = self.bot.get_guild(GUILD_ID_GSTAR)
        if not guild:
            return
        print(f"{self.bot.user.name} has connected to Discord!")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        guild = message.guild
        if guild.id != GUILD_ID_GSTAR:
            return

        channel = message.channel
        if channel.id != MUDAE_WAIFUS_CHANNEL_ID:
            return

        command_name = message.content

        author = message.author
        if message.interaction:
            author = message.interaction.user
            command_name = message.interaction.name
            if not message.embeds:
                return

        if author.bot:
            if "la roulette est limitée" in command_name:
                await channel.set_permissions(guild.default_role, send_messages=True)
                await channel.set_permissions(author, send_messages=None)
                self.user_timeout.pop(author.id, None)
            return

        if author.id in self.user_timeout:
            return

        if command_name not in SLASH_COMMANDS and command_name not in TEXT_COMMANDS:
            return

        chan_perms = channel.overwrites_for(guild.default_role)
        chan_perms.update(send_messages=False, view_channel=True)
        old_user_perms = channel.overwrites_for(author)
        user_perms = channel.overwrites_for(author)
        user_perms.update(send_messages=True)

        await channel.set_permissions(author, overwrite=user_perms)
        await channel.set_permissions(guild.default_role, overwrite=chan_perms)

        self.user_timeout[author.id] = datetime.now() + timedelta(seconds=TIMEOUT_DURATION)

        await asyncio.sleep(TIMEOUT_DURATION)

        chan_perms = channel.overwrites_for(guild.default_role)
        chan_perms.update(send_messages=True, view_channel=True)
        await channel.set_permissions(guild.default_role, overwrite=chan_perms)
        await channel.set_permissions(author, overwrite=old_user_perms)

        self.user_timeout.pop(author.id, None)


async def setup(bot):
    await bot.add_cog(MudaeRoleManager(bot))
