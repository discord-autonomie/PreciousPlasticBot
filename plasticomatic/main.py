import discord
from discord import ChannelType
import os
import re
import unidecode

from plasticomatic.config import get_configuration
from plasticomatic.regions_cluster import REGIONS_CLUSTERS


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
        base_match = re.search(
            r"((?P<region_number>\d+[ab]?)-)?(?P<region_name>[\w-]+)", base_role_name
        )
        transformed_base = transform_role_name(base_match.group("region_name"))
        given_match_number = re.search(r"(?P<region_number>\d+[ab]?)", given_role_name)
        given_match_name = re.search(
            r"(?P<region_name>[a-zA-Z_ ]+)", transform_role_name(given_role_name)
        )
        if (
            given_match_name
            and given_match_name.group("region_name") == transformed_base
        ):
            return True
        elif (
            base_match
            and "region_number" in base_match.groupdict()
            and given_match_number
            and "region_number" in given_match_number.groupdict()
        ):
            print(base_match.groupdict())
            if base_match.group("region_number").lstrip(
                "0"
            ) == given_match_number.group("region_number").lstrip("0"):
                return True


def get_needed_role(guild, role_name, strict=True, allowed_roles=[]):
    for role in guild.roles:
        if len(allowed_roles) == 0 or role.name in allowed_roles:
            if strict and role.name == role_name:
                return role
            elif not strict and role_match(role.name, role_name):
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
            region_list = get_region_list(message.guild)
            strict_region_role = get_needed_role(
                message.guild,
                region_name,
                strict=config["GEOLOC_STRICT_MATCH"],
                allowed_roles=region_list,
            )
            if strict_region_role and strict_region_role.name in region_list:
                if has_user_role(message.author, strict_region_role.name):
                    msg = await message.author.send(
                        f"Vous avez été retiré du département : '{strict_region_role.name}'"
                    )
                    await message.author.remove_roles(strict_region_role)
                    if config["REMOVE_GEOLOCS_MESSAGES"]:
                        await message.delete()
                    await refresh_geoloc_list(
                        self, message.guild, strict_region_role.name
                    )
                else:
                    react_emoji = config["GEOLOC_REACT_EMOJI"]
                    msg = await message.author.send(
                        f"Cliquez sur {react_emoji} pour rejoindre le département : '{strict_region_role.name}'"
                    )
                    await msg.add_reaction(f"{react_emoji}")
                    self.msg_watcher[msg.id] = {
                        "author": message.author,
                        "guild": message.guild,
                        "message": msg,
                        "region_name": strict_region_role.name,
                    }
                    if config["REMOVE_GEOLOCS_MESSAGES"]:
                        await message.delete()
            elif config["GEOLOC_ALLOW_CLUSTERS"] and transform_role_name(
                region_name
            ) in [
                transform_role_name(cluster_name)
                for cluster_name in REGIONS_CLUSTERS.keys()
            ]:
                real_region_name = [
                    transform_role_name(cluster_name)
                    for cluster_name in REGIONS_CLUSTERS.keys()
                ].index(transform_role_name(region_name))
                real_region_name = list(REGIONS_CLUSTERS.keys())[real_region_name]
                react_emoji = config["GEOLOC_REACT_EMOJI"]
                dept_list = "\n".join([
                    f"- {dept_name}" for dept_name in REGIONS_CLUSTERS[real_region_name]
                ])
                msg = await message.author.send(
                    f"Cliquez sur {react_emoji} pour rejoindre la région : '{real_region_name}'\n"
                    f"Cette action vous fera rejoindre les départements suivants :\n```\n{dept_list}\n```"
                )
                await msg.add_reaction(f"{react_emoji}")
                self.msg_watcher[msg.id] = {
                    "author": message.author,
                    "guild": message.guild,
                    "message": msg,
                    "region_name": REGIONS_CLUSTERS[real_region_name],
                }
                if config["REMOVE_GEOLOCS_MESSAGES"]:
                    await message.delete()
            else:
                await message.channel.send(
                    "Localisation inexistante ! Si la localisation qui vous intéresse n'existe pas, n'hésitez pas à demander sa création"
                )
        else:
            region_list = get_region_list(message.guild)
            raw_data = "\n".join([f"- {region_name}" for region_name in region_list])
            await message.author.send(
                f"Tapez `{config['GEOLOC_COMMAND_NAME']} Nom département / région` pour rejoindre une région spécifique"
            )
            await message.author.send(
                f"Départements disponibles :\n```\n{raw_data}\n```"
            )
            if config["GEOLOC_ALLOW_CLUSTERS"]:
                raw_data = "\n".join(
                    [f"- {cluster_name}" for cluster_name in REGIONS_CLUSTERS]
                )
                await message.author.send(
                    f"Régions disponibles :\n```\n{raw_data}\n```"
                )

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
            guild = data["guild"]
            react_emoji = get_configuration(guild.id)["GEOLOC_REACT_EMOJI"]
            if reaction.emoji == react_emoji and user == member:
                region_name = data["region_name"]
                if isinstance(region_name, str):
                    role = get_needed_role(guild, region_name)
                    await user.send(
                        f"Bien compris, vous avez rejoint le département '{region_name}'"
                    )
                    await member.add_roles(role)
                    await refresh_geoloc_list(self, guild, region_name)
                elif isinstance(region_name, list):
                    role_list = []
                    for dept in region_name:
                        role = get_needed_role(guild, dept, strict=False)
                        role_list.append(role)
                    raw_data = "\n".join([f"- {role.name}" for role in role_list])
                    await user.send(
                        f"Bien compris, vous avez rejoint les départements suivants :\n```\n{raw_data}\n```"
                    )
                    await member.add_roles(*role_list)
                    for role in role_list:
                        await refresh_geoloc_list(self, guild, role.name)
                else:
                    raise RuntimeError(f"Invalid value for region_name : {region_name}")
                self.msg_watcher.pop(reaction.message.id)



def run():
    client = MyClient()
    if "DISCORD_TOKEN" in os.environ:
        client.run(os.environ["DISCORD_TOKEN"])
    else:
        print("Missing DISCORD_TOKEN environment variable")