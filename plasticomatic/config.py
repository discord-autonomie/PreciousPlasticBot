# Add as many servers as you want here
CONFIGURATION = {
    "default": {
        "REGION_ROLE_COLOR": (46, 204, 113),  # Region role color (BE CAREFUL ABOUT THAT)
        "GEOLOC_DISPLAY_CHANNEL": "géoloc",  # Channel where to display the member list per region
        "GEOLOC_INPUT_CHANNELS": ["*"],  # Channels where the !geoloc command will work, * will accept all channels
        "GEOLOC_REACT_EMOJI": "✅",  # Emoji used for registering into a new region
        "DISPLAY_EMPTY_REGION": False,  # Display region which contain no members
        "MAX_USERS_PER_LINE": 3,  # Amount of users displayed per line in the region member list
        "DISPLAY_REGION_EMOJI": "🌍",  # The emoji displayed before the member list of a region
        "RUN_SYNC_ON_STARTUP": True,  # Defines whether the bot should refresh all members per region on startup
        "REMOVE_GEOLOCS_MESSAGES": True,  # Defines whether the bot should delete the !geoloc commands to avoid channel pollution
        "GEOLOC_COMMAND_NAME": "!geoloc",  # Defines the name of the geoloc command
        "GEOLOC_STRICT_MATCH": False  # Requires the region name to be exactly the same than the one defined in roles
    }
}


def get_configuration(server_id):
    if server_id in CONFIGURATION:
        return CONFIGURATION[server_id]
    else:
        return CONFIGURATION["default"]
