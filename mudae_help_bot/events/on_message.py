from nextcord.ext import commands
import nextcord

class OnMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == 1131889437958217809 and not message.author.bot:
            thread = await message.channel.create_thread(name=f"Question de {message.author.name}")
            await thread.send("Merci pour ces informations. Nous allons travailler à résoudre votre problème. Veuillez patienter pendant que nous traitons votre demande.")

def setup(bot):
    bot.add_cog(OnMessage(bot))
