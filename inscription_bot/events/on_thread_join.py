from nextcord.ext import commands

class OnThreadJoin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_thread_join(self, thread):
        if thread.parent_id == 1131889295121199134:  # Changez cela par votre ID de salon
            async for message in thread.history(limit=200):
                if message.author != self.bot.user and message.author != thread.recipient:
                    await message.delete()

async def setup(bot):
    await bot.add_cog(OnThreadJoin(bot))
