import asyncio
from datetime import datetime
from discord.ext import commands
import discord
from constants import *

def send_error_message(title, error_types):
    if error_types is None:
        error_types = []
    error_list = "\n- ".join(error_types)
    message = f"Votre titre **'{title}'** contient les erreurs suivantes :\n- {error_list}\n\nVeuillez cliquer sur le bouton **Modifier le titre** ci-dessous pour corriger votre titre."
    embed = discord.Embed(title="Erreur de Titre", description=message, color=discord.Color.red())
    return embed

def send_success_message(title):
    message = "Le fil est maintenant ouvert à tous pour la discussion."
    embed = discord.Embed(
        title="Titre validé",
        description=message,
        color=discord.Color.green()
    )
    return embed

class TitleModal(discord.ui.Modal):
    def __init__(self, thread, message_id, get_question_error, bot, original_message, author, webhook):
        super().__init__(title="Modifier le titre du fil")
        self.thread = thread
        self.message_id = message_id
        self.get_question_error = get_question_error
        self.bot = bot
        self.original_message = original_message
        self.author = author
        self.webhook = webhook
        self.add_item(discord.ui.TextInput(label="Nouveau titre", style=discord.TextStyle.short, placeholder="Entrez le nouveau titre du fil...", custom_id="new_title", max_length=100))

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("Seul l'auteur du fil peut modifier le titre.", ephemeral=True)
            return
        
        new_title = self.children[0].value
        error_types = self.get_question_error(new_title)

        if error_types:
            error_embed = send_error_message(new_title, error_types)
            await self.webhook.edit_message(self.message_id, content=self.author.mention, embed=error_embed)
            await interaction.response.send_message("Le titre contient encore des erreurs.", ephemeral=True)
        else:
            await self.thread.edit(name=new_title)
            success_embed = send_success_message(new_title)
            await self.webhook.edit_message(self.message_id, content=self.author.mention, embed=success_embed)
            await interaction.response.send_message("Le titre du fil a été mis à jour.", ephemeral=True)
            self.bot.get_cog('Question').delete_messages[self.thread.id] = False

            if self.original_message:
                try:
                    await self.original_message.delete()
                except discord.NotFound:
                    print(f"Original message ID: {self.original_message.id} not found for deletion.")

            role = discord.utils.get(self.thread.guild.roles, id=QUESTION_ROLE_ID)
            if role:
                await self.author.remove_roles(role)

class AnswerView(discord.ui.View):
    def __init__(self, thread, message_id, get_question_error, bot, message, author):
        super().__init__()
        self.thread = thread
        self.message_id = message_id
        self.get_question_error = get_question_error
        self.bot = bot
        self.message = message
        self.author = author

    @discord.ui.button(label="Modifier le titre", style=discord.ButtonStyle.grey)
    async def answer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("Seul l'auteur du fil peut modifier le titre.", ephemeral=True)
            return
        modal = TitleModal(self.thread, self.message_id, self.get_question_error, self.bot, self.original_message, self.author)
        await interaction.response.send_modal(modal)

