import asyncio
from discord.ext import commands
import discord
from constants import INSCRIPTION_BOT_CHANNEL_ID, ADMIN_ROLE_ID_GSTAR, INSCRIPTION_BOT_VALIDATION_CHANNEL_ID, INSCRIPTION_BOT_INVALIDATION_CHANNEL_ID

class Inscription(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_registrations = {}
        self.validated_registrations = {}
        self.original_messages = {}
        self.threads = {}
        self.threads_created = set()
        self.users_warned = set()

    async def ask_with_timeout(self, thread, message_content, check):
        while True:
            # Check if the bot has the necessary permissions
            permissions = thread.permissions_for(thread.guild.me)
            if not permissions.send_messages:
                print("The bot does not have the 'send_messages' permission.")
                return None
            if not permissions.mention_everyone:
                print("The bot does not have the 'mention_everyone' permission.")
                return None

            message = await thread.send(f"<@{thread.owner.id}> {message_content}")
            try:
                response = await self.bot.wait_for('message', check=check, timeout=600)
                if response.attachments and any(att.content_type.startswith('image/') for att in response.attachments):
                    return response
                else:
                    message_content = "Je n'ai pas compris votre réponse. Veuillez envoyer une capture d'écran."
                    continue
            except asyncio.TimeoutError:
                await thread.owner.send("Votre fil a été supprimé car vous avez mis plus de 10 minutes à répondre au questionnaire.")
                await thread.delete()
                return None

    @commands.Cog.listener()
    async def on_message(self, message):
        thread = message.channel
        if isinstance(thread, discord.Thread) and thread.id in self.threads and self.threads[thread.id] and message.author.id != self.threads[thread.id] and not any(role.id == ADMIN_ROLE_ID_GSTAR for role in message.author.roles) and not message.author.bot:
            await message.delete()
            await message.author.send("Vous n'êtes pas autorisé à écrire dans ce fil.")
            return
        if message.channel.id != INSCRIPTION_BOT_CHANNEL_ID or message.author.bot:
            return
        if message.id in self.threads_created:
            return
        try:
            thread = await message.create_thread(name=f"Inscription de {message.author.name}")
            self.threads[thread.id] = message.author.id
            self.threads_created.add(message.id)
            message_content = "Merci de votre intérêt pour le concours ! Pourriez-vous fournir une capture d'écran de votre personnage in-game ? Assurez-vous que votre personnage soit au minimum de niveau héroïque +30 et que le pseudo, le niveau, la date et l'heure soient bien visibles sur la capture d'écran."
        except Exception as e:
            return
        try:
            def check(m):
                return m.channel == thread and m.author == message.author
            screenshot_response = await self.ask_with_timeout(thread, message_content, check)
            if not screenshot_response or not screenshot_response.attachments:
                message_content = "Désolé, je n'ai pas compris votre message. Je m'attends à une capture d'écran."
                return
            personnage_screenshot = screenshot_response.attachments[0].url
            message_content = "Merci pour la capture d'écran ! Ensuite, avez-vous atteint l'étape 17 du tutoriel ? Si oui, pourriez-vous fournir une capture d'écran de la page 17 du tutoriel ?"
            tutorial_response = await self.ask_with_timeout(thread, message_content, check)
            if not tutorial_response or not tutorial_response.attachments:
                message_content = "Désolé, je n'ai pas compris votre message. Je m'attends à une capture d'écran."
                return
            tutorial_screenshot = tutorial_response.attachments[0].url
            await thread.send(f"<@{thread.owner.id}> Votre inscription au concours a été confirmée. Merci ! Un modérateur va maintenant valider votre inscription.")
            self.pending_registrations[message.author.id] = (personnage_screenshot, tutorial_screenshot)
            self.original_messages[message.id] = message.author.id
        except Exception as e:
            await thread.send(f"<@{thread.owner.id}> Une erreur est survenue : {e}")

    @commands.command()
    async def valide(self, ctx, user: discord.Member):
        if user.id in self.pending_registrations:
            validation_channel = self.bot.get_channel(INSCRIPTION_BOT_VALIDATION_CHANNEL_ID)
            await validation_channel.send(f":white_check_mark: L'inscription de <@{user.id}> a été validée.")
            self.validated_registrations[user.id] = self.pending_registrations[user.id]
            del self.pending_registrations[user.id]
            role = discord.utils.get(ctx.guild.roles, id=ADMIN_ROLE_ID_GSTAR)
            await user.add_roles(role)

    @commands.command()
    async def invalide(self, ctx, user: discord.Member, *, reason=None):
        if user.id in self.pending_registrations or user.id in self.validated_registrations:
            invalidation_channel = self.bot.get_channel(INSCRIPTION_BOT_INVALIDATION_CHANNEL_ID)
            if reason:
                await invalidation_channel.send(f"<:tag_non:1034266050872737923> L'inscription de <@{user.id}> a été invalidée pour la raison suivante : {reason}")
            else:
                await invalidation_channel.send(f"<:tag_non:1034266050872737923> L'inscription de <@{user.id}> a été invalidée.")
            role = discord.utils.get(ctx.guild.roles, id=ADMIN_ROLE_ID_GSTAR)
            if role in user.roles:
                await user.remove_roles(role)
            if user.id in self.pending_registrations:
                del self.pending_registrations[user.id]
            if user.id in self.validated_registrations:
                del self.validated_registrations[user.id]

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload):
        if payload.message_id in self.original_messages:
            user_id = self.original_messages[payload.message_id]
            if user_id in self.pending_registrations or user_id in self.validated_registrations:
                invalidation_channel = self.bot.get_channel(INSCRIPTION_BOT_INVALIDATION_CHANNEL_ID)
                await invalidation_channel.send(f"<:tag_non:1034266050872737923> <@{user_id}> a supprimé son message donc son inscription est annulé.")
                member = discord.utils.get(self.bot.get_all_members(), id=user_id)
                role = discord.utils.get(member.guild.roles, id=ADMIN_ROLE_ID_GSTAR)
                if role in member.roles:
                    await member.remove_roles(role)
                if user_id in self.pending_registrations:
                    del self.pending_registrations[user_id]
                if user_id in self.validated_registrations:
                    del self.validated_registrations[user_id]
                del self.original_messages[payload.message_id]
        elif payload.channel_id in self.threads:
            user_id = self.threads[payload.channel_id]
            if user_id in self.pending_registrations or user_id in self.validated_registrations:
                invalidation_channel = self.bot.get_channel(INSCRIPTION_BOT_INVALIDATION_CHANNEL_ID)
                await invalidation_channel.send(f"<:tag_non:1034266050872737923> <@{user_id}> a supprimé son fil donc son inscription est annulé.")
                member = discord.utils.get(self.bot.get_all_members(), id=user_id)
                role = discord.utils.get(member.guild.roles, id=ADMIN_ROLE_ID_GSTAR)
                if role in member.roles:
                    await member.remove_roles(role)
                if user_id in self.pending_registrations:
                    del self.pending_registrations[user_id]
                if user_id in self.validated_registrations:
                    del self.validated_registrations[user_id]
                del self.threads[payload.channel_id]

async def setup(bot):
    await bot.add_cog(Inscription(bot))
