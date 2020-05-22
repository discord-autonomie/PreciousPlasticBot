import asyncio
import discord
from discord import ChannelType
import os
import json
import time

from config import get_configuration

departements = json.loads(open("departements.json").read())
regions = json.loads(open("regions.json").read())


async def log(self, guild, message) :
    config = get_configuration(guild.id)
    print (time.strftime('[%d/%m/%Y %H:%M:%S]', time.localtime()), guild.name, ":", message)
    if config["LOG_CHANNEL"] :
        channel = discord.utils.find(lambda c: c.name == config["LOG_CHANNEL"], guild.channels)
        if channel :
            if guild.me.permissions_in(channel).send_messages :
                await channel.send(embed=discord.Embed(description=message, color=0x50bdfe))
            else :
                await contact_modos(self, guild, "Erreur: je n'ai pas la permission d'écrire dans "+channel.mention)
        else :
            await contact_modos(self, guild, "Erreur: le salon **#"+config["LOG_CHANNEL"]+"** n'existe pas.")


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
        await admin.send(message)


async def refresh_geoloc_list(self, guild):
    config = get_configuration(guild.id)

    display_channel = discord.utils.find(lambda m: m.name == config["GEOLOC_DISPLAY_CHANNEL"], guild.channels)

    if display_channel == None :
        await contact_modos("Erreur: je ne peux pas afficher la liste dans *"+config["GEOLOC_DISPLAY_CHANNEL"]+"* car le salon n'existe pas.")
        return
    elif not guild.me.permissions_in(display_channel).send_messages :
        await contact_modos("Erreur: je ne peux pas afficher la liste dans "+display_channel.mention+" car je n'ai pas les permission d'y écrire.")
        return

    async for message in display_channel.history(limit=len(departements) + 20, oldest_first=True):
        if message.author.id != self.user.id :
            await message.delete()
            continue

        if message.content == "": # embed 
            try :
                departement_code = message.embeds[0].title.split(" ")[0]
            except AttributeError:
                await message.delete()
                continue

            role = discord.utils.find(lambda r: r.name.startswith(departement_code+" -"), guild.roles)
            if not role :
                await contact_modos(self, guild, "le rôle **"+departement_code+" - "+departements[departement_code]["name"]+"** n'existe plus !!")
                return
            if len(role.members) == 0 :
                txt = "Personne \N{DISAPPOINTED BUT RELIEVED FACE}"
            else :
                txt = " | ".join([str(user) for user in role.members])
                if len(txt) > 2048 :
                    txt = txt[:2042]+" [...]"

            if set(txt.split(" | ")) != set(message.embeds[0].description.split(" | ")):
                await log(self, guild, "Je modifie la liste **"+departement_code+" - "+departements[departement_code]["name"]+"**")
                embed = discord.Embed(title=departement_code+" - "+departements[departement_code]["name"], description=txt, color=0x50bdfe)
                await message.edit(embed=embed)


