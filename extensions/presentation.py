import datetime
from nextcord.ext import commands
import nextcord
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

    @commands.Cog.listener()
    async def on_thread_join(self, thread):
        if thread.parent.id != PRESENTATION_BOT_CHANNEL_ID:
            return

        print(f"Le bot a rejoint le fil {thread.name}")
        self.threads[thread.id] = thread.owner.id

        def check(m):
            return m.channel == thread and m.author == thread.owner

        questions = [
            "Est-ce que votre pseudo en jeu est correctement affiché dans le titre ? (Répondez par oui ou non)",
            "Avez-vous inclus une capture d'écran de votre fiche personnage ? (Répondez par oui ou non et si ce n'est pas encore le cas, veuillez la poster)",
            "Avez-vous inclus des captures d'écran de votre arme principale, arme secondaire, armure, SP et résistances ? (Répondez par oui ou non et si ce n'est pas encore fait, veuillez les poster)"
        ]

        for question in questions:
            while True:
                await thread.send(question)
                response = await self.bot.wait_for('message', check=check)
                if response.content.lower() == 'oui':
                    break
                elif response.content.lower() == 'non':
                    await thread.send("Veuillez corriger votre présentation en fonction des instructions et poster à nouveau.")
                else:
                    await thread.send("Je n'ai pas compris votre réponse. Veuillez répondre par 'oui' ou 'non'.")

        while True:
            await thread.send("Merci d'avoir vérifié ces informations. Souhaitez-vous rejoindre Yertirand ou -GANG- ? Répondez par 'Yertirand' ou '-GANG-'.")
            response = await self.bot.wait_for('message', check=check)
            if response.content.lower() in ['yertirand', '-gang-']:
                await thread.send(generate_message(response.content.lower()))
                break
            else:
                await thread.send("Je n'ai pas compris votre réponse. Veuillez répondre par 'Yertirand' ou '-GANG-'.")

def setup(bot):
    bot.add_cog(Presentation(bot))
