#Author: Yoshi_E
#Date: 2019.06.14
#https://www.battleye.com/downloads/BERConProtocol.txt

#Supported Events:
# "on_disconnect" passed_args = None
# "login_Sucess"  passed_args = None
# "login_fail"    passed_args = None
# "received_ServerMessage"   passed_args = message: str
# "received_CommandMessage"  passed_args = message: str
# "on_command_fail"  passed_args = None



import socket
import re
import time
import zlib
import asyncio
from collections import deque
import datetime
import codecs
import inspect
import logging
# Author: Yoshi_E
# Date: 2019.06.14
# Updated: 2023.04.20
# Found on github: https://github.com/Yoshi-E/Python-BEC-RCon
# Python3.6 Implementation of data protocol: https://www.battleye.com/downloads/BERConProtocol.txt
# License: https://creativecommons.org/licenses/by-nc-sa/4.0/


            
class RCON():
    SERVERDATA_AUTH = 3
    SERVERDATA_EXECCOMMAND = 2
    SERVERDATA_RESPONSE_VALUE = 0

    def __init__(self, serverIP: str, RConPassword: str, serverPort = 2302, logger = None, options = {}):

        self.options = {
            'timeoutSec'    : 10,
            'autosaveBans'  : False,
        }

        self.logger = logger
        if not logger:
            self.logger = logging.getLogger(__name__)
         
        # Text encoding (not all codings are supported)
        self.codec = "iso-8859-1"
            
        # Connection status
        self.disconnected = True

        # Stores all recent server messages (Format: array([datetime, msg],...))
        self.serverMessage = deque(maxlen=100) 

        # Event Handlers (Format: array([name, function], [name2, function2]...)
        self.eventHandlers = []

        # Multi-packet buffer
        self.multiPackets = []

        # Timestamps of last send and receive
        self.lastSend = datetime.datetime.now()
        self.lastReceived = datetime.datetime.now()
        self.lastAuth = datetime.datetime(1900, 1, 1, 0, 0, 0)

        # Locks sending until space to send is available 
        self.sendLock = False

        # Number of commands waiting to be sent (limited to 10)
        # Prevents overflow from too many queued commands
        self.numPendingCommands = 0 

        # Limits how many data packages can be sent at the same time
        self.maxPendingCommands = 10 

        # Stores all recent command returned data (Format: array([datetime, msg],...))
        self.serverCommandData = deque(maxlen=1000) 

        # Denotes if the object is being destroyed
        self.terminated = False
        
        if (type(serverPort) != int or type(RConPassword) != str or type(serverIP) != str):
            raise Exception('Wrong constructor parameter type(s)!')
        if(serverIP == "localhost"): #localhost is not supported
            self.serverIP = "127.0.0.1"
        else:
            self.serverIP = serverIP
        self.serverPort = serverPort
        self.rconPassword = RConPassword
        self.options = {**self.options, **options}
        self.connect()
        
    def __del__(self):
        self.terminated = True
        self.disconnect()
    
    def disconnect(self):
        if (self.disconnected):
            return None
        self.logger.info("[rcon] Disconnected")
        self.socket.close()
        self.socket = None
        self.disconnected = True
        self.on_disconnect()
    
    def connect(self):
        self.sendLock = False
        if (self.disconnected == False):
            self.disconnect()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #
        self.socket.connect((self.serverIP,  self.serverPort)) # #"udp://"+
        if (self.socket == False):
            raise socket.error('Failed to create socket!')
        
        self.socket.setblocking(0)
        self.authorize()
        self.disconnected = False
        
        #spawn async tasks
        self.listenForDataTask = asyncio.ensure_future(self.listenForData())
        self.keepAliveLoopTask = asyncio.ensure_future(self.keepAliveLoop())
        self.checkLoginOkTask = asyncio.ensure_future(self.checkLoginOk())
        
    def reconnect(self):
        self.disconnect()
        self.connect()
        return None

    # Sends the login data to the server in order to send commands later
    def authorize(self):
        self.sendLock = True # released by checkLoginOk()
        sent = self.writeToSocket(self.getLoginMessage())

    # sends the RCon command, but waits until command is confirmed before sending another one
    async def send(self, command: str):
        self.numPendingCommands += 1
        for _ in range(0,10 * self.options['timeoutSec']):
            if(self.numPendingCommands > self.maxPendingCommands):
                break
            if(self.sendLock == False): #Lock released by waitForResponse()
                self.sendLock = True
                if (self.disconnected):
                    raise ConnectionError('Failed to send command, because the connection is closed!')
                head = self.getHead(command)
                if (self.writeToSocket(head, command) == False):
                    raise ConnectionError('Failed to send command!')
                self.numPendingCommands -= 1   
                
                return True
            else:
                await asyncio.sleep(0.1) #watis 0.1 second before checking again
        self.numPendingCommands -= 1
        if(self.numPendingCommands > self.maxPendingCommands):
            raise TimeoutError("Failed to send in time: "+command+ " too many commands in queue >"+str(self.maxPendingCommands))
        else:
            self.sendLock = False
            raise TimeoutError("Failed to send in time: "+command)

    # Writes the given message to the socket
    def writeToSocket(self, head, command=""):
        self.lastSend = datetime.datetime.now()
        a = bytes(head.encode(self.codec, 'replace'))
        b = bytes.fromhex(command.encode("utf-8", 'replace').hex())
        return self.socket.send(a+b)
        
    # Generates the password's CRC32 data
    def getAuthCRC(self):
        data = b'\xff\x00' + (self.rconPassword.strip()).encode(self.codec)
        authCRC = '%x' % zlib.crc32(bytes(data))
        authCRC = [authCRC[-2:], authCRC[-4:-2], authCRC[-6:-4], authCRC[0:2]]
        return authCRC
    
    # Generates the message's CRC32 data
    def getMsgCRC(self, command):
        header = b'\xff\x01\x00'
        payload = bytes.fromhex(command.encode(self.codec, 'replace').hex())
        data = header+payload
        msgCRC = ('%x' % zlib.crc32(data)).zfill(8)
        msgCRC = [msgCRC[-2:], msgCRC[-4:-2], msgCRC[-6:-4], msgCRC[0:2]]
        return msgCRC

    def getHead(self, command):
        msgCRC = self.getMsgCRC(command)
        ascii_chars = [chr(int(hex_str, 16)) for hex_str in msgCRC]
        return 'BE' + ''.join(ascii_chars) + '\xff\x01\x00'
        
    def getLoginMessage(self):
        authCRC = self.getAuthCRC()
        ascii_chars = [chr(int(hex_str, 16)) for hex_str in authCRC]
        loginMsg = 'BE' + ''.join(ascii_chars) + '\xff\x00' + self.rconPassword
        self.logger.debug("loginMsg", loginMsg)
        return loginMsg
        

