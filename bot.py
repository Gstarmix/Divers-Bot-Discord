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

bot.load_extension("extensions.inscription")
bot.load_extension("extensions.mudae_help")
bot.load_extension("extensions.presentation")
bot.load_extension("extensions.question")

bot.run(TOKEN)
