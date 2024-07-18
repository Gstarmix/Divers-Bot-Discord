import json
import logging
import os
from datetime import datetime, timedelta, timezone
import asyncio
import re
from discord.ext import commands
import discord
from constants import *

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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

INTERROGATIVE_WORDS = [
    "qui", "que", "quoi", "qu'", "où", "quand", "pourquoi", "comment", "est-ce", "combien", 
    "quel", "quelle", "quels", "quelles", "lequel", "laquelle", "lesquels", "lesquelles", 
    "à qui", "à quoi", "de qui", "de quoi", "avec qui", "avec quoi", "pour qui", "pour quoi", 
    "chez qui", "chez quoi", "contre qui", "contre quoi", "vers qui", "vers quoi", "par qui", 
    "par quoi", "sur qui", "sur quoi", "en qui", "en quoi", "sous qui", "sous quoi", "jusqu'à quand", 
    "jusqu'où", "depuis quand", "depuis où", "d'où", "pour combien de temps", "à quel point", 
    "à quelle heure", "à quel endroit", "dans quel cas", "dans quelle mesure", "en quel sens", 
    "en quelle année", "en quel mois", "en quel jour", "à quel moment", "pour quelle raison", 
    "pour quelle cause", "à quel but", "dans quel but",
    "est-ce que", "est-ce qu'il", "est-ce qu'elle", "est-ce qu'ils", "est-ce qu'elles",
    "qu'il", "qu'elle", "qu'ils", "qu'elles",
    "quand est-ce que", "où est-ce que", "pourquoi est-ce que", "comment est-ce que", "combien est-ce que", 
    "à quel moment est-ce que", "dans quel endroit est-ce que", "pour quelle raison est-ce que", 
    "à quelle heure est-ce que", "à quel point est-ce que", "dans quelle mesure est-ce que", 
    "pour combien de temps est-ce que", "jusqu'à quand est-ce que", "depuis quand est-ce que", 
    "d'où est-ce que", "jusqu'où est-ce que", "depuis où est-ce que",
    "est-ce que je", "est-ce que tu", "est-ce qu'il", "est-ce qu'elle", "est-ce que nous", "est-ce que vous", 
    "est-ce qu'ils", "est-ce qu'elles", "est-ce qu'on", "est-ce qu'", "qu'est-ce que je", "qu'est-ce que tu", 
    "qu'est-ce qu'il", "qu'est-ce qu'elle", "qu'est-ce que nous", "qu'est-ce que vous", "qu'est-ce qu'ils", 
    "qu'est-ce qu'elles", "qu'est-ce qu'on", "qu'est-ce qu'", "quand est-ce que je", "quand est-ce que tu", 
    "quand est-ce qu'il", "quand est-ce qu'elle", "quand est-ce que nous", "quand est-ce que vous", 
    "quand est-ce qu'ils", "quand est-ce qu'elles", "quand est-ce qu'on", "quand est-ce qu'", 
    "où est-ce que je", "où est-ce que tu", "où est-ce qu'il", "où est-ce qu'elle", "où est-ce que nous", 
    "où est-ce que vous", "où est-ce qu'ils", "où est-ce qu'elles", "où est-ce qu'on", "où est-ce qu'", 
    "comment est-ce que je", "comment est-ce que tu", "comment est-ce qu'il", "comment est-ce qu'elle", 
    "comment est-ce que nous", "comment est-ce que vous", "comment est-ce qu'ils", "comment est-ce qu'elles", 
    "comment est-ce qu'on", "comment est-ce qu'", "pourquoi est-ce que je", "pourquoi est-ce que tu", 
    "pourquoi est-ce qu'il", "pourquoi est-ce qu'elle", "pourquoi est-ce que nous", "pourquoi est-ce que vous", 
    "pourquoi est-ce qu'ils", "pourquoi est-ce qu'elles", "pourquoi est-ce qu'on", "pourquoi est-ce qu'", 
    "combien est-ce que je", "combien est-ce que tu", "combien est-ce qu'il", "combien est-ce qu'elle", 
    "combien est-ce que nous", "combien est-ce que vous", "combien est-ce qu'ils", "combien est-ce qu'elles", 
    "combien est-ce qu'on", "combien est-ce qu'", "à quel point est-ce que je", "à quel point est-ce que tu", 
    "à quel point est-ce qu'il", "à quel point est-ce qu'elle", "à quel point est-ce que nous", 
    "à quel point est-ce que vous", "à quel point est-ce qu'ils", "à quel point est-ce qu'elles", 
    "à quel point est-ce qu'on", "à quel point est-ce qu'", "dans quelle mesure est-ce que je", 
    "dans quelle mesure est-ce que tu", "dans quelle mesure est-ce qu'il", "dans quelle mesure est-ce qu'elle", 
    "dans quelle mesure est-ce que nous", "dans quelle mesure est-ce que vous", "dans quelle mesure est-ce qu'ils", 
    "dans quelle mesure est-ce qu'elles", "dans quelle mesure est-ce qu'on", "dans quelle mesure est-ce qu'", 
    "à quel moment est-ce que je", "à quel moment est-ce que tu", "à quel moment est-ce qu'il", 
    "à quel moment est-ce qu'elle", "à quel moment est-ce que nous", "à quel moment est-ce que vous", 
    "à quel moment est-ce qu'ils", "à quel moment est-ce qu'elles", "à quel moment est-ce qu'on", 
    "à quel moment est-ce qu'", "pour combien de temps est-ce que je", "pour combien de temps est-ce que tu", 
    "pour combien de temps est-ce qu'il", "pour combien de temps est-ce qu'elle", "pour combien de temps est-ce que nous", 
    "pour combien de temps est-ce que vous", "pour combien de temps est-ce qu'ils", "pour combien de temps est-ce qu'elles", 
    "pour combien de temps est-ce qu'on", "pour combien de temps est-ce qu'", "jusqu'à quand est-ce que je", 
    "jusqu'à quand est-ce que tu", "jusqu'à quand est-ce qu'il", "jusqu'à quand est-ce qu'elle", 
    "jusqu'à quand est-ce que nous", "jusqu'à quand est-ce que vous", "jusqu'à quand est-ce qu'ils", 
    "jusqu'à quand est-ce qu'elles", "jusqu'à quand est-ce qu'on", "jusqu'à quand est-ce qu'", 
    "depuis quand est-ce que je", "depuis quand est-ce que tu", "depuis quand est-ce qu'il", 
    "depuis quand est-ce qu'elle", "depuis quand est-ce que nous", "depuis quand est-ce que vous", 
    "depuis quand est-ce qu'ils", "depuis quand est-ce qu'elles", "depuis quand est-ce qu'on", 
    "depuis quand est-ce qu'", "d'où est-ce que je", "d'où est-ce que tu", "d'où est-ce qu'il", 
    "d'où est-ce qu'elle", "d'où est-ce que nous", "d'où est-ce que vous", "d'où est-ce qu'ils", 
    "d'où est-ce qu'elles", "d'où est-ce qu'on", "d'où est-ce qu'", "jusqu'où est-ce que je", 
    "jusqu'où est-ce que tu", "jusqu'où est-ce qu'il", "jusqu'où est-ce qu'elle", "jusqu'où est-ce que nous", 
    "jusqu'où est-ce que vous", "jusqu'où est-ce qu'ils", "jusqu'où est-ce qu'elles", "jusqu'où est-ce qu'on", 
    "jusqu'où est-ce qu'", "depuis où est-ce que je", "depuis où est-ce que tu", "depuis où est-ce qu'il", 
    "depuis où est-ce qu'elle", "depuis où est-ce que nous", "depuis où est-ce que vous", "depuis où est-ce qu'ils", 
    "depuis où est-ce qu'elles", "depuis où est-ce qu'on", "depuis où est-ce qu'"
]
INTERROGATIVE_EXPRESSIONS = [
    "-t-", "-on", "-je", "-tu", "-il", "-elle", "-nous", "-vous", "-ils", "-elles"
]