###################################################################################################
#####                                  common functions                                        ####
###################################################################################################
    # Debug funcion to view special chars
    def String2Hex(self,string):
        return string.encode(self.codec, 'replace').hex()

    #returns when a new command package was receive
    async def waitForResponse(self):
        d = len(self.serverCommandData)
        timeout = self.options['timeoutSec'] * 20 #10 = one second
        for i in range(0,timeout):
            if(d < len(self.serverCommandData)): #new command package was received
                self.sendLock = False #release the lock
                data = self.serverCommandData.pop()[1]
                if(len(self.serverCommandData) >= self.serverCommandData.maxlen/2):
                    self.serverCommandData.clear()
                return data
            await asyncio.sleep(0.05)
        self.logger.info("[rcon] Failed to keep connection - Disconnected")
        self.on_command_fail("Connection timed out")
        self.sendLock = False
        self.disconnect() #Connection Lost
        raise TimeoutError("Command timed out")
        
            
    def sendReciveConfirmation(self, sequence):
        if (self.disconnected):
            raise ConnectionError('Failed to send command, because the connection is closed!')
        
        #calculate CRC32
        data = b'\xff\x02' + sequence.encode(self.codec)
        msgCRC = ('%x' % zlib.crc32(data)).zfill(8)
        msgCRC = [msgCRC[-2:], msgCRC[-4:-2], msgCRC[-6:-4], msgCRC[0:2]]
        
        #generate send message
        ascii_chars = [chr(int(hex_str, 16)) for hex_str in msgCRC]
        msg = 'BE' + ''.join(ascii_chars) + '\xff\x02' + sequence
        
        if (self.writeToSocket(msg) == False):
            raise Exception('Failed to send confirmation!')
    
    async def listenForData(self):
        while (self.disconnected == False):
            answer = ""
            try:
                answer = self.socket.recv(102400).decode(self.codec)
               
                header =  answer[:7]
                crc32_checksum = header[2:-1] # TODO: verify checksum

                body = ""+self.String2Hex(answer[9:])
                body = codecs.decode(body, "hex", errors="strict") #
                body = body.decode(encoding="utf-8", errors='replace') #some encoding magic (iso-8859-1(with utf-8 chars) --> utf-8)
                
                packet_type = self.String2Hex(answer[7])

                self.lastReceived = datetime.datetime.now()
                self.logger.debug("[rcon] Received Package type: {}".format(packet_type))
                self.logger.debug("[rcon] Data: {}".format(body))
                if(packet_type=="02"): 
                    self.received_ServerMessage(answer, body)
                if(packet_type=="01"):
                    self.received_CommandMessage(answer, body)
                if(packet_type=="00"): #"Login packet"
                    if (ord(answer[len(answer)-1]) == 0): #Raise error when login failed
                        excption = 'Login failed, wrong password or wrong port!'
                        self.login_fail(excption)
                        raise PermissionError(excption)
                    else:
                        self.login_Sucess()
            except BlockingIOError: 
                pass
            if(answer==""):
                await asyncio.sleep(0.2)
                
            
    async def keepAliveLoop(self):
        while (self.disconnected == False):
            #package needs to be send every min:1s, max:44s 
            diff = datetime.datetime.now() - self.lastReceived
            if(diff.total_seconds() >= 40): 
                await self.keepAlive()
            await asyncio.sleep(2)  
  
    #Keep the stream alive. Send package to BE server. Use function before 45 seconds.
    async def keepAlive(self):
        try:
            self.logger.debug('[rcon] --Keep connection alive--'+"\n")
            await self.getBEServerVersion()
        except Exception as e:
            self.logger.debug("[rcon] Failed to keep Alive - Disconnected")
            self.disconnect() #connection lost    
            
    # Check if the login was sucessfull
    async def checkLoginOk(self):
        # Verify login succeeded by waiting for server response:
        for _ in range(0, self.options['timeoutSec']*10):
            await asyncio.sleep(0.1)

            delta = datetime.datetime.now() - self.lastAuth
            if(delta.total_seconds() <= self.options['timeoutSec']): 
                self.sendLock = False
                self.logger.debug('[rcon] --Login ok--'+"\n")
                return True
        
        self.sendLock = False
        self.login_fail("Login: Connection timed out")
        self.disconnect()
        raise TimeoutError("Login: Connection timed out")

        
