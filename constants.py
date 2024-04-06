# Channels

INSCRIPTION_CHANNEL_ID = 1131690975190855680
INSCRIPTION_INVALIDATION_CHANNEL_ID = 1132405464190165053
INSCRIPTION_VALIDATION_CHANNEL_ID = 1131725984253616230

LOG_CHANNEL_ID = 1134215338347737219
MEMES_CHANNEL_ID = 724265897794994186
MUDAE_CONTROL_CHANNEL_ID = 1152565814755602543
MUDAE_HELP_CHANNEL_ID = 1131562652913647657
MUDAE_IDEAS_CHANNEL_ID = 1151889033266483320
MUDAE_MODO_CHANNEL_ID = 1134213499464192190
MUDAE_POKESLOT_CHANNEL_ID = 1133868708528398397
MUDAE_SETTINGS_CHANNEL_2_ID = 1152565945341050880
MUDAE_SETTINGS_CHANNEL_ID = 1152567478669561897
MUDAE_WAIFUS_CHANNEL_2_ID = 1152565875958890516
MUDAE_WAIFUS_CHANNEL_ID = 1133868580342087761

PRESENTATION_CHANNEL_ID = 1183375149131628574
QUESTION_CHANNEL_ID = 1055993732505284690
RECHERCHE_KELKIN_CHANNEL_ID = 995990482167545856
SIGNALEMENT_VENTES_ID = 1217666437921898537
SUGGESTION_FAFA_CHANNEL_ID = 1126957845485735996
SUGGESTION_GSTAR_CHANNEL_ID = 809772368473882646
VIDEO_CHANNEL_ID = 709653621393850438
VDO_VDM_CHANNEL_ID = 775071451606155274

COMMERCES_ID = 1219314731022684171

VENTES_COSMOS_ID = 1217579779327397939
ACHATS_COSMOS_ID = 1219026259351437465

VENTES_NOSFIRE_ID = 1219026299637465234
ACHATS_NOSFIRE_ID = 1219026360672981165

ACTIVITES_ID = 1219320695578820758

FAMILLES_COSMOS_ID = 1219321701809127505
RAIDS_COSMOS_ID = 1219331804436238406
LEVELING_COSMOS_ID = 1219332516578594886
GROUPE_XP_COSMOS_ID = 1219332856942432400

FAMILLES_NOSFIRE_ID = 1219321732771610694
RAIDS_NOSFIRE_ID = 1219331769287966760
LEVELING_NOSFIRE_ID = 1219332588318228622
GROUPE_XP_NOSFIRE_ID = 1219333053139386389


ACTIVITY_CHANNELS = {
    "présentation-famille_cosmos": {"id": FAMILLES_COSMOS_ID, "timer_hours": 0.01},
    "recherche-famille_cosmos": {"id": FAMILLES_COSMOS_ID, "timer_hours": 0.01},
    "recherche-raid_cosmos": {"id": RAIDS_COSMOS_ID, "timer_hours": 0.01},
    "recherche-leveling_cosmos": {"id": LEVELING_COSMOS_ID, "timer_hours": 0.01},
    "recherche-groupe-xp_cosmos": {"id": GROUPE_XP_COSMOS_ID, "timer_hours": 0.01},
    "présentation-famille_nosfire": {"id": FAMILLES_NOSFIRE_ID, "timer_hours": 0.01},
    "recherche-famille_nosfire": {"id": FAMILLES_NOSFIRE_ID, "timer_hours": 0.01},
    "recherche-raid_nosfire": {"id": RAIDS_NOSFIRE_ID, "timer_hours": 1},
    "recherche-leveling_nosfire": {"id": LEVELING_NOSFIRE_ID, "timer_hours": 0.01},
    "recherche-groupe-xp_nosfire": {"id": GROUPE_XP_NOSFIRE_ID, "timer_hours": 0.01},
}

ACTIVITY_TYPES = {"présentation-famille", "recherche-famille", "recherche-raid", "recherche-leveling", "recherche-groupe-xp"}

