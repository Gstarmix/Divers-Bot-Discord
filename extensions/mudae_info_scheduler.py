from random import shuffle
import asyncio
import datetime
from discord.ext import commands
import json
from constants import *


class MudaeInfoScheduler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_message_index = None
        self.delay_minutes = 45


        with open('extensions/mudae_info_scheduler.json', 'r', encoding='utf-8') as f:
            self.shuffled_messages = json.load(f)

        shuffle(self.shuffled_messages)
        
        self.bot.loop.create_task(self.send_periodic_message())

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user.name} has connected to Discord!")

    async def send_periodic_message(self):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(MUDAE_SETTINGS_CHANNEL_2_ID)

        now = datetime.datetime.utcnow()

        # Détermine le prochain xx:30 le plus proche
        next_time = now.replace(minute=30, second=0, microsecond=0)
        if now.minute >= 30:
            next_time += datetime.timedelta(hours=1)

        wait_seconds = (next_time - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        while not self.bot.is_closed():
            await asyncio.sleep(self.delay_minutes * 60)
            
            if self.last_message_index is None or self.last_message_index >= len(self.shuffled_messages) - 1:
                self.last_message_index = 0
                shuffle(self.shuffled_messages)
            else:
                self.last_message_index += 1

            selected_message = self.shuffled_messages[self.last_message_index]
            await channel.send(
                f"**`{selected_message['title']}`**\n"
                f"{selected_message['description']}\n"
                f"{selected_message['command_desc']}"
            )


async def setup(bot):
    await bot.add_cog(MudaeInfoScheduler(bot))
