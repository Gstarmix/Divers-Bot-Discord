from nextcord.ext import commands
import nextcord
import asyncio

class OnMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == 1131889295121199134 and not message.author.bot:
            thread = await message.channel.create_thread(name=f"Concours d'inscription de {message.author.name}")
            bot_message = await thread.send("Merci de votre intérêt pour le concours ! Pourriez-vous commencer par partager votre pseudo in-game ?")
            def check(m):
                return m.channel == thread and m.author == message.author
            try:
                response = await self.bot.wait_for('message', check=check, timeout=60.0)
                if response.content:
                    await thread.send("Parfait ! Pourriez-vous maintenant fournir une capture d'écran de votre personnage in-game ? N'oubliez pas, votre personnage doit être au minimum de niveau héroïque +30. Assurez-vous que le pseudo et le niveau de votre personnage soient bien visibles sur le screenshot.")
                    screenshot_response = await self.bot.wait_for('message', check=check, timeout=60.0)
                    if screenshot_response.attachments:
                        await thread.send("Merci pour la capture d'écran ! Ensuite, avez-vous atteint l'étape 17 du tutoriel ? Si oui, pourriez-vous fournir une capture d'écran de la page 17 du tutoriel ?")
                        tutorial_response = await self.bot.wait_for('message', check=check, timeout=60.0)
                        if tutorial_response.attachments:
                            await thread.send("Votre inscription au concours a été confirmée. Merci !")
                        else:
                            await thread.send("Vous n'avez pas fourni de capture d'écran pour l'étape 17 du tutoriel. Veuillez réessayer.")
                    else:
                        await thread.send("Vous n'avez pas fourni de capture d'écran de votre personnage. Veuillez réessayer.")
                else:
                    await thread.send("Vous n'avez pas fourni de pseudo in-game. Veuillez réessayer.")
            except asyncio.TimeoutError:
                await thread.send("Vous n'avez pas répondu à temps. Veuillez réessayer.")
            except Exception as e:
                await thread.send(f"Une erreur est survenue : {e}")

def setup(bot):
    bot.add_cog(OnMessage(bot))
