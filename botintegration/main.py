import asyncio
import discord
import os
import json
import time
from datetime import datetime

from config import get_configuration

departements = json.loads(open("departements.json").read())
regions = json.loads(open("regions.json").read())


async def log(self, guild, message) :
    config = get_configuration(guild.id)
    with open("logs.txt", "a") as f : 
        f.write(time.strftime('[%d/%m/%Y %H:%M:%S] ', time.localtime())+guild.name+" : "+message+"\n")

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
        await contact_modos(self, guild, "Erreur: je ne peux pas afficher la liste dans *"+config["GEOLOC_DISPLAY_CHANNEL"]+"* car le salon n'existe pas.")
        return
    elif not guild.me.permissions_in(display_channel).send_messages :
        await contact_modos(self, guild, "Erreur: je ne peux pas afficher la liste dans "+display_channel.mention+" car je n'ai pas les permission d'y écrire.")
        return

    async for message in display_channel.history(limit=len(departements) + 30, oldest_first=True):
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
                txt = " | ".join(sorted([str(user) for user in role.members]))
                if len(txt) > 2048 :
                    txt = txt[:2042]+" [...]"

            if txt != message.embeds[0].description:
                await log(self, guild, "Je modifie la liste **"+departement_code+" - "+departements[departement_code]["name"]+"**")
                embed = discord.Embed(title=departement_code+" - "+departements[departement_code]["name"], description=txt, color=0x50bdfe)
                await message.edit(embed=embed)


