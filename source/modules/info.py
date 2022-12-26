import logging as log
log.basicConfig(format='[%(levelname)s] %(funcName)s: %(message)s', level=log.INFO)
myLogger = log.getLogger('myLogger')


import discord
from discord.ext import commands, tasks
import requests
import json


class InfoCog(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
    
    #weather
    @commands.command()
    async def weather(ctx, *args):
        myLogger.debug('called .weather')
        await ctx.message.delete()
        full_msg = '```'
        houses = {}
        loc_name = "Missouri_City"
        days = -1
        for val in args:
            if val[:4] == 'days':
                days = int(val[5:])
            elif val[:3] == 'loc':
                loc_name = val[4:]
            elif val[:5] == 'coods':
                coordinates = val[6:]
                temp_req = requests.get('https://api.weather.gov/points/{}'.format(coordinates))
                temp_r = json.loads(temp_req.text)
                houses['new_loc'] = temp_r['properties']['forecast']
                loc_name = 'new_loc'
        
        loc = houses[loc_name]
        req = requests.get(loc)
        r = json.loads(req.text)
        forecasts = r['properties']['periods']
        
        if days == -1:
            days = len(forecasts)
        
        for i in range(min(days, len(forecasts))):
            day = forecasts[i]
            full_msg += '{}: {}F, {}\n'.format(day['name'], day['temperature'], day['shortForecast'])
        full_msg += '```'
        await ctx.send(full_msg)