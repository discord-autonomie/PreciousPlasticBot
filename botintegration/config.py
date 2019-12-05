# Add as many servers as you want here
CONFIGURATION = {
    "default": {
        "REGION_ROLE_COLOR": (46, 204, 113),        # Region role color (BE CAREFUL ABOUT THAT)
        "DEPARTEMENT_ROLE_COLOR": (241, 196, 15),   # Region role color (BE CAREFUL ABOUT THAT)
        "GEOLOC_DISPLAY_CHANNEL": "géoloc",         # Channel where to display the member list per region
        "GEOLOC_INPUT_CHANNELS": ["*"],             # Channels where the !geoloc command will work, * will accept all channels
        "GEOLOC_REACT_EMOJI": "✅",                 # Emoji used for registering into a new region
        "DISPLAY_EMPTY_REGION": False,              # Display region which contain no members
        "MAX_USERS_PER_LINE": 3,                    # Amount of users displayed per line in the region member list
        "DISPLAY_REGION_EMOJI": "🌍",               # The emoji displayed before the member list of a region
        "RUN_SYNC_ON_STARTUP": True,                # Defines whether the bot should refresh all members per region on startup
        "REMOVE_GEOLOCS_MESSAGES": False,           # Defines whether the bot should delete the !geoloc commands to avoid channel pollution
        "GEOLOC_COMMAND_NAME": "!geoloc",           # Defines the name of the geoloc command
        "GEOLOC_STRICT_MATCH": False,               # Requires the region name to be exactly the same than the one defined in roles
        "GEOLOC_ALLOW_CLUSTERS": True,              # Allows a user to join a cluster of regions defined in regions_cluster.py
        "ADD_NEWUSER_ROLE": True,                   # Allows to add a role to new users
        "REMOVE_NEWUSER_ROLE": True,                # Allows to remove a role when adding a new region
        "NEWUSER_ROLE_NAME": "Arrivants",           # Selects the right role to add/remove
        "CONFIRMED_ROLE_NAME": "Autonomie",     
        "YOUNG_ROLE_NAME": "Jeunes -18 ans",        
        "ADMIN_ID": 321675705010225162              # To Mp in case of a problem
    }
}


def get_configuration(server_id):
    if server_id in CONFIGURATION:
        return CONFIGURATION[server_id]
    else:
        return CONFIGURATION["default"]
