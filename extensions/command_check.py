from discord.ext import commands
from constants import *

class CommandCheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_commands = {
            MUDAE_CONTROL_CHANNEL_ID: [],
            MUDAE_TUTORIAL_CHANNEL_ID: ["$tuto", "$chall"],
            MUDAE_WAIFUS_CHANNEL_ID: ["$w", "$h", "$m", "$wa", "$wg", "$ha", "$hg", "$ma", "$mg", "$dk", "$dailykakera", "$mu", "$ku", "$tu", "$rt", "$togglekakerarolls", "$toggleclaimrolls", "$togglelikerolls", "$vote", "$daily", "$rolls", "$usestack", "$rollsleft", "$waifu", "$waifua", "$waifug", "$waifub", "$husbando", "$husbandoa", "$husbandog", "$husbandob", "$marry", "$marrya", "$marryg", "$marryb", "$rollsup", "$setrolls", "$rdmimg", "$overview", "$mm", "$ima", "$im", "$ru", "$fc", "$search", "$changeimg", "$note", "$fn", "$sm", "$firstmarry", "$fm", "$al", "$alias", "$a2", "$top", "$topo", "$topl", "$topserv", "$topservk", "$tsk", "$left", "$myid", "$avatar", "$rc", "$setfooter", "$embedcolor", "$help", "$divorce", "$bonus", "$boostwish", "$bw", "$boostkakera", "$bk"],
            MUDAE_TRADE_CHANNEL_ID: ["$trade", "$marryexchange", "$pinexchange", "$give", "$givekakera", "$givepin", "$mm", "$givek", "$givekakera", "$ima", "$im", "$search", "$changeimg", "$note", "$fn", "$sm", "$firstmarry", "$fm", "$al", "$alias", "$a2", "$top", "$topo", "$topl", "$topserv", "$topservk", "$tsk", "$left", "$myid", "$avatar", "$givecustom", "$embedcolor", "$help", "$divorce", "$bonus"],
            MUDAE_WISH_CHANNEL_ID: ["$wl", "$wr", "$wp", "$wishdm", "$wish", "$wishremove", "$wishlist", "$wishremoveall", "$wishd", "$wishk", "$wishl", "$boostwish", "$wishdm", "$wishsort", "$wishpurge", "$firstwish", "$fw", "$wishseries", "$wishserieslist", "$clearwishes", "$qs", "$ql", "$qw", "$disable", "$disablelist", "$serverdisable", "$dl", "$sd", "$mm", "$antidisablelist", "$ad", "$antidisable", "$adl", "$enable", "$antienableall", "$antienable", "$add", "$wishk", "$ima", "$im", "$search", "$changeimg", "$note", "$fn", "$sm", "$firstmarry", "$fm", "$al", "$alias", "$a2", "$like", "$likelist", "$likeremove", "$lr", "$ll", "$l", "$top", "$topo", "$topl", "$topserv", "$topservk", "$tsk", "$left", "$myid", "$avatar", "$ae", "$togglewestern", "$embedcolor", "$help", "$divorce", "$bonus", "$boostwish", "$bw"],
            MUDAE_KAKERA_CHANNEL_ID: ["$k", "$dk", "$kl", "$lk", "$givek", "$kakera", "$kakerareward", "$togglekakerarolls", "$infokl", "$kakeraloot", "$kakeratower", "$dailykakera", "$wishk", "$kakeradm", "$givekakera", "$badgevalue", "$togglekakerasnipe", "$kakerareact", "$kakerarefund", "$kakeraremove", "$cleankakera", "$kakerarefundall", "$kakeraremoveall", "$kakerascrap", "$givescrap", "$mm", "$ima", "$im", "$ku", "$tu", "$search", "$changeimg", "$note", "$fn", "$sm", "$firstmarry", "$fm", "$al", "$alias", "$a2", "$top", "$topo", "$topl", "$topserv", "$topservk", "$tsk", "$left", "$badge", "$badges", "$bronze", "$silver", "$gold", "$sapphire", "$ruby", "$emerald", "$quantity", "$quality", "$myid", "$avatar", "$build", "$destroy", "$embedcolor", "$help", "$divorce", "$bonus", "$boostkakera", "$bk"],
            MUDAE_POKESLOT_CHANNEL_ID: ["$pokemon", "$p", "$pokedex", "$pd", "$sortpkm", "$ps", "$shinyhunt", "$sh", "$release", "$r", "$autorelease", "$arl", "$pokelike", "$pl", "$pokelikelist", "$togglepokelike", "$pokeprofile", "$pokerank", "$pokeserv", "$pokemode"],
            MULTI_GAMES_CHANNEL_ID: ["$blacktea", "$greentea", "$redtea", "$yellowtea", "$mixtea", "$quiz", "$jankenpon", "$pokeduel", "/bingo", "/chifumi", "/colormind", "/jeux", "/morpion", "/pendu", "/puissance4", "$42ball", "$mm", "$ima", "$im", "$search", "$changeimg", "$fate", "$quotimage", "$beam", "$blacktea", "$note", "$fn", "$sm", "$firstmarry", "$fm", "$al", "$alias", "$a2", "$top", "$topo", "$topl", "$topserv", "$topservk", "$tsk", "$left", "$myid", "$avatar", "$skills", "$embedcolor", "$help", "$divorce", "$skillsgm", "$vsgm", "$dsgm", "$favarenagm", "$bonus"],
            MUDAE_MODO_CHANNEL_ID: [],
            LOG_CHANNEL_ID: [],
            MUDAE_CONTROL_CHANNEL_ID: [],
            MUDAE_WAIFUS_CHANNEL_2_ID: ["$waifu", "$waifua", "$waifug", "$waifub", "$husbando", "$husbandoa", "$husbandog", "$husbandob", "$marry", "$marrya", "$marryg", "$marryb", "$w", "$h", "$m", "$wa", "$ha", "$ma", "$wg", "$hg", "$mg", "$us", "$usestack", "$tu", "$timersup", "$mu", "$marryup", "$ku", "$kakeraup", "$vote", "$daily", "$rolls", "$dk", "$dailykakera", "$rt", "$resetclaimtimer", "$fc", "$freeclaim"],
            MUDAE_SETTINGS_CHANNEL_2_ID: ["$tu", "$timersup", "$mu", "$marryup", "$ku", "$kakeraup", "$vote", "$daily", "$rolls", "$dk", "$dailykakera", "$rt", "$resetclaimtimer", "$fc", "$freeclaim"]
        }

        self.forbidden_commands = ["$lang", "$skiptuto", "$settings", "$setrare", "$settimer", "$setrolls", "$setclaim", "$shifthour", "$setinterval", "$haremlimit", "$togglereact", "$channelinstance", "$gamemode", "$servlimroul", "$togglebuttons", "$toggleclaimrolls", "$togglelikerolls", "$togglekakerarolls", "$togglehentai", "$toggledisturbing", "$toggleclaimrank", "$togglelikerank", "$serverdisable", "$togglesnipe", "$togglekakerasnipe", "$leftusers", "$restorelist", "$restore", "$channeldeny", "$channelrestrict", "$setchannel", "$restrict", "$deny", "$setpermission", "$togglesilent", "$givecustom", "$forcedivorce", "$cleanuser", "$userdivorce", "$thanos", "$thanosall", "$bitesthedust", "$clearnotes", "$clearwishes", "$resetalias2", "$fullreset", "$mk", "$togglekakera", "$badgevalue", "$cleankakera", "$givescrap", "$kakerascrap", "$addimg", "$addcustom", "$claimreact", "$kakerareact", "$wishseries", "$haremcopy", "$kakeracopy", "$limroul", "$setpermission", "$ic", "$togglekakerarolls", "$toggleclaimrolls", "$togglelikerolls"]
        
        self.mod_commands = []
        for channel_id, commands in self.allowed_commands.items():
            if channel_id not in [MUDAE_MODO_CHANNEL_ID, LOG_CHANNEL_ID, MUDAE_CONTROL_CHANNEL_ID, MUDAE_WAIFUS_CHANNEL_2_ID, MUDAE_SETTINGS_CHANNEL_2_ID]:
                self.mod_commands.extend(commands)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        split_message = message.content.split()
        command = split_message[0] if split_message else ""

        if command in self.forbidden_commands:
            if not any(role.id in [CHEF_SINGE_ROLE_ID, MUDAE_MODO_ROLE_ID] for role in message.author.roles):
                await message.delete()
                await message.channel.send(f"{message.author.mention} Vous avez envoyé la commande admin `{command}`. Cette commande est réservée à l'administrateur et aux modérateurs. Je vous prie de ne pas l'utiliser.")
            return

        if command.startswith('$') or command.startswith('/'):
            if command not in self.mod_commands:
                return

            if message.channel.id in [MUDAE_MODO_CHANNEL_ID, LOG_CHANNEL_ID, MUDAE_CONTROL_CHANNEL_ID]:
                return

            if message.channel.id == MUDAE_WAIFUS_CHANNEL_2_ID:
                if command in self.allowed_commands[MUDAE_POKESLOT_CHANNEL_ID]:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention} Vous avez envoyé la commande `{command}` dans le mauvais salon. Veuillez l'envoyer dans le bon salon : <#{MUDAE_POKESLOT_CHANNEL_ID}>.")
                    return
                if command not in self.allowed_commands[MUDAE_WAIFUS_CHANNEL_2_ID]:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention} Vous avez envoyé la commande `{command}` dans le mauvais salon. Veuillez l'envoyer dans le bon salon : <#{MUDAE_SETTINGS_CHANNEL_2_ID}>.")
                    return

            if message.channel.id == MUDAE_SETTINGS_CHANNEL_2_ID:
                if command in self.allowed_commands[MUDAE_POKESLOT_CHANNEL_ID] or command in self.forbidden_commands:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention} Vous avez envoyé la commande `{command}` dans le mauvais salon. Veuillez l'envoyer dans le bon salon : <#{MUDAE_POKESLOT_CHANNEL_ID}>.")
                    return
                elif command in self.allowed_commands[MUDAE_WAIFUS_CHANNEL_2_ID]:
                    await message.delete()
                    await message.channel.send(f"{message.author.mention} Vous avez envoyé la commande `{command}` dans le mauvais salon. Veuillez l'envoyer dans le bon salon : <#{MUDAE_WAIFUS_CHANNEL_2_ID}>.")
                    return
                else:
                    return

            allowed_channels = [channel_id for channel_id, commands in self.allowed_commands.items() if command in commands]
            allowed_channels_str = ', '.join([f"<#{channel_id}>" for channel_id in allowed_channels])

            if message.channel.id not in allowed_channels:
                await message.delete()
                wrong_channel_msg = f"{message.author.mention} Vous avez envoyé la commande `{command}` dans le mauvais salon. Veuillez l'envoyer dans le bon salon : {allowed_channels_str}."
                if message.channel.id == MUDAE_TUTORIAL_CHANNEL_ID:
                    wrong_channel_msg += " Une fois cela effectué, veuillez rafraîchir le tutoriel en tapant à nouveau `$tuto` dans ce salon."
                await message.channel.send(wrong_channel_msg)

async def setup(bot):
    await bot.add_cog(CommandCheck(bot))