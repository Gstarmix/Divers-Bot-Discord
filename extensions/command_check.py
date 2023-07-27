from discord.ext import commands
from constants import *

class CommandCheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_commands = {
            MUDAE_TUTORIAL_CHANNEL_ID: ["$tuto"],
            MUDAE_WAIFUS_CHANNEL_ID: ["$w", "$h", "$m", "$wa", "$wg", "$ha", "$hg", "$ma", "$mg", "$divorce", "$dk", "$bonus", "$mu", "$ku", "$tu", "$rt", "$dk", "$skillsgm", "$vsgm", "$dsgm", "$favarenagm", "$togglekakerarolls", "$toggleclaimrolls", "$togglelikerolls", "$vote", "$daily", "$rolls", "$usestack", "$rollsleft", "$waifu", "$waifua", "$waifug", "$waifub", "$husbando", "$husbandoa", "$husbandog", "$husbandob", "$marry", "$marrya", "$marryg", "$marryb", "$mk", "$rollsup", "$setrolls", "$rdmimg", "$overview", "$mm"],
            MUDAE_TRADE_CHANNEL_ID: ["$trade", "$marryexchange", "$pinexchange", "$give", "$givekakera", "$givepin", "$mm"],
            MUDAE_WISH_CHANNEL_ID: ["$wl", "$wr", "$wp", "$wishdm", "$wish", "$wishremove", "$wishlist", "$wishremoveall", "$wishd", "$wishk", "$wishl", "$boostwish", "$wishdm", "$wishsort", "$wishpurge", "$firstwish", "$wishseries", "$wishserieslist", "$clearwishes", "$qs", "$ql", "$qw", "$disable", "$disablelist", "$serverdisable", "$dl", "$sd", "$mm"],
            MUDAE_POKESLOT_CHANNEL_ID: ["$pokemon", "$p", "$pokedex", "$pd", "$sortpkm", "$ps", "$shinyhunt", "$sh", "$release", "$r", "$autorelease", "$arl", "$pokelike", "$pl", "$pokelikelist", "$togglepokelike", "$pokeprofile", "$pokerank", "$pokeserv", "$pokemode"],
            MULTI_GAMES_CHANNEL_ID: ["$blacktea", "$greentea", "$redtea", "$yellowtea", "$mixtea", "$quiz", "$jankenpon", "$pokeduel", "/bingo", "/chifumi", "/colormind", "/jeux", "/morpion", "/pendu", "/puissance4", "$42ball", "$mm"],
            MUDAE_MODO_CHANNEL_ID: [],
            LOG_CHANNEL_ID: []
        }

        self.mod_commands = []
        for channel_id, commands in self.allowed_commands.items():
            if channel_id not in [MUDAE_MODO_CHANNEL_ID, LOG_CHANNEL_ID]:
                self.allowed_commands[MUDAE_MODO_CHANNEL_ID].extend(commands)
                self.allowed_commands[LOG_CHANNEL_ID].extend(commands)
            self.mod_commands.extend(commands)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        message_sent = False
        for command in message.content.split():
            if command.startswith('$') or command.startswith('/'):
                if command not in self.mod_commands:
                    continue
                if command in self.mod_commands and message.channel.id in [MUDAE_MODO_CHANNEL_ID, LOG_CHANNEL_ID]:
                    return
                allowed_channels = []
                for channel_id, commands in self.allowed_commands.items():
                    if command in commands:
                        allowed_channels.append(channel_id)
                if message.channel.id not in allowed_channels and not message_sent:
                    content = message.content
                    await message.delete()
                    allowed_channels_str = ', '.join([f"<#{channel_id}>" for channel_id in allowed_channels if channel_id not in [MUDAE_MODO_CHANNEL_ID, LOG_CHANNEL_ID]])
                    await message.channel.send(f"{message.author.mention} Vous avez envoyé la commande `{content}` dans le mauvais salon. Veuillez l'envoyer dans le bon salon : {allowed_channels_str}.")
                    message_sent = True
                    return

async def setup(bot):
    await bot.add_cog(CommandCheck(bot))