
# Works with Python 3.6
# Discord 1.2.2
import asyncio
from collections import Counter
import concurrent.futures
import json
import os
import sys
import traceback
import discord
from discord.ext import commands
from discord.ext.commands import has_permissions, CheckFailure
import ast
import prettytable
from difflib import get_close_matches 
import textwrap
import time
from modules.rcon import rcon

class CommandRcon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.path = os.path.dirname(os.path.realpath(__file__))
        
        self.rcon_settings = {}
        if(os.path.isfile(self.path+"/rcon_cfg.json")):
            self.rcon_settings = json.load(open(self.path+"/rcon_cfg.json","r"))
        else:
            self.creatcfg() #make empty cfg file
            raise Exception("Error: You have to configure the rcon_cfg first!")
        
        self.epm_rcon = rcon.ARC(self.rcon_settings["ip"], 
                                 self.rcon_settings["password"], 
                                 self.rcon_settings["port"], 
                                 {'timeoutSec' : self.rcon_settings["timeoutSec"]}
                                )

        #Add Event Handlers
        self.epm_rcon.add_Event("received_ServerMessage", self.rcon_on_msg_received)
        self.epm_rcon.add_Event("on_disconnect", self.rcon_on_disconnect)

    
        
        
###################################################################################################
#####                                  common functions                                        ####
###################################################################################################
    def creatcfg(self):
        self.rcon_settings["ip"] = "000.000.000.000"
        self.rcon_settings["password"] = "<Enter Rcon Password here>"
        self.rcon_settings["port"] = 3302
        self.rcon_settings["timeoutSec"] = 1
        #save data
        with open(self.path+"/rcon_cfg.json", 'w') as outfile:
            json.dump(self.rcon_settings, outfile, sort_keys=True, indent=4, separators=(',', ': '))
    
    #converts unicode to ascii, until utf-8 is supported by rcon
    def setEncoding(self, msg):
        return bytes(msg.encode()).decode("ascii","ignore") 

###################################################################################################
#####                                   Bot commands                                           ####
###################################################################################################   
    def canUseCmds(ctx):
        roles = ["Admin", "Developer"]
        admin_ids = [165810842972061697] #can be used in PMS #
        msg = ctx.message.author.name+"#"+str(ctx.message.author.id)+": "+ctx.message.content
        print(msg)
        if(ctx.author.id in admin_ids):
            return True
        if(hasattr(ctx.author, 'roles')):
            for role in ctx.author.roles:
                if(role in roles):
                    return True        
        return False
###################################################################################################
#####                                BEC Rcon Event handler                                    ####
###################################################################################################  
    async def keepConnection(self):
        while(True):
            await asyncio.sleep(10) #wait 10s before attemping reconnection
            if(self.epm_rcon.disconnected == True):
                self.epm_rcon.connect() #reconnect
                print("Reconnecting to BEC Rcon")
    
    def rcon_on_msg_received(self, args):
        message=args[0]
        #print(message)    
    
    def rcon_on_disconnect(self):
        print("Disconnected")
        
    async def sendLong(self, ctx, msg):
        while(len(msg)>0):
            if(len(msg)>1800):
                await ctx.send(msg[:1800])
                msg = msg[1800:]
            else:
                await ctx.send(msg)
                msg = ""
###################################################################################################
#####                                BEC Rcon custom commands                                  ####
###################################################################################################  
    @commands.check(canUseCmds)   
    @commands.command(name='status',
        brief="Current connection status",
        pass_context=True)
    async def status(self, ctx, limit=20): 
        msg = ""
        if(self.epm_rcon.disconnected==False):
           msg+= "Connected to: "+ self.epm_rcon.serverIP+"\n"
        else:
            msg+= "Currently not connected: "+ self.epm_rcon.serverIP+"\n"
        msg+= str(len(self.epm_rcon.serverMessage))+ " Messages collected"
        await ctx.message.channel.send(msg) 
        
    @commands.check(canUseCmds)   
    @commands.command(name='getChat',
        brief="Sends a custom command to the server",
        pass_context=True)
    async def getChat(self, ctx, limit=20): 
        msg = ""
        data = self.epm_rcon.serverMessage.copy()
        start = len(data)-1
        if(start > limit):
            end = start-limit
        else:
            end = 0
        i = end
        while(i<=start):
            pair = data[i]
            time = pair[0]
            msg+= time.strftime("%H:%M:%S")+" | "+ pair[1]+"\n"
            i += 1
            if(len(msg)>1800): #splits message into multiple parts (discord max limit)
                await ctx.message.channel.send(msg) 
                msg=""
        if(len(msg)>0):
            await ctx.message.channel.send(msg) 
