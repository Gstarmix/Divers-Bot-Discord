import asyncio
from discord.ext import commands
import discord
from datetime import datetime
from constants import *

class Inscription(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_registrations = {}
        self.validated_registrations = {}
        self.original_messages = {}
        self.threads = {}
        self.threads_created = set()
        self.users_warned = set()
        self.user_message_times = {}

    async def ask_with_timeout(self, thread, user_id, message_content, check, original_message):
        while True:
            message = await thread.send(f"<@{user_id}> {message_content}")
            try:
                response = await self.bot.wait_for('message', check=check, timeout=600)
                if response.attachments and any(att.content_type.startswith('image/') for att in response.attachments):
                    return response
                else:
                    message_content = "Je n'ai pas compris votre réponse. Veuillez envoyer une capture d'écran."
                    continue
            except asyncio.TimeoutError:
                user = thread.guild.get_member(user_id)
                if user:
                    await user.send("Votre fil a été supprimé car vous avez mis plus de 10 minutes à répondre au questionnaire.")
                invalidation_channel = self.bot.get_channel(INSCRIPTION_INVALIDATION_CHANNEL_ID)
                await invalidation_channel.send(f"{self.bot.get_user(user_id).mention} a mis plus de 10 minutes à répondre donc son inscription est annulé.")
                if thread.guild.get_channel(thread.id) is not None:
                    await thread.delete()
                await original_message.delete()
                return None

    @commands.Cog.listener()
    async def on_message(self, message):
        thread = message.channel
        now = datetime.now()
        if isinstance(thread, discord.Thread) and thread.id in self.threads and self.threads[thread.id] and message.author.id != self.threads[thread.id] and not message.author.bot:
            await message.delete()
            await message.author.send("Vous n'êtes pas autorisé à écrire dans ce fil.")
            return
        if message.channel.id != INSCRIPTION_CHANNEL_ID or message.author.bot:
            return
        if message.id in self.threads_created:
            return
        if message.author.id in self.user_message_times and (now - self.user_message_times[message.author.id]).total_seconds() < 300:
            await message.author.send("Vous ne pouvez poser une nouvelle question que 5 minutes après votre précédente question.")
            await message.delete()
            return
        self.user_message_times[message.author.id] = now
        try:
            thread = await message.create_thread(name=f"Inscription de {message.author.name}")
            self.threads[thread.id] = message.author.id
            self.threads_created.add(message.id)
            message_content = "Merci de votre intérêt pour le concours ! Pourriez-vous partager une capture d'écran de votre personnage in-game ?"
        except:
            return
        try:
            def check(m):
                return m.channel == thread and m.author == message.author
            screenshot_response = await self.ask_with_timeout(thread, message.author.id, message_content, check, message)
            if not screenshot_response or not screenshot_response.attachments:
                return
            personnage_screenshot = screenshot_response.attachments[0].url
            await thread.send(f"<@{message.author.id}> Merci d'avoir partagé la capture d'écran ! Votre inscription au concours est en cours de vérification.")
            self.pending_registrations[message.author.id] = personnage_screenshot
            self.original_messages[message.id] = message.author.id
        except:
            await thread.send(f"<@{message.author.id}> Une erreur est survenue.")

    @commands.command()
    async def oui(self, ctx, user: discord.Member):
        if user.id in self.pending_registrations:
            validation_channel = self.bot.get_channel(INSCRIPTION_VALIDATION_CHANNEL_ID)
            await validation_channel.send(f"L'inscription de {user.mention} a été validée.")
            self.validated_registrations[user.id] = self.pending_registrations[user.id]
            del self.pending_registrations[user.id]
            role = discord.utils.get(ctx.guild.roles, id=INSCRIPTION_ROLE_ID)
            await user.add_roles(role)

    @commands.command()
    async def non(self, ctx, user: discord.Member, *, reason=None):
        if user.id in self.pending_registrations or user.id in self.validated_registrations:
            invalidation_channel = self.bot.get_channel(INSCRIPTION_INVALIDATION_CHANNEL_ID)
            if reason:
                await invalidation_channel.send(f"L'inscription de {user.mention} a été invalidée pour la raison suivante : {reason}")
            else:
                await invalidation_channel.send(f"L'inscription de {user.mention} a été invalidée.")
            if user.id in self.pending_registrations:
                del self.pending_registrations[user.id]
            if user.id in self.validated_registrations:
                del self.validated_registrations[user.id]
            role = discord.utils.get(ctx.guild.roles, id=INSCRIPTION_ROLE_ID)
            if role in user.roles:
                await user.remove_roles(role)

    @commands.command()
    async def check(self, ctx, user: discord.Member):
        if user.id in self.pending_registrations:
            await ctx.send(f"{user.mention} est en attente de validation.")
        elif user.id in self.validated_registrations:
            await ctx.send(f"{user.mention} a été validé.")
        else:
            await ctx.send(f"{user.mention} n'est pas inscrit.")

    @commands.command()
    async def close(self, ctx, thread: discord.Thread):
        if thread.id in self.threads:
            del self.threads[thread.id]
        await thread.delete()

    @commands.Cog.listener()
    async def on_thread_join(self, thread):
        if thread.id in self.threads and not self.threads[thread.id]:
            self.threads[thread.id] = thread.owner.id

    @commands.Cog.listener()
    async def on_thread_remove(self, thread):
        if thread.id in self.threads:
            del self.threads[thread.id]

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.id in self.pending_registrations:
            del self.pending_registrations[member.id]
        if member.id in self.validated_registrations:
            del self.validated_registrations[member.id]
        if member.id in self.user_message_times:
            del self.user_message_times[member.id]

async def setup(bot):
    await bot.add_cog(Inscription(bot))
