from datetime import datetime, timedelta
import asyncio

import discord
from discord.ext import commands, tasks
import json
import constants as const

# Définir le chemin relatif vers le dossier où se trouvent les fichiers JSON
COMMANDS_CONFIG_PATH = "extensions/commands_config.json"
LAST_MESSAGE_PATH = "extensions/last_messages.json"


class CommandCheck(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # Charger les configurations à partir du fichier JSON
        with open(COMMANDS_CONFIG_PATH, 'r') as f:
            config = json.load(f)

        self.forbidden_commands: list[str] = config['forbidden_commands']
        self.allowed_commands: dict[str, list[str]] = config['allowed_commands']
        self.specific_commands: list[str] = config['specific_commands']

        self.allowed_commands["MUDAE_WAIFUS_CHANNEL_2_ID"].extend(self.specific_commands)
        self.allowed_commands["MUDAE_SETTINGS_CHANNEL_2_ID"].extend(self.specific_commands)

        self.forbidden_commands = config['forbidden_commands']
        
        self.mod_commands = []
        for channel_name, commands_list in self.allowed_commands.items():
            if channel_name not in ["MUDAE_MODO_CHANNEL_ID", "LOG_CHANNEL_ID", "MUDAE_CONTROL_CHANNEL_ID", "MUDAE_WAIFUS_CHANNEL_2_ID", "MUDAE_SETTINGS_CHANNEL_2_ID", "MUDAE_IDEAS_CHANNEL_ID", "MUDAE_HELP_CHANNEL_ID"]:
                self.mod_commands.extend(commands_list)

        all_commands_except_poke_and_waifus = set(self.mod_commands) - set(self.allowed_commands["MUDAE_POKESLOT_CHANNEL_ID"]) - set(self.allowed_commands["MUDAE_WAIFUS_CHANNEL_2_ID"])
        self.allowed_commands["MUDAE_SETTINGS_CHANNEL_2_ID"] = list(all_commands_except_poke_and_waifus)

        # Charger les derniers messages à partir du fichier JSON
        try:
            with open(LAST_MESSAGE_PATH, 'r') as f:
                self.last_message_id: dict[str, int] = json.load(f)
        except FileNotFoundError:
            self.last_message_id: dict[str, int] = {}

        self.post_allowed_commands.start()
        self.message_counts: dict[int, int] = {}  # Nouveau dictionnaire pour suivre le nombre de messages par salon
        self.minimum_messages = 5  # Nombre minimum de messages pour conserver le message du bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        channel = message.channel
        parent_channel_id = channel.parent_id if isinstance(channel, discord.Thread) else None

        split_message = message.clean_content.split()
        command = split_message[0] if split_message else ""

        if command in self.forbidden_commands:
            if not any(role.id in {const.CHEF_SINGE_ROLE_ID, const.MUDAE_MODO_ROLE_ID} for role in message.author.roles):
                await message.delete()
                await channel.send(f"{message.author.mention} Vous avez envoyé la commande `{command}`. Cette commande est interdite. Je vous prie de ne plus l'envoyer.")
        if parent_channel_id in {const.MUDAE_IDEAS_CHANNEL_ID, const.MUDAE_HELP_CHANNEL_ID}:
            # Allow all commands in these threads
            return

        if channel.id in {const.MUDAE_WAIFUS_CHANNEL_2_ID, const.MUDAE_SETTINGS_CHANNEL_2_ID}:
            if command in self.specific_commands:
                return

        if command.startswith('$') or command.startswith('/'):
            if command not in self.mod_commands:
                return

            if channel.id in {const.MUDAE_MODO_CHANNEL_ID, const.LOG_CHANNEL_ID, const.MUDAE_CONTROL_CHANNEL_ID}:
                return

            if channel.id == const.MUDAE_WAIFUS_CHANNEL_2_ID:
                if command in self.allowed_commands["MUDAE_POKESLOT_CHANNEL_ID"]:
                    await message.delete()
                    await channel.send(f"{message.author.mention} Vous avez envoyé la commande `{command}` dans le mauvais salon. Veuillez l'envoyer dans le bon salon : <#{const.MUDAE_POKESLOT_CHANNEL_ID}>.")
                    return
                if command not in self.allowed_commands["MUDAE_WAIFUS_CHANNEL_2_ID"]:
                    await message.delete()
                    await channel.send(f"{message.author.mention} Vous avez envoyé la commande `{command}` dans le mauvais salon. Veuillez l'envoyer dans le bon salon : <#{const.MUDAE_SETTINGS_CHANNEL_2_ID}>.")  # FIXME: ce message là fait pas beaucoup de sens à mes yeux
                    return

            if channel.id == const.MUDAE_SETTINGS_CHANNEL_2_ID:
                if command in self.allowed_commands["MUDAE_POKESLOT_CHANNEL_ID"] or command in self.allowed_commands["MUDAE_WAIFUS_CHANNEL_2_ID"] or command in self.forbidden_commands:
                    await message.delete()
                    target_channel = const.MUDAE_POKESLOT_CHANNEL_ID if command in self.allowed_commands["MUDAE_POKESLOT_CHANNEL_ID"] else const.MUDAE_WAIFUS_CHANNEL_2_ID
                    await channel.send(f"{message.author.mention} Vous avez envoyé la commande `{command}` dans le mauvais salon. Veuillez l'envoyer dans le bon salon : <#{target_channel}>.")
                return

            allowed_channels: set[int] = {const.CHANNELS_NAME_TO_ID[channel_name] for channel_name, commands_list in self.allowed_commands.items() if command in commands_list and channel_name not in {"MUDAE_MODO_CHANNEL_ID", "LOG_CHANNEL_ID", "MUDAE_CONTROL_CHANNEL_ID", "MUDAE_SETTINGS_CHANNEL_2_ID"}}

            if channel.id not in allowed_channels:
                await message.delete()
                
                # Initialisation par défaut de wrong_channel_msg
                wrong_channel_msg = f"{message.author.mention} Vous avez envoyé la commande `{command}` dans le mauvais salon."
                
                # Ajout de MUDAE_SETTINGS_CHANNEL_2_ID pour tous les salons, sauf pour les commandes spécifiques à MUDAE_POKESLOT_CHANNEL_ID
                if command not in self.allowed_commands["MUDAE_POKESLOT_CHANNEL_ID"]:
                    allowed_channels.add(const.MUDAE_SETTINGS_CHANNEL_2_ID)
                
                # Triez les salons ici si nécessaire
                allowed_channels = sorted(allowed_channels)
                
                allowed_channels_str = ', '.join([f"<#{channel_id}>" for channel_id in allowed_channels])
                
                wrong_channel_msg += f" Veuillez l'envoyer dans l'un des salons suivants : {allowed_channels_str}."
                
                if channel.id == const.MUDAE_TUTORIAL_CHANNEL_ID:
                    wrong_channel_msg += " Une fois cela effectué, veuillez rafraîchir le tutoriel en tapant à nouveau `$tuto` dans ce salon."
                
                await channel.send(wrong_channel_msg)


            # Mettre à jour le compte de messages pour le salon
            if channel.id in self.message_counts:
                self.message_counts[channel.id] += 1
            else:
                self.message_counts[channel.id] = 1
            
    @tasks.loop(hours=3)
    async def post_allowed_commands(self):
        for channel_name, commands_list in self.allowed_commands.items():
            channel_id = const.CHANNELS_NAME_TO_ID[channel_name]
            if commands_list:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    # Supprimer le dernier message si existant
                    if str(channel_id) in self.last_message_id:
                        try:
                            message_to_delete = await channel.fetch_message(self.last_message_id[str(channel_id)])
                            await message_to_delete.delete()
                        except Exception as e:  # Attraper toutes les exceptions, comme le message déjà supprimé
                            print(f"Error deleting message: {e}")

                    # Envoyer le nouveau message et mettre à jour le dernier message_id
                    sorted_commands = sorted(commands_list)
                    sent_message = await channel.send(f"Voici toutes les commandes autorisées dans ce salon : {' '.join([f'`{cmd}`' for cmd in sorted_commands])}")
                    self.last_message_id[str(channel_id)] = sent_message.id
        
                    # Sauvegarder le dernier message_id dans le fichier JSON
                    with open(LAST_MESSAGE_PATH, 'w') as f:
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


async def setup(bot: commands.Bot):
    await bot.add_cog(CommandCheck(bot))