async def set_user_region(self, member, first_time=False, rappel=0, just_wait=False):
    if just_wait:
        await log(self, member.guild, "J'attends une réponse de "+member.mention)
    else :
        if rappel == 0 :
            await log(self, member.guild, "Je demande à "+member.mention+" sa région")
        else :
            await log(self, member.guild, "Je redemande à "+member.mention+" sa région, rappel n°"+str(rappel))

    config = get_configuration(member.guild.id)

    admin = self.get_user(config["ADMIN_ID"])  # Titou : 499530093539098624

    try :
        if not just_wait :
            if first_time :
                await member.send("Salut et bienvenue sur le serveur **"+member.guild.name+"** ! Je suis le robot chargé de l'accueil des nouveaux. Pour pouvoir accéder au serveur tu vas devoir me dire où tu habites et si tu es mineur ou majeur.")

            await member.send("Envoie moi le numéro de ton département (99 si tu es étranger) :")

        def check(m):
            return m.channel.type == discord.ChannelType.private and m.author == member
        def checkR(reaction, user):
                return user == member and str(reaction.emoji) in reacts

        rep = await client.wait_for('message', check=check, timeout=60*60*24)
        code = rep.content.upper()
        if len(code) == 1 : code = "0"+code
        while code not in departements and code != "99" :
            await member.send("Je ne connais pas ce numéro. Envoie `99` si tu es étranger sinon voici les numéros de départements français : "+", ".join(sorted(departements.keys())))
            rep = await client.wait_for('message', check=check, timeout=60*60*24)
            code = rep.content.upper()
            if len(code) == 1 : code = "0"+code

        if code == "99" :
            await member.send("Envoie moi l'émoji correspondant à ton pays :")
            try:
                rep = await client.wait_for('message', check=check, timeout=60*60*24)

                while not rep.content.encode()[0] == 0xf0 or len(rep.content) != 2:
                    await contact_modos(self, member.guild, member.mention+" a l'air de galérer avec avec l'ajout de rôle, vous pouvez peut-être voir pour l'aider si dans quelques minutes il n'a toujours pas de rôle")
                    await member.send("Envoie juste l'émoji, clique sur la petite tête à droite et cherche ton drapeau dans la liste (tu peux taper `flag` dans la barre de recherche).")
                    rep = await client.wait_for('message', check=check, timeout=60*60*24)

            except asyncio.TimeoutError:
                await contact_modos(self, member.guild, member.mention+" a l'air de galérer avec avec l'ajout de rôle, vous pouvez peut-être voir pour l'aider si dans quelques minutes il n'a toujours pas de rôle")
                await member.send("Bon OK je te propose de repartir de zéro. Si vraiment tu galères tu peux contacter "+admin.mention+" qui est l'administrateur.")
                await set_user_region(self, member)
                return


            if rep.content.encode() == b'\xf0\x9f\x87\xab\xf0\x9f\x87\xb7':
                await member.send("Si tu es français, il faut m'envoyer le numéro de ton département.")
                await set_user_region(self, member)
                return


            role = discord.utils.find(lambda r: r.name.split(" ")[0]==rep.content, member.guild.roles)

            if role == None :           
                await contact_modos(self, member.guild, "L'utilisateur "+member.mention+" me dit qu'il est étranger mais je ne connais pas son drapeau ("+rep.content+"), je vous laisse voir avec lui et créer le rôle.")
                await member.send("Je ne connais pas ce drapeau. J'ai contacté l'équipe de modérateurs ils devraient prendre contact avec toi d'ici 24h.")
                return

            else :

                msg = await member.send("Je vais t'ajouter ce rôle : "+role.name+"\nC'est bien ça ?")
                reacts = ["\N{WHITE HEAVY CHECK MARK}", "\N{CROSS MARK}"]
                for r in reacts :
                    await msg.add_reaction(r)            

                try:
                    reaction, user = await client.wait_for('reaction_add', timeout=60, check=checkR)
                except asyncio.TimeoutError:
                    await contact_modos(self, member.guild, member.mention+" a l'air de galérer avec avec l'ajout de rôle, vous pouvez peut-être voir pour l'aider si dans quelques minutes il n'a toujours pas de rôle")
                    await member.send("Bon OK je te propose de repartir de zéro. Si vraiment tu galères tu peux contacter "+admin.mention+" qui est l'administrateur.")
                    await set_user_region(self, member)
                    return

                if str(reaction.emoji) == "\N{CROSS MARK}" :
                    await contact_modos(self, member.guild, member.mention+" a l'air de galérer avec avec l'ajout de rôle, vous pouvez peut-être voir pour l'aider si dans quelques minutes il n'a toujours pas de rôle")
                    await member.send("Bon OK je on recommence.")
                    await set_user_region(self, member)
                    return

                await member.add_roles(role)
                await log(self, member.guild, "J'ajoute le rôle "+role.mention+" à "+member.mention)

            
        else :
            departement = departements[code]
            region = regions[departement["region_code"]]
            txt = "Je vais t'ajouter les rôles suivants :\nDépartement : **"+departement["name"]+"**\nRégion : **"+region["name"]+"**\nUtilise les réactions pour me dire si tu es d'accord."
            msg = await member.send(txt)
            reacts = ["\N{WHITE HEAVY CHECK MARK}", "\N{CROSS MARK}"]
            for r in reacts :
                await msg.add_reaction(r)

            try:
                reaction, user = await client.wait_for('reaction_add', timeout=60, check=checkR)
            except asyncio.TimeoutError:
                await contact_modos(self, member.guild, member.mention+" a l'air de galérer avec avec l'ajout de rôle, vous pouvez peut-être voir pour l'aider si dans quelques minutes il n'a toujours pas de rôle")
                await member.send("Bon OK je te propose de repartir de zéro. Si vraiment tu galères tu peux contacter "+admin.mention+" qui est l'administrateur.")
                await set_user_region(self, member)
                return

            if str(reaction.emoji) == "\N{CROSS MARK}" :
                await contact_modos(self, member.guild, member.mention+" a l'air de galérer avec avec l'ajout de rôle, vous pouvez peut-être voir pour l'aider si dans quelques minutes il n'a toujours pas de rôle")
                await member.send("Bon OK je on recommence.")
                await set_user_region(self, member)
                return

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

                if role == None :
                    await contact_modos(self, member.guild, "Erreur, je n'ai pas pu ajouter le rôle **"+code+" - "+departement["name"]+"** à "+member.mention+" car le rôle ne semble pas exister.")
                    return

                await member.add_roles(role)
                await log(self, member.guild, "J'ajoute le rôle "+role.mention+" à "+member.mention)
                await refresh_geoloc_list(self, member.guild)
                    

                role = discord.utils.get(member.guild.roles, name=region["name"])
                if role == None:
                    await contact_modos(self, member.guild, "Erreur, je n'ai pas pu ajouter le rôle *"+region["name"]+"* à "+member.mention+" car le rôle ne semble pas exister.")
                    return

                await member.add_roles(role)
                await log(self, member.guild, "J'ajoute le rôle "+role.mention+" à "+member.mention)
                    
           
        if config["REMOVE_NEWUSER_ROLE"] :
            role = discord.utils.get(member.guild.roles, name=config["NEWUSER_ROLE_NAME"])

            if role == None :
                await contact_modos(self, member.guild, "Erreur: le rôle "+config["NEWUSER_ROLE_NAME"]+" n'existe plus ou a changé de nom")
                return

            if role in member.roles :
                await member.remove_roles(role)
                await log(self, member.guild, "J'enlève le rôle "+role.mention+" à "+member.mention)
                        

        await member.send("OK maintenant écris moi `mineur` si tu as moins de 18 ans et `majeur` si tu as 18 ans ou plus :")
        rep = await client.wait_for('message', check=check, timeout=60*60*24)
        while rep.content.lower() != "mineur" and rep.content.lower() != "majeur" :
            await member.send("Je n'ai pas compris tu peux juste écrire `mineur` ou `majeur` stp.")
            rep = await client.wait_for('message', check=check, timeout=60*60*24)
        role = discord.utils.get(member.guild.roles, name=config["YOUNG_ROLE_NAME"])
        if role == None :
            await contact_modos(self, member.guild, "Erreur, je n'ai pas pu ajouter le rôle *"+config["YOUNG_ROLE_NAME"]+"* à "+member.mention+" car le rôle ne semble pas exister.")
            return


        if rep.content.lower() == "mineur" :
            await member.add_roles(role)
            await log(self, member.guild, "J'ajoute le rôle "+role.mention+" à "+member.mention)
        elif role in member.roles :
            await member.remove_roles(role)
            await log(self, member.guild, "J'enlève le rôle "+role.mention+" à "+member.mention)
            
        confirmedRole = discord.utils.get(member.guild.roles, name=config["CONFIRMED_ROLE_NAME"])
        if not confirmedRole :
            await contact_modos(self, member.guild, "Erreur: le rôle "+config["CONFIRMED_ROLE_NAME"]+" n'existe plus donc je ne peux plus le donner...")
            return
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
                        return


        await member.send("C'est tout bon, tu peux accéder au serveur !")

    except asyncio.TimeoutError :
        if config["NEWUSER_ROLE_NAME"] in [r.name for r in member.roles] :
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

    except discord.Forbidden :
        await contact_modos(self, member.guild, "Je n'ai pas la permission de contacter "+member.mention+" par MP, merci de gérer ses rôles manuellement.")



