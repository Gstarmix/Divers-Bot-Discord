import discord
from discord.ext import commands
import asyncio
import json
import os
import re
from datetime import datetime, timezone
from constants import *

class MudaeListener(commands.Cog):
    listener_instance = None

    def __init__(self, bot):
        self.bot = bot
        MudaeListener.listener_instance = self  # Initialiser l'instance ici
        self.ensure_directories_exist()
        self.load_state()

    def ensure_directories_exist(self):
        # Créer le dossier 'extensions' s'il n'existe pas
        if not os.path.exists("extensions"):
            os.makedirs("extensions")

    def load_state(self):
        self.active_fils = self.load_json(THREADS_STATE_PATH, {})
        self.pending_responses = self.load_json(PENDING_RESPONSES_PATH, {})

    def save_state(self):
        self.save_json(THREADS_STATE_PATH, self.active_fils)
        self.save_json(PENDING_RESPONSES_PATH, self.pending_responses)

    def load_json(self, path, default):
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        else:
            with open(path, 'w') as f:
                json.dump(default, f, indent=4)
            return default

    def save_json(self, path, data):
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)

    @commands.Cog.listener()
    async def on_ready(self):
        await self.check_fils()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        author = message.author
        command_name = None

        if message.content:
            command_name = message.content.split()[0]

        if message.interaction:
            author = message.interaction.user
            if isinstance(message.interaction, discord.MessageInteraction):
                command_name = message.interaction.name
            if not message.embeds:
                return

        if command_name is None:
            return

        # Ensure commands can only be used in specific channels or threads
        if message.channel.id == MUDAE_ROLLS_CHANNEL_ID:
            if command_name in {"$tu", "$ru"}:
                await self.wait_for_tu_response(message, author)
            elif command_name in {"$us", "$rolls", "$usestack"}:
                role = discord.utils.get(message.guild.roles, id=OTAKU_SPAM_ROLE_ID)
                if role in author.roles:
                    pass
                else:
                    await message.channel.send(
                        f"**{author.name}**, vous devez utiliser la commande `$tu` ou `$ru` d'abord.\n\nPour utiliser toutes les commandes sans restriction, vous pouvez créer un fil avec les commandes `$topux-`, à condition de ne pas posséder de personnages mariables dans votre limroul."
                    )
            else:
                await self.handle_message_in_rolls_channel(author, message.content, message.channel.id)
            return

        if message.channel.id not in [*MUDAE_SETTINGS_CHANNEL_IDS] and message.channel.id not in [fil["fil_id"] for fil in self.active_fils.values()]:
            return

        if any(cmd for cmd in TOPU_COMMANDS if message.content.startswith(cmd)):
            if str(author.id) in self.active_fils:
                fil_id = self.active_fils[str(author.id)]["fil_id"]
                fil = await self.bot.fetch_channel(fil_id)
                await message.channel.send(f"**{author.name}**, vous avez déjà un fil actif : {fil.mention}")
                return

            # Vérification du contenu additionnel pour les commandes TOPU
            if message.content.strip() not in TOPU_COMMANDS:
                correct_command = next(cmd for cmd in TOPU_COMMANDS if message.content.startswith(cmd))
                await message.channel.send(f"**{author.name}**, pour créer un fil, la commande `{correct_command}` ne doit pas être suivie ou précédée d'autre texte ou flag.")
                return

            self.pending_responses[str(author.id)] = {
                "time": message.created_at.isoformat(),
                "command": command_name
            }
            self.save_state()
            await self.wait_for_mudae_response(message, author)

        if message.channel.id in [fil["fil_id"] for fil in self.active_fils.values()]:
            self.update_last_activity(message.channel.id)
            if not self.is_valid_command(command_name, message.channel.id):
                await self.cleanup_user_fil(author, message.content, message.channel.id)

        elif command_name.startswith('$'):
            if str(author.id) in self.active_fils:
                if self.is_valid_command(command_name, message.channel.id):
                    pass
                elif any(command_name.startswith(cmd) for cmd in ALL_TOPU_COMMANDS):
                    pass
                else:
                    await self.cleanup_user_fil(author, message.content, message.channel.id)
            else:
                if command_name in {"$tu", "$ru"}:
                    await self.wait_for_tu_response(message, author)
                elif command_name in {"$us", "$rolls", "$usestack"}:
                    role = discord.utils.get(message.guild.roles, id=OTAKU_SPAM_ROLE_ID)
                    if role in author.roles:
                        pass
                    else:
                        await message.channel.send(
                            f"**{author.name}**, vous devez utiliser la commande `$tu` ou `$ru` d'abord.\n\nPour utiliser toutes les commandes sans restriction, vous pouvez créer un fil avec les commandes `$topux-`, à condition de ne pas posséder de personnages mariables dans votre limroul."
                        )

    async def handle_message_in_rolls_channel(self, user, message_content, channel_id):
        if str(user.id) in self.active_fils:
            await self.cleanup_user_fil(user, message_content, channel_id)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.application_command:
            user = interaction.user
            command_name = interaction.command.name if interaction.command else None

            if str(user.id) in self.active_fils:
                fil_id = self.active_fils[str(user.id)]["fil_id"]
                if interaction.channel_id == fil_id:
                    self.update_last_activity(interaction.channel_id)
                    if not self.is_valid_command(command_name, interaction.channel_id, is_slash=True):
                        await self.cleanup_user_fil(user, interaction.command.name, interaction.channel_id)
                else:
                    if not self.is_valid_command(command_name, fil_id, is_slash=True):
                        await self.cleanup_user_fil(user, interaction.command.name, interaction.channel_id)

    def update_last_activity(self, fil_id):
        for user_id, fil_data in self.active_fils.items():
            if fil_data["fil_id"] == fil_id:
                fil_data["last_activity"] = datetime.now(timezone.utc).isoformat()
                self.save_state()

    def is_valid_command(self, content, channel_id, is_slash=False):
        if is_slash:
            if content in SLASH_COMMANDS:
                return True

        command_parts = content.split()
        if not command_parts:
            return False
        if command_parts[0] in TEXT_COMMANDS:
            return True
        for fil in self.active_fils.values():
            if fil["fil_id"] == channel_id:
                specific_commands = fil.get("specific_commands", [])
                if command_parts[0] in specific_commands:
                    return True
        return False

    async def wait_for_mudae_response(self, original_message, user):
        topu_command = self.pending_responses[str(user.id)]["command"]
        sleep_time = 5 if topu_command == "$topux-" else 3
        await asyncio.sleep(sleep_time)

        for channel_id in MUDAE_SETTINGS_CHANNEL_IDS:
            channel = self.bot.get_channel(channel_id)
            async for message in channel.history(limit=10, after=datetime.fromisoformat(self.pending_responses[str(user.id)]["time"])):
                if message.author.id == MUDAE_BOT_ID:
                    if message.embeds:
                        embed = message.embeds[0]
                        if embed.description and "(Aucun résultat)" in embed.description:
                            await self.assign_role_and_create_fil(channel, user, original_message)
                            del self.pending_responses[str(user.id)]
                            self.save_state()
                            return
                        else:
                            await original_message.channel.send(f"**{user.name}**, il reste des personnages mariables, un fil ne peut pas être créé.")
                    else:
                        pass

    async def wait_for_tu_response(self, original_message, user):
        await asyncio.sleep(1)  # Petit délai pour permettre à Mudae de répondre

        # Rechercher les messages envoyés par Mudae dans le même canal après la commande
        channel = original_message.channel
        rolls_detected = False  # Ajout d'un flag pour détecter les rolls
        async for message in channel.history(limit=10, after=original_message.created_at):
            if message.author.id == MUDAE_BOT_ID:
                # Détection de "Vous avez 0 rolls" et validation du $us
                if "Vous avez **0** rolls" in message.content:
                    us_match = re.search(r"\(\+\*\*(\d+)\*\* \$us\)", message.content)
                    if us_match:
                        us_number = int(us_match.group(1))
                        if us_number > 0:
                            await original_message.channel.send(
                                f"**{user.name}**, vous avez 0 rolls restants mais il vous reste {us_number} $us. Vous devez avoir 0 rolls et 0 $us pour utiliser `$us` ou `$rolls`.\n\nPour utiliser toutes les commandes sans restriction, vous pouvez créer un fil avec les commandes `$topux-`, à condition de ne pas posséder de personnages mariables dans votre limroul."
                            )
                            return
                    role = discord.utils.get(message.guild.roles, id=OTAKU_SPAM_ROLE_ID)
                    if role:
                        await message.channel.send(
                            f"**{user.name}**, étant donné que vous avez 0 rolls restants, vous pouvez utiliser les commandes `$us` et `$rolls` pendant 10 secondes.\n\nPour utiliser toutes les commandes sans restriction, vous pouvez créer un fil avec les commandes `$topux-`, à condition de ne pas posséder de personnages mariables dans votre limroul."
                        )
                        await user.add_roles(role)
                        await asyncio.sleep(10)
                        await user.remove_roles(role)
                    return
                elif re.search(r"Vous avez (\d+) rolls", message.content) and "rolls reset" not in message.content:
                    rolls_detected = True  # Mettre à jour le flag
                    # Extraire le nombre de rolls et les $us restants
                    rolls_text = re.search(r"Vous avez (\d+) rolls", message.content)
                    us_text = re.search(r"\(\+\*\*(\d+)\*\* \$us\)", message.content)
                    if rolls_text:
                        rolls_number = int(rolls_text.group(1))
                        us_number = int(us_text.group(1)) if us_text else 0
                        if rolls_number != 0 or us_number != 0:
                            await original_message.channel.send(
                                f"**{user.name}**, vous avez {rolls_number} rolls et {us_number} `$us` restants. Il est nécessaire d'avoir 0 rolls et 0 `$us` restants pour utiliser `$us` ou `$rolls`.\n\nPour utiliser toutes les commandes sans restriction, vous pouvez créer un fil avec les commandes `$topux-`, à condition de ne pas posséder de personnages mariables dans votre limroul."
                            )
                        return
        if not rolls_detected:  # Si aucun rolls n'a été détecté
            await original_message.channel.send(
                f"**{user.name}**, il est nécessaire d'avoir 0 rolls restants pour utiliser `$us` ou `$rolls`.\n\nPour utiliser toutes les commandes sans restriction, vous pouvez créer un fil avec les commandes `$topux-`, à condition de ne pas posséder de personnages mariables dans votre limroul."
            )

    async def assign_role_and_create_fil(self, settings_channel, user, original_message):
        role = discord.utils.get(original_message.guild.roles, id=OTAKU_SPAM_ROLE_ID)
        if not role:
            return

        if str(user.id) in self.active_fils:
            fil_id = self.active_fils[str(user.id)]["fil_id"]
            fil = await self.bot.fetch_channel(fil_id)
            await settings_channel.send(f"**{user.name}**, vous avez déjà un fil actif : {fil.mention}")
            return

        await user.add_roles(role)
        topu_command = self.pending_responses[str(user.id)]["command"]

        # Créer le fil silencieusement
        rolls_channel = self.bot.get_channel(MUDAE_ROLLS_CHANNEL_ID)

        fil = await rolls_channel.create_thread(
            name=f"{topu_command} de {user.name}",
            auto_archive_duration=60,
            type=discord.ChannelType.private_thread,
            reason=f"Fil créé pour {user.name} pour la commande {topu_command}"
        )

        self.active_fils[str(user.id)] = {
            "fil_id": fil.id,
            "creation_time": datetime.now(timezone.utc).isoformat(),
            "last_activity": datetime.now(timezone.utc).isoformat(),
            "specific_commands": [],
            "original_channel_id": original_message.channel.id  # Ajouter l'ID du salon d'origine
        }

        # Ajouter les commandes spécifiques
        if topu_command in TOPU_COMMANDS_HG_MINUS:
            self.active_fils[str(user.id)]["specific_commands"].extend(["$ha", "ha", "/ha"])
        elif topu_command in TOPU_COMMANDS_WG_MINUS:
            self.active_fils[str(user.id)]["specific_commands"].extend(["$wa", "wa", "/wa"])
        elif topu_command in TOPU_COMMANDS_MG_MINUS:
            self.active_fils[str(user.id)]["specific_commands"].extend(["$ma", "ma", "/ma"])
        elif topu_command in TOPU_COMMANDS_HG:
            self.active_fils[str(user.id)]["specific_commands"].extend(["$hg", "hg", "/hg"])
        elif topu_command in TOPU_COMMANDS_WG:
            self.active_fils[str(user.id)]["specific_commands"].extend(["$wg", "wg", "/wg"])
        elif topu_command in TOPU_COMMANDS_MG:
            self.active_fils[str(user.id)]["specific_commands"].extend(["$mg", "mg", "/mg"])
        elif topu_command == "$topux-":
            self.active_fils[str(user.id)]["specific_commands"].extend(["$topux-"])

        authorized_commands = set(TEXT_COMMANDS)
        specific_commands = set(self.active_fils[str(user.id)]["specific_commands"])
        authorized_commands_str = ', '.join([f"`{cmd}`" for cmd in sorted(authorized_commands | specific_commands)])

        await fil.send(f"{user.mention}, vous pouvez utiliser ce fil pour vos interactions. Les commandes autorisées sont : {authorized_commands_str}")
        await settings_channel.send(f"**{user.name}**, un fil a été créé pour vous : {fil.jump_url}")

        self.save_state()

    async def cleanup_user_fil(self, user, command_used, channel_id):
        role = discord.utils.get(user.guild.roles, id=OTAKU_SPAM_ROLE_ID)
        if not role:
            return

        await user.remove_roles(role)

        fil_data = self.active_fils.pop(str(user.id), None)
        if fil_data:
            fil = await self.bot.fetch_channel(fil_data["fil_id"])
            await fil.edit(locked=True)
            await fil.send(f"{user.mention}, ce fil est maintenant verrouillé en raison de l'utilisation du message `{command_used}` dans le salon <#{channel_id}>.")
            await asyncio.sleep(600)
            await fil.delete()

        self.save_state()

    async def check_fils(self):
        now = datetime.now(timezone.utc)
        for user_id, fil_data in list(self.active_fils.items()):
            fil = await self.bot.fetch_channel(fil_data["fil_id"])
            last_activity = datetime.fromisoformat(fil_data["last_activity"])
            if (now - last_activity).total_seconds() > 600:
                await fil.send(f"{self.bot.get_user(int(user_id)).mention}, ce fil a été verrouillé en raison de 10 minutes d'inactivité. Veuillez créer un nouveau fil avec la commande `$topux-`.")
                await fil.edit(archived=True)

                # Retirer le rôle après verrouillage du fil
                user = self.bot.get_user(int(user_id))
                role = discord.utils.get(user.guild.roles, id=OTAKU_SPAM_ROLE_ID)
                if role:
                    await user.remove_roles(role)

                del self.active_fils[user_id]
        self.save_state()
        await asyncio.sleep(60)
        await self.check_fils()

async def setup(bot):
    await bot.add_cog(MudaeListener(bot))
    bot.loop.create_task(MudaeListener.listener_instance.check_fils())
