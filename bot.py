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
    
    await bot.load_extension("extensions.embed_logger")
    print("embed_logger extension loaded")
    
    
    # await bot.load_extension("extensions.mudae_listener")
    # print("mudae_listener extension loaded")
    
    # await bot.load_extension("extensions.thread_creator")
    # print("Thread Creator extension loaded")
    
    # await bot.load_extension("extensions.question")
    # print("Question extension loaded")

    # await bot.load_extension("extensions.image_forwarder")
    # print("Image Forwarder extension loaded")

    # await bot.load_extension("extensions.test_embed")
    # print("test_embed extension loaded")

    # await bot.load_extension("extensions.thread_manager")
    # print("thread_manager extension loaded")

    # await bot.load_extension("extensions.auto_repost_on_delete")
    # print("auto_repost_on_delete extension loaded")

    # await bot.load_extension("extensions.rules")
    # print("Rules extension loaded")

    # await bot.load_extension("extensions.presentation")
    # print("Presentation extension loaded")

    # await bot.load_extension("extensions.inscription")
    # print("Inscription extension loaded")
    
    # await bot.load_extension("extensions.command_check")
    # print("Command Check extension loaded")
    
    # await bot.load_extension("extensions.watch")
    # print("Watch extension loaded")
    
    # await bot.load_extension("extensions.mudae_info_scheduler")
    # print("Mudae Info Scheduler extension loaded")

    # await bot.load_extension("extensions.timeout_handler")
    # print("Timeout Handler extension loaded")

    # await bot.load_extension("extensions.role_management")
    # print("Role Management extension loaded")
    
    # await bot.load_extension("extensions.emoji_changer")
    # print("Emoji Changer extension loaded")
    
    # Uncomment the following lines as needed for other extensions
    # await bot.load_extension("extensions.faq_mudae_1")
    # print("FAQ Mudae 1 extension loaded")
    
    # await bot.load_extension("extensions.faq_mudae_2")
    # print("FAQ Mudae 2 extension loaded")
    
    # await bot.load_extension("extensions.channel_visibility_manager")
    # print("Channel Visibility Manager extension loaded")
    
    # await bot.load_extension("extensions.mudae_role_manager")
    # print("Mudae Role Manager extension loaded")

bot.run(TOKEN)
