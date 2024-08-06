import discord
from discord.ext import commands
import json
import os
import asyncio
from datetime import datetime

USER_ID = 200750717437345792
MUDAE_BOT_ID = 432610292342587392  # Remplace avec l'ID réel du bot Mudae
LOG_FILE_PATH = "embed_logs.json"
CHANNEL_ID = 1191348379406577704  # ID du salon à surveiller

SLASH_COMMANDS = {"wa", "ha", "ma", "wg", "hg", "mg", "wx", "hx", "mx"}
TEXT_COMMANDS = {"$w", "$h", "$m", "$wa", "$ha", "$ma", "$wg", "$hg", "$mg"}

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
        print(f"{self.bot.user} is ready.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id != CHANNEL_ID:
            return  # Ignorer les messages dans les autres salons

        author = message.author
        command_name = None

        if message.content:
            command_name = message.content.split()[0]

        print(f"Message received: {message.content}, Interaction: {message.interaction}")

        if author.id == USER_ID and command_name in TEXT_COMMANDS:
            print(f"Command message received from the specific user: {command_name}")

            def check(m):
                return m.author.id == MUDAE_BOT_ID and m.channel.id == message.channel.id

            try:
                mudae_message = await self.bot.wait_for('message', check=check, timeout=10.0)
                print(f"Mudae message captured: {mudae_message.content}")
                if mudae_message.embeds:
                    for embed in mudae_message.embeds:
                        buttons_info = self.extract_buttons_info(mudae_message.components)
                        self.log_embed(embed, author, command_name, buttons_info)
                else:
                    await message.channel.send(f"{author.mention}, no embeds found in the bot's response.")
                    print("No embeds found in the bot's response.")
            except asyncio.TimeoutError:
                await message.channel.send(f"{author.mention}, no response from the Mudae bot found.")
                print("No response from the Mudae bot found.")

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.channel_id != CHANNEL_ID:
            return  # Ignorer les interactions dans les autres salons

        if interaction.user.id == USER_ID and interaction.data["name"] in SLASH_COMMANDS:
            print(f"Interaction received from the specific user: {interaction.data['name']}")

            await interaction.response.defer()

            try:
                # Attendre un peu pour donner à Mudae le temps de répondre
                await asyncio.sleep(5)
                response_message = await interaction.original_response()
                print(f"Original response: {response_message.content}")
                if response_message.embeds:
                    for embed in response_message.embeds:
                        buttons_info = self.extract_buttons_info(response_message.components)
                        self.log_embed(embed, interaction.user, interaction.data["name"], buttons_info)
                else:
                    await interaction.followup.send(f"{interaction.user.mention}, no embeds found in the bot's response.")
                    print("No embeds found in the bot's response.")
            except discord.NotFound:
                await interaction.followup.send(f"{interaction.user.mention}, no response from the Mudae bot found.")
                print("No response from the Mudae bot found.")
            except discord.HTTPException as e:
                print(f"HTTPException: {e}")

async def setup(bot):
    await bot.add_cog(EmbedLogger(bot))
