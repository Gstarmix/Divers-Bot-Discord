from random import choice, random
import discord
from discord.ext import commands
from constants import *

SLASH_COMMANDS = {"wa", "ha", "ma", "wg", "hg", "mg", "wx", "hx", "mx"}
TEXT_COMMANDS = {"$w", "$h", "$m", "$wa", "$ha", "$ma", "$wg", "$hg", "$mg"}

messages = [
    {
        "description": "Pour vous initier à Mudae, utilisez la commande `$tuto` dans le salon <#1132979275469955172>. Notez que ce salon n'accepte pas d'autres commandes."
    },
]


class FaqMudae1(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user.name} has connected to Discord!")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id != MUDAE_WAIFUS_CHANNEL_ID:
            return
        
        command_type = None
        command_name = message.content
        user = message.author  # By default, use the message author

        if message.interaction:
            command_name = message.interaction.name
            command_type = 'slash'
            user = message.interaction.user  # Use the interaction user if available
        
        if command_name in SLASH_COMMANDS:
            command_type = 'slash'
        elif command_name in TEXT_COMMANDS:
            command_type = 'text'

        if command_type:
            if random() <= 0.1:
                selected_message = choice(messages)
                await message.channel.send(
                    f"<@{user.id}> {selected_message['description']}"
                )


async def setup(bot):
    await bot.add_cog(FaqMudae1(bot))