async def set_user_region(self, member, first_time=False, rappel=0):
    if rappel == 0 :
        await log(self, member.guild, "Je demande à "+member.mention+" sa région")
    else :
        await log(self, member.guild, "Je redemande à "+member.mention+" sa région, rappel n°"+str(rappel))
    config = get_configuration(member.guild.id)

    admin = self.get_user(config["ADMIN_ID"])  # Titou : 499530093539098624

    if first_time :
        await member.send("Salut et bienvenue sur le serveur **Réseautonome** ! Je suis le robot chargé de l'accueil des nouveaux. Pour pouvoir accéder au serveur tu vas devoir me dire où tu habites et si tu es mineur ou majeur.")

    await member.send("Envoie moi le numéro de ton département (99 si tu es étranger) :")

    try :
        def check(m): return m.channel.type == discord.ChannelType.private and m.author == member
        rep = await client.wait_for('message', check=check, timeout=60*60*24)
        code = rep.content.upper()
        if len(code) == 1 : code = "0"+code
        while code not in departements and code != "99" :
            await member.send("Je ne connais pas ce numéro. Envoies `99` si tu es étranger sinon voici les numéros de départements français : "+", ".join(departements.keys()))
            rep = await client.wait_for('message', check=check, timeout=60*60*24)
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

            def checkR(reaction, user):
                return user == member and str(reaction.emoji) in reacts

            try:
                reaction, user = await client.wait_for('reaction_add', timeout=60, check=checkR)
            except asyncio.TimeoutError:
                await contact_modos(self, member.guild, member.mention+" a l'air de galérer avec avec l'ajout de rôle, vous pouvez peut-être voir pour l'aider si dans quelques minutes il n'a toujours pas de rôle")
                await member.send("Bon OK je te propose de repartir de zéro. Si vraiment tu galères tu peux contacter "+admin.mention+" qui est l'administrateur.")
                await set_user_region(self, member)
                return
            if str(reaction.emoji) == "\N{WHITE HEAVY CHECK MARK}" :
                async with member.typing():
                    for role in member.roles :
                        if role.color.to_rgb() == config["REGION_ROLE_COLOR"] :
                            await member.remove_roles(role)
                            await log(self, member.guild, "J'enlève le rôle "+role.mention+" à "+member.mention)

                        if role.color.to_rgb() == config["DEPARTEMENT_ROLE_COLOR"]:
                            await member.remove_roles(role)
                            await log(self, member.guild, "J'enlève le rôle "+role.mention+" à "+member.mention)
                            await refresh_geoloc_list(self, member.guild)

                    role = discord.utils.find(lambda r: r.name.startswith(code+" -"), member.guild.roles)
                    if role :
                        await member.add_roles(role)
                        await log(self, member.guild, "J'ajoute le rôle "+role.mention+" à "+member.mention)
                        await refresh_geoloc_list(self, member.guild)
                    else :
                        await contact_modos(self, member.guild, "Erreur, je n'ai pas pu ajouter le rôle **"+code+" - "+departement["name"]+"** à "+member.mention+" car le rôle ne semble pas exister.")

                    role = discord.utils.get(member.guild.roles, name=region["name"])
                    if role :
                        await member.add_roles(role)
                        await log(self, member.guild, "J'ajoute le rôle "+role.mention+" à "+member.mention)
                        
                    else :
                        await contact_modos(self, member.guild, "Erreur, je n'ai pas pu ajouter le rôle *"+region["name"]+"* à "+member.mention+" car le rôle ne semble pas exister.")

                    if config["REMOVE_NEWUSER_ROLE"] :
                        role = discord.utils.get(member.guild.roles, name=config["NEWUSER_ROLE_NAME"])
                        if role :
                            if role in member.roles :
                                await member.remove_roles(role)
                                await log(self, member.guild, "J'enlève le rôle "+role.mention+" à "+member.mention)

                        else :
                            await contact_modos(self, member.guild, "Erreur: le rôle "+config["NEWUSER_ROLE_NAME"]+" n'existe plus ou a changé de nom")

                await member.send("OK maintenant écris moi `mineur` si tu as moins de 18 ans et `majeur` si tu as 18 ans ou plus :")
                rep = await client.wait_for('message', check=check, timeout=60*60*24)
                while rep.content.lower() != "mineur" and rep.content.lower() != "majeur" :
                    await member.send("Je n'ai pas compris tu peux juste écrire `mineur` ou `majeur` stp.")
                    rep = await client.wait_for('message', check=check, timeout=60*60*24)
                role = discord.utils.get(member.guild.roles, name=config["YOUNG_ROLE_NAME"])
                if role :
                    if rep.content.lower() == "mineur" :
                        await member.add_roles(role)
                        await log(self, member.guild, "J'ajoute le rôle "+role.mention+" à "+member.mention)
                    elif role in member.roles :
                        await member.remove_roles(role)
                        await log(self, member.guild, "J'enlève le rôle "+role.mention+" à "+member.mention)
                    
                else :
                    await contact_modos(self, member.guild, "Erreur, je n'ai pas pu ajouter le rôle *"+config["YOUNG_ROLE_NAME"]+"* à "+member.mention+" car le rôle ne semble pas exister.")

                confirmedRole = discord.utils.get(member.guild.roles, name=config["CONFIRMED_ROLE_NAME"])
                if not confirmedRole :
                    await contact_modos(self, member.guild, "Erreur: le rôle "+config["CONFIRMED_ROLE_NAME"]+" n'existe plus donc je ne peux plus le donner...")
                else :
                    if not confirmedRole in member.roles :
                        await member.add_roles(confirmedRole)
                        await log(self, member.guild, "J'ajoute le rôle "+confirmedRole.mention+" à "+member.mention)
                        if config["WELCOME_ANOUNCE"] :
                            chan = discord.utils.get(member.guild.channels, name=config["WELCOME_CHANNEL"])
                            if chan :
                                await chan.send("Bienvenue à "+member.mention)
                            else :
                                await contact_modos(self, member.guild, "Erreur: le salon **"+config["WELCOME_CHANNEL"]+"** n'existe pas pour dire bienvenue.")


                await member.send("C'est tout bon, tu peux accéder au serveur !")


            else :
                await contact_modos(self, member.guild, member.mention+" a l'air de galérer avec avec l'ajout de rôle, vous pouvez peut-être voir pour l'aider si dans quelques minutes il n'a toujours pas de rôle")
                await member.send("Bon OK je on recommence.")
                await set_user_region(self, member)
    except asyncio.TimeoutError :
        if rappel == 0 :
            await member.send("Désolé de te déranger mais ça fait 24h que tu ne m'as pas répondu. Il faut obligatoirement répondre à ces questions pour accéder au serveur. Ceci est le premier rappel. **Si je n'ai pas de réponse dans 48h tu seras exclu du serveur.**")
            await set_user_region(self, member, rappel=1)
        if rappel == 1 :
            await member.send("Désolé de te déranger à nouveau mais ça fait 24h que tu ne m'as pas répondu. Il faut obligatoirement répondre à ces questions pour accéder au serveur. Ceci est le deuxième rappel. **Si je n'ai pas de réponse dans 24h tu seras exclu de ce serveur.**")
            await set_user_region(self, member, rappel=2)
        if rappel == 2 :
            await member.send("Cela fait 72h que tu as rejoint le serveur et tu n'as toujours pas répondu aux questions. Je vais donc t'exclure. Tu pourras néanmoins rejoindre le serveur à nouveau avec un lien d'invitation.")
            await member.kick(reason="Pas de réponses aux questions d'accueil durant 72h.")
            await log(self, member.guild, "J'ai exclu "+member.mention+" après 72h sans réponse.")

            



