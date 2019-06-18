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

# Known Issues:
* Outbound messages can only contain ASCII charaters