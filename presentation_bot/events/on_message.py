import asyncio
from nextcord.ext import commands

class OnMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == 1131896627137871984:
            if message.author == self.bot.user:
                return

            def check(m):
                return m.author == message.author and m.channel == message.channel

            try:
                await message.channel.purge(limit=100, check=lambda m: m.author != self.bot.user and m.author != message.author)
            except Exception as e:
                print(f"Erreur lors de la suppression des messages : {e}")
                return

            await message.channel.send("Bonjour, je vois que vous voulez poser une question. Votre titre est-il formulé comme une question ? Répondez par 'Oui' ou 'Non'.")
            try:
                response = await self.bot.wait_for('message', check=check, timeout=60)
                if response.content.lower() == 'oui':
                    await message.channel.send("Très bien, votre titre semble approprié. Merci de votre coopération.")
                elif response.content.lower() == 'non':
                    await message.channel.send("Merci de reformuler votre titre en une question compréhensible et détaillée. Par exemple, au lieu de 'Conseil stuff', vous pourriez dire 'Quelles améliorations puis-je apporter à mon stuff ?'")
                    try:
                        await message.channel.purge(limit=100, check=lambda m: m.author != self.bot.user and m.author != message.author)
                    except Exception as e:
                        print(f"Erreur lors de la suppression des messages : {e}")
                        return
                    response = await self.bot.wait_for('message', check=check, timeout=60)
                    try:
                        await message.delete()
                    except Exception as e:
                        print(f"Erreur lors de la suppression du message : {e}")
                        return
                    try:
                        await message.channel.send(f"{message.author.name} a écrit : {response.content}")
                        await message.channel.send("Merci pour votre réponse. J'ai modifié le titre de votre post.")
                    except Exception as e:
                        print(f"Erreur lors de l'envoi du message : {e}")
                else:
                    await message.channel.send("Je n'ai pas compris votre réponse. Veuillez répondre par 'Oui' ou 'Non'.")
            except asyncio.TimeoutError:
                await message.channel.send("Désolé, vous avez dépassé le temps imparti pour répondre. Veuillez essayer à nouveau.")

def setup(bot):
    bot.add_cog(OnMessage(bot))
