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
    embed = discord.Embed(
        title="Titre validé",
        description="Le fil est maintenant ouvert à tous pour la discussion.",
        color=discord.Color.green()
    )
    return embed

class TitleModal(discord.ui.Modal):
    def __init__(self, channel, message_id, get_question_error, bot, original_message):
        super().__init__(title="Modifier le titre du fil")
        self.channel = channel
        self.message_id = message_id
        self.get_question_error = get_question_error
        self.bot = bot
        self.original_message = original_message
        self.add_item(discord.ui.TextInput(label="Nouveau titre", style=discord.TextStyle.short, placeholder="Entrez le nouveau titre du fil...", custom_id="new_title", max_length=100))

    async def on_submit(self, interaction: discord.Interaction):
        new_title = self.children[0].value
        error_types = self.get_question_error(new_title)
        try:
            message = await self.channel.fetch_message(self.message_id)
        except discord.NotFound:
            print(f"Message ID: {self.message_id} in Channel ID: {self.channel.id} not found.")
            await interaction.response.send_message("Le message original est introuvable.", ephemeral=True)
            return

        if error_types:
            error_embed = send_error_message(new_title, error_types)
            await message.edit(embed=error_embed)
            await interaction.response.send_message("Le titre contient encore des erreurs.", ephemeral=True)
        else:
            success_embed = send_success_message(new_title)
            await message.edit(content=self.channel.guild.owner.mention, embed=success_embed)
            await interaction.response.send_message("Le titre du fil a été mis à jour.", ephemeral=True)
            self.bot.get_cog('Question').delete_messages[self.channel.id] = False

            question_channel = self.bot.get_channel(QUESTION_CHANNEL_ID)
            new_thread = await question_channel.create_thread(
                name=new_title,
                auto_archive_duration=1440
            )

            await new_thread.send(content=self.original_message.content)

            await self.original_message.delete()

            await self.channel.send(content=f"Votre question a été déplacée dans le fil '{new_thread.id}'.")

class AnswerView(discord.ui.View):
    def __init__(self, channel, message_id, get_question_error, bot, original_message):
        super().__init__(timeout=None)
        self.channel = channel
        self.message_id = message_id
        self.get_question_error = get_question_error
        self.bot = bot
        self.original_message = original_message

    @discord.ui.button(label="Modifier le titre", style=discord.ButtonStyle.grey)
    async def answer(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.original_message.author:
            await interaction.response.send_message("Seul l'auteur du fil peut modifier le titre.", ephemeral=True)
            return
        modal = TitleModal(self.channel, self.message_id, self.get_question_error, self.bot, self.original_message)
        await interaction.response.send_modal(modal)

class Question(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channels = {}
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

    async def handle_timeout(self, channel):
        await channel.guild.owner.send("Votre fil a été supprimé car vous avez mis plus de 10 minutes à répondre au questionnaire.")
        await channel.delete()

    async def monitor_channel(self, channel):
        await asyncio.sleep(600)
        if self.delete_messages.get(channel.id, False):
            await self.handle_timeout(channel)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if isinstance(message.channel, discord.TextChannel) and message.channel.id == QUESTION_CHANNEL_ID:
            if self.delete_messages.get(message.channel.id, False):
                if message.author.id != self.channels.get(message.channel.id):
                    await message.delete()
                    await message.author.send(f"Vous ne pouvez pas écrire dans ce canal tant que le titre n'est pas corrigé : {message.channel.jump_url}")
                elif message.author.id == self.channels.get(message.channel.id):
                    await message.delete()
                    await message.author.send(f"Vous ne pouvez pas écrire dans ce canal tant que le titre n'est pas corrigé : {message.channel.jump_url}")

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
    async def on_channel_update(self, before, after):
        if before.id != QUESTION_CHANNEL_ID or before.name == after.name:
            return3

        error_types = self.get_question_error(after.name)
        try:
            message = await after.fetch_message(self.channels.get(after.id))
        except discord.NotFound:
            return

        if error_types:
            error_embed = send_error_message(after.name, error_types)
            view = AnswerView(after, self.channels.get(after.id), self.get_question_error, self.bot, None)
            await message.edit(content=after.guild.owner.mention if after.guild.owner else "", embed=error_embed, view=view)
            self.delete_messages[after.id] = True
        else:
            success_embed = send_success_message(after.name)
            await message.edit(content=after.guild.owner.mention if after.guild.owner else "", embed=success_embed)
            self.delete_messages[after.id] = False

class ConfirmView(discord.ui.View):
    def __init__(self, message, bot):
        super().__init__(timeout=None)
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
        new_thread = await question_channel.create_thread(
            name=self.message.content[:50],
            auto_archive_duration=1440
        )

        await new_thread.send(content=self.message.content)

        await self.message.delete()

        await interaction.response.send_message(f"Votre question a été déplacée dans le fil {new_thread.id}.", ephemeral=True)

        error_types = self.bot.get_cog('Question').get_question_error(new_thread.name)
        if error_types:
            error_embed = send_error_message(new_thread.name, error_types)
            await new_thread.send(embed=error_embed)
        else:
            success_embed = send_success_message(new_thread.name)
            await new_thread.send(embed=success_embed)

    @discord.ui.button(label="Non", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.message.author:
            await interaction.response.send_message("Seul l'auteur de la question peut effectuer cette action.", ephemeral=True)
            return
        await self.confirmation_message.delete()
        await interaction.response.send_message("Votre question n'a pas été déplacée.", ephemeral=True)
        self.stop()

async def setup(bot):
    await bot.add_cog(Question(bot))