###################################################################################################
#####                                  event handler                                           ####
###################################################################################################
    def add_Event(self, name: str, func):
        events = ["on_command_fail", "on_disconnect", "login_Sucess", "login_fail", "received_ServerMessage", "received_CommandMessage"]
        if(name in events):
            self.eventHandlers.append([name,func])
        else:
            raise ValueError("Failed to add unkown event: "+name)

            
    def check_Event(self, parent, *args):
        if(self.terminated == True):
            return
        for event in self.eventHandlers:
            func = event[1]
            if(inspect.iscoroutinefunction(func)): #is async
                if(event[0]==parent):
                    if(len(args)>0):
                        asyncio.ensure_future(func(args))
                    else:
                        asyncio.ensure_future(func())
            else:
                if(event[0]==parent):
                    if(len(args)>0):
                        func(args)
                    else:
                        func()

###################################################################################################
#####                                  event functions                                         ####
###################################################################################################

    def on_disconnect(self):
        self.check_Event("on_disconnect")
        
    def login_Sucess(self):
        self.lastAuth = datetime.datetime.now()
        self.check_Event("login_Sucess")
        
    def login_fail(self, exception):
        self.disconnect()
        self.check_Event("login_fail", exception)
     
    def received_ServerMessage(self, packet, message):
        self.serverMessage.append([datetime.datetime.now(), message])
        self.sendReciveConfirmation(packet[8]) #confirm with sequence id from packet  
        self.check_Event("received_ServerMessage", message)
    
    #waitForResponse() handles all inbound packets, you can still fetch them here though.
    def received_CommandMessage(self, packet, message):
        if(len(message)>3 and self.String2Hex(message[0]) =="00"): #is multi packet
            self.MultiPackets.append(message[3:])
            if(int(self.String2Hex(message[1]),16)-1 == int(self.String2Hex(message[2]),16)):
                self.serverCommandData.append([datetime.datetime.now(), "".join(self.MultiPackets)])
                self.MultiPackets = []
        else: #Normal Package
            self.serverCommandData.append([datetime.datetime.now(), message])
        self.check_Event("received_CommandMessage", message)
            
    def on_command_fail(self, exception):
        self.check_Event("on_command_fail", exception)



