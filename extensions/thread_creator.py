import asyncio
import datetime
import discord
from discord.ext import commands
from constants import *


class ThreadCreator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_message_times = {}
        self.thread_names = {
            MUDAE_HELP_CHANNEL_ID: "Aide Mudae",
            SUGGESTION_GSTAR_CHANNEL_ID: "Suggestion",
            SUGGESTION_FAFA_CHANNEL_ID: "Suggestion",
            VIDEO_CHANNEL_ID: "Vidéo",
            MEMES_CHANNEL_ID: "Meme",
            VDO_VDM_CHANNEL_ID: "Anecdote",
            RECHERCHE_KELKIN_CHANNEL_ID: "Recherche",
            COMMERCES_INT4_CHANNEL_ID: "Commerce",
            ACTIVITES_INT4_CHANNEL_ID: "Activité",
            MUDAE_IDEAS_CHANNEL_ID: "Idée Mudae"
        }
        self.channel_delays = {
            MUDAE_HELP_CHANNEL_ID: 600,
            SUGGESTION_GSTAR_CHANNEL_ID: 600,
            SUGGESTION_FAFA_CHANNEL_ID: 600,
            VIDEO_CHANNEL_ID: 600,
            VDO_VDM_CHANNEL_ID: 600,
            RECHERCHE_KELKIN_CHANNEL_ID: 600,
            COMMERCES_INT4_CHANNEL_ID: 600,
            ACTIVITES_INT4_CHANNEL_ID: 600,
            MUDAE_IDEAS_CHANNEL_ID: 600
        }

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id in self.thread_names.keys() and not message.author.bot:
            now = datetime.datetime.now()
            if message.author.id not in self.user_message_times:
                self.user_message_times[message.author.id] = {}
            if message.channel.id in self.user_message_times[message.author.id] and message.channel.id in self.channel_delays and (now - self.user_message_times[message.author.id][message.channel.id]).total_seconds() < self.channel_delays[message.channel.id]:
                await message.author.send(f"Vous devez attendre {self.channel_delays[message.channel.id] // 60} minutes avant de pouvoir envoyer un nouveau message. Si besoin, veuillez modifier votre dernier message.")
                try:
                    await message.delete()
                except discord.NotFound:
                    print("Message déjà supprimé.")
            else:
                self.user_message_times[message.author.id][message.channel.id] = now
                try:
                    # thread_name = self.thread_names[message.channel.id]
                    thread_name = f"{self.thread_names[message.channel.id]} de {message.author.name}"
                    thread = await message.channel.create_thread(message=message, name=thread_name)
                    await asyncio.sleep(5)
                    await thread.send("Réagissez ici !")
                except Exception as e:
                    print(f"Erreur lors de la création du fil : {e}")


async def setup(bot):
    await bot.add_cog(ThreadCreator(bot))
