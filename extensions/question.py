import asyncio
import logging
from discord.ext import commands
from constants import QUESTION_BOT_CHANNEL_ID, ADMIN_ROLE_ID

# Setup logging
logging.basicConfig(level=logging.DEBUG)

class Question(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logging.debug("Bot instance created")

    async def ask_question(self, thread, message, check, max_tries=5):
        logging.debug(f"[{thread.name}] Asking question: {message}")
        await thread.send(f"<@{thread.owner.id}> {message}")
        for _ in range(max_tries):
            try:
                response = await self.bot.wait_for('message', check=check, timeout=60)
                if response.content.lower() in ['oui', 'non']:
                    logging.debug(f"[{thread.name}] Received valid response: {response.content}")
                    return response.content.lower()
            except asyncio.TimeoutError:
                logging.debug(f"[{thread.name}] Timeout while waiting for response")
                continue
        return None

    @commands.Cog.listener()
    async def on_thread_join(self, thread):
        if thread.parent.id != QUESTION_BOT_CHANNEL_ID:
            return

        logging.info(f"[{thread.name}] Bot joined thread")

        def check(m):
            return m.channel == thread and m.author == thread.owner

        def check_all(m):
            return m.channel == thread and (m.author == thread.owner or any(role.id == ADMIN_ROLE_ID for role in m.author.roles))

        response = await self.ask_question(thread, "Bonjour, je vois que vous voulez poser une question. Votre titre est-il formulé comme une question ? Répondez par 'Oui' ou 'Non'.", check)
        
        if response == 'oui':
            await thread.send(f"<@{thread.owner.id}> Très bien, votre titre semble approprié. Merci de votre coopération.")
        elif response == 'non':
            await thread.send(f"<@{thread.owner.id}> Merci de reformuler votre titre en une question compréhensible et détaillée. Par exemple, au lieu de 'Conseil stuff', vous pourriez dire 'Quelles améliorations puis-je apporter à mon stuff ?'")

        # Only allow the thread owner or an admin to post in the thread.
        while True:
            try:
                message = await self.bot.wait_for('message', check=check_all)
                logging.debug(f"[{thread.name}] Message received: {message.content}")
                if message.author != thread.owner and not any(role.id == ADMIN_ROLE_ID for role in message.author.roles):
                    try:
                        await message.delete()
                        await message.author.send("Vous n'êtes pas autorisé à écrire dans ce fil.")
                    except Exception as e:
                        logging.error(f"[{thread.name}] Error deleting message: {e}")
            except Exception as e:
                logging.error(f"[{thread.name}] Error in message processing loop: {e}")

def setup(bot):
    bot.add_cog(Question(bot))
    logging.debug("Bot cog setup")
