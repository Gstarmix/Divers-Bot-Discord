import os
from dotenv import load_dotenv
from nextcord.ext import commands
import nextcord

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = nextcord.Intents.all()
intents.typing = False
intents.presences = False
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    
bot.load_extension("extensions.inscription")
bot.load_extension("extensions.mudae_help")
bot.load_extension("extensions.presentation")
bot.load_extension("extensions.question")

bot.run(TOKEN)