import asyncio
import traceback
from datetime import datetime
from discord.ext import commands
import discord
from constants import *
from transformers import pipeline

# Initialize the transformers pipeline for question detection
question_detector = pipeline('text-classification', model='mrm8488/bert-tiny-finetuned-question-detection')

def is_question(title):
    # Use the question detector to classify the title
    result = question_detector(title)
    return result[0]['label'] == 'LABEL_1'  # Assuming LABEL_1 is the class for questions

def send_error_message(title, error_types):
    if error_types is None:
        error_types = []
    error_list = "\n- ".join(error_types)
    message = f"Votre titre **'{title}'** contient les erreurs suivantes :\n- {error_list}\n\nVeuillez cliquer sur le bouton **Modifier le titre** ci-dessous pour corriger votre titre."
    embed = discord.Embed(title="Erreur de Titre", description=message, color=discord.Color.red())
    return embed

def send_success_message(title):
    embed = discord.Embed(
        title="Titre validé",
        description="Le fil est maintenant ouvert à tous pour la discussion.",
        color=discord.Color.green()
    )
    return embed

def disable_buttons(view):
    for item in view.children:
        if isinstance(item, discord.ui.Button):
            item.disabled = True

async def get_webhook(channel):
    webhooks = await channel.webhooks()
    webhook = discord.utils.find(lambda wh: wh.user == channel.guild.me, webhooks)
    if webhook is None:
        webhook = await channel.create_webhook(name="MessageForwarder", reason="Pour reposter les messages")
    return webhook

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
        if interaction.user != self.author:
            await interaction.response.send_message("Seul l'auteur du fil peut modifier le titre.", ephemeral=True)
            return
        
        new_title = self.children[0].value
        error_types = self.get_question_error(new_title)
        try:
            message = await self.thread.fetch_message(self.message_id)
        except discord.NotFound:
            await interaction.response.send_message("Le message original est introuvable.", ephemeral=True)
            return
            
        if error_types:
            error_embed = send_error_message(new_title, error_types)
            if message.author == self.bot.user:
                await message.edit(content=self.author.mention, embed=error_embed)
            else:
                await self.webhook.edit_message(self.message_id, content=self.author.mention, embed=error_embed, thread=self.thread)
            await interaction.response.send_message("Le titre contient encore des erreurs.", ephemeral=True)
        else:
            await self.thread.edit(name=new_title)
            success_embed = send_success_message(new_title)
            if message.author == self.bot.user:
                await message.edit(content=self.author.mention, embed=success_embed)
            else:
                await self.webhook.edit_message(self.message_id, content=self.author.mention, embed=success_embed, thread=self.thread)
            await interaction.response.send_message("Le titre du fil a été mis à jour.", ephemeral=True)
            self.bot.get_cog('Question').delete_messages[self.thread.id] = False

            if self.original_message:
                try:
                    await self.original_message.delete()
                except discord.NotFound:
                    pass

            role = discord.utils.get(self.thread.guild.roles, id=QUESTION_ROLE_ID)
            if role:
                await self.author.remove_roles(role)

class AnswerView(discord.ui.View):
    def __init__(self, thread, message_id, get_question_error, bot, original_message, author, webhook):
        super().__init__(timeout=None)
        self.thread = thread
        self.message_id = message_id
        self.get_question_error = get_question_error
        self.bot = bot
        self.original_message = original_message
        self.author = author
        self.webhook = webhook

    @discord.ui.button(label="Modifier le titre", style=discord.ButtonStyle.grey)
    async def answer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("Seul l'auteur du fil peut modifier le titre.", ephemeral=True)
            return
        modal = TitleModal(self.thread, self.message_id, self.get_question_error, self.bot, self.original_message, self.author, self.webhook)
        await interaction.response.send_modal(modal)