class MyClient(discord.Client):

    async def on_ready(self):
        for guild in self.guilds:
            
            await log(self, guild, "Je viens de redémarrer.")

            config = get_configuration(guild.id)

            if config["RUN_SYNC_ON_STARTUP"]:
                for member in guild.members :
                    if config["NEWUSER_ROLE_NAME"] in [role.name for role in member.roles] :
                        h = (datetime.now() - member.joined_at).total_seconds()/60/60
                        if h >= 72 :
                            await member.kick(reason="Pas de signes de vie depuis "+str(int(h/24))+" jours")
                            await log(self, member.guild, "J'expulse "+member.mention)
                        else:
                            asyncio.ensure_future(set_user_region(self, member, rappel=int(h/24), just_wait=True))

                await refresh_geoloc_list(self, guild)

    async def on_message(self, message):
        config = None
        if message.guild:
            config = get_configuration(message.guild.id)
        if config:
            geoloc_command = config["GEOLOC_COMMAND_NAME"]
            if message.content.startswith(geoloc_command):
                await set_user_region(self, message.author)
                if config["REMOVE_GEOLOCS_MESSAGES"]:
                    await message.delete()

    async def on_member_join(self, member):
        config = get_configuration(member.guild.id)

        if config["ADD_NEWUSER_ROLE"] :
            role = discord.utils.get(member.guild.roles, name=config["NEWUSER_ROLE_NAME"])
            if role :
                if not role in member.roles :
                    await member.add_roles(role)
            else :
               await contact_modos(self, member.guild, "Ereur: le rôle "+config["NEWUSER_ROLE_NAME"]+" n'existe plus ou a changé de nom.")

        await set_user_region(self, member, first_time=True)

    async def on_member_remove(member):
        config = get_configuration(member.guild.id)
        if config["GOODBYE_ANOUNCE"] :
            chan = discord.utils.get(member.guild.channels, name=config["GOODBYE_CHANNEL"])
            if chan :
                await chan.send("Au revoir "+member.mention)
            else :
                await contact_modos(self, member.guild, "Erreur: le salon **"+config["GOODBYE_CHANNEL"]+"** n'existe pas pour dire au revoir.")


intents = discord.Intents.default()
intents.members = True

client = MyClient(intents=intents)
if "DISCORD_TOKEN" in os.environ:
    client.run(os.environ["DISCORD_TOKEN"])
else:
    print("Missing DISCORD_TOKEN environment variable")
