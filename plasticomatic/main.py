import discord
from discord import ChannelType
import os
import re

from plasticomatic.config import get_configuration


def get_region_list(guild):
    role_list = []
    config = get_configuration(guild.id)
    for role in guild.roles:
        if role.color.to_rgb() == config["REGION_ROLE_COLOR"]:
            role_list.append(role.name)
    return role_list


def get_needed_role(guild, role_name):
    for role in guild.roles:
        if role.name == role_name:
            return role


def has_user_role(member, role_name):
    for role in member.roles:
        if role.name == role_name:
            return True
    return False


def is_channel_allowed_for_command(channel):
    config = get_configuration(channel.guild.id)
    if (
        channel.name in config["GEOLOC_INPUT_CHANNELS"]
        or "*" in config["GEOLOC_INPUT_CHANNELS"]
    ):
        return True
    else:
        return False


def generate_region_user_list(guild, region_name):
    config = get_configuration(guild.id)
    region_emoji = config["DISPLAY_REGION_EMOJI"]
    role = get_needed_role(guild, region_name)
    user_list = [f"{user.mention}" for user in role.members]
    if len(user_list) > 0 or config["DISPLAY_EMPTY_REGION"]:
        mupl = config["MAX_USERS_PER_LINE"]
        raw_user_list = "\n".join(
            [
                " | ".join(user_list[i : i + mupl])
                for i in range(0, len(user_list), mupl)
            ]
        )
        built_message = f"{region_emoji} {region_name}\n**__Membres__** :\n{'>>>' if len(user_list) > 0 else ''} {raw_user_list}\n"
        return built_message


async def refresh_geoloc_list(self, guild, refresh_region=None):
    config = get_configuration(guild.id)
    display_channel = next(
        filter(
            lambda channel: channel.name == config["GEOLOC_DISPLAY_CHANNEL"],
            guild.text_channels,
        )
    )
    region_emoji = config["DISPLAY_REGION_EMOJI"]
    region_list = get_region_list(guild)
    async for message in display_channel.history(
        limit=len(region_list) + 20, oldest_first=True
    ):
        if message.author.id == self.user.id:
            if message.content.startswith(region_emoji):
                res = re.match(
                    f"{region_emoji}\s(?P<region_name>[^\\n]+)\\n", message.content
                )
                if res:
                    region_name = res.groupdict()["region_name"]
                    if region_name in region_list and (
                        refresh_region is None or region_name == refresh_region
                    ):
                        region_user_msg = generate_region_user_list(guild, region_name)
                        if region_user_msg:
                            print("Editing region", region_name)
                            await message.edit(content=region_user_msg)
                            region_list.remove(region_name)
                        else:
                            await message.delete()
    for region in region_list:
        if refresh_region is None or region == refresh_region:
            region_user_msg = generate_region_user_list(guild, region)
            if region_user_msg:
                print("Missing region", region)
                await display_channel.send(region_user_msg)
            else:
                print("Ignore empty region", region)


async def command_geoloc(self, message):
    config = get_configuration(message.guild.id)
    if message.channel.type == ChannelType.text and is_channel_allowed_for_command(
        message.channel
    ):
        if len(message.content.split()) >= 2:
            region_name = " ".join(message.content.split()[1::])
            if region_name in get_region_list(message.guild):
                if has_user_role(message.author, region_name):
                    msg = await message.author.send(
                        f"Vous avez été retiré de la région : '{region_name}'"
                    )
                    role = get_needed_role(message.guild, region_name)
                    await message.author.remove_roles(role)
                    if config["REMOVE_GEOLOCS_MESSAGES"]:
                        await message.delete()
                    await refresh_geoloc_list(self, message.guild, region_name)
                else:
                    react_emoji = config["GEOLOC_REACT_EMOJI"]
                    msg = await message.author.send(
                        f"Cliquez sur {react_emoji} pour rejoindre la région : '{region_name}'"
                    )
                    await msg.add_reaction(f"{react_emoji}")
                    self.msg_watcher[msg.id] = {
                        "author": message.author,
                        "channel": message.channel,
                        "message": msg,
                        "region_name": region_name,
                    }
                    if config["REMOVE_GEOLOCS_MESSAGES"]:
                        await message.delete()
            else:
                await message.channel.send(
                    "Région inexistante ! Si la région qui vous intéresse n'existe pas, n'hésitez pas à demander sa création"
                )
        else:
            region_list = get_region_list(message.guild)
            raw_data = "\n".join([f"- {region_name}" for region_name in region_list])
            await message.author.send(
                f"Tapez `{config['GEOLOC_COMMAND_NAME']} Nom de la région` pour rejoindre une région spécifique"
            )
            await message.author.send(f"Régions disponibles :\n```\n{raw_data}\n```")
            if config["REMOVE_GEOLOCS_MESSAGES"]:
                await message.delete()


class MyClient(discord.Client):
    async def on_ready(self):
        print("Logged on as", self.user)
        self.msg_watcher = {}
        for guild in self.guilds:
            if get_configuration(guild.id)["RUN_SYNC_ON_STARTUP"]:
                await refresh_geoloc_list(self, guild)

    async def on_message(self, message):
        print(message.content)
        config = None
        if message.guild:
            config = get_configuration(message.guild.id)
        if message.author == self.user:
            print(message, message.content)
        if config:
            geoloc_command = config["GEOLOC_COMMAND_NAME"]
            if message.content.startswith(geoloc_command):
                await command_geoloc(self, message)

    async def on_reaction_add(self, reaction, user):
        if reaction.message.id in self.msg_watcher:
            data = self.msg_watcher[reaction.message.id]
            member = data["author"]
            channel = data["channel"]
            react_emoji = get_configuration(channel.guild.id)["GEOLOC_REACT_EMOJI"]
            if reaction.emoji == react_emoji and user == member:
                region_name = data["region_name"]
                role = get_needed_role(channel.guild, region_name)
                await user.send(
                    f"Bien compris, vous avez rejoint la région '{region_name}'"
                )
                await member.add_roles(role)
                await refresh_geoloc_list(self, channel.guild, region_name)
                self.msg_watcher.pop(reaction.message.id)


def run():
    client = MyClient()
    if "DISCORD_TOKEN" in os.environ:
        client.run(os.environ["DISCORD_TOKEN"])
    else:
        print("Missing DISCORD_TOKEN environment variable")