class ConfirmView(discord.ui.View):
    def __init__(self, message, bot):
        super().__init__(timeout=60)
        self.message = message
        self.bot = bot
        self.confirmation_message = None
        self.message_id = None

    @discord.ui.button(label="Oui", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.message.author:
            await interaction.response.send_message("Seul l'auteur de la question peut effectuer cette action.", ephemeral=True)
            return

        question_channel = self.bot.get_channel(QUESTION_CHANNEL_ID)
        
        initial_content = f"Posté par : {self.message.author.id}\n{self.message.content}"
        
        if not initial_content.strip():
            initial_content = "Contenu par défaut"

        new_thread = None
        thread_message = None

        try:
            webhook = await get_webhook(question_channel)
            webhook_message = await webhook.send(
                content=initial_content,
                username=self.message.author.display_name,
                avatar_url=self.message.author.display_avatar.url,
                wait=True,
                thread_name=self.message.content[:50]
            )
            thread_message = await webhook_message.fetch()
            new_thread = await self.bot.fetch_channel(thread_message.id)
            
            await new_thread.add_user(self.message.author)
            view = AnswerView(new_thread, thread_message.id, self.bot.get_cog('Question').get_question_error, self.bot, self.message, self.message.author, webhook)

            success_embed = discord.Embed(title="Succès", description="Le message a été déplacé avec succès.", color=discord.Color.green())
            await webhook.edit_message(thread_message.id, content=self.message.author.mention, embed=success_embed, view=view, thread=new_thread)

        except discord.HTTPException as e:
            traceback.print_exc()
            if e.code == 50006:
                pass
            error_embed = discord.Embed(title="Erreur", description=f"Il y a eu une erreur : {e}", color=discord.Color.red())
            await thread.send(content=self.message.author.mention, embed=error_embed)

        if new_thread:
            self.bot.get_cog('Question').threads[new_thread.id] = self.message.author.id

            try:
                await self.message.delete()
            except discord.NotFound:
                pass

            await self.bot.get_channel(DISCUSSION_CHANNEL_ID).send(f"{self.message.author.mention} Votre question a été déplacée dans le fil <#{new_thread.id}>.")

            await self.confirmation_message.delete()

            async for msg in new_thread.history(limit=10):
                if msg.author == self.bot.user and not msg.is_system() and msg.id != thread_message.id:
                    await msg.delete()

            error_types = self.bot.get_cog('Question').get_question_error(new_thread.name)
            if error_types:
                error_embed = send_error_message(new_thread.name, error_types)
                view = AnswerView(new_thread, thread_message.id, self.bot.get_cog('Question').get_question_error, self.bot, self.message, self.message.author, webhook)
                await webhook.edit_message(thread_message.id, content=self.message.author.mention, embed=error_embed, view=view, thread=new_thread)
            else:
                success_embed = send_success_message(new_thread.name)
                await webhook.edit_message(thread_message.id, content=self.message.author.mention, embed=success_embed, thread=new_thread)
        else:
            pass

    @discord.ui.button(label="Non", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.message.author:
            await interaction.response.send_message(f"Seul l'auteur de la question peut effectuer cette action.", ephemeral=True)
            return
        await self.confirmation_message.delete()
        await self.bot.get_channel(DISCUSSION_CHANNEL_ID).send(f"{self.message.author.mention} Votre question n'a pas été déplacée.")

    async def handle_timeout(self):
        await self.confirmation_message.delete()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        result = await super().interaction_check(interaction)
        if not result:
            await self.handle_timeout()
        return result

    async def on_timeout(self):
        await self.handle_timeout()

        self.stop()

class Question(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.threads = {}
        self.embed_messages = {}
        self.delete_messages = {}
        self.last_asked = {}
        self.interrogative_words = ["qui", "que", "quoi", "qu'", "où", "quand", "pourquoi", "comment", "est-ce", "combien", "quel", "quelle", "quels", "quelles", "lequel", "laquelle", "lesquels", "lesquelles"]

    def get_question_error(self, title):
        errors = []
        first_word_original = title.split(" ")[0]
        first_word = first_word_original.lower()
        lower_title = title.lower()

        if not first_word_original[0].isupper():
            errors.append("Le premier mot de votre titre doit commencer par une majuscule.")
        
        if not is_question(title):
            errors.append("Votre titre ne semble pas être une question.")
        
        if len(lower_title) < 20:
            errors.append("Votre titre est trop court. Il doit contenir au moins 20 caractères.")
        if len(lower_title) > 100:
            errors.append("Votre titre est trop long. Il doit être de 100 caractères ou moins.")
        if not lower_title.endswith('?'):
            errors.append("Votre titre ne se termine pas par un `?`.")
        
        return errors if errors else None

    async def handle_timeout(self, thread):
        if self.delete_messages.get(thread.id, False):
            await thread.send("Votre fil a été supprimé car vous avez mis plus de 10 minutes à répondre au questionnaire.")
            await thread.delete()

            role = discord.utils.get(thread.guild.roles, id=QUESTION_ROLE_ID)
            if role:
                await thread.owner.remove_roles(role)
        else:
            await thread.send("Le temps est écoulé, mais votre question n'a pas été déplacée.")

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

        self.threads[thread.id] = message.author.id
        self.delete_messages[thread.id] = True

        error_types = self.get_question_error(thread.name)
        
        if not error_types:
            success_embed = send_success_message(thread.name)
            embed_message = await thread.send(content=message.author.mention if message.author else "", embed=success_embed)
            self.embed_messages[thread.id] = embed_message.id
            self.delete_messages[thread.id] = False
        else:
            role = discord.utils.get(thread.guild.roles, id=QUESTION_ROLE_ID)
            if role and message.author and not message.author.bot:
                await message.author.add_roles(role)

            error_embed = send_error_message(thread.name, error_types)
            view = AnswerView(thread, message_id, self.get_question_error, self.bot, None, message.author, await get_webhook(thread.parent))
            embed_message = await thread.send(content=message.author.mention if message.author else "", embed=error_embed, view=view)
            self.embed_messages[thread.id] = embed_message.id
            view.message_id = embed_message.id
            asyncio.create_task(self.monitor_thread(thread))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if isinstance(message.channel, discord.Thread):
            thread = message.channel
            if self.delete_messages.get(thread.id, False):
                if message.author.id != self.threads.get(thread.id):
                    if message.type != discord.MessageType.channel_name_change and not message.is_system():
                        await message.delete()
                        await message.author.send(f"Vous ne pouvez pas écrire dans ce fil tant que le titre n'est pas corrigé : {thread.jump_url}")
                elif message.author.id == self.threads.get(thread.id):
                    if message.type != discord.MessageType.channel_name_change and not message.is_system():
                        await message.delete()
                        await message.author.send(f"Veuillez cliquer sur le bouton `Modifier le titre` de votre fil pour corriger le titre : {thread.jump_url}")

        if message.channel.id == DISCUSSION_CHANNEL_ID:
            content = message.content.lower()
            if message.channel.id == DISCUSSION_CHANNEL_ID and len(message.content) > 10 and message.content.endswith('?'):
                last_asked_time = self.last_asked.get(message.author.id)
                if last_asked_time and (datetime.now() - last_asked_time).total_seconds() < 86400:
                    return
                self.last_asked[message.author.id] = datetime.now()

                view = ConfirmView(message, self.bot)
                embed = discord.Embed(
                    title="Question détectée",
                    description=(
                        "Nous avons détecté une question. Conformément au [**règlement**](https://discord.com/channels/684734347177230451/724737757427269702), assurez-vous que votre question soit liée à NosTale. Ensuite, suivez les étapes suivantes :\n\n"
                        "1. **Cliquez sur le bouton 'Oui' pour déplacer le message vers [Questions](https://discord.com/channels/684734347177230451/1055993732505284690).**\n\n"
                        "2. **Modifiez le titre de votre fil pour qu'il soit conforme aux règles suivantes :**\n"
                        "   - Commencer par une majuscule.\n"
                        "   - Utiliser un mot ou une expression interrogative.\n"
                        "   - Avoir entre 20 et 100 caractères.\n"
                        "   - Terminer par un point d'interrogation (?).\n\n"
                        "3. **Une fois le titre validé, tous les membres pourront participer à la discussion.**"
                    ),
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
            message_id = self.embed_messages.get(after.id)
            embed_message = await after.fetch_message(message_id)
        except discord.NotFound:
            return

        if error_types:
            error_embed = send_error_message(after.name, error_types)
            view = AnswerView(after, message_id, self.get_question_error, self.bot, None, after.owner, await get_webhook(after.parent))
            await embed_message.edit(content=after.owner.mention, embed=error_embed, view=view)
            self.delete_messages[after.id] = True

            role = discord.utils.get(after.guild.roles, id=QUESTION_ROLE_ID)
            if role and not after.owner.bot:
                await after.owner.add_roles(role)
        else:
            success_embed = send_success_message(after.name)
            await embed_message.edit(content=after.owner.mention, embed=success_embed)
            self.delete_messages[after.id] = False

            role = discord.utils.get(after.guild.roles, id=QUESTION_ROLE_ID)
            if role and not after.owner.bot:
                await after.owner.remove_roles(role)

async def setup(bot):
    await bot.add_cog(Question(bot))
