﻿import socket
import os
import sys
import re
import zlib
import binascii
import asyncio
import time
import bec_rcon
#Author: Yoshi_E
#Date: 2019.06.14
#https://www.battleye.com/downloads/BERConProtocol.txt
#Code based on https://github.com/felixms/arma-rcon-class-php

#Supported Events:
# "on_disconnect" passed_args = None
# "login_Sucess"  passed_args = None
# "login_fail"    passed_args = None
# "received_ServerMessage"   passed_args = message: str
# "received_CommandMessage"  passed_args = message: str
# "on_command_fail"  passed_args = None


###################################################################################################
#####                    Custom Functions called by the Event Handler                          ####
###################################################################################################   

def msg(args):
    message = args[0]
    print(message) #Prints received message
    
def disco():
    print("Disconnected")
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
    #arma_rcon.serverMessage         # Contains all recent messages (limit = 100) Format: [obj(datetime), Str(Message)]
    #arma_rcon.serverCommandData     # Contains all recent command returned data (limit = 10) Format: [obj(datetime), Str(Data)]
    #arma_rcon.disconnect()          # Disconnects the client
    #arma_rcon.connect()             # Logs back in

###################################################################################################
#####                                Main Program                                              ####
###################################################################################################   

if __name__ == "__main__":
    ip = "000.000.000.000"  #Your Server IP
    pw = "Password"         #Your Rcon Password
    port = 3302             #Rcon Port
    
    arma_rcon = bec_rcon.ARC(ip, pw, port)
    arma_rcon.add_Event("received_ServerMessage", msg)
    arma_rcon.add_Event("on_disconnect", disco)
    
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
