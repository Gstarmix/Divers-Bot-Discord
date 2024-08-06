import discord
from discord.ext import commands
import json
import os
from datetime import datetime

USER_ID = 200750717437345792
MUDAE_BOT_ID = 432610292342587392
CHANNEL_ID = 1191348379406577704
LOG_FILE_PATH = "embed_logs.json"

SLASH_COMMANDS = {"ha"}
TEXT_COMMANDS = {"$ha"}

class EmbedLogger(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.ensure_log_file_exists()

    def ensure_log_file_exists(self):
        if not os.path.exists(LOG_FILE_PATH):
            with open(LOG_FILE_PATH, 'w') as f:
                json.dump([], f, indent=4)

    def log_embed(self, embed, author, command, buttons_info=None):
        log_entry = {
            "user_id": author.id,
            "username": author.name,
            "command": command,
            "timestamp": datetime.now().isoformat(),
            "embed": {
                "title": embed.title,
                "description": embed.description,
                "fields": [{"name": field.name, "value": field.value} for field in embed.fields],
                "footer": embed.footer.text if embed.footer else None,
                "image": embed.image.url if embed.image else None,
                "thumbnail": embed.thumbnail.url if embed.thumbnail else None,
                "author": {
                    "name": embed.author.name,
                    "url": embed.author.url,
                    "icon_url": embed.author.icon_url
                } if embed.author else None,
                "buttons": buttons_info,
                "url": embed.url
            }
        }

        with open(LOG_FILE_PATH, 'r') as f:
            logs = json.load(f)

        logs.append(log_entry)

        with open(LOG_FILE_PATH, 'w') as f:
            json.dump(logs, f, indent=4)

        print("Embed logged:", log_entry)

    def extract_buttons_info(self, components):
        buttons_info = []
        print(f"Components: {components}")
        for component in components:
            if isinstance(component, discord.ActionRow):
                for item in component.children:
                    if isinstance(item, discord.ui.Button):
                        buttons_info.append({
                            "label": item.label,
                            "emoji": str(item.emoji) if item.emoji else None
                        })
        return buttons_info

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user} est prêt.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id != CHANNEL_ID:
            return

        if message.author.id == MUDAE_BOT_ID:
            print(f"Message de Mudae capturé : {message.content}")
            command_name = None
            if message.interaction:
                command_name = message.interaction.name
            print(f"Command name: {command_name}")

            if message.embeds:
                for embed in message.embeds:
                    buttons_info = self.extract_buttons_info(message.components)
                    self.log_embed(embed, message.author, command_name, buttons_info)
            else:
                await message.channel.send(f"{message.author.mention}, aucun embed trouvé dans la réponse du bot.")
                print("Aucun embed trouvé dans la réponse du bot.")

async def setup(bot):
    await bot.add_cog(EmbedLogger(bot))
