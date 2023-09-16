from datetime import datetime, timedelta
import asyncio
from discord.ext import commands, tasks
import json
import os
from constants import *

class CommandCheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        # Définir le chemin absolu vers le dossier où se trouvent les fichiers JSON
        json_folder_path = 'C:/Users/Gstar/Desktop/Bot GSTAR/extensions/'

        # Charger les configurations à partir du fichier JSON
        with open(os.path.join(json_folder_path, 'commands_config.json'), 'r') as f:
            config = json.load(f)

        self.forbidden_commands = config['forbidden_commands']
        self.allowed_commands = config['allowed_commands']

        # Charger les derniers messages à partir du fichier JSON
        try:
            with open(os.path.join(json_folder_path, 'last_messages.json'), 'r') as f:
                self.last_message_id = json.load(f)
        except FileNotFoundError:
            self.last_message_id = {}

        self.specific_commands = config['specific_commands']
        self.allowed_commands = config['allowed_commands']

        self.allowed_commands[MUDAE_WAIFUS_CHANNEL_2_ID].extend(self.specific_commands)
        self.allowed_commands[MUDAE_SETTINGS_CHANNEL_2_ID].extend(self.specific_commands)

        self.forbidden_commands = config['forbidden_commands']
        
        self.mod_commands = []
        for channel_id, commands in self.allowed_commands.items():
            if channel_id not in [MUDAE_MODO_CHANNEL_ID, LOG_CHANNEL_ID, MUDAE_CONTROL_CHANNEL_ID, MUDAE_WAIFUS_CHANNEL_2_ID, MUDAE_SETTINGS_CHANNEL_2_ID]:
                self.mod_commands.extend(commands)

        all_commands_except_poke_and_waifus = set(self.mod_commands) - set(self.allowed_commands[MUDAE_POKESLOT_CHANNEL_ID]) - set(self.allowed_commands[MUDAE_WAIFUS_CHANNEL_2_ID])
        self.allowed_commands[MUDAE_SETTINGS_CHANNEL_2_ID] = list(all_commands_except_poke_and_waifus)

        self.post_allowed_commands.start()
        self.message_counts = {}  # Nouveau dictionnaire pour suivre le nombre de messages par salon
        self.last_message_id = {}  # Nouveau dictionnaire pour suivre le dernier message posté par le bot par salon
        self.minimum_messages = 5  # Nombre minimum de messages pour conserver le message du bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        split_message = message.content.split()
        command = split_message[0] if split_message else ""

        if command in self.forbidden_commands:
            if not any(role.id in [CHEF_SINGE_ROLE_ID, MUDAE_MODO_ROLE_ID] for role in message.author.roles):
                await message.delete()
                await message.channel.send(f"{message.author.mention} Vous avez envoyé la commande `{command}`. Cette commande est interdite. Je vous prie de ne plus l'envoyer.")
            return

        if message.channel.id == MUDAE_WAIFUS_CHANNEL_2_ID or message.channel.id == MUDAE_SETTINGS_CHANNEL_2_ID:
            if command in self.specific_commands:
                return

        if command.startswith('$') or command.startswith('/'):
            if command not in self.mod_commands:
                return

            if message.channel.id in [MUDAE_MODO_CHANNEL_ID, LOG_CHANNEL_ID, MUDAE_CONTROL_CHANNEL_ID]:
                return

            if message.channel.id == MUDAE_WAIFUS_CHANNEL_2_ID:
                if command in self.allowed_commands[MUDAE_POKESLOT_CHANNEL_ID]:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention} Vous avez envoyé la commande `{command}` dans le mauvais salon. Veuillez l'envoyer dans le bon salon : <#{MUDAE_POKESLOT_CHANNEL_ID}>.")
                    return
                if command not in self.allowed_commands[MUDAE_WAIFUS_CHANNEL_2_ID]:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention} Vous avez envoyé la commande `{command}` dans le mauvais salon. Veuillez l'envoyer dans le bon salon : <#{MUDAE_SETTINGS_CHANNEL_2_ID}>.")
                    return

            if message.channel.id == MUDAE_SETTINGS_CHANNEL_2_ID:
                if command in self.allowed_commands[MUDAE_POKESLOT_CHANNEL_ID] or command in self.allowed_commands[MUDAE_WAIFUS_CHANNEL_2_ID] or command in self.forbidden_commands:
                    await message.delete()
                    target_channel = MUDAE_POKESLOT_CHANNEL_ID if command in self.allowed_commands[MUDAE_POKESLOT_CHANNEL_ID] else MUDAE_WAIFUS_CHANNEL_2_ID
                    await message.channel.send(f"{message.author.mention} Vous avez envoyé la commande `{command}` dans le mauvais salon. Veuillez l'envoyer dans le bon salon : <#{target_channel}>.")
                    return
                else:
                    return

            allowed_channels = [channel_id for channel_id, commands in self.allowed_commands.items() if command in commands]
            allowed_channels = list(filter(lambda x: x not in [MUDAE_MODO_CHANNEL_ID, LOG_CHANNEL_ID, MUDAE_CONTROL_CHANNEL_ID, MUDAE_SETTINGS_CHANNEL_2_ID], allowed_channels))
            allowed_channels_str = ', '.join([f"<#{channel_id}>" for channel_id in allowed_channels])

            if message.channel.id not in allowed_channels:
                await message.delete()
                wrong_channel_msg = f"{message.author.mention} Vous avez envoyé la commande `{command}` dans le mauvais salon."
                
                # Ajout pour voir MUDAE_SETTINGS_CHANNEL_2_ID
                if message.channel.id in [MUDAE_TRADE_CHANNEL_ID, MUDAE_WISH_CHANNEL_ID, MUDAE_KAKERA_CHANNEL_ID, MULTI_GAMES_CHANNEL_ID]:
                    allowed_channels.append(MUDAE_SETTINGS_CHANNEL_2_ID)
                
                allowed_channels_str = ', '.join([f"<#{channel_id}>" for channel_id in allowed_channels])
                wrong_channel_msg += f" Veuillez l'envoyer dans le bon salon : {allowed_channels_str}."
                
                if message.channel.id == MUDAE_TUTORIAL_CHANNEL_ID:
                    wrong_channel_msg += " Une fois cela effectué, veuillez rafraîchir le tutoriel en tapant à nouveau `$tuto` dans ce salon."
                    
                await message.channel.send(wrong_channel_msg)

        # Mettre à jour le compte de messages pour le salon
        if message.channel.id in self.message_counts:
            self.message_counts[message.channel.id] += 1
        else:
            self.message_counts[message.channel.id] = 1
            
    @tasks.loop(hours=1)
    async def post_allowed_commands(self):
        for channel_id, commands_list in self.allowed_commands.items():
            if commands_list:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    # Supprimer le dernier message si le compte de messages est inférieur au minimum
                    if channel_id in self.message_counts and self.message_counts[channel_id] < self.minimum_messages:
                        if channel_id in self.last_message_id:
                            try:
                                message_to_delete = await channel.fetch_message(self.last_message_id[channel_id])
                                await message_to_delete.delete()
                            except:  # Attraper toutes les exceptions, comme le message déjà supprimé
                                pass

                    # Réinitialiser le compteur de messages pour ce salon
                    self.message_counts[channel_id] = 0

                    # Envoyer le nouveau message et mettre à jour le dernier message_id
                    sorted_commands = sorted(commands_list)
                    sent_message = await channel.send(f"Voici toutes les commandes autorisées dans ce salon : {' '.join([f'`{cmd}`' for cmd in sorted_commands])}")
                    self.last_message_id[channel_id] = sent_message.id
        # Mettre à jour le dernier message_id et sauvegarder dans le fichier JSON
        self.last_message_id[channel_id] = sent_message.id
        with open('last_messages.json', 'w') as f:
            json.dump(self.last_message_id, f)

    @post_allowed_commands.before_loop
    async def before_post_allowed_commands(self):
        now = datetime.now()
        next_run_time = now.replace(minute=0, second=0, microsecond=0)

        if now.minute > 0 or now.second > 0 or now.microsecond > 0:
            next_run_time = next_run_time + timedelta(hours=1)

        sleep_time = (next_run_time - now).total_seconds()
        await asyncio.sleep(sleep_time)

    def cog_unload(self):
        self.post_allowed_commands.cancel()


async def setup(bot):
    await bot.add_cog(CommandCheck(bot))
