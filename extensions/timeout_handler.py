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

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"GestionnaireMute est prêt !")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        author = message.author
        channel = message.channel
        created_at = message.created_at
        
        if channel.id not in {MUDAE_WAIFUS_CHANNEL_ID, MUDAE_WAIFUS_CHANNEL_2_ID}:
            return
            
        if author.bot and not message.interaction:
            return
            
        command_name = None
        
        if message.content:
            command_name = message.content.split()[0]
        
        if message.interaction:
            author = message.interaction.user
            command_name = message.interaction.name
            if not message.embeds:
                return
        
        is_command_A = command_name in SLASH_COMMANDS or command_name in TEXT_COMMANDS
        is_command_B = message.content.startswith("$") or message.interaction is not None

        active_user_channel = self.active_user.get(channel.id)

        if active_user_channel and active_user_channel != author.id and (created_at.timestamp() - self.user_last_command_time.get((active_user_channel, channel.id), 0)) < 3:
            if is_command_B:
                # Mute logic for user B
                print(f"Condition de mute atteinte pour l'utilisateur {author.name}.")
                overwrites = channel.overwrites_for(author)
                overwrites.send_messages = False
                elapsed_time = created_at.timestamp() - self.user_last_command_time.get((active_user_channel, channel.id), 0)
                try:
                    await channel.set_permissions(author, overwrite=overwrites)
                    mute_message = await channel.send(f"{author.mention} Tu as interrompu {self.bot.get_user(active_user_channel).mention} qui était en train de faire ses rolls, et ce, en moins de {elapsed_time:.2f} secondes (la limite autorisée est de 3 secondes). En conséquence, tu as été mis en sourdine dans ce salon pour une durée de 60 secondes. Il te reste 60 secondes de sourdine.")
                    
                    # Compte à rebours et mise à jour du message
                    for i in range(59, 0, -1):
                        await mute_message.edit(content=f"{author.mention} Tu as interrompu {self.bot.get_user(active_user_channel).mention} qui était en train de faire ses rolls, et ce, en moins de {elapsed_time:.2f} secondes (la limite autorisée est de 3 secondes). En conséquence, tu as été mis en sourdine dans ce salon pour une durée de 60 secondes. Il te reste {i} secondes de sourdine.")
                        await asyncio.sleep(1)
                    
                    overwrites.send_messages = True
                    await channel.set_permissions(author, overwrite=overwrites)
                    await mute_message.edit(content=f"{author.mention} Ta mise en sourdine a été levée.")
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
