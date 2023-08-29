import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import asyncio
from constants import * 
TIMEOUT_DURATION = 5

SLASH_COMMANDS = ["/wa", "/ha", "/ma", "/wg", "/hg", "/mg"]
TEXT_COMMANDS = ["$wa", "$ha", "$ma", "$wg", "$hg", "$mg", "$rolls", "$bw", "$bk", "$tu", "$mu", "$ku", "$rt", "$vote", "$daily"]

class MudaeRoleManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_timeout = {}

    @commands.Cog.listener()
    async def on_ready(self):
        guild = self.bot.get_guild(GUILD_ID_TEST)
        if not guild:
            print("Bot is not in the guild.")
            return
        print(f"{self.bot.user.name} has connected to Discord!")

    @commands.Cog.listener()
    async def on_message(self, message):
        guild = message.guild
        if guild.id != GUILD_ID_TEST:
            print("Bot is not in the guild.")
            return

        # Initialize command_name to None
        command_name = None

        # Check if the message is a slash command
        if message.application_id and message.interaction:
            command_name = f"/{message.interaction.name}"

        # Or if it's a text command
        elif not message.author.bot and message.content in TEXT_COMMANDS:
            command_name = message.content

        # If a valid command is detected
        if command_name in SLASH_COMMANDS or command_name in TEXT_COMMANDS:
            # Skip if the user is already in a timeout
            if message.author.id in self.user_timeout:
                return

            role_membre_test = guild.get_role(MEMBRE_TEST_ID)
            role_singe_mudae = guild.get_role(SINGE_MUDAE_ID)

            if not role_membre_test or not role_singe_mudae:
                print("One of the roles not found.")
                return

            channel = guild.get_channel(GENERAL_CHANNEL_ID)
            if not channel:
                print("Channel not found.")
                return

            await message.author.add_roles(role_singe_mudae)
            await channel.set_permissions(role_membre_test, send_messages=False)
            await channel.set_permissions(message.author, send_messages=True)

            self.user_timeout[message.author.id] = datetime.now() + timedelta(seconds=TIMEOUT_DURATION)

            await self.reset_role_and_channel_permissions(message.author.id)

    async def reset_role_and_channel_permissions(self, user_id):
        await asyncio.sleep(TIMEOUT_DURATION)

        guild = self.bot.get_guild(GUILD_ID_TEST)
        role_membre_test = guild.get_role(MEMBRE_TEST_ID)
        role_singe_mudae = guild.get_role(SINGE_MUDAE_ID)
        channel = guild.get_channel(GENERAL_CHANNEL_ID)
        user = guild.get_member(user_id)

        if not (role_membre_test and role_singe_mudae and channel and user):
            return

        await user.remove_roles(role_singe_mudae)
        await channel.set_permissions(role_membre_test, send_messages=True)
        await channel.set_permissions(user, send_messages=None)

        self.user_timeout.pop(user_id, None)

async def setup(bot):
    await bot.add_cog(MudaeRoleManager(bot))
