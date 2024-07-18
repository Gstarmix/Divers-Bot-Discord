import discord
from discord.ext import commands

class SPEmbedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="sp")
    async def sp_embed(self, ctx):
        description = "**Possèdes-tu au minimum ces stats de SP pour LoL ?**\n\nPour <:4e:1190358287707811851> <:7a:1190358289721077850> <:10m:1190358294091534407> <:4am:1190358285581303899> : Full attaque et reste élément. HPMP si besoin.\n- **Pour les +30 minimum :** `100/0/30/x`\n- **Pour les +60 minimum :** `100/0/60/x`\n\nPour <:7m:1190358291084234783> : Full élément et reste attaque. HPMP si besoin.\n- **Pour les +30 minimum :** `30/0/100/x`\n- **Pour les +60 minimum :** `60/0/100/x`\n\nPour <:10m:1190358294091534407> : Mixte attaque et élément. HPMP si besoin.\n- **Pour les +30 minimum :** `75/0/75/x`\n- **Pour les +60 minimum :** `85/0/85/x`\n\nPour <:sp1e:1203290448786096138> : Full HP/MP et reste défense.\n- **Exemple :** `0/x/0/100`\n\n**Liens utiles :**\n- [Liste des cartes SP](https://www.nostar.fr/sp_cards)\n- ~~[Simulateur de carte SP](https://www.nostar.fr/sp_upgrade)~~\n- [Simulateur de points de carte SP](https://www.nostar.fr/sp_points)"

        embed = discord.Embed(description=description, color=discord.Color(0x5960c4))
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SPEmbedCog(bot))