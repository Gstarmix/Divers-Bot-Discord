import asyncio
from discord.ext import commands
from constants import QUESTION_BOT_CHANNEL_ID, ADMIN_ROLE_ID_GSTAR, AUTHOR_ROLE_ID_GSTAR

class Question(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.threads = {}
        self.delete_messages = {}

    async def ask_question(self, thread, message, check, yes_no_question=True):
        while True:
            await thread.send(f"{thread.owner.mention} {message}")
            try:
                response = await self.bot.wait_for('message', check=check, timeout=600)
                if yes_no_question:
                    if response.content.lower() in ['oui', 'non']:
                        return response
                    else:
                        message = "Je n'ai pas compris votre réponse. Veuillez répondre par 'Oui' ou 'Non'."
                        continue
                else:
                    return response
            except asyncio.TimeoutError:
                await thread.owner.send("Votre fil a été supprimé car vous avez mis plus de 10 minutes à répondre au questionnaire.")
                await thread.delete()
                return None

    @commands.Cog.listener()
    async def on_message(self, message):
        thread = message.channel
        if thread.id in self.threads and self.delete_messages.get(thread.id, False) and message.author.id != self.threads[thread.id] and not any(role.id == ADMIN_ROLE_ID_GSTAR for role in message.author.roles) and message.author != self.bot.user:
            await message.delete()
            await message.author.send("Vous n'êtes pas autorisé à écrire dans ce fil pendant le déroulement du questionnaire.")

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if thread.parent.id != QUESTION_BOT_CHANNEL_ID:
            return

        # Ajouter le rôle AUTHOR_ROLE_ID_GSTAR à l'auteur du fil
        author_role = thread.guild.get_role(AUTHOR_ROLE_ID_GSTAR)
        await thread.owner.add_roles(author_role)

        # Initialize deletion status
        self.threads[thread.id] = thread.owner.id
        self.delete_messages[thread.id] = True

        def check(m):
            return m.channel == thread and m.author == thread.owner

        while True:
            response = await self.ask_question(thread, "Bonjour, je vois que vous voulez poser une question. Votre titre est-il formulé comme une question ? Répondez par 'Oui' ou 'Non'.", check)

            if response is None:
                break

            if response.content.lower() == 'oui':
                await thread.send(f"{thread.owner.mention} Très bien, votre titre semble approprié. Le fil est maintenant ouvert à tous pour la discussion. Merci de votre coopération.")
                # Retirer le rôle AUTHOR_ROLE_ID_GSTAR de l'auteur du fil
                await thread.owner.remove_roles(author_role)
                self.delete_messages[thread.id] = False
                break
            elif response.content.lower() == 'non':
                while True:
                    response = await self.ask_question(thread, "Veuillez écrire votre nouveau titre à la suite de ce message.", check, yes_no_question=False)
                    if response is None:
                        return
                    while len(response.content) > 100:  # Ajout d'une boucle while ici
                        response = await self.ask_question(thread, "Votre titre est trop long. Il doit être de 100 caractères ou moins. Veuillez le raccourcir.", check, yes_no_question=False)
                        if response is None:
                            return
                    try:
                        await thread.edit(name=response.content)
                        await thread.send(f"{thread.owner.mention} Votre titre a bien été modifié. Le fil est maintenant ouvert à tous pour la discussion. Merci de votre coopération.")
                        # Retirer le rôle AUTHOR_ROLE_ID_GSTAR de l'auteur du fil
                        await thread.owner.remove_roles(author_role)
                        self.delete_messages[thread.id] = False
                        break  # Ajout d'une instruction break ici
                    except Exception as e:
                        print(f"Erreur lors de la modification du titre du fil : {e}")
                break  # Ajout d'une autre instruction break ici pour sortir de la boucle while externe

async def setup(bot):
    await bot.add_cog(Question(bot))
