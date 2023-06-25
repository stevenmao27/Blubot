import logging as log
# log.FileHandler('logFile.log', mode='w')
log.basicConfig(format='[%(levelname)s] %(funcName)s(): %(message)s', level=log.INFO)
discordHandler = log.getLogger('discord')
discordHandler.setLevel(log.WARNING)
myLogger = log.getLogger('myLogger')


import discord
import discord.ext.bridge as bridge
import os


# Set up bot
intents = discord.Intents().all()
bot = bridge.Bot(debug_guilds=[523693679341207552, 783391965525049384, 784497167578300468, 1078177604374380574, 1120156902232436756], command_prefix='.', intents=intents) # type: ignore


# Import Cogs
from modules.music_player import *
from modules.miscellaneous import *
from modules.info import *
from modules.utility import *
from modules.game import *
from modules.poll import *
from modules.todo import *
from modules.chatgpt import *
bot.add_cog(MCog(bot))
# bot.add_cog(FunCog(bot))
# bot.add_cog(InfoCog(bot))
bot.add_cog(UtilityCog(bot))
bot.add_cog(GameCog(bot))
bot.add_cog(PollCog(bot))
bot.add_cog(TodoCog(bot))
bot.add_cog(ChatGPTCog(bot))


@bot.event
async def on_ready():
    myLogger.info('Blubot has logged in')


from dotenv import main
main.load_dotenv()
BLUBOT_API_TOKEN = os.environ.get('BLUBOT_API_TOKEN')
try:
    bot.run(BLUBOT_API_TOKEN)
except:
    myLogger.critical('Blubot failed to run')


# def displayHandlers():
#     for k,v in  log.Logger.manager.loggerDict.items()  :
#         print('+ [%s] {%s} ' % (str.ljust( k, 20)  , str(v.__class__)[8:-2]) )
#         if not isinstance(v, log.PlaceHolder):
#             for h in v.handlers:
#                 print('     +++',str(h.__class__)[8:-2] )