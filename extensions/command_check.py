from discord.ext import commands
from constants import *

class CommandCheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.allowed_commands = {
            MUDAE_CONTROL_CHANNEL_ID: [],
            MUDAE_TUTORIAL_CHANNEL_ID: ["$tuto", "$chall"],
            MUDAE_WAIFUS_CHANNEL_ID: ["$w", "$h", "$m", "$wa", "$wg", "$ha", "$hg", "$ma", "$mg", "$dk", "$dailykakera", "$mu", "$ku", "$tu", "$rt", "$togglekakerarolls", "$toggleclaimrolls", "$togglelikerolls", "$vote", "$daily", "$rolls", "$usestack", "$rollsleft", "$waifu", "$waifua", "$waifug", "$waifub", "$husbando", "$husbandoa", "$husbandog", "$husbandob", "$marry", "$marrya", "$marryg", "$marryb", "$mk", "$rollsup", "$setrolls", "$rdmimg", "$overview", "$mm", "$pr", "$profile", "$ima", "$im", "$ru", "$fc", "$search", "$changeimg", "$note", "$fn", "$sm", "$firstmarry", "$fm", "$al", "$alias", "$a2", "$like", "$likelist", "$likeremove", "$lr", "$ll", "$l", "$top", "$topo", "$topl", "$topserv", "$left", "$myid", "$avatar", "$rc", "$setfooter", "$embedcolor", "$help", "$divorce", "$bonus"],
            MUDAE_TRADE_CHANNEL_ID: ["$trade", "$marryexchange", "$pinexchange", "$give", "$givekakera", "$givepin", "$mm", "$pr", "$profile", "$givek", "$givekakera", "$ima", "$im", "$search", "$changeimg", "$note", "$fn", "$sm", "$firstmarry", "$fm", "$al", "$alias", "$a2", "$like", "$likelist", "$likeremove", "$lr", "$ll", "$l", "$top", "$topo", "$topl", "$topserv", "$left", "$myid", "$avatar", "$givecustom", "$embedcolor", "$help", "$divorce", "$bonus"],
            MUDAE_WISH_CHANNEL_ID: ["$wl", "$wr", "$wp", "$wishdm", "$wish", "$wishremove", "$wishlist", "$wishremoveall", "$wishd", "$wishk", "$wishl", "$boostwish", "$wishdm", "$wishsort", "$wishpurge", "$firstwish", "$fw", "$wishseries", "$wishserieslist", "$clearwishes", "$qs", "$ql", "$qw", "$disable", "$disablelist", "$serverdisable", "$dl", "$sd", "$mm", "$pr", "$profile", "$antidisablelist", "$ad", "$antidisable", "$adl", "$enable", "$antienableall", "$antienable", "$add", "$wishk", "$ima", "$im", "$search", "$changeimg", "$note", "$fn", "$sm", "$firstmarry", "$fm", "$al", "$alias", "$a2", "$like", "$likelist", "$likeremove", "$lr", "$ll", "$l", "$top", "$topo", "$topl", "$topserv", "$left", "$myid", "$avatar", "$ae", "$togglewestern", "$embedcolor", "$help", "$divorce", "$bonus"],
            MUDAE_KAKERA_CHANNEL_ID: ["$k", "$dk", "$kl", "$lk", "$givek", "$kakera", "$kakerareward", "$togglekakerarolls", "$infokl", "$kakeraloot", "$kakeratower", "$topservk", "$tsk", "$mk", "$dailykakera", "$wishk", "$kakeradm", "$givekakera", "$badgevalue", "$togglekakerasnipe", "$kakerareact", "$kakerarefund", "$kakeraremove", "$cleankakera", "$kakerarefundall", "$kakeraremoveall", "$kakerascrap", "$givescrap", "$mm", "$pr", "$profile", "$ima", "$im", "$ku", "$tu", "$search", "$changeimg", "$note", "$fn", "$sm", "$firstmarry", "$fm", "$al", "$alias", "$a2", "$like", "$likelist", "$likeremove", "$lr", "$ll", "$l", "$top", "$topo", "$topl", "$topserv", "$left", "$badge", "$badges", "$bronze", "$silver", "$gold", "$sapphire", "$ruby", "$emerald", "$quantity", "$quality", "$myid", "$avatar", "$build", "$destroy", "$embedcolor", "$help", "$divorce", "$bonus"],
            MUDAE_POKESLOT_CHANNEL_ID: ["$pokemon", "$p", "$pokedex", "$pd", "$sortpkm", "$ps", "$shinyhunt", "$sh", "$release", "$r", "$autorelease", "$arl", "$pokelike", "$pl", "$pokelikelist", "$togglepokelike", "$pokeprofile", "$pokerank", "$pokeserv", "$pokemode", "$pr", "$profile", "$help", "$bonus"],
            MULTI_GAMES_CHANNEL_ID: ["$blacktea", "$greentea", "$redtea", "$yellowtea", "$mixtea", "$quiz", "$jankenpon", "$pokeduel", "/bingo", "/chifumi", "/colormind", "/jeux", "/morpion", "/pendu", "/puissance4", "$42ball", "$mm", "$pr", "$profile", "$ima", "$im", "$search", "$changeimg", "$fate", "$quotimage", "$beam", "$blacktea", "$note", "$fn", "$sm", "$firstmarry", "$fm", "$al", "$alias", "$a2", "$like", "$likelist", "$likeremove", "$lr", "$ll", "$l", "$top", "$topo", "$topl", "$topserv", "$left", "$myid", "$avatar", "$skills", "$embedcolor", "$help", "$divorce", "$skillsgm", "$vsgm", "$dsgm", "$favarenagm", "$bonus"],
            MUDAE_MODO_CHANNEL_ID: [],
            LOG_CHANNEL_ID: []
        }

        for accomplishment_channel_id in ACCOMPLISSEMENT_CHANNEL_ID:
            self.allowed_commands[accomplishment_channel_id] = []

        self.mod_commands = []
        for channel_id, commands in self.allowed_commands.items():
            if channel_id not in [MUDAE_MODO_CHANNEL_ID, LOG_CHANNEL_ID, MUDAE_CONTROL_CHANNEL_ID] + ACCOMPLISSEMENT_CHANNEL_ID:
                self.allowed_commands[MUDAE_MODO_CHANNEL_ID].extend(commands)
                self.allowed_commands[LOG_CHANNEL_ID].extend(commands)
                self.allowed_commands[MUDAE_CONTROL_CHANNEL_ID].extend(commands)
                for accomplishment_channel_id in ACCOMPLISSEMENT_CHANNEL_ID:
                    self.allowed_commands[accomplishment_channel_id].extend(commands)
            self.mod_commands.extend(commands)

        self.forbidden_commands = ["$lang", "$skiptuto", "$settings", "$setrare", "$settimer", "$setrolls", "$setclaim", "$shifthour", "$setinterval", "$haremlimit", "$togglereact", "$channelinstance", "$gamemode", "$servlimroul", "$togglebuttons", "$toggleclaimrolls", "$togglelikerolls", "$togglekakerarolls", "$togglehentai", "$toggledisturbing", "$toggleclaimrank", "$togglelikerank", "$serverdisable", "$togglesnipe", "$togglekakerasnipe", "$leftusers", "$restorelist", "$restore", "$channeldeny", "$channelrestrict", "$setchannel", "$restrict", "$deny", "$setpermission", "$togglesilent", "$givecustom", "$forcedivorce", "$cleanuser", "$userdivorce", "$thanos", "$thanosall", "$bitesthedust", "$clearnotes", "$clearwishes", "$resetalias2", "$fullreset", "$mk", "$togglekakera", "$badgevalue", "$cleankakera", "$givescrap", "$kakerascrap", "$addimg", "$addcustom", "$claimreact", "$kakerareact", "$wishseries", "$haremcopy", "$kakeracopy", "$limroul", "$setpermission", "$ic", "$togglekakerarolls", "$toggleclaimrolls", "$togglelikerolls"]

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        split_message = message.content.split()
        if split_message:
            command = split_message[0]
        else:
            command = ""

        if command in self.forbidden_commands:
            if any(role.id in [CHEF_SINGE_ROLE_ID, MUDAE_MODO_ROLE_ID, MUDAE_CONTROL_CHANNEL_ID] for role in message.author.roles):
                return
            await message.delete()
            await message.channel.send(f"{message.author.mention} Vous avez envoyé la commande admin `{command}`. Cette commande est réservée à l'administrateur et aux modérateurs. Je vous prie de ne pas l'utiliser.")
            return

        if command.startswith('$') or command.startswith('/'):
            if command not in self.mod_commands:
                return
            if command in self.mod_commands and (message.channel.id in [MUDAE_MODO_CHANNEL_ID, LOG_CHANNEL_ID, MUDAE_CONTROL_CHANNEL_ID] or message.channel.id in ACCOMPLISSEMENT_CHANNEL_ID):
                return
            allowed_channels = []
            for channel_id, commands in self.allowed_commands.items():
                if command in commands:
                    allowed_channels.append(channel_id)
            if message.channel.id not in allowed_channels:
                content = message.content
                await message.delete()
                allowed_channels_str = ', '.join([f"<#{channel_id}>" for channel_id in allowed_channels if channel_id not in [MUDAE_MODO_CHANNEL_ID, LOG_CHANNEL_ID, MUDAE_CONTROL_CHANNEL_ID] + ACCOMPLISSEMENT_CHANNEL_ID])
                if message.channel.id == MUDAE_TUTORIAL_CHANNEL_ID:
                    await message.channel.send(f"{message.author.mention} Vous avez envoyé la commande `{content}` dans le mauvais salon. Veuillez l'envoyer dans le bon salon : {allowed_channels_str}. Une fois cela effectué, veuillez rafraîchir le tutoriel en tapant à nouveau `$tuto` dans ce salon.")
                else:
                    await message.channel.send(f"{message.author.mention} Vous avez envoyé la commande `{content}` dans le mauvais salon. Veuillez l'envoyer dans le bon salon : {allowed_channels_str}.")
                return

async def setup(bot):
    await bot.add_cog(CommandCheck(bot))