def is_question(sentence):
    start_pattern = re.compile(rf"^({'|'.join(re.escape(word) for word in INTERROGATIVE_WORDS)})", re.IGNORECASE)
    end_pattern = re.compile(r".*\?$")
    return bool(start_pattern.match(sentence)) or bool(end_pattern.match(sentence))

def naive_datetime(dt):
    return dt.replace(tzinfo=None)

async def delete_recent_bot_messages(bot, channel, exclude_message_ids, special_message_ids=[]):
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    time_limit = now - timedelta(seconds=65)
    try:
        async for message in channel.history(limit=100):
            if message.author == bot.user and naive_datetime(message.created_at) > naive_datetime(time_limit) and message.id not in exclude_message_ids and message.id not in special_message_ids:
                try:
                    await message.delete()
                except discord.NotFound:
                    pass
                except discord.Forbidden:
                    pass
    except Exception as e:
        pass

class Question(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.threads = {}
        self.embed_messages = {}
        self.delete_messages = {}
        self.last_asked = {}

    def get_question_error(self, title, selected_tags=None):
        errors = []
        words = title.split()
        first_word_original = words[0] if words else ""
        first_word = first_word_original.lower()
        lower_title = title.lower()

        if not first_word_original[0].isupper():
            errors.append("Le premier mot de votre titre doit commencer par une majuscule.")
        
        if not is_question(title):
            errors.append("Votre titre ne commence pas par un mot interrogatif ou une expression interrogative ou ne se termine pas par un ?.")
        
        if len(lower_title) < 20:
            errors.append("Votre titre est trop court. Il doit contenir au moins 20 caractères.")
        if len(lower_title) > 100:
            errors.append("Votre titre est trop long. Il doit être de 100 caractères ou moins.")
        
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

    def create_answer_view(self, thread, message_id, bot, original_message, author):
        return AnswerView(thread, message_id, self.get_question_error, bot, original_message, author)

    async def monitor_thread(self, thread):
        await asyncio.sleep(600)
        if self.delete_messages.get(thread.id, False):
            await self.handle_timeout(thread)

    @commands.Cog.listener()
    async def on_ready(self):
        discussion_channel = self.bot.get_channel(DISCUSSION_CHANNEL_ID)
        await delete_recent_bot_messages(self.bot, discussion_channel, [])

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if thread.parent_id != QUESTION_CHANNEL_ID:
            return

        message = None
        attempts = 3
        for _ in range(attempts):
            async for msg in thread.history(limit=1):
                message = msg
                await message.pin()
                message_id = message.id
                break
            if message:
                break
            await asyncio.sleep(1)

        if message is None:
            logger.error(f"Aucun message trouvé dans le fil {thread.id} après {attempts} tentatives")
            return

        self.threads[thread.id] = message.author.id
        self.delete_messages[thread.id] = True

        error_types = self.get_question_error(thread.name, thread.applied_tags)
        
        if not error_types:
            success_embed = send_success_message(thread.name)
            view = self.create_answer_view(thread, message_id, self.bot, None, message.author)
            view.remove_tag_select()
            embed_message = await thread.send(content=message.author.mention if message.author else "", embed=success_embed, view=view)
            self.embed_messages[thread.id] = embed_message.id
            self.delete_messages[thread.id] = False
        else:
            role = discord.utils.get(thread.guild.roles, id=QUESTION_ROLE_ID)
            if role and message.author and not message.author.bot:
                await message.author.add_roles(role)

            error_embed = send_error_message(thread.name, error_types)
            view = self.create_answer_view(thread, message_id, self.bot, None, message.author)
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
                        await message.author.send(f"Veuillez cliquer sur le bouton Modifier le titre de votre fil pour corriger le titre : {thread.jump_url}")

        if message.channel.id == DISCUSSION_CHANNEL_ID:
            if self.user_has_stopped(message.author.id):
                return
            
            content = message.content.strip()
            if (is_question(content) and len(content) >= 10):
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
            view = self.create_answer_view(after, message_id, self.bot, None, after.owner)
            await embed_message.edit(content=after.owner.mention, embed=error_embed, view=view)
            self.delete_messages[after.id] = True

            role = discord.utils.get(after.guild.roles, id=QUESTION_ROLE_ID)
            if role and not after.owner.bot:
                await after.owner.add_roles(role)
        else:
            success_embed = send_success_message(after.name)
            view = self.create_answer_view(after, message_id, self.bot, None, after.owner)
            view.remove_tag_select()
            await embed_message.edit(content=after.owner.mention, embed=success_embed, view=view)
            self.delete_messages[after.id] = False

            role = discord.utils.get(after.guild.roles, id=QUESTION_ROLE_ID)
            if role and not after.owner.bot:
                await after.owner.remove_roles(role)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        for view in self.bot.persistent_views:
            if isinstance(view, QuestionDetectedView) and view.confirmation_message and view.confirmation_message.id == message.id:
                try:
                    await view.message.delete()
                except discord.NotFound:
                    pass
                except discord.Forbidden:
                    pass
                break

async def setup(bot):
    await bot.add_cog(Question(bot))

class StopConfirmView(discord.ui.View):
    def __init__(self, message, bot, question_view):
        super().__init__(timeout=60)
        self.message = message
        self.bot = bot
        self.question_view = question_view
        self.confirmation_message = None
        self.confirmed_or_cancelled = False

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

    @discord.ui.button(label="Confirmer", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.message.author:
            await interaction.response.send_message("Seul l'auteur de la question peut effectuer cette action.", ephemeral=True)
            return

        await self.record_stop_user(interaction.user.id)
        special_message = await self.message.channel.send(f"{self.message.author.mention} Vous ne recevrez plus de notifications pour les questions détectées.")
        self.confirmed_or_cancelled = True
        self.disable_buttons()
        await delete_recent_bot_messages(self.bot, self.message.channel, [self.confirmation_message.id], special_message_ids=[special_message.id])
        if self.confirmation_message:
            try:
                await self.confirmation_message.delete()
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
            if interaction.user.id in stop_users:
                stop_users.remove(interaction.user.id)
                with open(stop_file, "w") as f:
                    json.dump(stop_users, f)
        await interaction.response.send_message("Action annulée. Vous continuerez à recevoir des notifications pour les questions détectées.", ephemeral=True)
        self.confirmed_or_cancelled = True
        self.disable_buttons()
        await delete_recent_bot_messages(self.bot, self.message.channel, [self.confirmation_message.id])
        if self.confirmation_message:
            try:
                await self.confirmation_message.delete()
            except discord.NotFound:
                pass

    async def on_timeout(self):
        if not self.confirmed_or_cancelled:
            timeout_message = await self.message.channel.send(f"{self.message.author.mention} Temps écoulé. Votre question n'a pas été déplacée.")
            await delete_recent_bot_messages(self.bot, self.message.channel, [timeout_message.id])
        else:
            await delete_recent_bot_messages(self.bot, self.message.channel, [])
        self.stop()

    def disable_buttons(self):
        for item in self.children:
            item.disabled = True
        self.stop()

class QuestionDetectedView(discord.ui.View):
    def __init__(self, message, bot):
        super().__init__(timeout=60)
        self.message = message
        self.bot = bot
        self.confirmation_message = None
        self.message_id = message.id
        self.confirmation_view = StopConfirmView(self.message, self.bot, self)
        self.stop_requested = False
        self.confirmed_or_cancelled = False

    @discord.ui.button(label="Oui", style=discord.ButtonStyle.green)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
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
            view = self.bot.get_cog('Question').create_answer_view(new_thread, thread_message.id, self.bot, self.message, self.message.author)

            success_embed = discord.Embed(title="Succès", description="Le message a été déplacé avec succès.", color=discord.Color.green())
            await webhook.edit_message(thread_message.id, content=self.message.author.mention, embed=success_embed, view=view, thread=new_thread)

        except discord.HTTPException as e:
            traceback.print_exc()
            if e.code == 50006:
                pass
            error_embed = discord.Embed(title="Erreur", description=f"Il y a eu une erreur : {e}", color=discord.Color.red())
            await question_channel.send(content=self.message.author.mention, embed=error_embed)
            await interaction.response.send_message("Il y a eu une erreur lors de la création du fil.", ephemeral=True)
            return

        if new_thread:
            self.bot.get_cog('Question').threads[new_thread.id] = self.message.author.id

            await delete_recent_bot_messages(self.bot, self.message.channel, [self.confirmation_message.id])

            special_message = await self.bot.get_channel(DISCUSSION_CHANNEL_ID).send(f"{self.message.author.mention} Votre question a été déplacée dans le fil <#{new_thread.id}>.")

            async for msg in new_thread.history(limit=10):
                if msg.author == self.bot.user and not msg.is_system() and msg.id != thread_message.id:
                    await msg.delete()

            error_types = self.bot.get_cog('Question').get_question_error(new_thread.name, new_thread.applied_tags)
            if error_types:
                error_embed = send_error_message(new_thread.name, error_types)
                view = self.bot.get_cog('Question').create_answer_view(new_thread, thread_message.id, self.bot, self.message, self.message.author)
                await webhook.edit_message(thread_message.id, content=self.message.author.mention, embed=error_embed, view=view, thread=new_thread)
            else:
                success_embed = send_success_message(new_thread.name)
                await webhook.edit_message(thread_message.id, content=self.message.author.mention, embed=success_embed, thread=new_thread)
            
            try:
                await self.message.delete()
            except discord.errors.NotFound:
                pass
            
            self.confirmed_or_cancelled = True
        else:
            await interaction.response.send_message("Il y a eu une erreur lors de la création du fil.", ephemeral=True)

    @discord.ui.button(label="Non", style=discord.ButtonStyle.red)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.message.author:
            await interaction.response.send_message(f"Seul l'auteur de la question peut effectuer cette action.", ephemeral=True)
            return

        try:
            if self.confirmation_message:
                await self.confirmation_message.delete()
        except discord.errors.NotFound:
            pass

        try:
            if interaction.message:
                await interaction.message.delete()
            else:
                pass
        except discord.errors.NotFound:
            pass

        await self.message.channel.send(f"{self.message.author.mention} Votre question n'a pas été déplacée.")
        self.confirmed_or_cancelled = True
        self.stop()

    @discord.ui.button(label="STOP", style=discord.ButtonStyle.grey)
    async def stop_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.message.author:
            await interaction.response.send_message("Seul l'auteur de la question peut effectuer cette action.", ephemeral=True)
            return
        self.stop_requested = True
        await self.show_confirmation(interaction)

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
        await interaction.response.send_message(embed=confirm_embed, view=confirm_view, ephemeral=False)
        self.confirmation_message = await interaction.original_response()
        confirm_view.confirmation_message = self.confirmation_message
        self.confirmation_view = confirm_view

    async def on_timeout(self):
        if self.stop_requested:
            return

        try:
            if self.confirmation_message:
                await self.confirmation_message.delete()
        except discord.errors.NotFound:
            pass

        if not self.confirmed_or_cancelled:
            timeout_message = await self.message.channel.send(f"{self.message.author.mention} Temps écoulé. Votre question n'a pas été déplacée.")
            await delete_recent_bot_messages(self.bot, self.message.channel, [timeout_message.id])
        else:
            await delete_recent_bot_messages(self.bot, self.message.channel, [])
        self.stop()

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
            view = self.bot.get_cog('Question').create_answer_view(self.thread, self.message_id, self.bot, self.original_message, self.author)
            view.remove_tag_select()
            
            if message.author.id == self.bot.user.id:
                await message.edit(content=self.author.mention, embed=success_embed, view=view)
            else:
                await self.webhook.edit_message(self.message_id, content=self.author.mention, embed=success_embed, view=view, thread=self.thread)
            await interaction.response.send_message("Le titre du fil a été mis à jour.", ephemeral=True)
            self.bot.get_cog('Question').delete_messages[self.thread.id] = False

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
    def __init__(self, thread, message_id, get_question_error, bot, original_message, author):
        super().__init__(timeout=None)
        self.thread = thread
        self.message_id = message_id
        self.get_question_error = get_question_error
        self.bot = bot
        self.original_message = original_message
        self.author = author
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
        modal = TitleModal(self.thread, self.message_id, self.get_question_error, self.bot, self.original_message, self.author, await get_webhook(self.thread.parent), self.selected_tags)
        await interaction.response.send_modal(modal)

async def get_webhook(channel):
    webhooks = await channel.webhooks()
    webhook = discord.utils.find(lambda wh: wh.user == channel.guild.me, webhooks)
    if webhook is None:
        webhook = await channel.create_webhook(name="MessageForwarder", reason="Pour reposter les messages")
    return webhook

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

async def setup(bot):
    await bot.add_cog(Question(bot))