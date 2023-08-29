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
        if guild is None:
            print("Bot is not in the guild.")
            return
        print(f"{self.bot.user.name} has connected to Discord!")

    @commands.Cog.listener()
    async def on_message(self, message):
        guild = self.bot.get_guild(GUILD_ID_TEST)
        if guild is None:
            print("Bot is not in the guild.")
            return

        # Check if the message is a slash command
        if message.application_id is not None and message.interaction is not None:
            command_name = message.interaction.name  # Get the name of the slash command

            # Check if the command is in the list of allowed slash commands
            if f"/{command_name}" in SLASH_COMMANDS:
                user = message.interaction.user  # Get the user who invoked the slash command

                # Log the details
                print(f"Slash command detected: {command_name}")
                print(f"User who invoked the command: {user.name}#{user.discriminator}")

        elif not message.author.bot and message.channel.id == GENERAL_CHANNEL_ID:
            if message.content in SLASH_COMMANDS or message.content in TEXT_COMMANDS:
                role_membre_test = discord.utils.get(guild.roles, id=MEMBRE_TEST_ID)
                role_singe_mudae = discord.utils.get(guild.roles, id=SINGE_MUDAE_ID)

                if role_membre_test is None:
                    print("MEMBRE_TEST role not found.")
                    return

                if role_singe_mudae is None:
                    print("SINGE_MUDAE role not found.")
                    return

                channel = guild.get_channel(GENERAL_CHANNEL_ID)
                if channel is None:
                    print("Channel not found.")
                    return

                await message.author.add_roles(role_singe_mudae)
                await channel.set_permissions(role_membre_test, send_messages=False)
                await channel.set_permissions(message.author, send_messages=True)

                self.user_timeout[message.author.id] = datetime.now() + timedelta(seconds=TIMEOUT_DURATION)

                asyncio.create_task(self.reset_role_and_channel_permissions(message.author.id))

    async def reset_role_and_channel_permissions(self, user_id):
        await asyncio.sleep(TIMEOUT_DURATION)

        guild = self.bot.get_guild(GUILD_ID_TEST)
        role_membre_test = discord.utils.get(guild.roles, id=MEMBRE_TEST_ID)
        role_singe_mudae = discord.utils.get(guild.roles, id=SINGE_MUDAE_ID)
        channel = guild.get_channel(GENERAL_CHANNEL_ID)
        user = guild.get_member(user_id)

        if role_membre_test is None or role_singe_mudae is None or channel is None or user is None:
            return

        await user.remove_roles(role_singe_mudae)
        await channel.set_permissions(role_membre_test, send_messages=True)
        await channel.set_permissions(user, send_messages=None)

        del self.user_timeout[user_id]

async def setup(bot):
    await bot.add_cog(MudaeRoleManager(bot))
