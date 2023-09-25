import json
import os
import asyncio
from json import JSONDecodeError
from discord import AllowedMentions, Forbidden, ChannelType
from discord.ext import commands
from discord.errors import NotFound
from constants import *


class Presentation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.threads = {}
        self.delete_messages = {}
        self.families = ["yertirand", "-gang-"]

        # Vérifiez et chargez les fichiers JSON
        self.load_json_files()

    def load_json_files(self):
        file_paths = [
            'extensions/presentation_messages.json',
            'extensions/previous_presentations.json',
            'extensions/saved_presentations.json'
        ]

        for file_path in file_paths:
            directory = os.path.dirname(file_path)
            if not os.path.exists(directory):
                os.makedirs(directory)

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if file_path.endswith('presentation_messages.json'):
                        self.data = data
                    elif file_path.endswith('previous_presentations.json'):
                        previous_presentations = data
                    elif file_path.endswith('saved_presentations.json'):
                        saved_presentations = data
            except FileNotFoundError:
                print(f"Erreur: Fichier {file_path} non trouvé.")
                if file_path.endswith('presentation_messages.json'):
                    self.data = {}
                elif file_path.endswith('previous_presentations.json'):
                    previous_presentations = {}
                elif file_path.endswith('saved_presentations.json'):
                    saved_presentations = {}
            except JSONDecodeError:
                print(f"Erreur: Le fichier {file_path} est mal formé.")
                # Initialisez les variables en fonction du fichier JSON mal formé
                if file_path.endswith('presentation_messages.json'):
                    self.data = {}
                elif file_path.endswith('previous_presentations.json'):
                    previous_presentations = {}
                elif file_path.endswith('saved_presentations.json'):
                    saved_presentations = {}
            except Exception as e:
                print(f"Erreur inattendue lors de la lecture de {file_path}: {e}")

        # Mettez à jour et écrivez dans saved_presentations.json
        try:
            saved_presentations.update(previous_presentations)
            with open('extensions/saved_presentations.json', 'w', encoding='utf-8') as f:
                json.dump(saved_presentations, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erreur lors de la mise à jour de saved_presentations.json: {e}")

    async def generate_message(self, thread, choice):
        recruitment_role_id = GARDIEN_YERTI_ROLE_ID if choice == "yertirand" else GARDIEN_GANG_ROLE_ID
        role_id = ROLE1_ID_FAFA
        new_roles = [self.bot.get_guild(GUILD_ID_FAFA).get_role(role_id) for role_id in [ROLE1_ID_FAFA, ROLE2_ID_FAFA, ROLE3_ID_FAFA, ROLE4_ID_FAFA, ROLE5_ID_FAFA]]

        for role in thread.owner.roles:
            if role not in new_roles:
                try:
                    await thread.owner.remove_roles(role)
                except NotFound:
                    print(f"Could not remove role {role.name}")

        await thread.owner.add_roles(*new_roles)

        # Utilisation du message généré à partir du fichier JSON
        return self.data['messages']['generate_message'].format(owner_mention=thread.owner.mention, role_id=role_id, recruitment_role_id=recruitment_role_id)

    async def ask_question(self, thread, question_key, check, yes_no_question=True, image_allowed=False):
        message = self.data['questions'][question_key]
        first_time = True
        while True:
            if first_time:
                user_message_sent = False
                async for msg in thread.history(limit=5):
                    if msg.author == thread.owner:
                        user_message_sent = True
                        break

                if not user_message_sent:
                    await asyncio.sleep(5)
                    continue

                await thread.send(f"{thread.owner.mention} {message}")
                first_time = False
            try:
                response = await self.bot.wait_for('message', check=check, timeout=600)
                if yes_no_question:
                    if response.content.lower() in ['oui', 'non']:
                        return response
                    else:
                        message = "Je n'ai pas compris votre réponse. Veuillez répondre par `Oui` ou `Non`."
                elif image_allowed and response.attachments:
                    return response
                else:
                    return response
            except asyncio.TimeoutError:
                await thread.owner.send("Votre fil a été supprimé car vous avez mis plus de 10 minutes à répondre au questionnaire.")
                await thread.delete()
                return None
            await thread.send(f"{thread.owner.mention} {message}")

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        if thread.parent.id != PRESENTATION_CHANNEL_ID:
            return

        self.threads[thread.id] = thread.owner.id
        self.delete_messages[thread.id] = True

        async for message in thread.history(limit=1):
            await message.pin()
            break

        def check(m):
            return m.channel == thread and m.author == thread.owner

        # Utilisation des questions à partir du fichier JSON
        response = await self.ask_question(thread, 'pseudo_correct', check)
        if response is None:
            return
        new_name = thread.name
        while response.content.lower() == 'non':
            response = await self.ask_question(thread, 'pseudo_in_game', check, yes_no_question=False)
            if response is None:
                return
            new_name = response.content
            if len(new_name) <= 32:
                response = await self.ask_question(thread, 'confirm_pseudo', check)
                if response is None:
                    return
                if response.content.lower() == 'oui':
                    try:
                        await thread.owner.edit(nick=new_name)
                        await thread.edit(name=new_name)
                    except Exception as e:
                        print(f"Erreur lors de la modification du pseudo Discord ou du titre du fil : {e}")
            else:
                await thread.send(f"{thread.owner.mention} {self.data['messages']['long_pseudo']}")
                return

        response = await self.ask_question(thread, 'send_screenshot', check)
        if response is None:
            return

        screenshots = []
        while response.content.lower() == 'non' or response.attachments:
            if response.attachments:
                screenshots.extend(attachment.url for attachment in response.attachments)
            # Demandez à l'utilisateur s'il souhaite envoyer d'autres captures d'écran
            response = await self.ask_question(thread, 'additional_screenshot', check, yes_no_question=True, image_allowed=True)
            if response is None:
                return
            if response.content.lower() == 'non':
                break  # Sortez de la boucle si l'utilisateur ne souhaite pas envoyer d'autres captures d'écran

        family_name = ""
        while family_name not in self.families:
            response = await self.ask_question(thread, 'choose_family', check, yes_no_question=False)
            if response is None:
                return
            family_name = response.content.lower()

        message = await self.generate_message(thread, family_name)
        allowed_mentions = AllowedMentions(everyone=False, users=True, roles=False)
        await thread.send(message, allowed_mentions=allowed_mentions)

        # Sauvegarde de la présentation dans le fichier JSON
        with open('extensions/saved_presentations.json', 'r') as f:
            presentations = json.load(f)

        presentations[str(thread.id)] = {
            "owner_id": str(thread.owner.id),
            "pseudo": new_name,
            "family": family_name,
            "screenshots": screenshots
        }

        with open('extensions/saved_presentations.json', 'w') as f:
            json.dump(presentations, f, indent=2)

        self.delete_messages[thread.id] = False

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.channel.type is ChannelType.public_thread and message.channel.id in self.threads and message.author.id == self.threads[message.channel.id]:
            try:
                await message.author.remove_roles(self.bot.get_guild(GUILD_ID_FAFA).get_role(ROLE1_ID_FAFA))
                await message.channel.delete()
                await message.author.send("Votre fil a été supprimé car un message a été supprimé. Vous devez recommencer votre présentation pour avoir accès aux salons.")
            except Forbidden:
                pass  # Handle permission error if necessary


async def setup(bot):
    await bot.add_cog(Presentation(bot))
