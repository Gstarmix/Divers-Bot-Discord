from discord.ext import commands, tasks
from constants import ANGE_DEMON_CHANNEL_ID


class EmojiChanger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.change_emoji.start()

    def cog_unload(self):
        self.change_emoji.cancel()

    @tasks.loop(minutes=10)
    async def change_emoji(self):
        channel = self.bot.get_channel(ANGE_DEMON_CHANNEL_ID)
        if not channel:
            print(f"Canal avec l'ID {ANGE_DEMON_CHANNEL_ID} introuvable.")
            return

        if "👼" in channel.name:
            new_name = channel.name.replace("👼", "😈")
        else:
            new_name = channel.name.replace("😈", "👼")

        await channel.edit(name=new_name)

    @change_emoji.before_loop
    async def before_change_emoji(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(EmojiChanger(bot))
