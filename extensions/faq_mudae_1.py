from random import choice, random
import discord
from discord.ext import commands
from constants import *

SLASH_COMMANDS = {"wa", "ha", "ma", "wg", "hg", "mg"}
TEXT_COMMANDS = {"$w", "$h", "$m", "$wa", "$ha", "$ma", "$wg", "$hg", "$mg"}

messages = [
    {
        "description": "Pour vous initier à Mudae, utilisez la commande `$tuto` dans le salon <#1132979275469955172>. Notez que ce salon n'accepte pas d'autres commandes."
    },
    {
        "description": "Utilisez les commandes `$w`, `$h`, ou `$m` dans ce salon toutes les 1 heures pour obtenir des personnages. Vous pouvez réagir à leur embed pour vous marier toutes les 3 heures."
    },
    {
        "description": "Pour avoir un aperçu de votre collection de personnages, utilisez la commande `$mm`."
    },
    {
        "description": "Accumulez des rolls resets en utilisant les commandes `$daily` et `$vote`, disponibles toutes les 20h et 12h respectivement."
    },
    {
        "description": "Échangez un roll reset contre 10 tirages en utilisant la commande `$rolls`, utilisable une fois par heure."
    },
    {
        "description": "Pour connaître tous vos temps restants, utilisez la commande `$tu`."
    },
    {
        "description": "Utilisez la commande `$wish` dans le salon <#1132365309127430224> pour augmenter le taux d'apparition des personnages souhaités."
    },
    {
        "description": "Les échanges de personnages se font dans le salon <#1132365077186613268>."
    },
    {
        "description": "Pour la gestion des kakeras, rendez-vous dans le salon <#1134516617317978133>."
    },
    {
        "description": "Les jeux secondaires de Mudae se trouvent dans le salon <#1131241853866479686>."
    },
    {
        "description": "Pour en savoir plus sur l'achat de badges avec des kakeras, utilisez la commande `$k` dans le salon <#1134516617317978133>."
    },
    {
        "description": "Lors du choix des personnages à marier, privilégiez ceux qui ont un grand nombre de kakeras dans leur embed."
    },
    {
        "description": "Accumulez des kakeras en utilisant les commandes `$divorce` et `$dk`."
    },
    {
        "description": "Utilisez la commande `$disable` dans <#1132365309127430224> pour désactiver certaines séries et ainsi augmenter vos chances d'obtenir des personnages spécifiques. Pour plus d'informations sur les séries à désactiver, consultez [ce tableau](https://docs.google.com/spreadsheets/d/1uSn_E6bdzkQzB-tmDii1Es21tz9hvbvEckc6pGOno40/edit). Notez que l'utilisation de `$wish` réactivera un personnage d'une série que vous aviez précédemment désactivée."
    },
    {
        "description": "L'utilisation de commandes slash comme `/wa`, `/ha`, etc., offre des avantages tels qu'une augmentation de 10% des chances de tirer un personnage souhaité, une augmentation de 10% du nombre de kakeras reçus, ainsi qu'un doublement du temps disponible pour se marier à un personnage ou récupérer un kakera, passant de 45 à 90 secondes."
    },
    {
        "description": "Si vous avez des questions supplémentaires, posez-les dans le salon <#1131562652913647657>."
    },
    {
        "description": "Le kakera est une monnaie virtuelle dans Mudae que vous pouvez obtenir en interagissant avec des personnages. Vous pouvez également utiliser ces kakeras pour acheter des badges."
    },
    {
        "description": "Consultez le salon <#1122920806155042997> pour des astuces et des commandes utiles."
    },
    {
        "description": "Pour jouer au jeu du tirage de Pokémon, rendez-vous dans le salon <#1122921340354179129>."
    }

]


class FaqMudae1(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user.name} has connected to Discord!")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id != MUDAE_WAIFUS_CHANNEL_ID:
            return
        
        command_type = None
        command_name = message.content
        user = message.author  # By default, use the message author

        if message.interaction:
            command_name = message.interaction.name
            command_type = 'slash'
            user = message.interaction.user  # Use the interaction user if available
        
        if command_name in SLASH_COMMANDS:
            command_type = 'slash'
        elif command_name in TEXT_COMMANDS:
            command_type = 'text'

        if command_type:
            if random() <= 0.1:
                selected_message = choice(messages)
                await message.channel.send(
                    f"<@{user.id}> {selected_message['description']}"
                )

async def setup(bot):
    await bot.add_cog(FaqMudae1(bot))
