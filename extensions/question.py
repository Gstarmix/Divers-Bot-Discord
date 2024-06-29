import json
import logging
import os
from datetime import datetime
from difflib import SequenceMatcher
import asyncio
import traceback
from discord.ext import commands
import discord
from constants import *

TAG_OPTIONS = [
    discord.SelectOption(label="Stuff | Rune", emoji="🏹"),
    discord.SelectOption(label="Carte SP", emoji="🃏"),
    discord.SelectOption(label="Equipment|Accessoire", emoji="💎"),
    discord.SelectOption(label="Pet | Partner", emoji="🐶"),
    discord.SelectOption(label="Buff | Debuff", emoji="🌠"),
    discord.SelectOption(label="XP | Quête | TS", emoji="📈"),
    discord.SelectOption(label="Or | Drop | Nosmall", emoji="💰"),
    discord.SelectOption(label="PvE Raid | PvE Mob", emoji="🏰"),
    discord.SelectOption(label="PvP", emoji="⚔"),
    discord.SelectOption(label="Évènement", emoji="🎉"),
    discord.SelectOption(label="Informatique | Bug", emoji="🖥"),
    discord.SelectOption(label="Autre", emoji="❓"),
]

DATA_PATH = "extensions/threads.json"
KEYWORDS_PATH = "extensions/nostale_keywords.json"

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

INTERROGATIVE_WORDS = ["qui", "que", "quoi", "qu'", "où", "quand", "pourquoi", "comment", "est-ce", "combien", "quel", "quelle", "quels", "quelles", "lequel", "laquelle", "lesquels", "lesquelles"]
INTERROGATIVE_EXPRESSIONS = ["-t-", "-on", "-je", "-tu", "-il", "-elle", "-nous", "-vous", "-ils", "-elles"]

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

async def get_webhook(channel):
    webhooks = await channel.webhooks()
    webhook = discord.utils.find(lambda wh: wh.user == channel.guild.me, webhooks)
    if webhook is None:
        webhook = await channel.create_webhook(name="MessageForwarder", reason="Pour reposter les messages")
    return webhook

class TitleModal(discord.ui.Modal):
    def __init__(self, thread, message_id, get_question_error, bot, original_message, author, webhook, selected_tags):
        super().__init__(title="Modifier le titre du fil")
        self.thread = thread
        self.message_id = message_id
        self.get_question_error = get_question_error
        self.bot = bot
        self.original_message = original_message
        self.author = author
        self.webhook = webhook
        self.selected_tags = selected_tags
        self.add_item(discord.ui.TextInput(
            label="Nouveau titre",
            style=discord.TextStyle.short,
            placeholder="Entrez le nouveau titre du fil...",
            custom_id="new_title",
            min_length=20,
            max_length=100
        ))

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.send_message("Seul l'auteur du fil peut modifier le titre.", ephemeral=True)
            return
        
        new_title = self.children[0].value

        error_types = self.get_question_error(new_title, self.selected_tags)
        try:
            message = await self.thread.fetch_message(self.message_id)
        except discord.NotFound:
            await interaction.response.send_message("Le message original est introuvable.", ephemeral=True)
            return
            
        if error_types:
            error_embed = send_error_message(new_title, error_types)
            if message.author.id == self.bot.user.id:
                await message.edit(content=self.author.mention, embed=error_embed)
            else:
                await self.webhook.edit_message(self.message_id, content=self.author.mention, embed=error_embed, thread=self.thread)
            await interaction.response.send_message("Le titre contient encore des erreurs.", ephemeral=True)
        else:
            forum_tags = [tag for tag in self.thread.parent.available_tags if tag.name in self.selected_tags]
            await self.thread.edit(name=new_title, applied_tags=forum_tags)
            
            success_embed = send_success_message(new_title)
            view = self.bot.get_cog('Question').create_answer_view(self.thread, self.message_id, self.get_question_error, self.bot, self.original_message, self.author, self.webhook)
            view.remove_tag_select()
            
            if message.author.id == self.bot.user.id:
                await message.edit(content=self.author.mention, embed=success_embed, view=view)
            else:
                await self.webhook.edit_message(self.message_id, content=self.author.mention, embed=success_embed, view=view, thread=self.thread)
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