TRADE_CHANNELS = {
    "achat_cosmos": {"id": ACHATS_COSMOS_ID, "timer_hours": 0.01},
    "vente_cosmos": {"id": VENTES_COSMOS_ID, "timer_hours": 0.01},
    "achat_nosfire": {"id": ACHATS_NOSFIRE_ID, "timer_hours": 0.01},
    "vente_nosfire": {"id": VENTES_NOSFIRE_ID, "timer_hours": 0.01},
}

LOCKED_CHANNELS_1 = {COMMERCES_ID, VENTES_COSMOS_ID, ACHATS_COSMOS_ID, VENTES_NOSFIRE_ID, ACHATS_NOSFIRE_ID}

LOCKED_CHANNELS_2 = {FAMILLES_COSMOS_ID, RAIDS_COSMOS_ID, LEVELING_COSMOS_ID, GROUPE_XP_COSMOS_ID, FAMILLES_NOSFIRE_ID, RAIDS_NOSFIRE_ID, LEVELING_NOSFIRE_ID, GROUPE_XP_NOSFIRE_ID}


RAID_ROLE_MAPPING = {
    "cosmos": {
        "Evènement": "1219914901519073321",
        "Namaju": "1093937218445398166",
        "Poule": "1093937216813809794",
        "Cuby": "1093937219728846959",
        "Ginseng": "1095042505516531802",
        "Castra": "1102463563420926022",
        "Araignée": "1116784746287071282",
        "Slade": "1116784762871357571",
        "Fafnir": "718960085920907365",
        "Yertirand": "718959620831576076",
        "Draco": "718959617006239864",
        "Glacerus": "718959617278869514",
        "Laurena": "718959620319870983",
        "Ibrahim": "718959615613599967",
        "Kertos": "718959447208230963",
        "Valakus": "718959581706977341",
        "Grenigas": "718959448491819058",
        "Zénas": "718959445496955010",
        "Erenia": "718958893950042134",
        "Fernon": "718959447048847460",
        "Kirollas": "718959618474246164",
        "Carno": "718959619267100834",
        "Bélial": "718959619426222172",
        "Paimon": "730355445839036467",
        "Paimon ressuscité": "867333150978736158",
        "Valehir": "920365045794365440",
        "Alzanor": "920365332605071371",
        "Asgobas": "1052818238850994227",
        "Pollutus": "1184041291747696640",
        "Arma": "1184041296797650944"
    },
    "nosfire": {
        "Evènement": "1219914896783839253",
        "Namaju": "1219914893634048091",
        "Poule": "1219915902397714432",
        "Cuby": "1219915760370061402",
        "Ginseng": "1219915759162232883",
        "Castra": "1219915758117589012",
        "Araignée": "1219915757689901106",
        "Slade": "1219915756087541853",
        "Fafnir": "1219915755634688050",
        "Yertirand": "1219915754695299102",
        "Draco": "1219915753592193115",
        "Glacerus": "1219915752413597727",
        "Laurena": "1219915751780126770",
        "Ibrahim": "1219915751012438016",
        "Kertos": "1219915750035427390",
        "Valakus": "1219915749200498718",
        "Grenigas": "1219915748038672425",
        "Zénas": "1219915747522908160",
        "Erenia": "1219915746851815517",
        "Fernon": "1219915745853440000",
        "Kirollas": "1219915745048268800",
        "Carno": "1219915743982784574",
        "Bélial": "1219915743416553472",
        "Paimon": "1219915742624088115",
        "Paimon ressuscité": "1219915741805936661",
        "Valehir": "1219915741046898698",
        "Alzanor": "1219915739943931904",
        "Asgobas": "1219915739796869150",
        "Pollutus": "1219915738073141249",
        "Arma": "1219915736806326302",
    }
}


RAIDS_LIST = ["Evènement", "Arma", "Pollutus", "Asgobas", "Alzanor", "Valehir", "Paimon ressuscité", "Paimon", "Bélial", "Carno", "Kirollas", "Fernon", "Erenia", "Zénas", "Grenigas", "Valakus", "Kertos", "Ibrahim", "Laurena", "Glacerus", "Draco", "Yertirand", "Fafnir", "Slade", "Araignée", "Castra", "Ginseng", "Cuby", "Poule", "Namaju"]

