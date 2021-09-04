# Add as many servers as you want here
CONFIGURATION = {
    "default": {
        "REGION_ROLE_COLOR": (46, 204, 113),        # Region role color (BE CAREFUL ABOUT THAT)
        "DEPARTEMENT_ROLE_COLOR": (241, 196, 15),   # Departement role color (BE CAREFUL ABOUT THAT)
        "COUNTRY_COLOR": (245,202,10),              # Country role color (BE CAREFUL ABOUT THAT)
        "GEOLOC_DISPLAY_CHANNEL": "géoloc",         # Channel where to display the member list per region
        "GEOLOC_INPUT_CHANNELS": ["*"],             # Channels where the !geoloc command will work, * will accept all channels
        "DISPLAY_EMPTY_REGION": False,              # Display region which contain no members
        "RUN_SYNC_ON_STARTUP": True,                # Defines whether the bot should refresh all members per region on startup
        "REMOVE_GEOLOCS_MESSAGES": False,           # Defines whether the bot should delete the !geoloc commands to avoid channel pollution
        "GEOLOC_COMMAND_NAME": "!geoloc",           # Defines the name of the geoloc command
        "ADD_NEWUSER_ROLE": True,                   # Allows to add a role to new users
        "REMOVE_NEWUSER_ROLE": True,                # Allows to remove a role when adding a new region
        "NEWUSER_ROLE_NAME": "Arrivant",            # Selects the right role to add/remove
        "CONFIRMED_ROLE_NAME": "Autonomie",     
        "YOUNG_ROLE_NAME": "Jeunes -18 ans",        
        "ADMIN_ID": 321675705010225162,             # To MP in case of a problem
        "MODO_CHANNEL": "infos-modérateurs",
        "MODO_ROLE": "Modérateurs",
        "WELCOME_ANOUNCE": True,
        "WELCOME_CHANNEL": "blabla-libre-autonomie",
        "GOODBYE_ANOUNCE": True,
        "GOODBYE_CHANNEL": "blabla-libre-autonomie",
        "LOG_CHANNEL": "logs-bot-intégration"
    },
    699953170956156989: {
        "REGION_ROLE_COLOR": (46, 204, 113),     
        "DEPARTEMENT_ROLE_COLOR": (241, 196, 15),
        "GEOLOC_DISPLAY_CHANNEL": "liste-membres",      
        "GEOLOC_INPUT_CHANNELS": ["*"],          
        "DISPLAY_EMPTY_REGION": False,           
        "RUN_SYNC_ON_STARTUP": True,             
        "REMOVE_GEOLOCS_MESSAGES": False,        
        "GEOLOC_COMMAND_NAME": "!geoloc",        
        "ADD_NEWUSER_ROLE": True,                
        "REMOVE_NEWUSER_ROLE": True,             
        "NEWUSER_ROLE_NAME": "arrivants01",         
        "CONFIRMED_ROLE_NAME": "confirmés01",     
        "YOUNG_ROLE_NAME": "m18",     
        "ADMIN_ID": 699864843091443803,          
        "MODO_CHANNEL": "contact-modo",
        "MODO_ROLE": "modo01",
        "WELCOME_ANOUNCE": True,
        "WELCOME_CHANNEL": "blabla-01-écrit",
        "GOODBYE_ANOUNCE": False,
        "GOODBYE_CHANNEL": "",
        "LOG_CHANNEL": "log-bot-auto"
    }
}


def get_configuration(server_id):
    if server_id in CONFIGURATION:
        return CONFIGURATION[server_id]
    else:
        return CONFIGURATION["default"]