class TagSelect(discord.ui.Select):
    def __init__(self, author_id, selected_tags, message_id, get_question_error, thread, bot):
        self.author_id = author_id
        self.selected_tags = selected_tags
        self.message_id = message_id
        self.get_question_error = get_question_error
        self.thread = thread
        self.bot = bot
        super().__init__(placeholder="Sélectionnez des tags", min_values=1, max_values=len(TAG_OPTIONS), options=TAG_OPTIONS)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Vous n'avez pas l'autorisation de faire cela.", ephemeral=True)
            return
        self.selected_tags[:] = self.values

        error_types = self.get_question_error(self.thread.name, self.selected_tags)
        try:
            message = await self.thread.fetch_message(self.message_id)
        except discord.NotFound:
            await interaction.response.send_message("Le message original est introuvable.", ephemeral=True)
            return

        if error_types:
            error_embed = send_error_message(self.thread.name, error_types)
            if message.author.id == self.bot.user.id:
                await message.edit(content=message.author.mention, embed=error_embed)
            else:
                webhook = await get_webhook(self.thread.parent)
                await webhook.edit_message(self.message_id, content=message.author.mention, embed=error_embed, thread=self.thread)
            await interaction.response.send_message("Les tags ont été mis à jour mais le titre contient encore des erreurs.", ephemeral=True)
        else:
            forum_tags = [tag for tag in self.thread.parent.available_tags if tag.name in self.selected_tags]
            await self.thread.edit(applied_tags=forum_tags)
            
            success_embed = send_success_message(self.thread.name)
            if message.author.id == self.bot.user.id:
                await message.edit(content=message.author.mention, embed=success_embed)
            else:
                webhook = await get_webhook(self.thread.parent)
                await webhook.edit_message(self.message_id, content=message.author.mention, embed=success_embed, thread=self.thread)
            await interaction.response.send_message("Les tags ont été mis à jour et le titre est maintenant validé.", ephemeral=True)
            self.bot.get_cog('Question').delete_messages[self.thread.id] = False

