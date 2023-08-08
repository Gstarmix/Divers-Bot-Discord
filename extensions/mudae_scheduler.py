
import asyncio
import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from constants import MUDAE_TOP_100_CHANNEL_ID

DEFAULT_START_HOUR = 8
DEFAULT_START_MINUTE = 5
DEFAULT_DURATION_MINUTES = 1

class MudaeScheduler(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.now().replace(hour=DEFAULT_START_HOUR, minute=DEFAULT_START_MINUTE, second=0, microsecond=0)
        self.duration = timedelta(minutes=DEFAULT_DURATION_MINUTES)
        self.disable_channel_permissions.start()
        self.execute_mudae_commands.start()
        self.enable_channel_permissions.start()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def set_start_time(self, ctx, hour: int, minute: int):
        "Set the start time for the tasks."
        self.start_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        await ctx.send(f"Start time set to {hour}:{minute}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def set_duration(self, ctx, minutes: int):
        "Set the duration for which the channel permissions are disabled."
        self.duration = timedelta(minutes=minutes)
        await ctx.send(f"Duration set to {minutes} minutes")

    @tasks.loop(hours=24)
    async def disable_channel_permissions(self):
        "Task to disable channel permissions."
        channel = self.bot.get_channel(MUDAE_TOP_100_CHANNEL_ID)
        await channel.set_permissions(self.bot.guild.default_role, send_messages=False)
        print(f"Channel permissions for {channel.name} disabled at {datetime.now()}")

    @tasks.loop(hours=24)
    async def execute_mudae_commands(self):
        "Task to execute Mudae commands."
        channel = self.bot.get_channel(MUDAE_TOP_100_CHANNEL_ID)
        await channel.send("$toput $1")
        await channel.send("$toput $2")
        print(f"Mudae commands executed in {channel.name} at {datetime.now()}")

    @tasks.loop(hours=24)
    async def enable_channel_permissions(self):
        "Task to enable channel permissions after the configured duration."
        await asyncio.sleep(self.duration.total_seconds())
        channel = self.bot.get_channel(MUDAE_TOP_100_CHANNEL_ID)
        await channel.set_permissions(self.bot.guild.default_role, send_messages=True)
        print(f"Channel permissions for {channel.name} enabled at {datetime.now()}")

    @disable_channel_permissions.before_loop
    async def before_disable_channel_permissions(self):
        await self.bot.wait_until_ready()
        now = datetime.now()
        delta = self.start_time - now
        if delta.total_seconds() < 0:
            delta += timedelta(days=1)
        await asyncio.sleep(delta.total_seconds())

    @execute_mudae_commands.before_loop
    async def before_execute_mudae_commands(self):
        await self.bot.wait_until_ready()
        now = datetime.now()
        delta = self.start_time + timedelta(minutes=DEFAULT_DURATION_MINUTES) - now
        if delta.total_seconds() < 0:
            delta += timedelta(days=1)
        await asyncio.sleep(delta.total_seconds())

    @enable_channel_permissions.before_loop
    async def before_enable_channel_permissions(self):
        await self.bot.wait_until_ready()
        now = datetime.now()
        delta = self.start_time + self.duration + timedelta(minutes=DEFAULT_DURATION_MINUTES) - now
        if delta.total_seconds() < 0:
            delta += timedelta(days=1)
        await asyncio.sleep(delta.total_seconds())

def setup(bot):
    bot.add_cog(MudaeScheduler(bot))
