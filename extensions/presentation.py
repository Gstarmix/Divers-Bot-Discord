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

        print(f"Message reçu de {message.author.name} dans le canal {message.channel.id}")
        if message.channel.id == PRESENTATION_BOT_CHANNEL_ID and not message.author.bot:
            now = datetime.datetime.now()
            if message.author.id in self.user_message_times and (now - self.user_message_times[message.author.id]).total_seconds() < 300:
                await message.author.send("Vous ne pouvez poser une nouvelle question que 5 minutes après votre précédente question. Veuillez modifier votre dernier message si nécessaire.")
                await message.delete()
            else:
                self.user_message_times[message.author.id] = now
                thread = await message.channel.create_thread(name=f"Thread for {message.author.name}")
                self.threads[thread.id] = thread.owner.id
                await thread.send("This is a message from the bot.")

    async def ask_question(self, channel, question, check):
        await channel.send(question)
        while True:
            try:
                response = await self.bot.wait_for('message', timeout=60)
                if check(response) and response.content.lower() == 'oui':
                    return True
                elif check(response) and response.content.lower() == 'non':
                    await channel.send("Veuillez corriger votre présentation en fonction des instructions et poster à nouveau à la suite de ce message.")
                else:
                    await channel.send("Je n'ai pas compris votre réponse. Veuillez répondre par 'oui' ou 'non'.")
            except asyncio.TimeoutError:
                await channel.send("Je n'ai pas reçu de réponse. Souhaitez-vous continuer le questionnaire ? Répondez par 'Oui' ou 'Non'.")
                await asyncio.sleep(1)
                try:
                    response = await self.bot.wait_for('message', timeout=60)
                    if check(response) and response.content.lower() == 'non':
                        return False
                except asyncio.TimeoutError:
                    await channel.send("Je n'ai pas reçu de réponse. Le questionnaire va être arrêté.")
                    return False

    async def ask_choice(self, channel, check):
        await channel.send("Merci d'avoir vérifié ces informations. Souhaitez-vous rejoindre Yertirand ou -GANG- ? Répondez par 'Yertirand' ou '-GANG-'.")
        while True:
            try:
                response = await self.bot.wait_for('message', timeout=60)
                if check(response) and response.content.lower() in ['yertirand', '-gang-']:
                    await channel.send(generate_message(response.content.lower()))
                    return True
                else:
                    await channel.send("Je n'ai pas compris votre réponse. Veuillez répondre par 'Yertirand' ou '-GANG-'.")
            except asyncio.TimeoutError:
                await channel.send("Je n'ai pas reçu de réponse. Souhaitez-vous continuer le questionnaire ? Répondez par 'Oui' ou 'Non'.")
                await asyncio.sleep(1)
                try:
                    response = await self.bot.wait_for('message', timeout=60)
                    if check(response) and response.content.lower() == 'non':
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
        self.threads[thread.id] = thread.owner.id

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        print("Event on_thread_create triggered")
        if thread.parent.id != PRESENTATION_BOT_CHANNEL_ID:
            return

        print(f"Un fil a été créé {thread.id}")
        self.threads[thread.id] = thread.owner.id

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