###################################################################################################
#####                                   BEC Rcon commands                                      ####
###################################################################################################   
        
    @commands.check(canUseCmds)   
    @commands.command(name='command',
        brief="Sends a custom command to the server",
        pass_context=True)
    async def command(self, ctx, *message): 
        message = " ".join(message)
        message = self.setEncoding(message)
        await self.epm_rcon.command(message)
        msg = "Executed command: ``"+message+"``"
        await ctx.message.channel.send(msg)    
        
    @commands.check(canUseCmds)   
    @commands.command(name='kickPlayer',
        brief="Kicks a player who is currently on the server",
        pass_context=True)
    async def kickPlayer(self, ctx, player_id: int, *message): 
        message = " ".join(message)
        message = self.setEncoding(message)
        await self.epm_rcon.kickPlayer(player_id, message)
            
        msg = "kicked player: "+str(player_id)
        await ctx.message.channel.send(msg)
            
    @commands.check(canUseCmds)   
    @commands.command(name='say',
        brief="Sends a global message",
        pass_context=True)
    async def sayGlobal(self, ctx, *message): 
        name = ctx.message.author.name
        message = " ".join(message)
        message = self.setEncoding(message)
        await self.epm_rcon.sayGlobal(name+": "+message)
        msg = "Send: ``"+message+"``"
        await ctx.message.channel.send(msg)    
        
    @commands.check(canUseCmds)   
    @commands.command(name='sayPlayer',
        brief="Sends a message to a specific player",
        pass_context=True)
    async def sayPlayer(self, ctx, player_id: int, *message): 
        message = " ".join(message)
        message = self.setEncoding(message)
        name = ctx.message.author.name
        if(len(message)<2):
            message = "Ping"
        await self.epm_rcon.sayPlayer(player_id, name+": "+message)
        msg = "Send msg: ``"+str(player_id)+"``"+message
        await ctx.message.channel.send(msg)
    
    @commands.check(canUseCmds)   
    @commands.command(name='loadScripts',
        brief="Loads the 'scripts.txt' file without the need to restart the server",
        pass_context=True)
    async def loadScripts(self, ctx): 
        await self.epm_rcon.loadScripts()
        msg = "Loaded Scripts!"
        await ctx.message.channel.send(msg)    
            
            
    @commands.check(canUseCmds)   
    @commands.command(name='maxPing',
        brief="Changes the MaxPing value. If a player has a higher ping, he will be kicked from the server",
        pass_context=True)
    async def maxPing(self, ctx, ping: int): 
        await self.epm_rcon.maxPing(ping)
        msg = "Set maxPing to: "+ping
        await ctx.message.channel.send(msg)       

    @commands.check(canUseCmds)   
    @commands.command(name='changePassword',
        brief="Changes the RCon password",
        pass_context=True)
    async def changePassword(self, ctx, *password): 
        password = " ".join(password)
        await self.epm_rcon.changePassword(password)
        msg = "Set Password to: ``"+password+"``"
        await ctx.message.channel.send(msg)        
        
    @commands.check(canUseCmds)   
    @commands.command(name='loadBans',
        brief="(Re)load the BE ban list from bans.txt",
        pass_context=True)
    async def loadBans(self, ctx): 
        await self.epm_rcon.loadBans()
        msg = "Loaded Bans!"
        await ctx.message.channel.send(msg)    
        
    @commands.check(canUseCmds)   
    @commands.command(name='players',
        brief="lists current players on the server",
        pass_context=True)
    async def players(self, ctx):
        players = await self.epm_rcon.getPlayersArray()
        msgtable = prettytable.PrettyTable()
        msgtable.field_names = ["ID", "Name", "IP", "GUID"]
        msgtable.align["ID"] = "r"
        msgtable.align["Name"] = "l"
        msgtable.align["IP"] = "l"
        msgtable.align["GUID"] = "l"

        limit = 100
        i = 1
        new = False
        msg  = ""
        for player in players:
            if(i <= limit):
                msgtable.add_row([player[0], player[4], player[1],player[3]])
                if(len(str(msgtable)) < 1800):
                    i += 1
                    new = False
                else:
                    msg += "```"
                    msg += str(msgtable)
                    msg += "```"
                    await ctx.message.channel.send(msg)
                    msgtable.clear_rows()
                    msg = ""
                    new = True
        if(new==False):
            msg += "```"
            msg += str(msgtable)
            msg += "```"
            await ctx.message.channel.send(msg)  
            

    @commands.check(canUseCmds)   
    @commands.command(name='getMissions',
        brief="Gets a list of all Missions",
        pass_context=True)
    async def getMissions(self, ctx):
        missions = await self.epm_rcon.getMissions()
        missions = missions[1]
        await self.sendLong(ctx, missions)
                
    @commands.check(canUseCmds)   
    @commands.command(name='banPlayer',
        brief="Ban a player's BE GUID from the server. If time is not specified or 0, the ban will be permanent.",
        pass_context=True)
    async def banPlayer(self, ctx, player_id, time=0, *message): 
        message = " ".join(message)
        message = self.setEncoding(message)
        print("banPlayer", player_id, message)
        matches = ["?"]
        if(len(player_id) >3 and player_id.isdigit()==False):
            #find player
            players = {}
            players_list = await self.epm_rcon.getPlayersArray()[1]
            for cplayer in players_list:
                players[cplayer[4]] = cplayer[0] 
                
            matches = get_close_matches(player_id, players.keys(), cutoff = 0.5, n = 3)   
            if(len(matches) > 0):
                player = players[matches[0]]
            else:
                matches = ["?"]
                player = player_id
        else:
            player = int(player_id)
        if(len(message)<2):
            await self.epm_rcon.banPlayer(player=player, time=time)
        else:
            await self.epm_rcon.banPlayer(player, message, time)
            
        msg = "Banned player: ``"+str(player)+" - "+matches[0]+"`` with reason: "+message
        await ctx.message.channel.send(msg)    
        
        
    @commands.check(canUseCmds)   
    @commands.command(name='addBan',
        brief="Same as 'banPlayer', but allows to ban a player that is not currently on the server",
        pass_context=True)
    async def addBan(self, ctx, GUID, time=0, *message): 
        message = " ".join(message)
        message = self.setEncoding(message)
        player = player_id
        matches = ["?"]
        if(len(GUID) != 32):
            raise Exception("Invalid GUID")
        if(len(message)<2):
            await self.epm_rcon.addBan(player=player, time=time)
        else:
            await self.epm_rcon.addBan(player, message, time)
            
        msg = "Banned player: ``"+str(player)+" - "+matches[0]+"`` with reason: "+message
        await ctx.message.channel.send(msg)   

    @commands.check(canUseCmds)   
    @commands.command(name='removeBan',
        brief="Removes a ban",
        pass_context=True)
    async def removeBan(self, ctx, banID: int): 
        await self.epm_rcon.removeBan(banID)
            
        msg = "Removed ban: ``"+str(banID)+"``"
        await ctx.message.channel.send(msg)    
        
    @commands.check(canUseCmds)   
    @commands.command(name='getBans',
        brief="Removes a ban",
        pass_context=True)
    async def getBans(self, ctx): 
        bans = await self.epm_rcon.getBansArray()
        bans.reverse() #news bans first
        msgtable = prettytable.PrettyTable()
        msgtable.field_names = ["ID", "GUID", "Time", "Reason"]
        msgtable.align["ID"] = "r"
        msgtable.align["Name"] = "l"
        msgtable.align["IP"] = "l"
        msgtable.align["GUID"] = "l"

        limit = 20
        i = 1
        new = False
        msg  = ""
        for ban in bans:
            if(i <= limit):
                if(len(str(msgtable)) < 1700):
                    msgtable.add_row([ban[0], ban[1], ban[2],ban[3]])
                    i += 1
                    new = False
                else:
                    msg += "```"
                    msg += str(msgtable)
                    msg += "```"
                    await ctx.message.channel.send(msg)
                    msgtable.clear_rows()
                    msg = ""
                    new = True
        if(new==False):
            msg += "```"
            msg += str(msgtable)
            msg += "```"
            await ctx.message.channel.send(msg)   
        if(i>=limit):
            msg = "Limit of "+str(limit)+" reached. There are still "+str(len(bans)-i)+" more bans"
            await ctx.message.channel.send(msg)   
            
    @commands.check(canUseCmds)   
    @commands.command(name='getBEServerVersion',
        brief="Gets the current version of the BE server",
        pass_context=True)
    async def getBEServerVersion(self, ctx): 
        version = await self.epm_rcon.getBEServerVersion()
        msg = "BE version: ``"+str(version[1])+"``"
        await ctx.message.channel.send(msg)      
    
    ###################################################################################################
    #####                                  Debug Commands & Error Handeling                 ####
    ###################################################################################################

    async def handle_exception(self, myfunction):
        coro = getattr(self, myfunction)
        for i in range (0,5):
            try:
                await coro()
            except Exception as ex:
                ex = str(ex)+"/n"+str(traceback.format_exc())
                user=await self.bot.get_user_info("165810842972061697")
                await user.send(user, "Caught exception")
                await user.send(user, (ex[:1800] + '..') if len(ex) > 1800 else ex)
                logging.error('Caught exception')
                await asyncio.sleep(10)  
    
local_module = None
def setup(bot):
    global local_module
    module = CommandRcon(bot)
    local_module = module #access for @check decorators
    bot.loop.create_task(module.handle_exception("keepConnection"))
    
    bot.add_cog(module)    
    