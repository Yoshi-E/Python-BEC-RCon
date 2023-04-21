import asyncio

import sys, os
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, parent_dir)
from bec_rcon import RCON_ARMA

###################################################################################################
#####                    Custom Functions called by the Event Handler                          ####
###################################################################################################   

def msg(args):
    message = args[0]
    print(message) #Prints received message
    
def disco():
    print("Disconnected")

def fail(exception):
    print(f"login fail: {exception}")

def sucess():
    print("login sucess")
    #Now you can for example call to reconnect the client (add a delay)
    #sleep(60)
    #arma_rcon.connect()

###################################################################################################
#####          Async task keeping the script alive, while a connection exsits                  ####
###################################################################################################   

# The execution of rcon commands is asynchronous and requires an "await" in an "async" function
# All commands are listed in BEC commands in rcon.py
async def main():
    print("Players:",await arma_rcon.getPlayersArray()) #get Array with all player on server
    await arma_rcon.listenForDataTask    # waits until on_disconnect
    print("Connection Lost")
    # arma_rcon.serverMessage         # Contains all recent messages (limit = 100) Format: [obj(datetime), Str(Message)]
    # arma_rcon.serverCommandData     # Contains all recent command returned data (limit = 10) Format: [obj(datetime), Str(Data)]
    # arma_rcon.disconnect()          # Disconnects the client
    # arma_rcon.connect()             # Logs back in

###################################################################################################
#####                                Main Program                                              ####
###################################################################################################   

if __name__ == "__main__":
    ip = "000.000.000.000"  #Your Server IP
    pw = "PASSWORD"         #Your Rcon Password
    port = 3302             #Rcon Port
    

    # creating the instance will also automatically create an async method "keepAliveLoop"
    # that will maintain the connection
    arma_rcon = RCON_ARMA(ip, pw, port)

    # Simply attach the events to the client that you need
    arma_rcon.add_Event("received_ServerMessage", msg)
    arma_rcon.add_Event("on_disconnect", disco)
    arma_rcon.add_Event("login_fail", fail)
    arma_rcon.add_Event("login_Sucess", sucess)
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
