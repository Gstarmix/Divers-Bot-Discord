import asyncio
from nextcord.ext import commands

def generate_message(choice):
    role_id = "<@&1036402538620129351>" if choice == "yertirand" else "<@&923190695190233138>"
    return (f":white_small_square: — Je t'ai attribué le rôle <@&923002565602467840> pour te donner accès à tous les salons, notamment le salon <#1031609454527000616> où tu dois lire les règles et le salon <#1056343806196318248> où tu dois sélectionner tes rôles afin de pouvoir réserver un créneau de LoL et participer aux discussions dans les salons dédiés au LoL.\n"
            f":white_small_square: — J'ai modifié ton pseudo Discord pour qu'il corresponde à celui indiqué dans ta présentation. Si ce n'est pas encore fait, modifie-le toi-même, car nous devons pouvoir te reconnaître.\n"
            f":white_small_square: — Lorsque tu seras prêt à être recruté, mentionne le rôle {role_id} ici.\n"
            f":white_small_square: — Tout doit se dérouler dans ta présentation. Alors ne nous envoie pas de MP ou ne nous mentionne pas ailleurs que <a:tention:1093967837992849468> **DANS TA PRÉSENTATION** <a:tention:1093967837992849468> pour te faire recruter.")

class OnMessage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == 1131896683626766346:
            if message.author == self.bot.user:
                return

            def check(m):
                return m.author == message.author and m.channel == message.channel

            questions = [
                "Votre pseudo en jeu est-il correctement indiqué dans le titre ?",
                "Avez-vous inclus une capture d'écran de votre fiche personnage ?",
                "Avez-vous inclus des captures d'écran de votre arme principale, arme secondaire, armure, SP et résistances ?"
            ]

            for question in questions:
                await message.channel.send(question)
                await message.channel.purge(limit=100, check=lambda m: m.author != self.bot.user and m.author != message.author)
                try:
                    response = await self.bot.wait_for('message', check=check, timeout=60)
                    if response.content.lower() != 'oui':
                        await message.channel.send("Veuillez corriger votre présentation en fonction des instructions et poster à nouveau.")
                        return
                except asyncio.TimeoutError:
                    await message.channel.send("Désolé, vous avez dépassé le temps imparti pour répondre. Veuillez essayer à nouveau.")
                    return

            await message.channel.send("Merci d'avoir vérifié ces informations. Souhaitez-vous rejoindre Yertirand ou -GANG- ? Répondez par 'Yertirand' ou '-GANG-'.")
            try:
                response = await self.bot.wait_for('message', check=check, timeout=60)
                if response.content.lower() in ['yertirand', '-gang-']:
                    await message.channel.send(generate_message(response.content.lower()))
                else:
                    await message.channel.send("Je n'ai pas compris votre réponse. Veuillez répondre par 'Yertirand' ou '-GANG-'.")
            except asyncio.TimeoutError:
                await message.channel.send("Désolé, vous avez dépassé le temps imparti pour répondre. Veuillez essayer à nouveau.")

def setup(bot):
    bot.add_cog(OnMessage(bot))
