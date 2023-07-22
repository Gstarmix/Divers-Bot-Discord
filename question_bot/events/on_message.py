import asyncio
from nextcord.ext import commands
from constants import QUESTION_BOT_CHANNEL_ID

class OnMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        print(f"Message reçu de {message.author.name} dans le canal {message.channel.id}")

    @commands.Cog.listener()
    async def on_thread_join(self, thread):
        if thread.parent.id != QUESTION_BOT_CHANNEL_ID:
            return

        print(f"Le bot a rejoint le fil {thread.name}")

        def check(m):
            return m.channel == thread and m.author == thread.owner

        while True:
            await thread.send("Bonjour, je vois que vous voulez poser une question. Votre titre est-il formulé comme une question ? Répondez par 'Oui' ou 'Non'.")
            response = await self.bot.wait_for('message', check=check)
            if response.content.lower() == 'oui':
                await thread.send("Très bien, votre titre semble approprié. Merci de votre coopération.")
                break
            elif response.content.lower() == 'non':
                await thread.send("Merci de reformuler votre titre en une question compréhensible et détaillée. Par exemple, au lieu de 'Conseil stuff', vous pourriez dire 'Quelles améliorations puis-je apporter à mon stuff ?'")
            else:
                await thread.send("Je n'ai pas compris votre réponse. Veuillez répondre par 'Oui' ou 'Non'.")

def setup(bot):
    bot.add_cog(OnMessage(bot))
