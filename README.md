# API and Discord Module for BEC RCon

# Install

API: Download rcon.py and simply import it.  
Discord: Download all files and add discord_module.py to your bot as [Cogs](https://discordpy.readthedocs.io/en/latest/ext/commands/cogs.html).  
Example Structure:  
 discord_bot/  
 ├── bot.py (Your discord bot)    
 ├── modules/  
 │     └── rcon/  
 │          ├── __init__.py  
 │          ├── module.py  
 │          ├── rcon.py  
 │          └── rcon_cfg.json  

# Demo
Check out the full demo in api_example.py.  
This short example connects to a RCon server and prints all server messages it receives.
```python

def msg(message):
    print(message)

import rcon
rcon_client = rcon.ARC("192.168.000.001", "MyPassword", 2302)
rcon_client.add_Event("received_ServerMessage", msg)

```
# Known Issues:
* [Outbound messages can only contain ASCII charaters](https://github.com/Yoshi-E/Python-BEC-RCon/issues/1)

# Contact me:
Join my Discord: https://discordapp.com/invite/YhBUUSr  
Bohemia Interactive Forum Thread: https://forums.bohemia.net/forums/topic/223835-api-bec-rcon-api-for-python-and-discord/

# Documentation
## Event Handlers:
The passed functions can by async and can be class objects.

| Event                   | passed args   |
|:----------------------- |:--------------|
| on_disconnect           | none          |
| login_Sucess            | none          |
| login_fail              | none          |
| on_command_fail         | none          |
| received_ServerMessage  | message: str  |
| received_CommandMessage | message: str  |

## Variables:
* rcon_client.serverMessage: Contains all recent messages (limit = 100) Format: [datetime: datetime, message: str]
* rcon_client.serverCommandData: Contains all returned data from commands (limit = 10) Format: [datetime: datetime, data: str]
* rcon_client.disconnected: When connected = False, else True
* rcon_client.serverPort: ServerPort (int)
* rcon_client.serverIP: ServerIP (str)
* rcon_client.rconPassword: ServerPassword (str)
* rcon_client.Events: List of all user added Event handlers Format: [str(event_name), function(custom_function)]

## API Functions:

###### ARC = ARC(serverIP: str, RConPassword: str, serverPort = 2302, options = {})
* serverIP: 			IPv4 adress in the format: 000.000.000.000 - 255.255.255.255
* RConPassword: str 	your Rcon password
* serverPort: int 		port Rcon is running on your server
options is an diconatry for addional settings: 
* timeoutSec: int		time in seconds a RCon command has to be executed within (Default: 5, Min: 0.2, Max: None)
* autosaveBans: boolean	Saves bans to file when ever a ban is added or removed (Default: False)
* debug: boolean		Prints additonal package and debug information into console (Default: False)
This class constructor automatically connects to given server and attempts to maintain the connection.
###### ARC.disconnect()
Closed the connection to the server and fires the Event "on_disconnect".
###### ARC.connect()
Connects to the server.
###### ARC.reconnect()
Closes the connection and connects to the server.
###### ARC.authorize()
Authorizes the connection using the RConPassword
###### ARC.send(command: str) <async>
Waits for an opportunity to send a command to the rcon server.  
Only one send will be executed at a time. At most ARC.max_waiting_for_send (Defaut: 10) can be waiting.  
Will raise the "Failed to send command!" exception if it failed to send the command within the timeout limit.  
ARC.activeSend tracks how many commands are trying to be send at the same time.  
###### ARC.add_Event(event_name: str, function: function)
Events are: "on_command_fail", "on_disconnect", "login_Sucess", "login_fail", "received_ServerMessage" and "received_CommandMessage".  
Function can be class function and can be asynchronous.  
Addtional, custom parameters however can not be passed.  

## RCon Commands:
See rcon.py for details
* command
* kickPlayer
* sayGlobal
* sayPlayer
* loadScripts
* maxPing
* changePassword
* loadBans
* getPlayers
* getPlayersArray
* getAdmins
* getAdminsArray
* getMissions
* loadMission
* banPlayer
* addBan
* removeBan
* getBansArray
* getBans
* writeBans
* getBEServerVersion

## Arma 3 Commands
See https://community.bistudio.com/wiki/Multiplayer_Server_Commands for details
* lock
* unlock
* shutdown
* restart
* restartServer
* restartserveraftermission
* shutdownserveraftermission
* reassign
* monitords
* goVote

