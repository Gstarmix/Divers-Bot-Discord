import discord
from discord.ext import commands
import json
import os
from datetime import datetime

USER_ID = 200750717437345792
MUDAE_BOT_ID = 432610292342587392
LOG_FILE_PATH = "embed_logs.json"
KAKERA_L_EMOJI_ID = 1097914945699581973
KAKERA_R_EMOJI_ID = 1097914903915925716
KAKERA_W_EMOJI_ID = 608192076286263297
KAKERA_P_EMOJI_ID = 1097914822462545951

KAKERA_ICONS = {
    KAKERA_R_EMOJI_ID: "<:kakeraR:1270430307346022430>",
    KAKERA_W_EMOJI_ID: "<:kakeraW:1270430305882341377>",
    KAKERA_L_EMOJI_ID: "<:kakeraL:1270430612888621067>",
    KAKERA_P_EMOJI_ID: "<:kakeraP:1270448786442948639>"
}

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

    def extract_buttons_info(self, components):
        buttons_info = []
        for component in components:
            if isinstance(component, discord.ActionRow):
                for item in component.children:
                    if isinstance(item, discord.Button):
                        buttons_info.append({
                            "label": item.label,
                            "emoji": str(item.emoji) if item.emoji else None
                        })
        return buttons_info

    async def send_private_message(self, user, content, icon, image_url):
        try:
            embed_message = discord.Embed(description=f"{icon} {content}")
            if image_url:
                embed_message.set_image(url=image_url)
            await user.send(embed=embed_message)
        except Exception as e:
            print(f"Erreur lors de l'envoi du message privé: {e}")

    def contains_specific_kakera(self, components, emoji_id):
        for component in components:
            if isinstance(component, discord.ActionRow):
                for item in component.children:
                    if isinstance(item, discord.Button) and item.emoji and item.emoji.id == emoji_id:
                        return True
        return False

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user} est prêt.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.id == MUDAE_BOT_ID:
            command_name = message.interaction.name if message.interaction else None

            if message.embeds:
                for embed in message.embeds:
                    buttons_info = self.extract_buttons_info(message.components)
                    self.log_embed(embed, message.author, command_name, buttons_info)

                    footer_text = embed.footer.text if embed.footer else ""
                    description = embed.description if embed.description else ""

                    # Conditions pour envoyer un MP pour kakeraL
                    if self.contains_specific_kakera(message.components, KAKERA_L_EMOJI_ID):
                        if "<:sw:1163913219782492220>" in description and "Appartient à gstar" in footer_text and "⭐" in footer_text:
                            user = self.bot.get_user(USER_ID)
                            await self.send_private_message(user, f"Un kakera spécial a été détecté dans un embed spécial ! [Lien vers le message]({message.jump_url})", KAKERA_ICONS[KAKERA_L_EMOJI_ID], embed.image.url)

                    # Conditions pour envoyer un MP pour kakeraP
                    if self.contains_specific_kakera(message.components, KAKERA_P_EMOJI_ID):
                        if "<:sw:1163913219782492220>" in description and "Appartient à gstar" in footer_text and "⭐" in footer_text:
                            user = self.bot.get_user(USER_ID)
                            await self.send_private_message(user, f"Un kakera spécial a été détecté dans un embed spécial ! [Lien vers le message]({message.jump_url})", KAKERA_ICONS[KAKERA_P_EMOJI_ID], embed.image.url)

                    # Conditions pour envoyer un MP pour kakeraR et kakeraW
                    if self.contains_specific_kakera(message.components, KAKERA_R_EMOJI_ID):
                        if "Appartient à gstar" in footer_text and ("🔑" in footer_text or "⭐" in footer_text):
                            user = self.bot.get_user(USER_ID)
                            await self.send_private_message(user, f"Un kakera spécial a été détecté ! [Lien vers le message]({message.jump_url})", KAKERA_ICONS[KAKERA_R_EMOJI_ID], embed.image.url)


                    if self.contains_specific_kakera(message.components, KAKERA_W_EMOJI_ID):
                        if "Appartient à gstar" in footer_text and ("🔑" in footer_text or "⭐" in footer_text):
                            user = self.bot.get_user(USER_ID)
                            await self.send_private_message(user, f"Un kakera spécial a été détecté ! [Lien vers le message]({message.jump_url})", KAKERA_ICONS[KAKERA_W_EMOJI_ID], embed.image.url)

async def setup(bot):
    await bot.add_cog(EmbedLogger(bot))