import asyncio
import discord
from discord import ChannelType
import os
import re
import unidecode
import json

from config import get_configuration


def get_region_list(guild):
    role_list = []
    config = get_configuration(guild.id)
    for role in guild.roles:
        if role.color.to_rgb() == config["REGION_ROLE_COLOR"]:
            role_list.append(role.name)
    return role_list


def transform_role_name(role_name):
    transformed = unidecode.unidecode(role_name).lower()
    transformed = re.sub(r"\s+", " ", transformed).strip()
    transformed = transformed.replace('"', "").replace("'", "")
    transformed = transformed.replace(" ", "_").replace("-", "_")
    return transformed


def role_match(base_role_name, given_role_name):
    if transform_role_name(base_role_name) == transform_role_name(given_role_name):
        return True
    else:
        base_match = re.search(r"((?P<region_number>\d+[ab]?)-)?(?P<region_name>[\w-]+)", base_role_name)
        transformed_base = transform_role_name(base_match.group("region_name"))
        given_match_number = re.search(r"(?P<region_number>\d+[ab]?)", given_role_name)
        given_match_name = re.search(r"(?P<region_name>[a-zA-Z_ ]+)", transform_role_name(given_role_name))
        if given_match_name and given_match_name.group("region_name") == transformed_base :
            return True
        elif (
            base_match
            and "region_number" in base_match.groupdict()
            and given_match_number
            and "region_number" in given_match_number.groupdict()
        ):
            print(base_match.groupdict())
            if base_match.group("region_number").lstrip("0") == given_match_number.group("region_number").lstrip("0"):
                return True

def has_user_role(member, role_name):
    for role in member.roles:
        if role.name == role_name:
            return True
    return False


def is_channel_allowed_for_command(channel):
    config = get_configuration(channel.guild.id)
    if channel.name in config["GEOLOC_INPUT_CHANNELS"] or "*" in config["GEOLOC_INPUT_CHANNELS"] :
        return True
    else:
        return False


def generate_region_user_list(guild, region_name):
    config = get_configuration(guild.id)
    region_emoji = config["DISPLAY_REGION_EMOJI"]
    role = discord.utils.find(lambda r: r.name == region_name, guild.roles)
    user_list = [user.mention for user in role.members]
    if len(user_list) > 0 or config["DISPLAY_EMPTY_REGION"]:
        embed = discord.Embed(description=region_emoji+" "+region_name, color=0x50bdfe)
        txt = ""
        newTxt = ""
        for i in range(len(user_list)) :
            newTxt += " "+user_list[i]
            if len(newTxt) > 1000 :
                if len(embed)+len(newTxt) < 6000 :
                    embed.add_field(name=".", value=txt, inline=True)
                    txt = user_list[i]
                    newTxt = user_list[i]
                else :
                    break

            if i == len(user_list)-1:
                embed.add_field(name=".", value=newTxt, inline=True)

        #print(embed)
        return embed
    else : return False     

async def contact_modos(self, guild, message):
    config = get_configuration(guild.id)

    admin = self.get_user(config["ADMIN_ID"])
    modo_channel = discord.utils.find(lambda c: c.name == config["MODO_CHANNEL"], guild.channels)
    modo_role = discord.utils.find(lambda r: r.name == config["MODO_ROLE"], guild.roles)

    if not modo_channel :
        await admin.send("\N{WARNING SIGN} Le salon '"+config["MODO_CHANNEL"]+"' n'existe pas, je ne peux plus contacter les modérateurs alors je m'adresse à toi.")
    elif not guild.me.permissions_in(modo_channel).send_messages :
        modo_channel = None
        await admin.send("\N{WARNING SIGN} Je n'ai plus le droit d'écrire dans #"+config["MODO_CHANNEL"]+" du serveur "+guild.name+" donc je ne peux plus contacter les modérateurs donc je m'adresse à toi.")

    if modo_channel :
        if modo_role :
            await modo_channel.send(modo_role.mention+", "+message)
        else:
            await modo_channel.send("Erreur : je ne peux pas mentionner les modérateurs car le rôle @"+config["MODO_ROLE"]+" a disparu.")
            await modo_channel.send(message)
    else :
        admin.send(message)

