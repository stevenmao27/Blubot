from wsgiref import headers
import discord
from discord.ext import commands
import requests
import json
import time
import random
import asyncio
import datetime
import os

database = {
    'loop': 0
}
TERMINATION_KEYWORDS = ['stop', 'here', 'ok', 'aqui', 'alright', 'coming', 'oi', 'e']

intents = discord.Intents().all()
bot = commands.Bot(command_prefix='.', intents=intents)

@bot.event
async def on_ready():
    print('Logged in as', bot.user)

@bot.event
async def on_message(msg):
    if msg.author == bot.user:
        return
    
    msg_text = msg.content
    
    #for .spam command
    if msg_text in TERMINATION_KEYWORDS:
        database['loop'] = 999

    if msg_text.lower() == 'hi blubot':
        await msg.channel.send('hi ' + msg.author.name + '!')

    if msg_text.startswith('gimme') and msg_text.split(' ')[1][0].isnumeric():
        minutes = int(msg_text.split(' ')[1]) if 'ish' not in msg_text.split(' ') else int(msg_text.split(' ')[1]) * (1 + random.randint(3,7)/10.)
        #get_context() itself is an coroutine obj, but somehow returns as a context obj
        context_obj = await bot.get_context(msg)
        await context_obj.invoke(bot.get_command('bombtimer'), user=msg.author, minutes=minutes, seconds=0, custom_message='{} set a timer that will blow at {}:{}')
    
    #allows commands
    await bot.process_commands(msg)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('you used the command wrong')


################################################
################################################
############    BOT COMMANDS "."    ############
################################################
################################################

#help
@bot.command()
async def helpme(ctx):
    await ctx.message.delete()
    msg = '```Commands (prefix= . ):\n.ping [@user]'
    msg += '\n.spam [@user] [number of times (1/sec)] note: anyone can reply to stop spam'
    msg += '\n.bombtimer [@user] [minutes] [(optional) seconds] ["custom message"] note: only victim can reply to stop timer'
    msg += "\n.weather days=[number of entries] loc=[specific_location] coods=[29.38472,-95.23413] note: i don't know why i made this"
    msg += '\n.cf note: flip a coin!'
    msg += '\n.game [@role] [(optional) max_team_size] note: fully functional!```'
    await ctx.send(msg)

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
    while database['loop'] < repeats:
        await ctx.send(user.mention, delete_after=repeats)
        await asyncio.sleep(1)
        database['loop'] += 1
    database['loop'] = 0

#bombtimer
@bot.command()
async def bombtimer(ctx, user: discord.User, minutes: int, seconds: int = 0, custom_message: str = ''):
    totalTime = minutes * 60 + seconds
    INIT_MSG = 'Beginning bomb timer on {} in {} minutes and {} seconds\nReply "stop" to terminate the timer' if custom_message == '' else custom_message
    FAIL_MSG = "{} capped, he's not coming back"
    SUCCESS_MSG = 'Welcome back, {}'
    def isStop(m):
        if m.content in TERMINATION_KEYWORDS:
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
    await ctx.message.delete()
    full_msg = '```'
    houses = {
        #Basically Missouri City
        "Missouri_City": 'https://api.weather.gov/gridpoints/HGX/56,87/forecast'
    }
    loc_name = "Missouri_City"
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
    full_msg += '```'
    await ctx.send(full_msg)

#coinflip
class CoinflipView(discord.ui.View):
    def __init__(self, heads, tails):
        super().__init__()
        self.total_heads = heads
        self.total_tails = tails
        self.vals = {0: '🗣️ Heads', 1: '🪙 Tails'}
        self.recent_result = None
        self.E_down = False
        self.emojiBank = ['😩','😊','🤣','❤️','😁','😘','😳','😎','🪙','👌','🤐','😣','😏','🤑','🙃']
    def updated_message(self):
        return f'You flipped **{self.vals[self.recent_result]}!** `Your head:tail ratio is {self.total_heads}:{self.total_tails}`'
    @discord.ui.button(label="FLIP ME", style=discord.ButtonStyle.primary, emoji='😩')
    async def button_callback(self, button, interaction):
        button.emoji = self.emojiBank[random.randint(0, len(self.emojiBank) - 1)]
        if len(button.label) < 80 and not self.E_down:
            button.label += 'E'
        else:
            button.label = button.label[:len(button.label) - 1]
        if len(button.label) == 80 or len(button.label) == 7:
            self.E_down = not self.E_down

        self.recent_result = random.randint(0,1)
        if self.recent_result == 0:
            self.total_heads += 1
        else:
            self.total_tails += 1
        await interaction.response.edit_message(content=self.updated_message(), view=self) #add view b/c need to update view

@bot.command()
async def cf(ctx):
    await ctx.message.delete()
    print('.cf called')
    first_roll = random.randint(0,1)
    heads = 1 if first_roll == 0 else 0
    tails = 1 if first_roll == 1 else 0
    first_result = '🗣️ Heads' if first_roll == 0 else '🪙 Tails'
    message_string = f'You flipped **{first_result}!** `Your head:tail ratio is {heads}:{tails}`'
    await ctx.send(message_string, view=CoinflipView(heads, tails))

from dotenv import main
main.load_dotenv()
BLUBOT_API_TOKEN = os.environ.get('BLUBOT_API_TOKEN')
try:
    bot.run(BLUBOT_API_TOKEN)
except:
    print("bot didn't run somehow")