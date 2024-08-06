from discord.ext import commands
import discord

class SPEmbedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="stuff")
    async def stuff_embed(self, ctx):
        separator = "https://www.zupimages.net/up/24/24/stl1.png"
        
        description_30 = (
            "**Stuffs requis pour le LoL +30** :\n"
            "<:escri:1264030729994506330> : **[**<:epee10:1264238406553309215> ou <:epee25a:1264238407928905791> ou <:epee25d:1264238409744908318>**]** "
            "**[**<:arba10:1264237868298014740> ou <:arba25a:1264237869384597565> ou <:arba25d:1264237870651150477>**]** "
            "**[**<:armuree10:1264238130899456205> ou <:armuree28d:1264238132799340557> ou <:armuree28a:1264238132145164338>**]**\n"
            "<:archer:1264030728958775367> : **[**<:arc10:1264238029472796702> ou <:arc25a:1264237882466500699> ou <:arc25d:1264238030567510119>**]** "
            "**[**<:dague10:1264238297564315762> ou <:dague25a:1264238362118586458> ou <:dague25d:1264238363406368850>**]** "
            "**[**<:armurea10:1264238057830355005> ou <:armurea28d:1264238060468699320> ou <:armurea28a:1264238059474653224>**]**\n"
            "<:mage:1264030727708606527> : **[**<:baba10:1264245111471083581> ou <:baba25a:1264245112578375852> ou <:baba25d:1264245113643728927>**]** "
            "**[**<:gun10:1264238493819863082> ou <:gun25a:1264238494860050443> ou <:gun25d:1264238496231723030>**]** "
            "**[**<:armurem10:1264238172146237613> ou <:armurem28d:1264238173547139122> ou <:armurem28a:1264238174713024512>**]**\n"
            "<:am:1264030726345592873> : **[**<:gant10:1264238460403974145> ou <:gant25:1264238461700018246>**]** "
            "**[**<:insigne85bl:1264238630285742172> ou <:insigne10:1264238534139711579> ou <:insigne25tank:1264286129843077160> ou <:insigne25a:1264238535297470544> ou <:insigne25d:1264238536433860618>**]** "
            "**[**<:armuream10:1264238091233661118> ou <:armuream28:1264238092127043626>**]**\n"
        )

        description_45 = (
            "**Stuffs requis pour le LoL +45** :\n"
            "<:escri:1264030729994506330> : **[**<:epee25a:1264238407928905791> ou <:epee25d:1264238409744908318> ou <:epee45:1264238411162718228> ou <:epee55:1264238412160958565>**]** "
            "**[**<:arba25a:1264237869384597565> ou <:arba25d:1264237870651150477>**]** "
            "**[**<:armuree28d:1264238132799340557> ou <:armuree28a:1264238132145164338> ou <:armuree53:1264238134237986838> ou <:armuree58:1264238167020666892>**]**\n"
            "<:archer:1264030728958775367> : **[**<:arc25a:1264237882466500699> ou <:arc25d:1264238030567510119> ou <:arc55:1264237885494788117>**]** "
            "**[**<:dague25a:1264238362118586458> ou <:dague25d:1264238363406368850> ou <:dague45:1264238365247537222>**]** "
            "**[**<:armurea28d:1264238060468699320> ou <:armurea28a:1264238059474653224> ou <:armurea53:1264238061655425096> ou <:armurea58:1264238062662320180>**]**\n"
            "<:mage:1264030727708606527> : **[**<:baba25a:1264245112578375852> ou <:baba25d:1264245113643728927> ou <:baba45:1264238289183834233> ou <:baba55:1264238290354307113>**]** "
            "**[**<:gun25a:1264238494860050443> ou <:gun25d:1264238496231723030>**]** "
            "**[**<:armurem28d:1264238173547139122> ou <:armurem28a:1264238174713024512> ou <:armurem53:1264238176076300448> ou <:armurem58:1264245105259319387>**]**\n"
            "<:am:1264030726345592873> : **[**<:gant10:1264238460403974145> ou <:gant25:1264238461700018246> ou <:gant45:1264238462878482533>**]** "
            "**[**<:insigne85bl:1264238630285742172> ou <:insigne25a:1264238535297470544> ou <:insigne25d:1264238536433860618>**]** "
            "**[**<:armuream28:1264238092127043626> ou <:armuream48:1264284628001493022> ou <:armuream53:1264238093335138315> ou <:armuream58:1264238094652145766>**]**\n"
        )

        description_65 = (
            "**Stuffs requis pour le LoL +65** :\n"
            "<:escri:1264030729994506330> : **[**<:epee45:1264238411162718228> ou <:epee60:1264238413221990481> ou <:epee65:1264238414426017834>**]** "
            "**[**<:arba60:1264237872119283772> ou <:arba65:1264237873259872337>**]** "
            "**[**<:armuree28d:1264238132799340557> ou <:armuree28a:1264238132145164338> ou <:armuree53:1264238134237986838> ou <:armuree58:1264238167020666892> ou <:armuree65:1264238168396529725>**]**\n"
            "<:archer:1264030728958775367> : **[**<:arc60:1264238031792111677> ou <:arc65:1264237888946704534>**]** "
            "**[**<:dague45:1264238365247537222> ou <:dague60:1264238368049598656> ou <:dague65:1264238369379057724>**]** "
            "**[**<:armurea28d:1264238060468699320> ou <:armurea28a:1264238059474653224> ou <:armurea53:1264238061655425096> ou <:armurea58:1264238062662320180> ou <:armurea65:1264238085168824392>**]**\n"
            "<:mage:1264030727708606527> : **[**<:baba45:1264238289183834233> ou <:baba60:1264238291503288360> ou <:baba65:1264238292941930598>**]** "
            "**[**<:gun60:1264238526912794738> ou <:gun65:1264238529039302728>**]** "
            "**[**<:armurem28d:1264238173547139122> ou <:armurem28a:1264238174713024512> ou <:armurem53:1264238176076300448> ou <:armurem58:1264245105259319387> ou <:armurem65:1264245106547097724>**]**\n"
            "<:am:1264030726345592873> : **[**<:gant60:1264238465474891777> ou <:gant65:1264238488220467271>**]** "
            "**[**<:insigne55:1264238617966936155> ou <:insigne60:1264238619011448925> ou <:insigne65:1264238620471070721>**]** "
            "**[**<:armuream28:1264238092127043626> ou <:armuream48:1264284628001493022> ou <:armuream53:1264238093335138315> ou <:armuream58:1264238094652145766> ou <:armuream65:1264238125841121321>**]**\n"
        )

        options_recommendations = (
            "**<:runearme:1264310395993194536> Tier List des runes pour les armes <:escri:1264030729994506330> <:archer:1264030728958775367> <:am:1264030726345592873> :**\n"
            "- **SL :** G + Atq + Elem **>** G + Atq **>** G + Elem **>** Atq + Elem **>** Atq\n"
            "- **Dégâts :** S-Relatif **>** Dgt CC **>=** Atq Aug **>=** Proba CC\n\n"
            
            "**<:runearme:1264310395993194536> Tier List des runes pour les armes <:mage:1264030727708606527> :**\n"
            "- **SL :** G + Elem + Atq **>** G + Elem **>** G + Atq **>** Elem + Atq **>** Elem\n"
            "- **Dégâts :** S-Relatif **>** Atq Aug\n\n"
            
            "**<:runearmure:1264310397255680152> Tier List des runes pour les armures <:escri:1264030729994506330> <:archer:1264030728958775367> <:mage:1264030727708606527> <:am:1264030726345592873> :**\n"
            "- S-Résistances si **<** Full Multi-Résistances\n"
            "- S-Effet Négatif si **>** Full Multi-Résistances\n\n"
        )

        equipment_requirements = (
            "**Ton stuff respecte-t-il au minimum ces critères pour LoL ?**\n\n"
            "- **Arme principale :**\n"
            " - Correspond à ton niveau héroïque actuel ;\n"
            " - Améliorée à +7 ;\n"
            " - SL Attaque + SL Élément ;\n"
            " - S-Relatif ou 10% Attaque Runique.\n\n"
            "- **Arme secondaire :**\n"
            " - Correspond à ton niveau héroïque actuel.\n\n"
            "- **Armure :**\n"
            " - Correspond à ton niveau héroïque actuel ;\n"
            " - Améliorée à +5 ;\n"
            " - S-Résistances ou S-Effet Négatif.\n\n"
            "**Liens utiles :**\n"
            "🔗 [Équipements et accessoires](https://www.nostar.fr/stuffs)\n"
            "🔗 [Livres](https://www.nostar.fr/books)\n"
            "🔗 [Tutoriel runes](https://www.nostar.fr/shells)\n"
            "~~🔗 [Simulateur de combinaison](https://www.nostar.fr/combine)~~"
        )


        descriptions = [description_30, description_45, description_65]
        
        for desc in descriptions:
            embed = discord.Embed(description=desc, color=discord.Color(0x5960c4))
            embed.set_image(url=separator)
            await ctx.send(embed=embed)

        options_embed = discord.Embed(description=options_recommendations, color=discord.Color(0x5960c4))
        options_embed.set_image(url=separator)
        await ctx.send(embed=options_embed)
        
        requirements_embed = discord.Embed(description=equipment_requirements, color=discord.Color(0x5960c4))
        requirements_embed.set_image(url=separator)
        await ctx.send(embed=requirements_embed)

async def setup(bot):
    await bot.add_cog(SPEmbedCog(bot))