async def refresh_geoloc_list(self, guild, refresh_region=None):
    if guild.name == "Réseautonome":
        return
    config = get_configuration(guild.id)

    display_channel = discord.utils.find(lambda m: m.name == config["GEOLOC_DISPLAY_CHANNEL"], guild.channels)

    if display_channel == None :
        await contact_modos("Erreur: je ne peux pas afficher la liste dans *"+config["GEOLOC_DISPLAY_CHANNEL"]+"* car le salon n'existe pas.")
        return
    elif not guild.me.permissions_in(display_channel).send_messages :
        await contact_modos("Erreur: je ne peux pas afficher la liste dans "+display_channel.mention+" car je n'ai pas les permission d'y écrire.")
        return

    region_emoji = config["DISPLAY_REGION_EMOJI"]
    region_list = get_region_list(guild)
    async for message in display_channel.history(limit=len(region_list) + 20, oldest_first=True):
        if message.content != "" : # no embeded message
            await message.delete()
            
        elif message.author.id == self.user.id:
            content = message.embeds[0].to_dict()["description"]
            if content.startswith(region_emoji):
                res = re.match(f"^{region_emoji}\s(?P<region_name>.+)$", content)
                if res:
                    region_name = res.groupdict()["region_name"]
                    if region_name in region_list and (refresh_region == None or region_name == refresh_region):
                        region_user_msg = generate_region_user_list(guild, region_name)
                        if region_user_msg:
                            print("Editing region", region_name)
                            await message.edit(embed=region_user_msg)
                            region_list.remove(region_name)
                        else:
                            await message.delete()
    for region in region_list:
        if refresh_region is None or region == refresh_region:
            region_user_msg = generate_region_user_list(guild, region)
            if region_user_msg:
                print("Missing region", region)
                await display_channel.send(embed=region_user_msg)
            else:
                print("Ignore empty region", region)

async def set_user_region(self, member, first_time=False):
    config = get_configuration(member.guild.id)
    departements = json.loads(open("departements.json").read())                                                  
    regions = json.loads(open("regions.json").read())

    admin = self.get_user(config["ADMIN_ID"])  # Titou : 499530093539098624

    if first_time :
        await member.send("Salut et bienvenue sur le serveur **Réseautonome** ! Je suis le robot chargé de l'accueil des nouveaux. Pour pouvoir accéder au serveur tu vas devoir me dire où tu habites et si tu es mineur ou majeur.")

    await member.send("Envoie moi le numéro de ton département (99 si tu es étranger) :")

    def check(m): return m.author == member
    rep = await client.wait_for('message', check=check)
    code = rep.content.upper()
    if len(code) == 1 : code = "0"+code
    while code not in departements and code != "99" :
        await member.send("Je ne connais pas ce numéro. Envoies `99` si tu es étranger sinon voici les numéros de départements français : "+", ".join(departements.keys()))
        rep = await client.wait_for('message', check=check)
        print (rep.content)
        code = rep.content.upper()
        if len(code) == 1 : code = "0"+code

    if code == "99" :
        await contact_modos(self, member.guild, "L'utilisateur "+member.mention+" me dit qu'il est étranger, je vous laisse lui mettre le bon rôle.")
        await member.send("OK j'ai contacté l'équipe de modérateurs ils devraient prendre contact avec toi d'ici 24h.")
    else :
        departement = departements[code]
        region = regions[departement["region_code"]]
        txt = "Je vais t'ajouter les rôles suivants :\nDépartement : **"+departement["name"]+"**\nRégion : **"+region["name"]+"**\nUtilise les réactions pour me dire si tu es d'accord."
        msg = await member.send(txt)
        reacts = ["\N{WHITE HEAVY CHECK MARK}", "\N{CROSS MARK}"]
        for r in reacts : await msg.add_reaction(r)

        def check(reaction, user):
            return user == member and str(reaction.emoji) in reacts

        try:
            reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
            if str(reaction.emoji) == "\N{WHITE HEAVY CHECK MARK}" :

                for role in member.roles :
                    if role.color.to_rgb() == config["REGION_ROLE_COLOR"] :
                        await member.remove_roles(role)
                        await refresh_geoloc_list(self, member.guild, refresh_region=role.name)

                    if role.color.to_rgb() == config["DEPARTEMENT_ROLE_COLOR"]:
                        await member.remove_roles(role)

                role = discord.utils.find(lambda r: r.name == config["CONFIRMED_ROLE_NAME"], member.guild.roles)
                if role : await member.add_roles(role)
                else : await contact_modos(self, member.guild, "Erreur: le rôle "+config["CONFIRMED_ROLE_NAME"]+" n'existe plus donc je ne peux plus le donner...")

                #name = code+" - "+departement["name"]
                right_role = None
                for role in member.guild.roles :
                    if role.name.startswith(code) : right_role = role
                #role = discord.utils.find(lambda r: r.name == name, member.guild.roles)
                if right_role : await member.add_roles(right_role)
                else : await contact_modos(self, member.guild, "Erreur, je n'ai pas pu ajouter le rôle *"+name+"* à "+member.name+" car le rôle ne semble pas exister.")

                role = discord.utils.find(lambda r: r.name == region["name"], member.guild.roles)
                if role :
                    await member.add_roles(role)
                    await refresh_geoloc_list(self, member.guild, refresh_region=region["name"])
                else :
                    await contact_modos(self, member.guild, "Erreur, je n'ai pas pu ajouter le rôle *"+region["name"]+"* à "+member.name+" car le rôle ne semble pas exister.")

                if config["REMOVE_NEWUSER_ROLE"] :
                    role = discord.utils.find(lambda r: r.name == config["NEWUSER_ROLE_NAME"], member.guild.roles)
                    if role :
                        if has_user_role(member, role.name):
                            await member.remove_roles(role)
                    else :
                        await contact_modos(self, member.guild, "Erreur: le rôle "+config["NEWUSER_ROLE_NAME"]+" n'existe plus ou a changé de nom")

                await member.send("OK maintenant écris moi `mineur` si tu as moins de 18 ans et `majeur` si tu as 18 ans ou plus :")
                def check(m): return m.author == member
                rep = await client.wait_for('message', check=check)
                while rep.content.lower() != "mineur" and rep.content.lower() != "majeur" :
                    await member.send("Je n'ai pas compris tu peux juste écrire `mineur` ou `majeur` stp.")
                    rep = await client.wait_for('message', check=check)
                role = discord.utils.find(lambda r: r.name == config["YOUNG_ROLE_NAME"], member.guild.roles)
                if role :
                    if rep.content.lower() == "mineur" : await member.add_roles(role)
                    elif role in member.roles : await member.remove_roles(role)
                    
                else :
                    await contact_modos(self, member.guild, "Erreur, je n'ai pas pu ajouter le rôle *"+config["YOUNG_ROLE_NAME"]+"* à "+member.name+" car le rôle ne semble pas exister.")

                await member.send("C'est tout bon, tu peux accéder au serveur !")

            else :
                await contact_modos(self, member.guild, member.mention+" a l'air de galérer avec avec l'ajout de rôle, vous pouvez peut-être voir pour l'aider si dans quelques minutes il n'a toujours pas de rôle")
                await member.send("Bon OK je on recommence.")
                await set_user_region(self, member)

        except asyncio.TimeoutError:
            await contact_modos(self, member.guild, member.mention+" a l'air de galérer avec avec l'ajout de rôle, vous pouvez peut-être voir pour l'aider si dans quelques minutes il n'a toujours pas de rôle")
            await member.send("Bon OK je te propose de repartir de zéro. Si vraiment tu galères tu peux contacter "+admin.mention+" qui est l'administrateur.")
            await set_user_region(self, member)



