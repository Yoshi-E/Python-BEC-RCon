# API and Discord Module for BEC RCon

# Install

Just download the scripts and add them to your discord python bot, or make your scripts with it.

# Demo
Check out the demo in api_example.py.
```python

import ARC
rcon_client = rcon.ARC("000.000.000.000", "Password", 2302)
rcon_client.add_Event("received_ServerMessage", msg)

```

# Documentation
## Event Handlers:

| Event                   | passed args   |
| ----------------------- |:-------------:|
| on_disconnect           | none          |
| login_Sucess            | none          |
| login_fail              | none          |
| on_command_fail         | none          |
| received_ServerMessage  | message: str  |
| received_CommandMessage | message: str  |

## Variables:
* rcon_client.serverMessage: Contains all recent messages (limit = 100) Format: [obj(datetime), Str(Message)]
* rcon_client.serverCommandData: Contains all returned data from commands (limit = 10) Format: [obj(datetime), Str(Data)]
* rcon_client.disconnected: When connected = False, else True
* rcon_client.serverPort: ServerPort (int)
* rcon_client.serverIP: ServerIP (str)
* rcon_client.rconPassword: ServerPassword (str)
* rcon_client.Events: List of all user added Event handlers Format: [str(event_name), function(custom_function)]

## Discord Commands:
*  addBan             Same as 'banPlayer', but allows to ban a player that is ...
*  banPlayer          Ban a player's BE GUID from the server. If time is not s...
*  changePassword     Changes the RCon password
*  command            Sends a custom command to the server
*  getBEServerVersion Gets the current version of the BE server
*  getBans            Removes a ban
*  getChat            Sends a custom command to the server
*  getMissions        Gets a list of all Missions
*  kickPlayer         Kicks a player who is currently on the server
*  loadBans           (Re)load the BE ban list from bans.txt
*  loadScripts        Loads the 'scripts.txt' file without the need to restart...
*  maxPing            Changes the MaxPing value. If a player has a higher ping...
*  players            lists current players on the server
*  removeBan          Removes a ban
*  say                Sends a global message
*  sayPlayer          Sends a message to a specific player
*  status             Current connection status

# Known Issues:
* Outbound messages can only contain ASCII charaters
* Not all commands are available yet

# Contact me:
Join my Discord: https://discordapp.com/invite/YhBUUSr
or on the Bohemia Interactive Forum Thread: