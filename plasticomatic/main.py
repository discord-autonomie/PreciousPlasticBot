import discord
import os
from threading import Thread

def get_region_list(channel):
    role_list = []
    for role in channel.guild.roles:
        if role.color.to_rgb() == (46, 204, 113):
            role_list.append(role.name)
    return role_list

def get_needed_role(channel, role_name):
    for role in channel.guild.roles:
        if role.name == role_name:
            return role

def has_user_role(member, role_name):
    for role in member.roles:
        if role.name == role_name:
            return True
    return False

class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)
        self.msg_watcher = {}

    async def on_message(self, message):
        if message.author == self.user:
            print(message, message.content)
        if message.content == 'ping':
            await message.channel.send('pong')
        if message.content.startswith("!geoloc"):
            if len(message.content.split()) >= 2:
                region_name = " ".join(message.content.split()[1::])
                if region_name in get_region_list(message.channel):
                    if has_user_role(message.author, region_name):
                        msg = await message.author.send(f"Vous avez été retiré de la région : '{region_name}'")
                        role = get_needed_role(message.channel, region_name)
                        await message.author.remove_roles(role)
                        await message.delete()
                    else:
                        msg = await message.author.send(f"Cliquez sur ✅ pour rejoindre la région : '{region_name}'")
                        await msg.add_reaction("✅")
                        self.msg_watcher[msg.id] = {
                            "author": message.author, 
                            "channel": message.channel, 
                            "message": msg,
                            "region_name": region_name
                        }
                        await message.delete()
                else:
                    await message.channel.send("Région inexistante ! Si la région qui vous intéresse n'existe pas, n'hésitez pas à demander sa création")
            else:
                region_list = get_region_list(message.channel)
                raw_data = "\n".join([f"- {region_name}" for region_name in region_list])
                await message.channel.send("Tapez '!geoloc <Nom de la région>' pour rejoindre une région spécifique")
                await message.channel.send(f"Régions disponibles :\n```\n{raw_data}\n```")

    async def on_reaction_add(self, reaction, user):
        if reaction.message.id in self.msg_watcher and reaction.emoji == "✅" and user == self.msg_watcher[reaction.message.id]["author"]:
            data = self.msg_watcher.pop(reaction.message.id)
            region_name = data["region_name"]
            channel = data["channel"]
            member = data["author"]
            role = get_needed_role(channel, region_name)
            await user.send(f"Bien compris, vous avez rejoint la région '{region_name}'")
            await member.add_roles(role)

def run():
    client = MyClient()
    if "DISCORD_TOKEN" in os.environ:
        client.run(os.environ["DISCORD_TOKEN"])
    else:
        print("Missing DISCORD_TOKEN environment variable")