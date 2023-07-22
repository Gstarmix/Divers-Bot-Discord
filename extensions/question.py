import asyncio
from discord.ext import commands
from constants import QUESTION_BOT_CHANNEL_ID, ADMIN_ROLE_ID

class Question(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.threads = {}

    async def ask_question(self, thread, message, check, max_tries=5):
        await thread.send(f"{thread.owner.mention} {message}")
        for _ in range(max_tries):
            try:
                response = await self.bot.wait_for('message', check=check, timeout=60)
                if response.content.lower() in ['oui', 'non']:
                    return response.content.lower()
            except asyncio.TimeoutError:
                continue
        return None

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        print(f"Message reçu de {message.author.name} dans le canal {message.channel.id}")
        if message.channel.id == QUESTION_BOT_CHANNEL_ID and not message.author.bot:
            thread = await message.channel.create_thread(name=f"Thread for {message.author.name}")
            self.threads[thread.id] = thread.owner.id
            await thread.send("This is a message from the bot.")

    @commands.Cog.listener()
    async def on_thread_join(self, thread):
        print("Event on_thread_join triggered")
        if thread.parent.id != QUESTION_BOT_CHANNEL_ID:
            return

        def check(m):
            return m.channel == thread and m.author == thread.owner

        def check_all(m):
            return m.channel == thread and (m.author == thread.owner or any(role.id == ADMIN_ROLE_ID for role in m.author.roles))

        response = await self.ask_question(thread, "Bonjour, je vois que vous voulez poser une question. Votre titre est-il formulé comme une question ? Répondez par 'Oui' ou 'Non'.", check)
        
        if response == 'oui':
            await thread.send(f"{thread.owner.mention} Très bien, votre titre semble approprié. Merci de votre coopération.")
        elif response == 'non':
            await thread.send(f"{thread.owner.mention} Merci de reformuler votre titre en une question compréhensible et détaillée. Par exemple, au lieu de 'Conseil stuff', vous pourriez dire 'Quelles améliorations puis-je apporter à mon stuff ?'")

        while True:
            try:
                message = await self.bot.wait_for('message', check=check_all)
                if message.author != thread.owner and not any(role.id == ADMIN_ROLE_ID for role in message.author.roles):
                    try:
                        await message.delete()
                        await message.author.send("Vous n'êtes pas autorisé à écrire dans ce fil.")
                    except Exception as e:
                        pass
            except Exception as e:
                pass

    @commands.Cog.listener()
    async def on_thread_create(self, thread):
        print("Event on_thread_create triggered")
        if thread.parent.id != QUESTION_BOT_CHANNEL_ID:
            return

        print(f"Un fil a été créé {thread.id}")
        self.threads[thread.id] = thread.owner.id

async def setup(bot):
    await bot.add_cog(Question(bot))
