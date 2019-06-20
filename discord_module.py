
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
import prettytable

#Example Structure (used here):
# discord_bot/
# ├── bot.py       
# ├── modules/
# │     └── rcon/
# │          ├── __init__.py
# │          ├── module.py
# │          ├── rcon.py
# │          └── rcon_cfg.json

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
        self.rcon_settings["ip"] = "192.168.000.001"
        self.rcon_settings["password"] = "<Enter Rcon Password here>"
        self.rcon_settings["port"] = 3302
        self.rcon_settings["timeoutSec"] = 1
        #save data
        with open(self.path+"/rcon_cfg.json", 'w') as outfile:
            json.dump(self.rcon_settings, outfile, sort_keys=True, indent=4, separators=(',', ': '))
    
    #converts unicode to ascii, until utf-8 is supported by rcon
    def setEncoding(self, msg):
        return bytes(msg.encode()).decode("ascii","ignore") 
    
    #sends a message thats longer than what discord can handel
    async def sendLong(self, ctx, msg):
        discord_limit = 1900 #discord limit is 2000
        while(len(msg)>0): 
            if(len(msg)>discord_limit): 
                await ctx.send(msg[:discord_limit])
                msg = msg[discord_limit:]
            else:
                await ctx.send(msg)
                msg = ""
###################################################################################################
#####                                   Bot commands                                           ####
###################################################################################################   
    def canUseCmds(ctx):
        roles = ["Admin", "Developer"] #Does not work in PMs for now
        admin_ids = [165810842972061697] #can be used in PMS
        print(ctx.message.author.name+"#"+str(ctx.message.author.id)+": "+ctx.message.content)
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
    #function called when a new message is received by rcon
    def rcon_on_msg_received(self, args):
        message=args[0]
        #print(message) or post them into a discord channel
    
    #event supports async functions
    #function is called when rcon disconnects
    async def rcon_on_disconnect(self):
        await asyncio.sleep(10)
        print("Reconnecting to BEC Rcon")
        self.epm_rcon.reconnect()
        
###################################################################################################
#####                                BEC Rcon custom commands                                  ####
###################################################################################################  
    @commands.check(canUseCmds)   
    @commands.command(name='debug',
        brief="Toggles RCon debug mode",
        pass_context=True)
    async def cmd_debug(self, ctx, limit=20): 
        if(self.epm_rcon.options['debug']==True):
            self.epm_rcon.options['debug'] = False
        else:
            self.epm_rcon.options['debug'] = True
       
        msg= "Set debug mode to:"+str(self.epm_rcon.options['debug'])
        await ctx.message.channel.send(msg)     
    
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
            msg += time.strftime("%H:%M:%S")+" | "+ pair[1]+"\n"
            i+=1
        await self.sendLong(ctx, msg)
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
        data = await self.epm_rcon.command(message)
        msg = "Executed command: ``"+str(message)+"`` wich returned: "+str(data)
        self.sendLong(ctx,msg)
        
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
        await self.sendLong(ctx, missions)
                
    @commands.check(canUseCmds)   
    @commands.command(name='banPlayer',
        brief="Ban a player's BE GUID from the server. If time is not specified or 0, the ban will be permanent.",
        pass_context=True)
    async def banPlayer(self, ctx, player_id, time=0, *message): 
        message = " ".join(message)
        message = self.setEncoding(message)
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
        msg = "BE version: ``"+str(version)+"``"
        await ctx.message.channel.send(msg)         
        
    @commands.check(canUseCmds)   
    @commands.command(name='getUptime',
        brief="Gets the current uptime of the server",
        pass_context=True)
    async def getUptime(self, ctx): 
        data = await self.epm_rcon.getUptime()
        msg = "Uptime: ``"+str(data)+"``"
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
                user=self.bot.get_user(165810842972061697)
                await user.send(user, "Caught exception")
                await user.send(user, (ex[:1800] + '..') if len(ex) > 1800 else ex)
                logging.error('Caught exception')
                await asyncio.sleep(10)  
    
def setup(bot):
    bot.add_cog(CommandRcon(bot))    
    