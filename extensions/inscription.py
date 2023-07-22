from nextcord.ext import commands
import nextcord
from constants import (
    INSCRIPTION_BOT_CHANNEL_ID,
    INSCRIPTION_BOT_ROLE_ID,
    INSCRIPTION_BOT_VALIDATION_CHANNEL_ID,
    INSCRIPTION_BOT_INVALIDATION_CHANNEL_ID,
)

class Inscription(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.pending_registrations = {}
        self.validated_registrations = {}
        self.original_messages = {}
        self.threads = {}
        self.threads_created = set()

    @commands.Cog.listener()
    async def on_message(self, message):
        print(f"Message reçu de {message.author.name} dans le canal {message.channel.id}")
        if message.channel.id == INSCRIPTION_BOT_CHANNEL_ID and not message.author.bot:
            if message.id in self.threads_created:
                print(f"Un fil a déjà été créé pour le message de {message.author.name}. Ignorer le message.")
                return
            try:
                print("Création du fil...")
                thread = await message.create_thread(name=f"Inscription de {message.author.name}")
                self.threads[thread.id] = message.author.id
                self.threads_created.add(message.id)
            except Exception as e:
                print(f"Erreur lors de la création du fil : {e}")
                return

            try:
                bot_message = await thread.send("Merci de votre intérêt pour le concours ! Pourriez-vous fournir une capture d'écran de votre personnage in-game ? Assurez-vous que votre personnage soit au minimum de niveau héroïque +30 et que le pseudo, le niveau, la date et l'heure soient bien visibles sur la capture d'écran.")
                def check(m):
                    return m.channel == thread and m.author == message.author

                while True:
                    screenshot_response = await self.bot.wait_for('message', check=check)
                    if screenshot_response.attachments:
                        break
                    else:
                        await thread.send("Vous n'avez pas fourni de capture d'écran de votre personnage. Veuillez réessayer.")
                personnage_screenshot = screenshot_response.attachments[0].url

                await thread.send("Merci pour la capture d'écran ! Ensuite, avez-vous atteint l'étape 17 du tutoriel ? Si oui, pourriez-vous fournir une capture d'écran de la page 17 du tutoriel ?")
                while True:
                    tutorial_response = await self.bot.wait_for('message', check=check)
                    if tutorial_response.attachments:
                        break
                    else:
                        await thread.send("Vous n'avez pas fourni de capture d'écran pour l'étape 17 du tutoriel. Veuillez réessayer.")
                tutorial_screenshot = tutorial_response.attachments[0].url

                await thread.send("Votre inscription au concours a été confirmée. Merci ! Un modérateur va maintenant valider votre inscription.")
                self.pending_registrations[message.author.id] = (personnage_screenshot, tutorial_screenshot)
                self.original_messages[message.id] = message.author.id
            except Exception as e:
                await thread.send(f"Une erreur est survenue : {e}")
            except Exception as e:
                print(f"Erreur lors de la création du fil : {e}")

    @commands.Cog.listener()
    async def on_thread_join(self, thread):
        def check(m):
            return m.channel == thread and m.author != self.bot.user
        while True:
            try:
                message = await self.bot.wait_for('message', check=check)
                if message.author.id != self.threads[thread.id] and not any(role.id == INSCRIPTION_BOT_ROLE_ID for role in message.author.roles):
                    await message.author.send("Vous n'êtes pas autorisé à écrire dans ce fil.")
                    await message.delete()
            except Exception as e:
                print(f"Une erreur est survenue lors de la suppression d'un message non autorisé : {e}")

    @commands.command()
    async def valide(self, ctx, user: nextcord.Member):
        if user.id in self.pending_registrations:
            validation_channel = self.bot.get_channel(INSCRIPTION_BOT_VALIDATION_CHANNEL_ID)
            await validation_channel.send(f":white_check_mark: L'inscription de {user.mention} a été validée.")
            self.validated_registrations[user.id] = self.pending_registrations[user.id]
            del self.pending_registrations[user.id]
            role = nextcord.utils.get(ctx.guild.roles, id=INSCRIPTION_BOT_ROLE_ID)
            await user.add_roles(role)

    @commands.command()
    async def invalide(self, ctx, user: nextcord.Member, *, reason=None):
        if user.id in self.pending_registrations or user.id in self.validated_registrations:
            invalidation_channel = self.bot.get_channel(INSCRIPTION_BOT_INVALIDATION_CHANNEL_ID)
            if reason:
                await invalidation_channel.send(f"<:tag_non:1034266050872737923> L'inscription de {user.mention} a été invalidée pour la raison suivante : {reason}")
            else:
                await invalidation_channel.send(f"<:tag_non:1034266050872737923> L'inscription de {user.mention} a été invalidée.")
            role = nextcord.utils.get(ctx.guild.roles, id=INSCRIPTION_BOT_ROLE_ID)
            if role in user.roles:
                print(f"Trying to remove role from {user.name}")
                await user.remove_roles(role)
                print(f"Role removed from {user.name}")
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
                member = nextcord.utils.get(self.bot.get_all_members(), id=user_id)
                role = nextcord.utils.get(member.guild.roles, id=INSCRIPTION_BOT_ROLE_ID)
                if role in member.roles:
                    print(f"Trying to remove role from {member.name}")
                    await member.remove_roles(role)
                    print(f"Role removed from {member.name}")
                if user_id in self.pending_registrations:
                    del self.pending_registrations[user_id]
                if user_id in self.validated_registrations:
                    del self.validated_registrations[user_id]
                del self.original_messages[payload.message_id]
        elif payload.channel_id in self.threads:
            user_id = self.threads[payload.channel_id]
            if user_id in self.pending_registrations or user_id in self.validated_registrations:
                invalidation_channel = self.bot.get_channel(INSCRIPTION_BOT_INVALIDATION_CHANNEL_ID)
                await invalidation_channel.send(f"<:tag_non:1034266050872737923> <@{user_id}> a supprimé un message dans son fil donc son inscription est annulé.")
                member = nextcord.utils.get(self.bot.get_all_members(), id=user_id)
                role = nextcord.utils.get(member.guild.roles, id=INSCRIPTION_BOT_ROLE_ID)
                if role in member.roles:
                    print(f"Trying to remove role from {member.name}")
                    await member.remove_roles(role)
                    print(f"Role removed from {member.name}")
                if user_id in self.pending_registrations:
                    del self.pending_registrations[user_id]
                if user_id in self.validated_registrations:
                    del self.validated_registrations[user_id]
                del self.threads[payload.channel_id]

def setup(bot):
    bot.add_cog(Inscription(bot))
