import asyncio
from discord.ext import commands
from constants import *

class Question(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.threads = {}
        self.delete_messages = {}
        self.interrogative_words = ["qui", "quoi", "où", "quand", "pourquoi", "comment", "est-ce", "qu'est-ce", "combien", "quel", "quelle", "quels", "quelles"]

    def get_question_error(self, title):
        lower_title = title.lower()
        if not any(lower_title.startswith(word) for word in self.interrogative_words):
            return "starts_with_interrogative_word"
        if len(lower_title) < 20:
            return "length_too_short"
        if len(lower_title) > 100:
            return "length_too_long"
        if not lower_title.endswith('?'):
            return "does_not_end_with_question_mark"
        return None

    def send_error_message(self, error_type, thread):
        if error_type == "starts_with_interrogative_word":
            return f"{thread.owner.mention} Votre titre ne commence pas par un mot interrogatif. Il doit commencer par un mot comme `qui`, `quoi`, `où`, `quand`, `pourquoi`, `comment`, `est-ce que`, `qu'est-ce que`, `combien`, `quel`, `quelle`, `quels`, `quelles`. Veuillez le changer et écrire votre nouveau titre à la suite de ce message."
        elif error_type == "length_too_short":
            return f"{thread.owner.mention} Votre titre est trop court. Il doit contenir au moins 20 caractères. Veuillez l'étendre et écrire votre nouveau titre à la suite de ce message."
        elif error_type == "length_too_long":
            return f"{thread.owner.mention} Votre titre est trop long. Il doit être de 100 caractères ou moins. Veuillez le raccourcir et écrire votre nouveau titre à la suite de ce message."
        elif error_type == "does_not_end_with_question_mark":
            return f"{thread.owner.mention} Votre titre ne se termine pas par un `?`. Veuillez ajouter un `?` à la fin et écrire votre nouveau titre à la suite de ce message."

    async def ask_question(self, thread, message, check, yes_no_question=True):
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
                await thread.owner.remove_roles(QUESTION_ROLE_ID)
                await thread.delete()
                return None
            await thread.send(f"{thread.owner.mention} {message}")

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if thread.parent_id != QUESTION_CHANNEL_ID:
            return
        def check(m):
            return m.channel == thread and m.author == thread.owner

        question_role = thread.guild.get_role(QUESTION_ROLE_ID)
        await thread.owner.add_roles(question_role)

        while True:
            error_type = self.get_question_error(thread.name)
            if error_type:
                error_message = self.send_error_message(error_type, thread)
                await thread.send(error_message)

                try:
                    response = await self.bot.wait_for('message', check=check, timeout=600)
                    thread.name = response.content
                    continue
                except asyncio.TimeoutError:
                    await thread.owner.send("Votre fil a été supprimé car vous avez mis plus de 10 minutes à répondre au questionnaire.")
                    await thread.owner.remove_roles(question_role)
                    await thread.delete()
                    return
            else:
                await thread.edit(name=response.content)
                await thread.send(f"{thread.owner.mention} Très bien, votre titre semble approprié. Le fil est maintenant ouvert à tous pour la discussion. Merci de votre coopération.")
                await thread.owner.remove_roles(question_role)
                break

    @commands.Cog.listener()
    async def on_message(self, message):
        thread = message.channel
        if thread.id in self.threads and self.delete_messages.get(thread.id, False) and message.author.id != self.threads[thread.id] and not any(role.id == CHEF_SINGE_ROLE_ID for role in message.author.roles) and message.author != self.bot.user:
            await message.delete()
            await message.author.send("Vous n'êtes pas autorisé à écrire dans ce fil pendant le déroulement du questionnaire.")

async def setup(bot):
    await bot.add_cog(Question(bot))