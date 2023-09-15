import os
from dotenv import load_dotenv
import discord
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

PREFIX = "!"
intents = discord.Intents.all()

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    await bot.load_extension("extensions.inscription")
    await bot.load_extension("extensions.thread_creator")
    await bot.load_extension("extensions.presentation")
    await bot.load_extension("extensions.question")
    await bot.load_extension("extensions.command_check")
    await bot.load_extension("extensions.watch")
    await bot.load_extension("extensions.mudae_info_scheduler")
    # await bot.load_extension("extensions.faq_mudae_1")
    # await bot.load_extension("extensions.faq_mudae_2")
    # await bot.load_extension("extensions.emoji_changer")
    # await bot.load_extension("extensions.channel_visibility_manager")
    # await bot.load_extension("extensions.mudae_role_manager")

bot.run(TOKEN)

