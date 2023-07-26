import datetime
import discord
from discord.ext import commands
from constants import MUDAE_HELP_CHANNEL_ID, SUGGESTION_GSTAR_CHANNEL_ID, SUGGESTION_FAFA_CHANNEL_ID, VIDEO_CHANNEL_ID, MEMES_CHANNEL_ID, VDO_VDM_CHANNEL_ID, RECHERCHE_KELKIN_CHANNEL_ID

class ThreadCreator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_message_times = {} 
        self.channel_messages = {
            MUDAE_HELP_CHANNEL_ID: "Demande d'aide pour Mudae reçue. Nous l'examinerons bientôt.",
            SUGGESTION_GSTAR_CHANNEL_ID: "Suggestion reçue. Nous l'examinerons bientôt.",
            SUGGESTION_FAFA_CHANNEL_ID: "Suggestion reçue. Nous l'examinerons bientôt.",
            VIDEO_CHANNEL_ID: "Vidéo soumise. Hâte de la regarder ! Les commentaires suivront.",
            MEMES_CHANNEL_ID: "Meme soumis. Hâte de rire ! Les commentaires suivront.",
            VDO_VDM_CHANNEL_ID: "Anecdote soumise. Hâte de la lire ! Les commentaires suivront.",
            RECHERCHE_KELKIN_CHANNEL_ID: "Demande de recherche reçue. Nous l'examinerons bientôt.",
        }
        self.thread_names = {
            MUDAE_HELP_CHANNEL_ID: "Aide Mudae",
            SUGGESTION_GSTAR_CHANNEL_ID: "Suggestion",
            SUGGESTION_FAFA_CHANNEL_ID: "Suggestion",
            VIDEO_CHANNEL_ID: "Vidéo",
            MEMES_CHANNEL_ID: "Meme",
            VDO_VDM_CHANNEL_ID: "Anecdote",
            RECHERCHE_KELKIN_CHANNEL_ID: "Recherche",
        }
        self.channel_delays = {
            MUDAE_HELP_CHANNEL_ID: 600,
            SUGGESTION_GSTAR_CHANNEL_ID: 600,
            SUGGESTION_FAFA_CHANNEL_ID: 600,
            VIDEO_CHANNEL_ID: 600,
            MEMES_CHANNEL_ID: 600,
            VDO_VDM_CHANNEL_ID: 600,
            RECHERCHE_KELKIN_CHANNEL_ID: 600,
        }

    @commands.Cog.listener()
    async def on_message(self, message):
        print(f"Message reçu de {message.author.name} dans le canal {message.channel.id}")
        if message.channel.id in self.channel_messages.keys() and not message.author.bot:
            now = datetime.datetime.now()
            if message.author.id not in self.user_message_times:
                self.user_message_times[message.author.id] = {}
            if message.channel.id in self.user_message_times[message.author.id] and (now - self.user_message_times[message.author.id][message.channel.id]).total_seconds() < self.channel_delays[message.channel.id]:
                await message.author.send(f"Vous devez attendre {self.channel_delays[message.channel.id] // 60} minutes avant de pouvoir envoyer un nouveau message. Si besoin, veuillez modifier votre dernier message.")
                await message.delete()
            else:
                self.user_message_times[message.author.id][message.channel.id] = now
                try:
                    print("Création du fil...")
                    thread_name = f"{self.thread_names[message.channel.id]} de {message.author.name}"
                    thread = await message.channel.create_thread(message=message, name=thread_name)
                    await thread.send(self.channel_messages[message.channel.id])
                except Exception as e:
                    print(f"Erreur lors de la création du fil : {e}")

async def setup(bot):
    await bot.add_cog(ThreadCreator(bot))