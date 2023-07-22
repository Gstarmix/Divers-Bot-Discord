import asyncio
from discord.ext import commands
from constants import QUESTION_BOT_CHANNEL_ID, ADMIN_ROLE_ID, OTHER_ROLE_ID, AUTHOR_ROLE_ID

class Question(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.threads = {}

    async def ask_question(self, thread, message, check):
        while True:
            await thread.send(f"{thread.owner.mention} {message}")
            try:
                response = await self.bot.wait_for('message', check=check, timeout=60)
                return response
            except asyncio.TimeoutError:
                await thread.send(f"{thread.owner.mention} Je n'ai pas reçu de réponse. Veuillez répondre par 'Oui' ou 'Non'.")

    @commands.Cog.listener()
    async def on_thread_join(self, thread):
        if thread.parent.id != QUESTION_BOT_CHANNEL_ID:
            return
        if thread.id not in self.threads:
            self.threads[thread.id] = thread.owner.id

        def check(m):
            return m.channel == thread and m.author != self.bot.user

        while True:
            try:
                message = await self.bot.wait_for('message', check=check)
                if message.author.id != self.threads[thread.id] and not any(role.id in [ADMIN_ROLE_ID, AUTHOR_ROLE_ID] for role in message.author.roles):
                    await message.author.send("Vous n'êtes pas autorisé à écrire dans ce fil.")
                    await message.delete()
            except Exception as e:
                print(f"Une erreur est survenue lors de la gestion des messages dans le fil : {e}")

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if thread.parent.id != QUESTION_BOT_CHANNEL_ID:
            return

        # Ajouter le rôle AUTHOR_ROLE_ID à l'auteur du fil
        author_role = thread.guild.get_role(AUTHOR_ROLE_ID)
        await thread.owner.add_roles(author_role)

        def check(m):
            return m.channel == thread and m.author == thread.owner

        response = await self.ask_question(thread, "Bonjour, je vois que vous voulez poser une question. Votre titre est-il formulé comme une question ? Répondez par 'Oui' ou 'Non'.", check)
        
        if response.content.lower() == 'oui':
            await thread.send(f"{thread.owner.mention} Très bien, votre titre semble approprié. Le fil est maintenant ouvert à tous pour la discussion. Merci de votre coopération.")
            # Retirer le rôle AUTHOR_ROLE_ID de l'auteur du fil
            await thread.owner.remove_roles(author_role)
            # Donner la permission de parler aux membres ayant le rôle OTHER_ROLE_ID
            other_role = thread.guild.get_role(OTHER_ROLE_ID)
            await thread.set_permissions(other_role, send_messages=True)
        elif response.content.lower() == 'non':
            while True:
                new_title = await self.ask_question(thread, "Merci de reformuler votre titre en une question compréhensible et détaillée. Par exemple, au lieu de 'Conseil stuff', vous pourriez dire 'Quelles améliorations puis-je apporter à mon stuff ?' Ecrivez donc à la suite de ce message votre nouveau titre.", check)
                if len(new_title.content) > 100:
                    await thread.send(f"{thread.owner.mention} Votre titre est trop long. Il doit être de 100 caractères ou moins. Veuillez le raccourcir.")
                    continue
                confirmation = await self.ask_question(thread, f"Vous avez choisi le titre '{new_title.content}'. Est-ce correct ? Répondez par 'Oui' ou 'Non'.", check)
                if confirmation.content.lower() == 'non':
                    continue
                try:
                    await thread.edit(name=new_title.content)
                    await thread.send(f"{thread.owner.mention} Votre titre a bien été modifié. Le fil est maintenant ouvert à tous pour la discussion. Merci de votre coopération.")
                    # Retirer le rôle AUTHOR_ROLE_ID de l'auteur du fil
                    await thread.owner.remove_roles(author_role)
                    # Donner la permission de parler aux membres ayant le rôle OTHER_ROLE_ID
                    other_role = thread.guild.get_role(OTHER_ROLE_ID)
                    await thread.set_permissions(other_role, send_messages=True)
                except Exception as e:
                    print(f"Erreur lors de la modification du titre du fil : {e}")
                break
        else:
            await thread.send(f"{thread.owner.mention} Je n'ai pas compris votre réponse.")
            await self.on_thread_create(thread)

async def setup(bot):
    await bot.add_cog(Question(bot))
