from discord.ext import commands
from datetime import datetime
import asyncio
from constants import *

DEFAULT_DURATION_MINUTES = 10

class MudaeScheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user.name} has connected to Discord!")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot and message.channel.id == MUDAE_CONTROL_CHANNEL_ID:
            await self.hide_channel()

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if not message.author.bot and message.channel.id == MUDAE_CONTROL_CHANNEL_ID:
            await self.hide_channel()

    async def hide_channel(self):
        channel = self.bot.get_channel(MUDAE_CONTROL_CHANNEL_ID)
        guild = channel.guild
        default_role = guild.default_role
        await channel.set_permissions(default_role, view_channel=False)
        self.bot.loop.create_task(self.restore_channel_visibility())

    async def restore_channel_visibility(self):
        "Task to restore channel visibility after DEFAULT_DURATION_MINUTES."
        await asyncio.sleep(DEFAULT_DURATION_MINUTES * 60)
        channel = self.bot.get_channel(MUDAE_CONTROL_CHANNEL_ID)
        await channel.set_permissions(channel.guild.default_role, view_channel=True)
        print(f"Channel visibility restored in {channel.name} at {datetime.now()}")

async def setup(bot):
    await bot.add_cog(MudaeScheduler(bot))
