import asyncio
from discord.ext import commands
from constants import *

class Presentation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.threads = {}
        self.delete_messages = {}
        self.families = ["yertirand", "-gang-"]

    async def generate_message(self, choice):
        recruitment_role_id = GARDIEN_YERTI_ROLE_ID if choice == "yertirand" else GARDIEN_GANG_ROLE_ID
        role_id = ROLE1_ID_FAFA
        new_roles = [self.bot.get_guild(GUILD_ID_FAFA).get_role(role_id) for role_id in [ROLE1_ID_FAFA, ROLE2_ID_FAFA, ROLE3_ID_FAFA, ROLE4_ID_FAFA, ROLE5_ID_FAFA]]
        
        await self.thread.owner.remove_roles(*self.thread.owner.roles)
        
        await self.thread.owner.add_roles(*new_roles)
        
        return (
            f":white_small_square: - Félicitations ! Tu as désormais le rôle <@&{role_id}>, ce qui te donne accès à tous les salons du serveur. "
            f"N'oublie pas de te rendre dans le salon <#1031609454527000616> pour consulter les règles et le salon <#1056343806196318248> pour choisir tes rôles. De cette façon, tu pourras réserver un créneau pour LoL et participer aux discussions dans les salons dédiés au LoL.\n"
            f":white_small_square: - Ton pseudo Discord a été mis à jour pour correspondre à celui indiqué dans ta présentation. Si cela n'a pas encore été fait, modifie-le toi-même afin que nous puissions te reconnaître facilement.\n"
            f":white_small_square: - Lorsque tu seras prêt à être recruté, mentionne le rôle <@&{recruitment_role_id}> ici.\n"
            f":white_small_square: - Nous souhaitons que tout se déroule dans ta présentation. N'envoie donc pas de messages privés et ne nous mentionne nulle part ailleurs que <a:tention:1093967837992849468> **DANS TA PRÉSENTATION** <a:tention:1093967837992849468> si tu souhaites être recruté."
        )

    async def ask_question(self, thread, message, check, yes_no_question=True, image_allowed=False):
        first_time = True
        while True:
            if first_time:
                await thread.send(f"{thread.owner.mention} {message}")
                first_time = False
            try:
                response = await self.bot.wait_for('message', check=check, timeout=600)
                if yes_no_question:
                    if response.content.lower() in ['oui', 'non']:
                        return response
                    else:
                        message = "Je n'ai pas compris votre réponse. Veuillez répondre par `Oui` ou `Non`."
                elif image_allowed and response.attachments:
                    return response
                else:
                    return response
            except asyncio.TimeoutError:
                await thread.owner.send("Votre fil a été supprimé car vous avez mis plus de 10 minutes à répondre au questionnaire.")
                await thread.delete()
                return None
            await thread.send(f"{thread.owner.mention} {message}")

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if thread.parent.id != PRESENTATION_CHANNEL_ID:
            return

        self.threads[thread.id] = thread.owner.id
        self.delete_messages[thread.id] = True

        async for message in thread.history(limit=1):
            await message.pin()
            break

        def check(m):
            return m.channel == thread and m.author == thread.owner

        response = await self.ask_question(thread, "Est-ce que votre pseudo en jeu est correctement affiché dans le titre ? Répondez par `Oui` ou `Non`.", check)
        if response is None:
            return
        while response.content.lower() == 'non':
            response = await self.ask_question(thread, "Veuillez écrire votre pseudo en jeu à la suite de ce message.", check, yes_no_question=False)
            if response is None:
                return
            new_name = response.content
            response = await self.ask_question(thread, f"Vous avez choisi le pseudo `{new_name}`. Est-ce correct ? Répondez par `Oui` ou `Non`.", check)
            if response is None:
                return
            if response.content.lower() == 'oui':
                try:
                    await thread.owner.edit(nick=new_name)
                    await thread.edit(name=new_name)
                except Exception as e:
                    print(f"Erreur lors de la modification du pseudo Discord ou du titre du fil : {e}")

        response = await self.ask_question(thread, "Avez-vous inclus une capture d'écran de votre fiche personnage, arme principale, arme secondaire, armure, SP et résistances ? Répondez par `Oui` ou `Non`.", check)
        if response is None:
            return
        while response.content.lower() == 'non' or response.attachments:
            response = await self.ask_question(thread, "Voulez-vous envoyer d'autres captures d'écran pour compléter votre réponse précédente ? Répondez par `Non` ou envoyez une nouvelle `capture d'écran`.", check, yes_no_question=False, image_allowed=True)
            if response is None:
                return
            if response.content.lower() == 'non':
                break

        response = await self.ask_question(thread, "Quel est le nom de la famille où vous voulez être recruté ? Répondez par `Yertirand` ou `-GANG-`.", check, yes_no_question=False)
        if response is None:
            return
        family_name = response.content.lower()
        if family_name in self.families:
            message = self.generate_message(family_name)
            await thread.send(message)
        else:
            await thread.send(f"{thread.owner.mention} Le nom de la famille que vous avez fourni n'est pas valide. Veuillez fournir un nom de famille valide, soit `Yertirand` ou `-GANG-`.")

        self.delete_messages[thread.id] = False

async def setup(bot):
    await bot.add_cog(Presentation(bot))