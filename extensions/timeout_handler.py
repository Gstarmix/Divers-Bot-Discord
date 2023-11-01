import discord
from discord.ext import commands
import asyncio
from constants import *

SLASH_COMMANDS = {"wa", "ha", "ma", "wg", "hg", "mg", "wx", "hx", "mx"}
TEXT_COMMANDS = {"$w", "$h", "$m", "$wa", "$ha", "$ma", "$wg", "$hg", "$mg"}

class GestionnaireMute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.user_last_command_time = {}
        self.active_user = {}
        self.embed_countdown = {}

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"GestionnaireMute est prêt !")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        print("Interaction détectée")
        if interaction.type == discord.InteractionType.application_command:
            print("C'est une commande slash")
            await self.process_command_logic(interaction.message, interaction.user, interaction.channel, interaction.created_at, interaction.data['name'])

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        print("Message détecté")
        await self.process_command_logic(message, message.author, message.channel, message.created_at, message.content.split()[0] if message.content else None)

    async def process_command_logic(self, message, author, channel, created_at, command_name):
        print(f"Traitement du message/interaction de {author.name}: {command_name}")
        if channel.id not in {MUDAE_WAIFUS_CHANNEL_ID, MUDAE_WAIFUS_CHANNEL_2_ID}:
            return
        
        if author.bot:
            if "la roulette est limitée à" in message.content:
                print("Message 'la roulette est limitée à' détecté")
                return

            if message.embeds:
                for embed in message.embeds:
                    if embed.footer and "⚠️ 2 ROLLS RESTANTS ⚠️" in embed.footer.text:
                        self.embed_countdown[author.id] = 2
                        return
                    elif author.id in self.embed_countdown:
                        self.embed_countdown[author.id] -= 1
                        if self.embed_countdown[author.id] == 0:
                            self.active_user[channel.id] = None
                            await channel.send("script arrêté")
                            del self.embed_countdown[author.id]
                        return
            return

        if not command_name:
            return

        is_command_A = command_name in SLASH_COMMANDS or command_name in TEXT_COMMANDS
        is_command_B = command_name.startswith("$") or command_name in SLASH_COMMANDS

        active_user_channel = self.active_user.get(channel.id)

        if active_user_channel and active_user_channel != author.id and (created_at.timestamp() - self.user_last_command_time.get((active_user_channel, channel.id), 0)) < 3:
            if is_command_B:
                overwrites = channel.overwrites_for(author)
                overwrites.send_messages = False
                elapsed_time = created_at.timestamp() - self.user_last_command_time.get((active_user_channel, channel.id), 0)
                try:
                    await channel.set_permissions(author, overwrite=overwrites)
                    mute_message = await channel.send(f"{author.mention}, tu as interrompu {self.bot.get_user(active_user_channel).mention} qui était en train de faire ses rolls, et ce, en moins de {elapsed_time:.2f} secondes. Tu as été mis en sourdine pour 60 secondes. Il te reste 60 secondes de sourdine.")
                    
                    for i in range(59, 0, -1):
                        await mute_message.edit(content=f"{author.mention}, tu as interrompu {self.bot.get_user(active_user_channel).mention} qui était en train de faire ses rolls, et ce, en moins de {elapsed_time:.2f} secondes. Tu as été mis en sourdine pour 60 secondes. Il te reste {i} secondes de sourdine.")
                        await asyncio.sleep(1)
                    
                    overwrites.send_messages = True
                    await channel.set_permissions(author, overwrite=overwrites)
                    await mute_message.edit(content=f"{author.mention}, ta mise en sourdine a été levée.")
                except discord.Forbidden:
                    print(f"Erreur de permission lors de la tentative de mute de {author.name}.")
                except discord.HTTPException as e:
                    print(f"Exception HTTP : {e}")
                return
        elif is_command_A:
            self.active_user[channel.id] = author.id
            self.user_last_command_time[(author.id, channel.id)] = created_at.timestamp()

async def setup(bot):
    await bot.add_cog(GestionnaireMute(bot))