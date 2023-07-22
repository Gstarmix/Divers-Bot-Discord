import os
import asyncio
from dotenv import load_dotenv
from nextcord.ext import commands
import nextcord

load_dotenv()
TOKENS = {
    'inscription_bot': os.getenv('INSCRIPTION_BOT_TOKEN'),
    'mudae_help_bot': os.getenv('MUDAE_HELP_BOT_TOKEN'),
    'question_bot': os.getenv('QUESTION_BOT_TOKEN'),
    'presentation_bot': os.getenv('PRESENTATION_BOT_TOKEN'),
}

intents = nextcord.Intents.all()
intents.typing = False
intents.presences = False
intents.messages = True

def run_bot(bot_name):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    bot = commands.Bot(command_prefix='!', intents=intents, loop=loop)

    @bot.event
    async def on_ready():
        print(f'{bot.user.name} has connected to Discord!')

        script_dir = os.path.dirname(os.path.abspath(__file__))  
        bot_dir = os.path.join(script_dir, bot_name)
        events_dir = os.path.join(bot_dir, 'events')  
        for filename in os.listdir(events_dir):
            if filename.endswith('.py'):
                module_name = f"{bot_name}.events.{filename[:-3]}"
                bot.load_extension(module_name)

    bot.run(TOKENS[bot_name])

run_bot('inscription_bot')
run_bot('mudae_help_bot')
run_bot('question_bot')
run_bot('presentation_bot')