class MyClient(discord.Client):

    async def on_ready(self):
        for guild in self.guilds:
            if guild.id == 525004499748651018:
                continue
            await log(self, guild, "Je viens de redémarrer.")
            if get_configuration(guild.id)["RUN_SYNC_ON_STARTUP"]:
                await refresh_geoloc_list(self, guild)

    async def on_message(self, message):
        if message.guild and message.guild.id == 525004499748651018:
            return
        config = None
        if message.guild:
            config = get_configuration(message.guild.id)
        if config:
            geoloc_command = config["GEOLOC_COMMAND_NAME"]
            if message.content.startswith(geoloc_command):
                await set_user_region(self, message.author)
                if config["REMOVE_GEOLOCS_MESSAGES"]:  await message.delete()

    async def on_member_join(self, member):
        if member.guild.id == 525004499748651018:
            return
        config = get_configuration(member.guild.id)

        if config["ADD_NEWUSER_ROLE"] :
            role = discord.utils.get(member.guild.roles, name=config["NEWUSER_ROLE_NAME"])
            if role :
                if not role in member.roles :
                    await member.add_roles(role)
            else :
               await contact_modos(self, member.guild, "Ereur: le rôle "+config["NEWUSER_ROLE_NAME"]+" n'existe plus ou a changé de nom.")

        await set_user_region(self, member, first_time=True)


client = MyClient()
if "DISCORD_TOKEN" in os.environ:
    client.run(os.environ["DISCORD_TOKEN"])
else:
    print("Missing DISCORD_TOKEN environment variable")
