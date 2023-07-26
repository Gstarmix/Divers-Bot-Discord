from discord.ext import commands
from constants import *

class CommandCheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_commands = {
            MUDAE_WISH_CHANNEL_ID: ["$wl", "$wr", "$wp", "$wishdm", "$wish", "$wishremove", "$wishlist", "$wishremoveall", "$wishd", "$wishk", "$wishl", "$boostwish", "$wishdm", "$wishsort", "$wishpurge", "$firstwish", "$wishseries", "$wishserieslist", "$clearwishes", "$qs", "$ql", "$qw"],
            MUDAE_TRADE_CHANNEL_ID: ["$trade", "$marryexchange", "$pinexchange", "$give", "$givekakera", "$givepin"],
            MUDAE_POKESLOT_CHANNEL_ID: ["$pokemon", "$p", "$pokedex", "$pd", "$sortpkm", "$ps", "$shinyhunt", "$sh", "$release", "$r", "$autorelease", "$arl", "$pokelike", "$pl", "$pokelikelist", "$togglepokelike", "$pokeprofile", "$pokerank", "$pokeserv", "$pokemode"],
            MULTI_GAMES_CHANNEL_ID: ["$blacktea", "$greentea", "$redtea", "$yellowtea", "$mixtea", "$quiz", "$jankenpon", "$pokeduel", "/bingo", "/chifumi", "/colormind", "/jeux", "/morpion", "/pendu", "/puissance4"],
            MUDAE_WAIFUS_CHANNEL_ID: ["$w", "$h", "$m", "$wa", "$wg", "$ha", "$hg", "$ma", "$mg", "$divorce", "$dk", "$bonus", "$mu", "$ku", "$tu", "$rt", "$dk", "$skillsgm", "$vsgm", "$dsgm", "$favarenagm", "$togglekakerarolls", "$toggleclaimrolls", "$togglelikerolls", "$vote", "$daily", "$rolls", "$usestack", "$rollsleft", "$waifu", "$waifua", "$waifug", "$waifub", "$husbando", "$husbandoa", "$husbandog", "$husbandob", "$marry", "$marrya", "$marryg", "$marryb", "$mk", "$rollsup", "$setrolls"],
            MUDAE_TUTORIAL_CHANNEL_ID: ["$tuto"]
        }

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        for command in message.content.split():
            if command.startswith('$') or command.startswith('/'):
                for channel_id, commands in self.allowed_commands.items():
                    if command in commands and message.channel.id != channel_id:
                        await message.delete()
                        await message.channel.send(f"{message.author.mention} Vous avez envoyé une commande dans le mauvais salon. Veuillez l'envoyer dans le bon salon : <#{channel_id}>.")
                        return

async def setup(bot):
    await bot.add_cog(CommandCheck(bot))
