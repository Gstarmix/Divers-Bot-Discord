import datetime
import discord
from discord.ext import commands
from constants import MUDAE_HELP_CHANNEL_ID, SUGGESTION_GSTAR_CHANNEL_ID, SUGGESTION_FAFA_CHANNEL_ID, VIDEO_CHANNEL_ID, MEMES_CHANNEL_ID, VDO_VDM_CHANNEL_ID, RECHERCHE_KELKIN_CHANNEL_ID

class ThreadCreator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_message_times = {}  # This will now store a dictionary for each user
        self.channel_messages = {
            MUDAE_HELP_CHANNEL_ID: "Votre demande d'aide concernant le bot Mudae a été prise en compte. Nous l'examinerons attentivement et vous fournirons une réponse dans les plus brefs délais. Merci de votre patience !",
            SUGGESTION_GSTAR_CHANNEL_ID: "Votre suggestion a été prise en compte. Nous l'examinerons et vous fournirons une réponse dans les plus brefs délais. Merci de votre patience !",
            SUGGESTION_FAFA_CHANNEL_ID: "Votre suggestion a été prise en compte. Nous l'examinerons et vous fournirons une réponse dans les plus brefs délais. Merci de votre patience !",
            VIDEO_CHANNEL_ID: "Votre vidéo a été soumise. Ce sera un plaisir de la regarder ! Les commentaires seront faits dans ce fil. Merci de votre créativité !",
            MEMES_CHANNEL_ID: "Votre meme a été soumis. C'est un plaisir de rigoler avec vous ! Les commentaires seront faits dans ce fil. Merci de votre créativité !",
            VDO_VDM_CHANNEL_ID: "Votre anecdote a été soumise. Nous l'avons bien reçue ! Les commentaires seront faits dans ce fil. Merci du partage de votre histoire !",
            RECHERCHE_KELKIN_CHANNEL_ID: "Votre demande de recherche a été soumise. Nous l'examinerons et vous fournirons une réponse dans les plus brefs délais. Merci de votre patience !",
        }

    @commands.Cog.listener()
    async def on_message(self, message):
        print(f"Message reçu de {message.author.name} dans le canal {message.channel.id}")
        if message.channel.id in self.channel_messages.keys() and not message.author.bot:
            now = datetime.datetime.now()
            if message.author.id not in self.user_message_times:
                self.user_message_times[message.author.id] = {}
            if message.channel.id in self.user_message_times[message.author.id] and (now - self.user_message_times[message.author.id][message.channel.id]).total_seconds() < 300:
                await message.author.send("Vous devez attendre 5 minutes avant de pouvoir envoyer un nouveau message. Si besoin, veuillez modifier votre dernier message.")
                await message.delete()
            else:
                self.user_message_times[message.author.id][message.channel.id] = now
                try:
                    print("Création du fil...")
                    thread = await message.channel.create_thread(message=message, name=f"Question de {message.author.name}")
                    await thread.send(self.channel_messages[message.channel.id])
                except Exception as e:
                    print(f"Erreur lors de la création du fil : {e}")

async def setup(bot):
    await bot.add_cog(ThreadCreator(bot))
