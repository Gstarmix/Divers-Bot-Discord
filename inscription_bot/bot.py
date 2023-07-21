import os
from dotenv import load_dotenv
from nextcord.ext import commands
import nextcord

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = nextcord.Intents.default()
intents.typing = False
intents.presences = False

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    
    script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the directory of the current script
    events_dir = os.path.join(script_dir, 'events')  # Use it to define the path to the 'events' directory

    for filename in os.listdir(events_dir):
        if filename.endswith('.py'):
            module_name = f"events.{filename[:-3]}"
            await bot.load_extension(module_name)

bot.run(TOKEN)
