import discord
from discord.ext import commands

class RoleManagement(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name='roleadd')
    async def role_add(self, ctx: commands.Context, role: discord.Role, members: commands.Greedy[discord.Member], *, message: str):
        for member in members:
            await member.add_roles(role)
            await member.send(message)
        await ctx.send(f"Rôle {role.name} ajouté à {len(members)} membres et message envoyé.")

    @commands.command(name='roleremove')
    async def role_remove(self, ctx: commands.Context, role: discord.Role, members: commands.Greedy[discord.Member], *, message: str):
        for member in members:
            await member.remove_roles(role)
            await member.send(message)
        await ctx.send(f"Rôle {role.name} retiré de {len(members)} membres et message envoyé.")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Commande introuvable.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("Il manque des arguments requis.")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("Argument invalide.")
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("Vous n'avez pas les permissions nécessaires pour exécuter cette commande.")
        else:
            await ctx.send("Une erreur inattendue s'est produite.")
            print(f"Erreur non gérée : {error}")

    @commands.command(name='testrolemanagement')
    async def test_role_management(self, ctx: commands.Context):
        await ctx.send("RoleManagement Cog is working!")

async def setup(bot):
    await bot.add_cog(RoleManagement(bot))

