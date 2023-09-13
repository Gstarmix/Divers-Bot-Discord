from random import choice, random
import discord
from discord.ext import commands
from constants import *

SLASH_COMMANDS = {"wa", "ha", "ma", "wg", "hg", "mg"}
TEXT_COMMANDS = {"$w", "$h", "$m", "$wa", "$ha", "$ma", "$wg", "$hg", "$mg"}

messages = [
    {
        "title": "Comment fonctionne ce concours Mudae ?",
        "description": "- Le concours est basé sur la collecte de kakeras. Plus vous avez de kakeras, plus grande sera votre récompense.",
        "emoji": ":camera_with_flash:",
        "command_desc": "[Utilisation de la commande `$tsk`](https://image.noelshack.com/fichiers/2023/35/7/1693706903-tsk.png)"
    },
    {
        "title": "Qu'est-ce que le kakera ?",
        "description": "- Le kakera est une monnaie virtuelle dans Mudae que vous pouvez obtenir en interagissant avec des personnages. Vous pouvez également utiliser ces kakeras pour acheter des badges.",
        "emoji": ":clapper:",
        "command_desc": "[Utilisation de la commande `$kakera` ou `$k` et achat d'un badge](https://i.imgur.com/iK09CHh.gif)"
    },
    {
        "title": "Quel est l'ordre optimal pour obtenir les badges ?",
        "description": "- Pour économiser plus de 10 000 kakeras, l'ordre recommandé pour obtenir les badges est : Bronze 2, Silver 2, Gold 2 (dans l'ordre que vous préférez), suivi de Ruby 4, puis ce que vous voulez ensuite.",
        "emoji": ":camera_with_flash:",
        "command_desc": "[Ordre recommandé pour obtenir les badges](https://www.zupimages.net/up/23/37/ip79.png)"
    },
    {
        "title": "Comment obtenir le kakera arc-en-ciel ?",
        "description": "- Le **kakera arc-en-ciel** <:kakera_rainbow:1146568126465577020> apparaît aléatoirement lors des tirages de certains personnages déjà mariés. La probabilité est de 0.044%.",
        "command_desc": ":camera_with_flash: [Apparition et récupération d'un kakera arc-en-ciel](https://image.noelshack.com/fichiers/2023/35/7/1693706863-kakeraarcenciel.png)\n"
                    ":camera_with_flash: [Tableau des probabilités d'apparition des kakeras](https://image.noelshack.com/fichiers/2023/35/7/1693707489-dropratekakera.png)"
    },
    {
        "title": "Que faire si j'obtiens un kakera arc-en-ciel ?",
        "description": "- Cliquez sur le kakera pour le récupérer. Vous recevrez un montant en kakera et une image du kakera apparaîtra sur votre profil. Ensuite, envoyez-moi un message privé pour que je vous récompense en or ou €.",
        "emoji": ":camera_with_flash:",
        "command_desc": "[Utilisation de la commande `$profile` ou `pr` avec un kakera arc-en-ciel de visible](https://image.noelshack.com/fichiers/2023/35/7/1693706863-profile.png)"
    },
    {
        "title": "Comment optimiser mes gains de récompenses en or ou € ?",
        "description": "- Pour recevoir la totalité de la récompense, soit 300m ou 30€, vous devez cumuler au moins 300 000 kakeras accumulés. Vous pouvez vérifier votre total de kakeras accumulés avec la commande `$tsk`.",
        "command_desc": ":camera_with_flash: [Répartition des gains selon le total de kakeras accumulés en or](https://image.noelshack.com/fichiers/2023/36/1/1693847731-kakera-cumule.png)\n"
                        ":camera_with_flash: [Répartition des gains selon le total de kakeras accumulés en € et $](https://www.zupimages.net/up/23/37/w5vx.png)"
    },
    {
        "title": "Où sont annoncés les gagnants et peuvent-ils gagner plusieurs fois ?",
        "description": "- Les noms des gagnants sont publiés dans le salon <#1146566186012778556>. Un même joueur peut y apparaître plusieurs fois s'il a remporté plusieurs victoires, c'est-à-dire qu'il a fait apparaître et a récupéré le **kakera arc-en-ciel** <:kakera_rainbow:1146568126465577020> à plusieurs reprises.",
        "command_desc": ":camera_with_flash: [Salon des accomplissements](https://image.noelshack.com/fichiers/2023/35/7/1693706863-accomplissement.png)"
    },
    {
        "title": "Pourquoi créer une deuxième instance ?",
        "description": "- Tandis que l'Instance 1 se focalise sur la collecte de personnages, l'Instance 2 est focalisé sur le divorce de personnages afin de récupérer des kakeras et maximiser la récompense en or ou €. Les kakeras accumulés dans l'Instance 2 seront transférés vers l'Instance 1 à la fin du concours.",
        "command_desc": ":camera_with_flash: [Salons de l'instance 1 et 2](https://image.noelshack.com/fichiers/2023/35/7/1693708002-instance1-2.png)"
    },
    {
        "title": "Comment débuter avec Mudae ?",
        "description": "- Pour vous initier, lancez le tutoriel en tapant `$tuto` dans le salon <#1146892017402662912>. Après avoir terminé une sous-étape, pensez à rafraîchir le tutoriel en tapant à nouveau `$tuto` pour passer à la page suivante.",
        "command_desc": ":camera_with_flash: [Utilisation de la commande `$tuto`](https://image.noelshack.com/fichiers/2023/35/7/1693706882-tuto.png)"
    },
    {
        "title": "Comment obtenir des personnages ?",
        "description": "- Utilisez les commandes `$w`, `$h`, ou `$m` dans ce salon toutes les 1 heures pour obtenir des personnages. Vous pouvez réagir à leur embed pour vous marier toutes les 3 heures.",
        "command_desc": ":clapper: [Exemple de mariage lors d'un tirage de personnages](https://i.imgur.com/xn6cQcE.gif)"
    },
    {
        "title": "Qu'est-ce que le salon de paramétrage ?",
        "description": "- Le salon <#1146892017402662912> est votre tableau de bord pour ajuster les paramètres du jeu et gérer les kakeras.",
        "command_desc": ":camera_with_flash: [Salon mudae-settings](https://image.noelshack.com/fichiers/2023/35/7/1693706903-salonseetings.png)"
    },
    {
        "title": "Comment gagner des kakeras ?",
        "description": "- Utilisez `$divorce` et `$dk` dans <#1146892017402662912>, et réagissez aux kakeras aléatoires dans <#1146542491290579094>.",
        "command_desc": ":clapper: [Utilisation de la commande `$divorce`](https://i.imgur.com/Ot2dJQQ.gif)\n"
                    ":clapper: [Utilisation de la commande `$dk`](https://i.imgur.com/WWhfuSA.gif)\n"
                    ":clapper: [Apparition et récupération d'un kakera](https://i.imgur.com/7lSfm9I.gif)"
    },
    {
        "title": "Comment optimiser mes tirages ?",
        "description": "- Utilisez la commande `$disable` dans <#1146892017402662912> pour désactiver certaines séries et ainsi augmenter vos chances d'obtenir des personnages spécifiques. Pour plus d'informations sur les séries à désactiver, consultez [ce tableau](https://docs.google.com/spreadsheets/d/1uSn_E6bdzkQzB-tmDii1Es21tz9hvbvEckc6pGOno40/edit). Notez que l'utilisation de `$wish` réactivera un personnage d'une série que vous aviez précédemment désactivée.",
        "command_desc": ":clapper: [Utilisation de la commande `$disable`](https://i.imgur.com/Vtc6dw1.gif)"
    },
    {
        "title": "Où trouver des astuces et la liste des commandes ?",
        "description": "- Consultez le salon <#1122920806155042997> pour des astuces et des commandes utiles.",
        "command_desc": ":camera_with_flash: [Salon mudae-commands](https://image.noelshack.com/fichiers/2023/35/7/1693706863-saloncommands.png)"
    },
    {
        "title": "Où poser des questions supplémentaires ?",
        "description": "- Si vous avez des questions supplémentaires, posez-les dans le salon <#1131562652913647657>.",
        "command_desc": ":camera_with_flash: [Salon mudae-help](https://image.noelshack.com/fichiers/2023/35/7/1693706903-salonhelp.png)"
    }
]

class FaqMudae2(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"{self.bot.user.name} has connected to Discord!")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id != MUDAE_WAIFUS_CHANNEL_2_ID:
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
                    f"<@{user.id}> **`{selected_message['title']}`**\n"
                    f"{selected_message['description']}\n"
                    f"{selected_message['command_desc']}"
                )

async def setup(bot):
    await bot.add_cog(FaqMudae2(bot))
