import asyncio
from discord import AllowedMentions
from discord.ext import commands
from constants import *

def generate_message(choice):
    recruitment_role_id = GARDIEN_YERTI_ROLE_ID if choice == "yertirand" else GARDIEN_GANG_ROLE_ID
    role_id = ROLE1_ID_FAFA
    return (
        f":white_small_square: - Félicitations ! Tu as désormais le rôle <@&{role_id}>, ce qui te donne accès à tous les salons du serveur. "
        f"N'oublie pas de te rendre dans le salon <#1031609454527000616> pour consulter les règles et le salon <#1056343806196318248> pour choisir tes rôles. De cette façon, tu pourras réserver un créneau pour LoL et participer aux discussions dans les salons dédiés au LoL.\n"
        f":white_small_square: - Ton pseudo Discord a été mis à jour pour correspondre à celui indiqué dans ta présentation. Si cela n'a pas encore été fait, modifie-le toi-même afin que nous puissions te reconnaître facilement.\n"
        f":white_small_square: - Lorsque tu seras prêt à être recruté, mentionne le rôle <@&{recruitment_role_id}> ici.\n"
        f":white_small_square: - Nous souhaitons que tout se déroule dans ta présentation. N'envoie donc pas de messages privés et ne nous mentionne nulle part ailleurs que <a:tention:1093967837992849468> **DANS TA PRÉSENTATION** <a:tention:1093967837992849468> si tu souhaites être recruté."
    )

class Presentation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.threads = {}
        self.delete_messages = {}

    async def ask_question(self, thread, message, check):
        await thread.send(f"{thread.owner.mention} {message}")
        try:
            response = await self.bot.wait_for('message', check=check, timeout=600)
            return response
        except asyncio.TimeoutError:
            await thread.owner.send("Votre fil a été supprimé car vous avez mis plus de 10 minutes à répondre au questionnaire.")
            await thread.delete()
            return None

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        thread = message.channel
        if thread.id in self.threads:
            user_id = self.threads[thread.id]
            user = thread.guild.get_member(user_id) 

            presentation_role = thread.guild.get_role(PRESENTATION_ROLE_ID)
            if presentation_role in user.roles:
                await user.remove_roles(presentation_role)

            role_ids = [ROLE1_ID_FAFA, ROLE2_ID_FAFA, ROLE3_ID_FAFA, ROLE4_ID_FAFA, ROLE5_ID_FAFA]
            for role in user.roles:
                if role.id not in role_ids and role != thread.guild.default_role and role != thread.guild.me.top_role:
                    await user.remove_roles(role)

            for role_id in role_ids:
                role = thread.guild.get_role(role_id)
                if role not in user.roles:
                    await user.add_roles(role)

            await user.send("Votre fil de discussion a été supprimé et vos rôles ont été réinitialisés.")
            await thread.delete()

            del self.threads[thread.id]

    @commands.Cog.listener()
    async def on_message(self, message):
        thread = message.channel
        if thread.id in self.threads and self.delete_messages.get(thread.id, False) and message.author.id != self.threads[thread.id] and not any(role.id in [GARDIEN_YERTI_ROLE_ID, GARDIEN_GANG_ROLE_ID] for role in message.author.roles) and message.author != self.bot.user:
            await message.delete()
            await message.author.send("Vous n'êtes pas autorisé à écrire dans ce fil pendant le déroulement du questionnaire.")

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if thread.parent.id != PRESENTATION_CHANNEL_ID:
            return

        author_role = thread.guild.get_role(PRESENTATION_ROLE_ID)
        await thread.owner.add_roles(author_role)

        self.threads[thread.id] = thread.owner.id
        self.delete_messages[thread.id] = True

        async for message in thread.history(limit=1):
            await message.pin()
            break

        def check(m):
            return m.channel == thread and m.author == thread.owner

        while True:
            response = await self.ask_question(thread, "Est-ce que votre pseudo en jeu est correctement affiché dans le titre ? Répondez par ``Oui`` ou ``Non``.", check)
            while response is not None and response.content.lower() not in ['oui', 'non']:
                await thread.send(f"{thread.owner.mention} Je n'ai pas compris votre réponse. Veuillez répondre par ``Oui`` ou ``Non``.")
                response = await self.bot.wait_for('message', check=check, timeout=600)
            if response is None:
                return
            if response.content.lower() == 'oui':
                try:
                    await thread.owner.edit(nick=thread.name)
                except Exception as e:
                    print(f"Erreur lors de la modification du pseudo de l'utilisateur : {e}")
                    await thread.send(f"{thread.owner.mention} Une erreur s'est produite lors de la tentative de modification de votre pseudo. Le processus continue malgré tout.")
                break
            elif response.content.lower() == 'non':
                while True:
                    response = await self.ask_question(thread, "Veuillez écrire votre pseudo en jeu à la suite de ce message.", check)
                    if response is None:
                        return
                    if len(response.content) <= 32:
                        confirmation = await self.ask_question(thread, f"Vous avez choisi le pseudo `{response.content}`. Est-ce correct ? Répondez par ``Oui`` ou ``Non``.", check)
                        if confirmation is None:
                            return
                        if confirmation.content.lower() == 'oui':
                            try:
                                await thread.owner.edit(nick=response.content)
                                await thread.edit(name=response.content)
                                break
                            except Exception as e:
                                print(f"Erreur lors de la modification du titre du fil ou du pseudo de l'utilisateur : {e}")
                break
            else:
                await thread.send("Votre pseudo est trop long. Il doit être de 32 caractères ou moins. Veuillez le raccourcir.")
                response = None

        questions = [
            "Avez-vous inclus une capture d'écran de votre fiche personnage ? Répondez par ``Oui`` ou si ce n'est pas le cas, envoyez des captures d'écran.",
            "Avez-vous inclus des captures d'écran de votre arme principale, arme secondaire, armure, SP et résistances ? Répondez par ``Oui`` ou si ce n'est pas le cas, envoyez des captures d'écran."
        ]

        for question in questions:
            response = await self.ask_question(thread, question, check)
            if response is None:
                return
            while response.content.lower() != 'oui':
                if response.attachments:
                    response = await self.ask_question(thread, "Voulez-vous envoyer d'autres captures d'écran pour compléter votre réponse précédente ? Répondez par ``Non`` ou envoyez votre capture d'écran.", check)
                    if response is None:
                        return
                    elif response.content.lower() == 'non':
                        break
                else:
                    response = await self.ask_question(thread, "Veuillez écrire ``Oui`` ou envoyer une capture d'écran pour répondre à la question.", check)
                    if response is None:
                        return

        await self.ask_choice(thread, check)

allowed_mentions = AllowedMentions.none()

async def setup(bot):
    await bot.add_cog(Presentation(bot))
