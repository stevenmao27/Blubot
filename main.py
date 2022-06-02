from wsgiref import headers
import discord
from discord.ext import commands
import requests
import json
import time
import random
import asyncio
import datetime

bot = commands.Bot(command_prefix='$')

@bot.event
async def on_ready():
    print('Logged in as', bot.user)

@bot.event
async def on_message(msg):
    if msg.author == bot.user:
        return
    
    msg_text = msg.content
    
    if msg_text.lower() == 'hi blubot':
        await msg.channel.send('hi ' + msg.author.name + '!')

    if msg_text.lower().startswith('fuck') and ('you' in msg_text or 'u' in msg_text):
        await msg.channel.send('well fuck you ' + msg.author.name + ' eat shit')

    if msg_text.startswith('gimme') and msg_text.split(' ')[1][0].isnumeric():
        minutes = int(msg_text.split(' ')[1]) if 'ish' not in msg_text.split(' ') else int(msg_text.split(' ')[1]) * (1 + random.randint(3,7)/10.)
        #get_context() itself is an coroutine obj, but somehow returns as a context obj
        context_obj = await bot.get_context(msg)
        await context_obj.invoke(bot.get_command('bombtimer'), user=msg.author, minutes=minutes, seconds=0, custom_message='{} set a timer that will blow at {}:{}')
    #allows commands
    await bot.process_commands(msg)

#command error
@bot.event
async def on_command_error(error, ctx):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('you used the command wrong ahaha')



############################
####    Bot Commands    ####
############################

#ping
@bot.command()
async def ping(ctx, user:discord.User):
    await ctx.send(user.mention)

#spam
@bot.command()
async def spam(ctx, user: discord.User, repeats: int):
    if repeats > 12:
        await ctx.send('abuse is bad, {}'.format(ctx.author.name))
        return
    await ctx.send('spamming {} {} times'.format(user.name, repeats))
    #func
    for x in range(repeats):
        await ctx.send(user.mention)
        await asyncio.sleep(1)

#bombtimer
@bot.command()
async def bombtimer(ctx, user: discord.User, minutes: int, seconds: int = 0, custom_message: str = ''):
    totalTime = minutes * 60 + seconds
    INIT_MSG = 'Beginning bomb timer on {} in {} minutes and {} seconds\nReply "stop" to terminate the timer' if custom_message == '' else custom_message
    FAIL_MSG = '{} capped'
    SUCCESS_MSG = 'Welcome back, {}'
    def isStop(m):
        if m.content == 'stop':
            if m.author == user:
                return True
            else:
                bot.loop.create_task(m.channel.send('not you, dummy'))
                return False
        else:
            return False
    if INIT_MSG[0] == 'B':
        await ctx.send(INIT_MSG.format(user.name, minutes, seconds))
    else:
        now = datetime.datetime.now()
        mins = int((now.minute + minutes)%60)
        hrs = int(now.hour + (now.minute + minutes)//60)
        await ctx.send(INIT_MSG.format(user.name, hrs, mins))
    try:
        msg = await bot.wait_for('message', timeout=totalTime, check=isStop)
    except asyncio.TimeoutError:
        await ctx.send(FAIL_MSG.format(user.mention))
        await ctx.invoke(bot.get_command('spam'), user=user, repeats=minutes)
    else:
        await ctx.send(SUCCESS_MSG.format(user.mention))

#weather
@bot.command()
async def weather(ctx, *args):
    full_msg = ''
    houses = {
        #Basically Missouri City
        "steven's_house": 'https://api.weather.gov/gridpoints/HGX/56,87/forecast',
        "jason's_house": 'https://api.weather.gov/gridpoints/HGX/56,87/forecast'
    }
    loc_name = "steven's_house"
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
    try:
        days
    except:
        days = len(forecasts)
    
    for i in range(min(days, len(forecasts))):
        day = forecasts[i]
        full_msg += '{}: {}F, {}\n'.format(day['name'], day['temperature'], day['shortForecast'])
    await ctx.send(full_msg)

@bot.command()
async def game(ctx, role: discord.Role):
    print('placeholder')
#run
bot.run('OTgxMDM1MjEyMzE2MjMzNzg5.G8ZdQ4.p8gij5Rr_wtTPg_Fyv4KI4ghouSSS7THhHAfnY')