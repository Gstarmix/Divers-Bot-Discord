import asyncio
import datetime
import discord
from discord.ext import commands
from constants import PRESENTATION_BOT_CHANNEL_ID

def generate_message(choice):
    role_id = "<@&1036402538620129351>" if choice == "yertirand" else "<@&923190695190233138>"
    return (
        f":white_small_square: - Félicitations ! Tu as désormais le rôle {role_id}, ce qui te donne accès à tous les salons du serveur. "
        f"N'oublie pas de te rendre dans le salon <#1031609454527000616> pour consulter les règles et le salon <#1056343806196318248> pour choisir tes rôles. De cette façon, tu pourras réserver un créneau pour LoL et participer aux discussions dans les salons dédiés au LoL.\n"
        f":white_small_square: - Ton pseudo Discord a été mis à jour pour correspondre à celui indiqué dans ta présentation. Si cela n'a pas encore été fait, modifie-le toi-même afin que nous puissions te reconnaître facilement.\n"
        f":white_small_square: - Lorsque tu seras prêt à être recruté, mentionne le rôle {role_id} ici.\n"
        f":white_small_square: - Nous souhaitons que tout se déroule dans ta présentation. N'envoie donc pas de messages privés et ne nous mentionne nulle part ailleurs que <a:tention:1093967837992849468> **DANS TA PRÉSENTATION** <a:tention:1093967837992849468> si tu souhaites être recruté."
    )

class Presentation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_message_times = {}
        self.threads = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

    async def ask_question(self, channel, question, check):
        await channel.send(question)
        while True:
            try:
                response = await self.bot.wait_for('message', timeout=60, check=check)
                if response.content.lower() == 'oui':
                    return True
                elif response.content.lower() == 'non':
                    await channel.send("Veuillez corriger votre présentation en fonction des instructions et poster à nouveau à la suite de ce message.")
                else:
                    await channel.send("Je n'ai pas compris votre réponse. Veuillez répondre par 'oui' ou 'non'.")
            except asyncio.TimeoutError:
                await channel.send("Je n'ai pas reçu de réponse. Souhaitez-vous continuer le questionnaire ? Répondez par 'Oui' ou 'Non'.")
                await asyncio.sleep(1)
                try:
                    response = await self.bot.wait_for('message', timeout=60, check=check)
                    if response.content.lower() == 'non':
                        return False
                except asyncio.TimeoutError:
                    await channel.send("Je n'ai pas reçu de réponse. Le questionnaire va être arrêté.")
                    return False

    async def ask_choice(self, channel, check):
        await channel.send("Merci d'avoir vérifié ces informations. Souhaitez-vous rejoindre Yertirand ou -GANG- ? Répondez par 'Yertirand' ou '-GANG-'.")
        while True:
            try:
                response = await self.bot.wait_for('message', timeout=60, check=check)
                if response.content.lower() in ['yertirand', '-gang-']:
                    await channel.send(generate_message(response.content.lower()))
                    return True
                else:
                    await channel.send("Je n'ai pas compris votre réponse. Veuillez répondre par 'Yertirand' ou '-GANG-'.")
            except asyncio.TimeoutError:
                await channel.send("Je n'ai pas reçu de réponse. Souhaitez-vous continuer le questionnaire ? Répondez par 'Oui' ou 'Non'.")
                await asyncio.sleep(1)
                try:
                    response = await self.bot.wait_for('message', timeout=60, check=check)
                    if response.content.lower() == 'non':
                        return False
                except asyncio.TimeoutError:
                    await channel.send("Je n'ai pas reçu de réponse. Le questionnaire va être arrêté.")
                    return False

    @commands.Cog.listener()
    async def on_thread_join(self, thread):
        print("Event on_thread_join triggered")
        if thread.parent.id != PRESENTATION_BOT_CHANNEL_ID:
            return

        print(f"Le bot a rejoint le fil {thread.id}")
        self.threads[thread.id] = thread.owner.mention

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        print("Event on_thread_create triggered")
        if thread.parent.id != PRESENTATION_BOT_CHANNEL_ID:
            return

        print(f"Un fil a été créé {thread.id}")
        self.threads[thread.id] = thread.owner.mention

        def check(m):
            return m.channel.id == thread.id and m.author == thread.owner

        await self.bot.wait_for('message', check=check)

        questions = [
            "Est-ce que votre pseudo en jeu est correctement affiché dans le titre ? (Répondez par oui ou non)",
            "Avez-vous inclus une capture d'écran de votre fiche personnage ? (Répondez par oui ou non et si ce n'est pas encore le cas, veuillez la poster)",
            "Avez-vous inclus des captures d'écran de votre arme principale, arme secondaire, armure, SP et résistances ? (Répondez par oui ou non et si ce n'est pas encore fait, veuillez les poster)"
        ]

        for question in questions:
            if not await self.ask_question(thread, question, check):
                return

        await self.ask_choice(thread, check)

async def setup(bot):
    await bot.add_cog(Presentation(bot))