RAIDS_EMOTES = {
    "Evènement": "<:iconeevent:1225984383098294272>",
    "Arma": "<:arma:1225981400339976303>",
    "Pollutus": "<:pollutus:1225981401367707669>",
    "Asgobas": "<:raidasgobas:1052817952585568316>",
    "Alzanor": "<:Alzanor:920364236792823818>",
    "Valehir": "<:Valehir:920364236847321088>",
    "Paimon ressuscité": "<:Paimonressucite:867332592046702592>",
    "Paimon": "<:Paimon:730356031506612274>",
    "Bélial": "<:Belial:719111138595438623>",
    "Carno": "<:Carno:719111138419408907>",
    "Kirollas": "<:Kirollas:719111138566078524>",
    "Fernon": "<:Fernon:971225082754109440>",
    "Erenia": "<:Erenia:719111138427666486>",
    "Zénas": "<:Zenas:719111138247442466>",
    "Grenigas": "<:Grenigas:719111138540781588>",
    "Valakus": "<:Valakus:719111138620735560>",
    "Kertos": "<:Kertos:719111138545238096>",
    "Ibrahim": "<:Ibrahim:971225789372719156>",
    "Laurena": "<:Laurena:719111138276540437>",
    "Glacerus": "<:Glacerus:719111138360426567>",
    "Draco": "<:Draco:719111558952648715>",
    "Yertirand": "<:Yertirand:719111138620735540>",
    "Fafnir": "<:Fafnir:719111138234859542>",
    "Slade": "<:Slade:739077081018794037>",
    "Araignée": "<:Araigne:739077081148817430>",
    "Castra": "<:Castra:739077081354338365>",
    "Ginseng": "<:Ginseng:739077080976982028>",
    "Cuby": "<:Cuby:739077081396150343>",
    "Poule": "<:Poule:739077081442418728>",
    "Namaju": "<:Namaju:739077098307715154>"
}

CHANNELS_NAME_TO_ID = {
    "LOG_CHANNEL_ID": LOG_CHANNEL_ID,
    "MUDAE_CONTROL_CHANNEL_ID": MUDAE_CONTROL_CHANNEL_ID,
    "MUDAE_HELP_CHANNEL_ID": MUDAE_HELP_CHANNEL_ID,
    "MUDAE_IDEAS_CHANNEL_ID": MUDAE_IDEAS_CHANNEL_ID,
    "MUDAE_MODO_CHANNEL_ID": MUDAE_MODO_CHANNEL_ID,
    "MUDAE_POKESLOT_CHANNEL_ID": MUDAE_POKESLOT_CHANNEL_ID,
    "MUDAE_SETTINGS_CHANNEL_2_ID": MUDAE_SETTINGS_CHANNEL_2_ID,
    "MUDAE_SETTINGS_CHANNEL_ID": MUDAE_SETTINGS_CHANNEL_ID,
    "MUDAE_WAIFUS_CHANNEL_2_ID": MUDAE_WAIFUS_CHANNEL_2_ID,
    "MUDAE_WAIFUS_CHANNEL_ID": MUDAE_WAIFUS_CHANNEL_ID,
}

# Roles

CHEF_SINGE_ROLE_ID = 684742675726991436
GARDIEN_GANG_ROLE_ID = 923190695190233138
GARDIEN_YERTI_ROLE_ID = 1036402538620129351
INSCRIPTION_ROLE_ID = 1132681566213111818
MUDAE_MODO_ROLE_ID = 1138210604977508422
PRESENTATION_ROLE_ID = 1132655709268475905
QUESTION_ROLE_ID = 1131336486101467176
ROLE1_ID_FAFA = 923002565602467840
ROLE2_ID_FAFA = 1056284304801550396
ROLE3_ID_FAFA = 1056284337261256764
ROLE4_ID_FAFA = 1056284371885248573
ROLE5_ID_FAFA = 1056284345633095771


# Guilds

GUILD_ID_FAFA = 922991241443041300
GUILD_ID_GSTAR = 684734347177230451

# Users

GSTAR_USER_ID = 200750717437345792