###################################################################################################
#####                                  BEC Commands                                            ####
###################################################################################################   
#
#                                    *** Warning ***
#               Depending on your configuation of BEC not all commands might work
#                                    *** Warning ***

class RCON_ARMA(RCON):
    # Converts BE text "array" list to array
    def formatList(self, str):
        #Create return array
        result = []
        #Loop True the main arrays, each holding a value
        for pair in str:
            #Combines each main value into new array
            result.append([])
            for val in pair:
                result[-1].append(val.strip())
        return result

    # Remove control characte	rs
    def cleanList(self, str):
        return re.sub('/[\x00-\x09\x0B\x0C\x0E-\x1F\x7F]/', '', str)

    # Sends a custom command to the server
    async def command(self, command: str):
        await self.send(command)
        return await self.waitForResponse()

    # Kicks a player who is currently on the server
    async def kickPlayer(self, player, reason = 'Admin Kick'):
        if (type(player) != int and type(player) != str):
            raise Exception('Expected parameter 1 to be string or integer, got %s' % type(player))
        if (type(reason) != str):
            raise Exception('Expected parameter 2 to be string, got %s' % type(reason))
        await self.send("kick "+str(player)+" "+reason)
        return await self.waitForResponse()

    # Sends a global message to all players
    async def sayGlobal(self, message: str):
        await self.send("Say -1 "+message)
        return await self.waitForResponse()

    # Sends a message to a specific player
    async def sayPlayer(self, player: int, message: str):
        await self.send("Say "+str(player)+" "+message)
        return await self.waitForResponse()

    # Loads the "scripts.txt" file without the need to restart the server
    async def loadScripts(self):
        await self.send('loadScripts')
        return await self.waitForResponse()

    # Changes the MaxPing value. If a player has a higher ping, he will be kicked from the server
    async def maxPing(self, ping: int):
        await self.send("MaxPing "+str(ping))
        return await self.waitForResponse()
    
    # Changes the RCon password
    async def changePassword(self, password: str):
        await self.send(f"RConPassword {password}")
        return await self.waitForResponse()
    
    # (Re)load the BE ban list from bans.txt
    async def loadBans(self):
        await self.send('loadBans')
        return await self.waitForResponse()

    # Gets a list of all players currently on the server
    async def getPlayers(self):
        await self.send('players')
        return await self.waitForResponse()

    # Gets a list of all players currently on the server as an array
    async def getPlayersArray(self):
        playersRaw = await self.getPlayers()
        players = self.cleanList(playersRaw)
        data = re.findall(r"(\d+)\s+(\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+\b)\s+(\d+)\s+([0-9a-fA-F]+)\(\w+\)\s([\S ]+)", players)
        return self.formatList(data)
        
    # Gets a list of all admins connected to the server
    async def getAdmins(self):
        await self.send('admins')
        result = await self.waitForResponse()
        return result #strip timedate
        
    # Gets a list of all players currently on the server as an array
    async def getAdminsArray(self):
        adminsRaw = await self.getAdmins()
        admins = self.cleanList(adminsRaw)
        str = re.findall(r"(\d+)\s+(\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+\b)", admins)
        return self.formatList(str)
    
    # Gets a list of all bans
    async def getMissions(self):
        await self.send('missions')
        return await self.waitForResponse()    
        
    # Loads a mission
    # Mission file name without .pbo at the end!
    async def loadMission(self, mission: str):
        await self.send('#mission '+mission)
        return await self.waitForResponse()    
    
    # Loads Events
    async def loadEvents(self):
        await self.send('loadEvents')
        return await self.waitForResponse()    

    # Ban a player's BE GUID from the server. If time is not specified or 0, the ban will be permanent.
    # If reason is not specified the player will be kicked with the message "Banned".
    async def banPlayer(self, player_id, reason = 'Banned', time = 0):
        if (type(player_id) != str and type(player_id) != int):
            raise Exception('Expected parameter 1 to be integer or string, got %s' % type(player_id))
        if (type(reason) != str or type(time) != int):
            raise Exception('Wrong parameter type(s)!')
        await self.send("ban "+str(player_id)+" "+str(time)+" "+reason)
        if (self.options['autosaveBans']):
            self.writeBans()
        return await self.waitForResponse()   

    # Same as "banPlayer", but allows to ban a player that is not currently on the server
    async def addBan(self, guid: int, reason = 'Banned', time = 0):
        await self.send("addBan "+guid+" "+str(time)+" "+reason)
        if (self.options['autosaveBans']):
            self.writeBans()
        return await self.waitForResponse()

    # Removes a ban
    async def removeBan(self, banId: int):
        await self.send("removeBan "+str(banId))
        if (self.options['autosaveBans']):
            self.writeBans()
        return await self.waitForResponse()

    # Gets an array of all bans
    async def getBansArray(self):
        bansRaw = await self.getBans()
        bans = self.cleanList(bansRaw)
        str = re.findall(r'(\d+)\s+([0-9a-fA-F]+)\s([perm|\d]+)\s([\S ]+)', bans)
        return self.formatList(str)

    # Gets a list of all bans
    async def getBans(self):
        await self.send('bans')
        return await self.waitForResponse()

    # Removes expired bans from bans file
    async def writeBans(self):
        await self.send('writeBans')
        return await self.waitForResponse()

    # Gets the current version of the BE server
    async def getBEServerVersion(self):
        await self.send('version')
        return await self.waitForResponse() 
        
