import datetime
from nextcord.ext import commands
import nextcord
from constants import MUDAE_HELP_BOT_CHANNEL_ID

class MudaeHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_message_times = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        print(f"Message reçu de {message.author.name} dans le canal {message.channel.id}")
        if message.channel.id == MUDAE_HELP_BOT_CHANNEL_ID and not message.author.bot:
            now = datetime.datetime.now()
            if message.author.id in self.user_message_times and (now - self.user_message_times[message.author.id]).total_seconds() < 300:
                await message.author.send("Vous ne pouvez poser une nouvelle question que 5 minutes après votre précédente question. Veuillez modifier votre dernier message si nécessaire.")
                await message.delete()
            else:
                self.user_message_times[message.author.id] = now
                try:
                    print("Création du fil...")  # Log thread creation
                    thread = await message.create_thread(name=f"Question de {message.author.name}")
                    await thread.send("La question a été prise en compte. Nous vous fournirons une réponse complète et précise dans les plus brefs délais. Merci de votre patience !")
                except Exception as e:
                    print(f"Erreur lors de la création du fil : {e}")

def setup(bot):
    bot.add_cog(MudaeHelp(bot))