import asyncio
from discord.ext import commands
from constants import *

class Presentation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.threads = {}
        self.delete_messages = {}

    async def ask_question(self, thread, question, check, yes_no_question=True):
        first_time = True
        while True:
            if first_time:
                user_message_sent = False
                async for msg in thread.history(limit=5):
                    if msg.author == thread.owner:
                        user_message_sent = True
                        break

                if not user_message_sent:
                    await asyncio.sleep(5)
                    continue

                await thread.send(f"{thread.owner.mention} {question}")
                first_time = False

            try:
                response = await self.bot.wait_for('message', check=check, timeout=600)
                return response
            except asyncio.TimeoutError:
                await thread.owner.send("Votre fil a été supprimé car vous avez mis plus de 10 minutes à répondre au questionnaire.")
                await thread.delete()
                return None

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if thread.parent.id != PRESENTATION_CHANNEL_ID:
            return

        # Définition des nouveaux rôles
        role_id = ROLE1_ID_FAFA
        new_roles = [self.bot.get_guild(GUILD_ID_FAFA).get_role(role_id) for role_id in [ROLE1_ID_FAFA, ROLE2_ID_FAFA, ROLE3_ID_FAFA, ROLE4_ID_FAFA, ROLE5_ID_FAFA]]

        self.threads[thread.id] = thread.owner.id
        self.delete_messages[thread.id] = True

        async for message in thread.history(limit=1):
            await message.pin()
            break

        def check(m):
            return m.channel == thread and m.author == thread.owner

        # Liste des questions et des réponses attendues
        questions_capture = [
            {
                "question": "Possédez-vous un pseudo en jeu correctement affiché dans le titre ? Répondez par `Oui` ou `Non`. Par exemple, 'PseudoEnJeu123' est correctement affiché dans le titre.",
                "reponse": "Oui ou Non",
                "exemple": "Si vous répondez 'Non', veuillez choisir un nouveau pseudo en jeu et écrivez-le dans le fil."
            },
            {
                "question": "Possédez-vous des Stuffs héroïques adaptés à votre niveau ? Répondez par `Oui` ou `Non`. Par exemple, si vous êtes de niveau +65, vous devez avoir un stuff +65 ou +60.",
                "reponse": "Oui ou Non"
            },
            {
                "question": "Possédez-vous au moins 10% de dégâts relatifs ? Répondez par `Oui` ou `Non`. Par exemple, si vous avez 12% de dégâts relatifs, vous répondez 'oui'.",
                "reponse": "Oui ou Non"
            },
            {
                "question": "Possédez-vous un minimum de 7% d'attaque runique ? Répondez par `Oui` ou `Non`. Par exemple, si vous avez 8% d'attaque runique, vous répondez 'oui'.",
                "reponse": "Oui ou Non"
            },
            {
                "question": "Possédez-vous au moins 100 points d'attaque et 60 points d'élément ou 60 points d'attaque et 100 points d'élément dans les statistiques SP ? Répondez par `Oui` ou `Non`. Par exemple, si vous avez :escri:+:archer:+:am: + :regard_perant: Position attaque, vous répondez 'oui'.",
                "reponse": "Oui ou Non"
            },
            {
                "question": "Possédez-vous un minimum de 25 points d'attaque et 25 points d'élément en perfectionnements SP ? Répondez par `Oui` ou `Non`. Par exemple, si vous avez 30 points d'attaque et 25 points d'élément en perfectionnements SP, vous répondez 'oui'.",
                "reponse": "Oui ou Non"
            },
            {
                "question": "Possédez-vous au moins 110% de résistances globales ? Répondez par `Oui` ou `Non`. Par exemple, si vous avez 120% de résistances globales, vous répondez 'oui'.",
                "reponse": "Oui ou Non"
            },
            {
                "question": "Possédez-vous une fée avec au moins 80% d'efficacité, sans le Renforcement féérique ? Répondez par `Oui` ou `Non`. Par exemple, si vous avez :elfe: Archère elfe sylvestre Forga [SSS], vous répondez 'oui'.",
                "reponse": "Oui ou Non"
            },
            {
                "question": "Possédez-vous un set de costumes orienté DPS avec au moins 8% d'attaque au minimum ? Répondez par `Oui` ou `Non`. Par exemple, si vous avez :dino1: :dino2: :dino3: Ensemble de dino 10% atq, vous répondez 'oui'.",
                "reponse": "Oui ou Non"
            },
            {
                "question": "Possédez-vous une aile orientée DPS ? Répondez par `Oui` ou `Non`. Par exemple, si vous avez :arborescente: Arborescentes, vous répondez 'oui'.",
                "reponse": "Oui ou Non"
            },
            {
                "question": "Possédez-vous un tatouage orienté DPS en +5 au minimum ? Répondez par `Oui` ou `Non`. Par exemple, si vous avez :escri:+:archer:+:am:: :regard_perant: Regard perçant + :pa: Position attaque, vous répondez 'oui'.",
                "reponse": "Oui ou Non"
            },
            {
                "question": "Possédez-vous un titre orienté DPS ? Répondez par `Oui` ou `Non`. Par exemple, si vous avez :titre: Éternel, vous répondez 'oui'.",
                "reponse": "Oui ou Non"
            },
            {
                "question": "Possédez-vous un partenaire orienté DPS ? Répondez par `Oui` ou `Non`. Par exemple, si vous avez :elfe: Archère elfe sylvestre Forga [SSS], vous répondez 'oui'.",
                "reponse": "Oui ou Non"
            }
        ]

        # Pose des questions et traitement des réponses
        for question in questions_capture:
            response = await self.ask_question(thread, question["question"], check)
            if response is None:
                return

            if response.content.lower() == 'oui':
                justification_message = f"{thread.owner.mention} Veuillez envoyer une capture d'écran pour justifier votre réponse. Une fois que vous avez envoyé la capture d'écran, écrivez 'Justifié' pour passer à la question suivante."
                await thread.send(justification_message)
                while True:
                    justif_response = await self.ask_question(thread, "", check, yes_no_question=False)
                    if justif_response is None:
                        return
                    if justif_response.content.lower() == 'justifié':
                        break
                    else:
                        await thread.send(f"{thread.owner.mention} Pour passer à la question suivante, veuillez écrire 'Justifié'.")

            elif response.content.lower() == 'non':
                if "Capture d'écran" in question["question"]:
                    justification_message = f"{thread.owner.mention} Veuillez envoyer une capture d'écran pour justifier votre réponse. Une fois que vous avez envoyé la capture d'écran, écrivez `Justifié` pour passer à la question suivante."
                    await thread.send(justification_message)
                    while True:
                        justif_response = await self.ask_question(thread, "", check, yes_no_question=False)
                        if justif_response is None:
                            return
                        if justif_response.content.lower() == 'justifié':
                            break
                        else:
                            await thread.send(f"{thread.owner.mention} Pour passer à la question suivante, veuillez écrire 'Justifié'.")
                continue

            if "Capture d'écran" in question["question"]:
                reponse_question = "Oui"
            else:
                reponse_question = "Non"

            while True:
                reponse = await self.ask_question(thread, f"Vous avez choisi la réponse : {reponse_question}. Est-ce correct ?", check)
                if reponse is None:
                    return
                if reponse.content.lower() == 'oui' and "Capture d'écran" in question["question"]:
                    break
                elif reponse.content.lower() == 'non' and "Capture d'écran" not in question["question"]:
                    break
                else:
                    await thread.send(f"{thread.owner.mention} Votre réponse n'a pas été prise en compte. Veuillez répondre avec 'Oui' si c'est le cas, sinon répondez avec 'Non'.")

        # Question sur le choix de la famille
        response = await self.ask_question(thread, "Quel est le nom de la famille où vous voulez être recruté (Yertirand ou -GANG-)", check)
        if response is None:
            return

        family_name = response.content.lower()
        while family_name not in ["yertirand", "-gang-"]:
            response = await self.ask_question(thread, "Le nom de la famille que vous avez fourni n'est pas valide. Veuillez fournir un nom de famille valide, soit `Yertirand` ou `-GANG-`.", check)
            if response is None:
                return

        recruitment_role_id = GARDIEN_YERTI_ROLE_ID if family_name == "yertirand" else GARDIEN_GANG_ROLE_ID

        # Retirer les anciens rôles et attribuer les nouveaux
        for role in thread.owner.roles:
            if role not in new_roles:
                try:
                    await thread.owner.remove_roles(role)
                except Exception as e:
                    print(f"Could not remove role {role.name}")

        await thread.owner.add_roles(*new_roles)

        message = (
            f":white_small_square: - Félicitations {thread.owner.mention} ! Vous avez désormais le rôle <@&{recruitment_role_id}>, ce qui vous donne accès à tous les salons du serveur. "
            f"N'oubliez pas de consulter les règles dans le salon <#1031609454527000616> et de choisir vos rôles dans <#1056343806196318248> pour participer aux discussions dans les salons dédiés au LoL.\n"
            f":white_small_square: - Votre pseudo Discord a été mis à jour pour correspondre à celui indiqué dans votre présentation. Si cela a supprimé vos autres pseudos, ajoutez-les vous-même séparés par un `|` pour que nous puissions reconnaître tous vos personnages facilement.\n"
            f":white_small_square: - Lorsque vous serez prêt à être recruté, mentionnez le rôle <@&{recruitment_role_id}> ici.\n"
            f":white_small_square: - Assurez-vous que toute communication se fasse dans cette présentation. N'envoyez pas de messages privés et ne nous mentionnez nulle part ailleurs que <a:tention:1093967837992849468> **DANS VOTRE PRÉSENTATION** <a:tention:1093967837992849468> si vous souhaitez être recruté."
        )

        await thread.send(message)

async def setup(bot):
    await bot.add_cog(Presentation(bot))