###################################################################################################
#####                                  Arma Server Commands                                    ####
################################################################################################### 
# Commands starting with a '#' can be execuded, but will return no data

    # Locks the server. No one will be able to join
    async def lock(self):
        await self.send('#lock')
        return await self.waitForResponse()
        
    # Unlocks the Server
    async def unlock(self):
        await self.send('#unlock')
        return await self.waitForResponse()
    
    # Shutdowns the Server
    # args: [x, "abort", "info"] x= time in seconds till shutdown
    async def shutdown(self):
        await self.send('#shutdown')
        return await self.waitForResponse()    
    
    # Restart mission with current player slot selection
    async def restart(self):
        await self.send('#restart')
        return await self.waitForResponse()       
        
    # Shuts down and restarts the server immediately
    async def restartServer(self):
        await self.send('#restartserver')
        return await self.waitForResponse()    
    
    # Shuts down and restarts the server after mission ends
    async def restartserveraftermission(self):
        await self.send('#restartserveraftermission')
        return await self.waitForResponse()        
    
    # Shuts down the server after mission ends 
    async def shutdownserveraftermission(self):
        await self.send('#shutdownserveraftermission')
        return await self.waitForResponse()    
        
    # Restart the mission with new player slot selection
    async def reassign(self):
        await self.send('#reassign')
        return await self.waitForResponse()    
            
    # Shows performance information in the dedicated server console. Interval 0 means to stop monitoring.
    async def monitords(self, inveral: int):
        await self.send('#monitords '+str(inveral))
        return await self.waitForResponse()     
        
    # Users can vote for the mission selection.
    async def goVote(self):
        await self.send('#vote missions')
        return await self.waitForResponse()    