class MyClient(discord.Client):

    async def on_ready(self):
        print("Logged on as", self.user)
        print (get_configuration("default"))
        self.msg_watcher = {}
        for guild in self.guilds:
            if get_configuration(guild.id)["RUN_SYNC_ON_STARTUP"]:
                await refresh_geoloc_list(self, guild)

    async def on_message(self, message):
        config = None
        if message.guild:
            config = get_configuration(message.guild.id)
        if config:
            geoloc_command = config["GEOLOC_COMMAND_NAME"]
            if message.content.startswith(geoloc_command):
                await set_user_region(self, message.author)
                if config["REMOVE_GEOLOCS_MESSAGES"]:  await message.delete()

    async def on_member_join(self, member):
        config = get_configuration(member.guild.id)
        admin = self.get_user(config["ADMIN_ID"])

        modos = discord.utils.find(lambda c: c.name == config["MODO_CHANNEL"], member.guild.channels)
        if not modos :
            await admin.send("\N{WARNING SIGN} Le salon '"+config["MODO_CHANNEL"]+"' n'existe pas, je ne peux plus contacter les modérateurs !")
        elif member.guild.me.permissions_in(modos).send_messages == False :
            await admin.send("\N{WARNING SIGN} Je n'ai plus le droit d'écrire dans #"+config["MODO_CHANNEL"]+" du serveur "+member.guild.name+" donc je ne peux plus contacter les modérateurs !")

        if config["ADD_NEWUSER_ROLE"] :
            role = discord.utils.find(lambda r: r.name == config["NEWUSER_ROLE_NAME"], member.guild.roles)
            if role :
                if not has_user_role(member, role.name): await member.add_roles(role)
            elif modos :
                modos.send("Ereur: le rôle "+config["NEWUSER_ROLE_NAME"]+" n'existe plus ou a changé de nom.")

        await set_user_region(self, member, first_time=True)


client = MyClient()
if "DISCORD_TOKEN" in os.environ:
    client.run(os.environ["DISCORD_TOKEN"])
else:
    print("Missing DISCORD_TOKEN environment variable")