class TagSelectView(discord.ui.View):
    def __init__(self, author_id, selected_tags, message_id, get_question_error, thread, bot):
        super().__init__(timeout=None)
        self.add_item(TagSelect(author_id, selected_tags, message_id, get_question_error, thread, bot))

    def remove_tag_select(self):
        for item in self.children:
            if isinstance(item, TagSelect):
                self.remove_item(item)
                break

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
        self.selected_tags = [tag.name for tag in thread.applied_tags]
        if not self.selected_tags:
            self.add_item(TagSelect(author.id, self.selected_tags, message_id, get_question_error, thread, bot))

    def remove_tag_select(self):
        for item in self.children:
            if isinstance(item, TagSelect):
                self.remove_item(item)

    @discord.ui.button(label="Modifier le titre", style=discord.ButtonStyle.grey)
    async def modify_title(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.author:
            await interaction.response.send_message("Seul l'auteur du fil peut modifier le titre.", ephemeral=True)
            return
        modal = TitleModal(self.thread, self.message_id, self.get_question_error, self.bot, self.original_message, self.author, self.webhook, self.selected_tags)
        await interaction.response.send_modal(modal)

class StopConfirmView(discord.ui.View):
    def __init__(self, message, bot, question_view):
        super().__init__(timeout=60)
        self.message = message
        self.bot = bot
        self.question_view = question_view

    @discord.ui.button(label="Confirmer", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.message.author:
            await interaction.response.send_message("Seul l'auteur de la question peut effectuer cette action.", ephemeral=True)
            return
        await interaction.response.send_message("Vous ne recevrez plus de notifications pour les questions détectées.", ephemeral=True)
        self.disable_buttons()
        try:
            await self.question_view.confirmation_message.delete()
        except discord.NotFound:
            pass
        try:
            await interaction.message.delete()
        except discord.NotFound:
            pass

    @discord.ui.button(label="Annuler", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.message.author:
            await interaction.response.send_message("Seul l'auteur de la question peut effectuer cette action.", ephemeral=True)
            return
        stop_file = "stop_users.json"
        if os.path.exists(stop_file):
            with open(stop_file, "r") as f:
                stop_users = json.load(f)
            stop_users.remove(interaction.user.id)
            with open(stop_file, "w") as f:
                json.dump(stop_users, f)
        await interaction.response.send_message("Action annulée. Vous continuerez à recevoir des notifications pour les questions détectées.", ephemeral=True)
        self.disable_buttons()
        try:
            await self.question_view.confirmation_message.delete()
        except discord.NotFound:
            pass
        try:
            await interaction.message.delete()
        except discord.NotFound:
            pass

    def disable_buttons(self):
        for item in self.children:
            item.disabled = True

    async def on_timeout(self):
        try:
            await self.question_view.confirmation_message.delete()
        except discord.NotFound:
            pass
        try:
            await self.message.delete()
        except discord.NotFound:
            pass

class QuestionDetectedView(discord.ui.View):
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
            await question_channel.send(content=self.message.author.mention, embed=error_embed)

        if new_thread:
            self.bot.get_cog('Question').threads[new_thread.id] = self.message.author.id

            try:
                await self.confirmation_message.delete()
            except discord.NotFound:
                pass

            await self.bot.get_channel(DISCUSSION_CHANNEL_ID).send(f"{self.message.author.mention} Votre question a été déplacée dans le fil <#{new_thread.id}>.")

            async for msg in new_thread.history(limit=10):
                if msg.author == self.bot.user and not msg.is_system() and msg.id != thread_message.id:
                    await msg.delete()

            error_types = self.bot.get_cog('Question').get_question_error(new_thread.name, new_thread.applied_tags)
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
        try:
            await self.confirmation_message.delete()
        except discord.NotFound:
            pass
        await self.bot.get_channel(DISCUSSION_CHANNEL_ID).send(f"{self.message.author.mention} Votre question n'a pas été déplacée.")

    @discord.ui.button(label="STOP", style=discord.ButtonStyle.grey)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.message.author:
            await interaction.response.send_message("Seul l'auteur de la question peut effectuer cette action.", ephemeral=True)
            return
        await self.record_stop_user(interaction.user.id)
        await self.show_confirmation(interaction)

    async def record_stop_user(self, user_id):
        stop_file = "stop_users.json"
        if os.path.exists(stop_file):
            with open(stop_file, "r") as f:
                stop_users = json.load(f)
        else:
            stop_users = []

        if user_id not in stop_users:
            stop_users.append(user_id)

        with open(stop_file, "w") as f:
            json.dump(stop_users, f)

    async def show_confirmation(self, interaction):
        confirm_view = StopConfirmView(self.message, self.bot, self)
        confirm_embed = discord.Embed(
            title="Confirmation",
            description=(
                "Vous avez choisi de désactiver les notifications pour les questions détectées. "
                "Cette action est permanente et vous ne recevrez plus ces notifications. "
                "Voulez-vous confirmer cette action ?\n\n"
                "Si vous ne faites pas attention, vous risquez des sanctions plus sévères à l'avenir."
            ),
            color=discord.Color.orange()
        )
        confirmation_message = await interaction.response.send_message(embed=confirm_embed, view=confirm_view, ephemeral=False)
        confirm_view.confirmation_message = confirmation_message

    async def handle_timeout(self):
        try:
            await self.confirmation_message.delete()
        except discord.NotFound:
            pass
        try:
            await self.message.delete()
        except discord.NotFound:
            pass

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

    def get_question_error(self, title, selected_tags=None):
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
        
        if not selected_tags and not self.thread_has_tags(selected_tags):
            errors.append("Vous devez sélectionner un tag.")
        
        return errors if errors else None

    def thread_has_tags(self, selected_tags):
        if selected_tags:
            return True
        if hasattr(self, "thread") and self.thread and self.thread.applied_tags:
            return True
        return False

    async def handle_timeout(self, thread):
        if self.delete_messages.get(thread.id, False):
            await thread.send("Votre fil a été supprimé car vous avez mis plus de 10 minutes à répondre au questionnaire.")
            await thread.delete()

            role = discord.utils.get(thread.guild.roles, id=QUESTION_ROLE_ID)
            if role:
                await thread.owner.remove_roles(role)
        else:
            await thread.send("Le temps est écoulé, mais votre question n'a pas été déplacée.")

    def create_answer_view(self, thread, message_id, get_question_error, bot, original_message, author, webhook):
        return AnswerView(thread, message_id, get_question_error, bot, original_message, author, webhook)

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

        error_types = self.get_question_error(thread.name, thread.applied_tags)
        
        if not error_types:
            success_embed = send_success_message(thread.name)
            view = AnswerView(thread, message_id, self.get_question_error, self.bot, None, message.author, await get_webhook(thread.parent))
            view.remove_tag_select()
            embed_message = await thread.send(content=message.author.mention if message.author else "", embed=success_embed, view=view)
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

    def user_has_stopped(self, user_id):
        stop_file = "stop_users.json"
        if os.path.exists(stop_file):
            with open(stop_file, "r") as f:
                stop_users = json.load(f)
            return user_id in stop_users
        return False

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
            if self.user_has_stopped(message.author.id):
                return
            
            content = message.content.lower()
            if (any(word in content for word in self.interrogative_words) or content.endswith('?')) and len(content) > 10:
                last_asked_time = self.last_asked.get(message.author.id)
                if last_asked_time and (datetime.now() - last_asked_time).total_seconds() < 259200:
                    return
                self.last_asked[message.author.id] = datetime.now()

                view = QuestionDetectedView(message, self.bot)
                embed = discord.Embed(
                    title="Question détectée",
                    description=(
                        "Nous avons détecté une question. Conformément au [**règlement**](https://discord.com/channels/684734347177230451/724737757427269702), assurez-vous que votre question soit liée à NosTale. Ensuite, suivez les étapes suivantes :\n\n"
                        "1. **Cliquez sur le bouton Oui pour déplacer le message vers [Questions](https://discord.com/channels/684734347177230451/1055993732505284690).**\n\n"
                        "2. **Modifiez le titre de votre fil pour qu'il soit conforme aux règles suivantes :**\n"
                        "   - Commencer par une majuscule.\n"
                        "   - Utiliser un mot ou une expression interrogative.\n"
                        "   - Avoir entre 20 et 100 caractères.\n"
                        "   - Terminer par un point d'interrogation (?).\n"
                        "   - Sélectionner au moins un tag approprié pour votre question.\n\n"
                        "3. **Une fois le titre validé, tous les membres pourront participer à la discussion.**\n\n"
                        "Si vous ne souhaitez plus recevoir ces notifications, cliquez sur le bouton **STOP**."
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

        error_types = self.get_question_error(after.name, after.applied_tags)
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
            view = AnswerView(after, message_id, self.get_question_error, self.bot, None, after.owner, await get_webhook(after.parent))
            view.remove_tag_select()
            await embed_message.edit(content=after.owner.mention, embed=success_embed, view=view)
            self.delete_messages[after.id] = False

            role = discord.utils.get(after.guild.roles, id=QUESTION_ROLE_ID)
            if role and not after.owner.bot:
                await after.owner.remove_roles(role)

async def setup(bot):
    await bot.add_cog(Question(bot))
