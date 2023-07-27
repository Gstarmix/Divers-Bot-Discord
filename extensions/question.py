import asyncio
from discord.ext import commands
from constants import *

class Question(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.threads = {}
        self.delete_messages = {}
        self.interrogative_words = ["qui", "quoi", "où", "quand", "pourquoi", "comment", "est-ce que", "qu'est-ce que", "combien", "quel", "quelle", "quels", "quelles"]

    def is_valid_question(self, title):
        lower_title = title.lower()
        return any(lower_title.startswith(word) for word in self.interrogative_words) and len(lower_title) >= 20 and '?' in lower_title and lower_title.split()[0] in self.interrogative_words


    async def ask_question(self, thread, message, check, yes_no_question=True):
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
                else:
                    return response
            except asyncio.TimeoutError:
                await thread.owner.send("Votre fil a été supprimé car vous avez mis plus de 10 minutes à répondre au questionnaire.")
                author_role = thread.guild.get_role(QUESTION_ROLE_ID)
                await thread.owner.remove_roles(author_role)
                await thread.delete()
                return None
            await thread.send(f"{thread.owner.mention} {message}")

    @commands.Cog.listener()
    async def on_message(self, message):
        thread = message.channel
        if thread.id in self.threads and self.delete_messages.get(thread.id, False) and message.author.id != self.threads[thread.id] and not any(role.id == CHEF_SINGE_ROLE_ID for role in message.author.roles) and message.author != self.bot.user:
            await message.delete()
            await message.author.send("Vous n'êtes pas autorisé à écrire dans ce fil pendant le déroulement du questionnaire.")

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if thread.parent.id != QUESTION_CHANNEL_ID:
            return

        author_role = thread.guild.get_role(QUESTION_ROLE_ID)
        await thread.owner.add_roles(author_role)

        self.threads[thread.id] = thread.owner.id
        self.delete_messages[thread.id] = True

        async for message in thread.history(limit=1):
            await message.pin()
            break

        def check(m):
            return m.channel == thread and m.author == thread.owner

        if self.is_valid_question(thread.name):
            await thread.send(f"{thread.owner.mention} Très bien, votre titre semble approprié. Le fil est maintenant ouvert à tous pour la discussion. Merci de votre coopération.")
            await thread.owner.remove_roles(author_role)
            self.delete_messages[thread.id] = False
        else:
            while True:
                response = await self.ask_question(thread, "Le titre que vous avez validé n'est pas une question. Une question doit commencer par un mot interrogatif (comme `qui`, `quoi`, `où`, `quand`, `pourquoi`, `comment`, `est-ce que`, `qu'est-ce que`, `combien`, `quel`, `quelle`, `quels`, `quelles`), doit contenir au moins 20 caractères et doit se terminer par un `?`. Veuillez écrire votre nouveau titre à la suite de ce message.", check, yes_no_question=False)
                if response is None:
                    return
                while len(response.content) > 100:
                    response = await self.ask_question(thread, "Votre titre est trop long. Il doit être de 100 caractères ou moins. Veuillez le raccourcir et écrire votre nouveau titre à la suite de ce message.", check, yes_no_question=False)
                    if response is None:
                        return
                if self.is_valid_question(response.content):
                    try:
                        await thread.edit(name=response.content)
                        await thread.send(f"{thread.owner.mention} Votre titre a bien été modifié. Le fil est maintenant ouvert à tous pour la discussion. Merci de votre coopération.")
                        await thread.owner.remove_roles(author_role)
                        self.delete_messages[thread.id] = False
                        break
                    except Exception as e:
                        print(f"Erreur lors de la modification du titre du fil : {e}")
                else:
                    if len(response.content) < 20:
                        response = await self.ask_question(thread, "Votre titre est trop court. Il doit contenir au moins 20 caractères. Veuillez le rallonger et écrire votre nouveau titre à la suite de ce message.", check, yes_no_question=False)
                        if response is None:
                            return
                    if '?' not in response.content:
                        response = await self.ask_question(thread, "Votre titre ne se termine pas par un `?`. Veuillez ajouter un `?` à la fin et écrire votre nouveau titre à la suite de ce message.", check, yes_no_question=False)
                        if response is None:
                            return
                    if not any(response.content.lower().split()[0] == word for word in self.interrogative_words):
                        response = await self.ask_question(thread, "Votre titre ne commence pas par un mot interrogatif. Il doit commencer par un mot comme `qui`, `quoi`, `où`, `quand`, `pourquoi`, `comment`, `est-ce que`, `qu'est-ce que`, `combien`, `quel`, `quelle`, `quels`, `quelles`. Veuillez le changer et écrire votre nouveau titre à la suite de ce message.", check, yes_no_question=False)
                        if response is None:
                            return

async def setup(bot):
    await bot.add_cog(Question(bot))