class Question(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.threads = {}
        self.delete_messages = {}
        self.last_asked = {}
        self.interrogative_words = ["qui", "que", "quoi", "qu'", "où", "quand", "pourquoi", "comment", "est-ce", "combien", "quel", "quelle", "quels", "quelles", "lequel", "laquelle", "lesquels", "lesquelles", "d'où", "depuis", "jusqu'", "à", "de", "en"]

    def get_question_error(self, title):
        errors = []
        first_word_original = title.split(" ")[0]
        first_word = first_word_original.lower()
        lower_title = title.lower()

        if not first_word_original[0].isupper():
            errors.append("Le premier mot de votre titre doit commencer par une majuscule.")
        
        if not any(first_word.startswith(word) for word in self.interrogative_words):
            if not any(ending in first_word for ending in ["-t-", "-on", "-je", "-tu", "-il", "-elle", "-nous", "-vous", "-ils", "-elles"]):
                errors.append("Votre titre ne commence pas par un mot interrogatif ou une expression interrogative.")
        
        if len(lower_title) < 20:
            errors.append("Votre titre est trop court. Il doit contenir au moins 20 caractères.")
        if len(lower_title) > 100:
            errors.append("Votre titre est trop long. Il doit être de 100 caractères ou moins.")
        if not lower_title.endswith('?'):
            errors.append("Votre titre ne se termine pas par un `?`.")
        
        return errors if errors else None

    async def handle_timeout(self, thread):
        await thread.owner.send("Votre fil a été supprimé car vous avez mis plus de 10 minutes à répondre au questionnaire.")
        await thread.delete()

        role = discord.utils.get(thread.guild.roles, id=QUESTION_ROLE_ID)
        if role:
            await thread.owner.remove_roles(role)

    async def monitor_thread(self, thread):
        await asyncio.sleep(600)
        if self.delete_messages.get(thread.id, False):
            await self.handle_timeout(thread)

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if thread.parent_id != QUESTION_CHANNEL_ID:
            return

        async for message in thread.history(limit=1):
            await message.pin()
            message_id = message.id
            break

        if not hasattr(self.bot, 'threads'):
            self.bot.threads = {}

        if thread.owner:
            self.threads[thread.id] = thread.owner.id
        else:
            print(f"Thread ID: {thread.id} has no owner.")

        self.delete_messages[thread.id] = True

        error_types = self.get_question_error(thread.name)
        role = discord.utils.get(thread.guild.roles, id=QUESTION_ROLE_ID)
        
        if role and thread.owner and not thread.owner.bot:
            await thread.owner.add_roles(role)

        if not error_types:
            success_embed = send_success_message(thread.name)
            await thread.send(content=thread.owner.mention if thread.owner else "", embed=success_embed)
            self.delete_messages[thread.id] = False
        else:
            error_embed = send_error_message(thread.name, error_types)
            view = AnswerView(thread, message_id, self.get_question_error, self.bot, None, thread.owner)
            msg = await thread.send(content=thread.owner.mention if thread.owner else "", embed=error_embed, view=view)
            view.message_id = msg.id
            asyncio.create_task(self.monitor_thread(thread))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if isinstance(message.channel, discord.Thread):
            thread = message.channel
            if self.delete_messages.get(thread.id, False):
                if message.author.id != self.threads.get(thread.id):
                    await message.delete()
                    await message.author.send(f"Vous ne pouvez pas écrire dans ce fil tant que le titre n'est pas corrigé : {thread.jump_url}")
                elif message.author.id == self.threads.get(thread.id):
                    await message.delete()
                    await message.author.send(f"Veuillez cliquer sur le bouton `Modifier le titre` de votre fil pour corriger le titre : {thread.jump_url}")

        if message.channel.id == DISCUSSION_CHANNEL_ID:
            content = message.content.lower()
            if (any(word in content for word in self.interrogative_words) or content.endswith('?')) and len(content) > 10:
                last_asked_time = self.last_asked.get(message.author.id)
                if last_asked_time and (datetime.now() - last_asked_time).total_seconds() < 86400:
                    return
                self.last_asked[message.author.id] = datetime.now()

                view = ConfirmView(message, self.bot)
                embed = discord.Embed(
                    title="Question détectée",
                    description="Nous avons détecté votre message comme étant une question. Selon le règlement, les questions doivent être posées dans le salon dédié. Souhaitez-vous déplacer votre question dans le salon approprié ?",
                    color=discord.Color.blue()
                )
                confirmation_message = await message.reply(embed=embed, view=view)
                view.confirmation_message = confirmation_message
                view.message_id = message.id

    @commands.Cog.listener()
    async def on_thread_update(self, before, after):
        if before.parent_id != QUESTION_CHANNEL_ID or before.name == after.name:
            return

        error_types = self.get_question_error(after.name)
        try:
            message = await after.fetch_message(self.threads.get(after.id))
        except discord.NotFound:
            return

        if error_types:
            error_embed = send_error_message(after.name, error_types)
            view = AnswerView(after, self.threads.get(after.id), self.get_question_error, self.bot, None, after.owner)
            await message.edit(content=after.owner.mention if after.owner else "", embed=error_embed, view=view)
            self.delete_messages[after.id] = True

            role = discord.utils.get(after.guild.roles, id=QUESTION_ROLE_ID)
            if role and not after.owner.bot:
                await after.owner.remove_roles(role)
        else:
            success_embed = send_success_message(after.name)
            await message.edit(content=after.owner.mention if after.owner else "", embed=success_embed)
            self.delete_messages[after.id] = False

            role = discord.utils.get(after.guild.roles, id=QUESTION_ROLE_ID)
            if role and not after.owner.bot:
                await after.owner.add_roles(role)

class ConfirmView(discord.ui.View):
    def __init__(self, message, bot):
        super().__init__(timeout=None)
        self.message = message
        self.bot = bot
        self.confirmation_message = None
        self.message_id = None

    async def get_webhook(self, channel):
        webhooks = await channel.webhooks()
        webhook = discord.utils.find(lambda wh: wh.user == channel.guild.me, webhooks)
        if webhook is None:
            webhook = await channel.create_webhook(name="MessageForwarder", reason="Pour reposter les messages")
        return webhook

    @discord.ui.button(label="Oui", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.message.author:
            await interaction.response.send_message("Seul l'auteur de la question peut effectuer cette action.", ephemeral=True)
            return

        question_channel = self.bot.get_channel(QUESTION_CHANNEL_ID)
        
        webhook = await self.get_webhook(question_channel)
        initial_content = f"Posté par : {self.message.author.id}\n{self.message.content}"
        sent_message = await webhook.send(
            content=initial_content,
            username=self.message.author.display_name,
            avatar_url=self.message.author.display_avatar.url,
            thread_name=self.message.content[:50],
            wait=True
        )

        try:
            new_thread = question_channel.get_thread(sent_message.id)
            view = AnswerView(new_thread, sent_message.id, self.bot.get_cog('Question').get_question_error, self.bot, self.message, self.message.author)
            error_embed = discord.Embed(title="Erreur", description="Il y a eu une erreur.", color=discord.Color.red())
            await sent_message.edit(content=self.message.author.mention, embed=error_embed)
            print(f"Message edited successfully.")
        except Exception as e:
            print(f"An error occurred: {e}")

        print(f"Thread ID: {new_thread.id}")

        if not hasattr(self.bot, 'threads'):
            self.bot.threads = {}

        self.bot.threads[new_thread.id] = self.message.author.id


        role = discord.utils.get(new_thread.guild.roles, id=QUESTION_ROLE_ID)
        if role and not self.message.author.bot:
            await self.message.author.add_roles(role)

        try:
            await self.message.delete()
        except discord.NotFound:
            print(f"Message ID: {self.message.id} not found for deletion.")

        await self.bot.get_channel(DISCUSSION_CHANNEL_ID).send(f"{self.message.author.mention} Votre question a été déplacée dans le fil <#{new_thread.id}>.")

        await self.confirmation_message.delete()

        async for msg in new_thread.history(limit=10):
            if msg.author == self.bot.user:
                await msg.delete()

        error_types = self.bot.get_cog('Question').get_question_error(new_thread.name)
        if error_types:
            error_embed = send_error_message(new_thread.name, error_types)
            view = AnswerView(new_thread, sent_message.id, self.bot.get_cog('Question').get_question_error, self.bot, self.message, self.message.author, webhook)
            await webhook.edit_message(sent_message.id, content=self.message.author.mention, embed=error_embed, view=view)
        else:
            success_embed = send_success_message(new_thread.name)
            await webhook.edit_message(sent_message.id, content=self.message.author.mention, embed=success_embed)


    @discord.ui.button(label="Non", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.message.author:
            await interaction.response.send_message(f"{self.message.author.mention} Seul l'auteur de la question peut effectuer cette action.", ephemeral=True)
            return
        await self.confirmation_message.delete()
        await self.bot.get_channel(DISCUSSION_CHANNEL_ID).send(f"Votre question n'a pas été déplacée.")

        self.stop()

async def setup(bot):
    await bot.add_cog(Question(bot))
