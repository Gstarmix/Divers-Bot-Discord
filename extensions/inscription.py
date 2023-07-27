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
                await invalidation_channel.send(f"<:tag_non:1034266050872737923> {self.bot.get_user(user_id).mention} a mis plus de 10 minutes à répondre donc son inscription est annulé.")
                # Check if the thread still exists before trying to delete it
                if thread.guild.get_channel(thread.id) is not None:
                    await thread.delete()
                await original_message.delete()
                return None
            except discord.errors.NotFound:
                print("Le canal n'existe plus.")
                return None
            except Exception as e:
                print(f"Une erreur inattendue est survenue : {e}")
                return None

    @commands.Cog.listener()
    async def on_message(self, message):
        thread = message.channel
        now = datetime.now()
        if isinstance(thread, discord.Thread) and thread.id in self.threads and self.threads[thread.id] and message.author.id != self.threads[thread.id] and not any(role.id == CHEF_SINGE_ROLE_ID for role in message.author.roles) and not message.author.bot:
            try:
                await message.delete()
            except discord.Forbidden:
                print("Bot does not have the 'Manage Messages' permission.")
            except discord.NotFound:
                print("The message was not found.")
            except discord.HTTPException as e:
                print(f"An HTTP exception occurred: {e}")
            await message.author.send("Vous n'êtes pas autorisé à écrire dans ce fil.")
            return
        if message.channel.id != INSCRIPTION_CHANNEL_ID or message.author.bot:
            return
        if message.id in self.threads_created:
            return
        if message.author.id in self.user_message_times and (now - self.user_message_times[message.author.id]).total_seconds() < 300:
            await message.author.send("Vous ne pouvez poser une nouvelle question que 5 minutes après votre précédente question. Veuillez modifier votre dernier message si nécessaire.")
            await message.delete()
            return
        self.user_message_times[message.author.id] = now
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
            screenshot_response = await self.ask_with_timeout(thread, message.author.id, message_content, check, message)
            if not screenshot_response or not screenshot_response.attachments:
                message_content = "Désolé, je n'ai pas compris votre message. Je m'attends à une capture d'écran."
                return
            personnage_screenshot = screenshot_response.attachments[0].url
            message_content = "Merci d'avoir fourni la capture d'écran ! Passons à la suite, avez-vous atteint l'étape 17 du tutoriel ? Si c'est le cas, pourriez-vous partager une capture d'écran de la page 17 du tutoriel ? Dans le cas contraire, veuillez effectuer le tutoriel jusqu'à la page 17 (il n'est pas nécessaire de le terminer) en tapant `$tuto` dans le salon <#{MUDAE_TUTORIAL_CHANNEL_ID}>."
            tutorial_response = await self.ask_with_timeout(thread, message.author.id, message_content, check, message)
            if not tutorial_response or not tutorial_response.attachments:
                message_content = "Désolé, je n'ai pas compris votre message. Je m'attends à une capture d'écran."
                return
            tutorial_screenshot = tutorial_response.attachments[0].url
            await thread.send(f"<@{message.author.id}> Votre inscription au concours a été confirmée. Merci ! <@200750717437345792> va maintenant valider votre inscription.")
            self.pending_registrations[message.author.id] = (personnage_screenshot, tutorial_screenshot)
            self.original_messages[message.id] = message.author.id
        except Exception as e:
            await thread.send(f"<@{message.author.id}> Une erreur est survenue : {e}")

    @commands.command()
    async def oui(self, ctx, user: discord.Member):
        if user.id in self.pending_registrations:
            validation_channel = self.bot.get_channel(INSCRIPTION_VALIDATION_CHANNEL_ID)
            await validation_channel.send(f":white_check_mark: L'inscription de {user.mention} a été validée.")
            self.validated_registrations[user.id] = self.pending_registrations[user.id]
            del self.pending_registrations[user.id]
            role = discord.utils.get(ctx.guild.roles, id=INSCRIPTION_ROLE_ID)
            await user.add_roles(role)

    @commands.command()
    async def non(self, ctx, user: discord.Member, *, reason=None):
        if user.id in self.pending_registrations or user.id in self.validated_registrations:
            invalidation_channel = self.bot.get_channel(INSCRIPTION_INVALIDATION_CHANNEL_ID)
            if reason:
                await invalidation_channel.send(f"<:tag_non:1034266050872737923> L'inscription de {user.mention} a été invalidée pour la raison suivante : {reason}")
            else:
                await invalidation_channel.send(f"<:tag_non:1034266050872737923> L'inscription de {user.mention} a été invalidée.")
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
    async def on_thread_delete(self, thread):
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

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        print(self.original_messages)
        if isinstance(message.channel, discord.Thread) and message.channel.id in self.threads:
            user_id = self.threads[message.channel.id]
            user = message.guild.get_member(user_id)

            if message.author.id != user_id and not any(role.id == CHEF_SINGE_ROLE_ID for role in message.author.roles) and not message.author.bot:
                return
            print("hello gaylord")

            original_message_ids = [k for k, v in self.original_messages.items() if v == user_id]
            if original_message_ids: 
                original_message_id = original_message_ids[0]
                original_channel = self.bot.get_channel(INSCRIPTION_CHANNEL_ID)
                try: 
                    original_message = original_channel.get_partial_message(original_message_id)
                    print("hello choupi")
                    await original_message.delete()
                except discord.NotFound:
                    print(f"Original message with ID {original_message_id} not found.")
                except discord.Forbidden:
                    print(f"Bot does not have permissions to delete the original message with ID {original_message_id}.")
                except discord.HTTPException as e:
                    print(f"An HTTP exception occurred while trying to delete the original message with ID {original_message_id}: {e}")


            await message.channel.delete()

            role = user.get_role(INSCRIPTION_ROLE_ID)
            if role:
                await user.remove_roles(role)

            await user.send("Votre inscription a été annulée car un message dans votre fil de discussion a été supprimé.")

            invalidation_channel = self.bot.get_channel(INSCRIPTION_INVALIDATION_CHANNEL_ID)
            await invalidation_channel.send(f"L'inscription de {user.mention} a été annulée car un message dans son fil de discussion a été supprimé.")

async def setup(bot):
    await bot.add_cog(Inscription(bot))
