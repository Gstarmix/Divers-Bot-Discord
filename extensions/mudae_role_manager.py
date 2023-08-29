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
            print("Hello 0: Bot is not in the correct guild.")
            return
        print(f"{self.bot.user.name} has connected to Discord!")

    @commands.Cog.listener()
    async def on_message(self, message):
        print(repr(message.content))

        guild = message.guild
        if guild.id != GUILD_ID_TEST:
            print("Hello 1: Message is not from the correct guild.")
            return

        channel = message.channel
        if channel.id != GENERAL_CHANNEL_ID:
            print("Hello 2: Message is not from the correct channel.")
            return

        author = message.author
        if message.interaction:
            author = message.interaction.user

        command_name = None

        if not message.embeds:
            print("Hello 3: Message does not contain an embed.")
            return

        if message.application_id and message.interaction:
            command_name = message.interaction.name

        elif not author.bot and message.content in TEXT_COMMANDS:
            command_name = message.content

        if command_name in SLASH_COMMANDS or command_name in TEXT_COMMANDS:
            if author.id in self.user_timeout:
                print("Hello 4: Author is in timeout.")
                return

            role_membre_test = guild.default_role

            print("Hello 5: Setting permissions.")
            await channel.set_permissions(role_membre_test, send_messages=False)
            await channel.set_permissions(author, send_messages=True)

            self.user_timeout[author.id] = datetime.now() + timedelta(seconds=TIMEOUT_DURATION)

            await asyncio.sleep(TIMEOUT_DURATION)

            print("Hello 6: Resetting permissions.")
            await channel.set_permissions(role_membre_test, send_messages=True)
            await channel.set_permissions(author, send_messages=None)

            self.user_timeout.pop(author.id, None)

async def setup(bot):
    await bot.add_cog(MudaeRoleManager(bot))
