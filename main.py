from wsgiref import headers
import discord
from discord.ext import commands
import requests
import json
import time
import random
import asyncio
from datetime import timedelta, datetime
import os

print('Printing to console log: main.py has started.')

database = {
    'loop': 0
}
TERMINATION_KEYWORDS = ['stop', 'here', 'ok', 'aqui', 'alright', 'coming', 'oi', 'e']

intents = discord.Intents().all()
bot = commands.Bot(debug_guilds=[523693679341207552, 783391965525049384, 784497167578300468], command_prefix='.', intents=intents)
bot.load_extension('music_module')

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
        await ctx.send('you used the command wrong', delete_after=2)

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

@bot.command(aliases=['coinflip'])
async def cf(ctx):
    await ctx.message.delete()
    print('.cf called')
    first_roll = random.randint(0,1)
    heads = 1 if first_roll == 0 else 0
    tails = 1 if first_roll == 1 else 0
    first_result = '🗣️ Heads' if first_roll == 0 else '🪙 Tails'
    message_string = f'You flipped **{first_result}!** `Your head:tail ratio is {heads}:{tails}`'
    await ctx.send(message_string, view=CoinflipView(heads, tails))

#View subclass extension
class GameInterface(discord.ui.View):
    #__init__ overrides parent constructor, so you need to call parent first
    def __init__(self, role: discord.Role, author: discord.User, maxSize: int):
        super().__init__(timeout=None)
        self.role = role
        self.author = author
        self.maxSize = maxSize
        self.players = [author.mention]
        self.prospectives = ['\nPerhaps:']
    def update_message(self):
        prospective_string = ' '.join(self.prospectives) if len(self.prospectives) > 1 else ''
        final_string = f"**{f'{self.role.mention}' if len(self.players) < self.maxSize else 'TEAM IS NOW FULL'}"
        for i in range(len(self.players)):
            final_string += f'\n{i+1}. {self.players[i]}'
        final_string += f'{prospective_string}**'
        return final_string

    @discord.ui.button(label="add", style=discord.ButtonStyle.success)
    async def button1_callback(self, button, interaction):
        print(interaction.user.name, 'pressed e button')
        #check if roster full
        if len(self.players) >= self.maxSize: 
            await interaction.response.send_message(content='The roster is full!', delete_after=1)
        #check if you're already in roster
        elif interaction.user.mention in self.players:
            pass
        else:
            if interaction.user.mention in self.prospectives:
                del self.prospectives[self.prospectives.index(interaction.user.mention)]
            self.players.append(interaction.user.mention)
        await interaction.response.edit_message(content=self.update_message()) # Send a message when the button is clicked

    @discord.ui.button(label="remove", style=discord.ButtonStyle.danger)
    async def button2_callback(self, button, interaction):
        print(interaction.user.name, 'pressed dip button')
        #check if you're in the roster, if so, delete, if not, don't say much
        if interaction.user.mention in self.players:
            del self.players[self.players.index(interaction.user.mention)]
        if interaction.user.mention in self.prospectives:
            del self.prospectives[self.prospectives.index(interaction.user.mention)]
        await interaction.response.edit_message(content=self.update_message())
    
    @discord.ui.button(label="perhaps", style=discord.ButtonStyle.secondary)
    async def button3_callback(self, button, interaction):
        print(interaction.user.name, 'pressed prospective button')
        #if in roster, delete from list, add to prospective
        if interaction.user.mention in self.players:
            del self.players[self.players.index(interaction.user.mention)]
            self.prospectives.append(interaction.user.mention)
        #if already in prospective, remove
        elif interaction.user.mention in self.prospectives:
            del self.prospectives[self.prospectives.index(interaction.user.mention)]
        #add to prospective
        else:
            self.prospectives.append(interaction.user.mention)
        #update
        await interaction.response.edit_message(content=self.update_message())

#event holder: create message with one reaction, create reaction-listener that edits/adds names to the message (and deletes)
@bot.command()
async def game(ctx, role: discord.Role, maxSize: int = 5):
    await ctx.message.delete()
    print('.game called')
    message_string = f'**{f"{role.mention}" if maxSize != 1 else "TEAM IS NOW FULL"}\n1. {ctx.author.mention}**'
    #input error verification
    if maxSize < 1 or maxSize > 20:
        await ctx.send('cmdError: .game team size must be between range 1 ≤ maxSize ≤ 20', delete_after=3)
        return
    await ctx.send(message_string, view = GameInterface(role, ctx.author, maxSize))

#subclasses Button to add callback/logic functionality
class PollButton(discord.ui.Button):
    def __init__(self, view, label, style = discord.ButtonStyle.primary, emoji = None, custom_id = None, row = 0):
        super().__init__(label=label, style=style, custom_id=custom_id, emoji=emoji, row=row)
        self.custom_view = view

    #contains every button logic
    async def callback(self, interaction):
        #search for user
        user = ['', -1, -1] #[choice, member object, index]
        for choice, member_list in self.custom_view.results.items():
            for i in range(len(member_list)):
                if member_list[i] == interaction.user:
                    user[0] = choice
                    user[1] = member_list[i]
                    user[2] = i
                    break
            else:
                continue
            break
        
        if user[1] != -1: #already part of list... two choices: move choice or remove yourself. both delete first, only moving adds
            if user[0] != self.label: #user's current choice != clicked button, wants to change choice
                self.custom_view.results[self.label].append(interaction.user)
            del self.custom_view.results[user[0]][user[2]]
        else: #add user to choice's list
            self.custom_view.results[self.label].append(interaction.user)
        await interaction.response.edit_message(content=self.custom_view.update_message())

#Interface for Polling on send_message()
class PollInterface(discord.ui.View):
    def __init__(self, ctx, question, choices):
        super().__init__(timeout=None)
        self.choices = choices
        self.author = ctx.author
        self.question = question
       #self.results = dict{str:list} : {choice1: [members], choice2: [members]...}
        self.lengths = [len(choice) + 3 for choice in choices]

        #create buttons and an object holding all choices and the supporters
        if len(choices) == 0: #creates yes/no buttons
            yes_button = PollButton(self, label='yes', row=0)
            no_button = PollButton(self, label='no', row=0)
            self.add_item(yes_button)
            self.add_item(no_button)
            self.results = {'yes':[], 'no':[]}
        else: #creates variable buttons
            self.results = {}
            for i, choice in enumerate(choices):
                self.add_item(PollButton(self, label=choice, row=i//5))
                self.results[choice] = []

    #rtype: str
    #returns display message
    def update_message(self): #shows choosers
        full_string = '```\n' + self.question + '\n'
        for choice, members in self.results.items():
            #full_string += f'"{choice}"\n    {", ".join(members)}' #shows name MEMBERS ARE OBJECTS NOT STRINGS YET
            diff = (max(self.lengths) - self.lengths[self.choices.index(choice)]) * ' '
            full_string += f'"{choice}": {diff}{len(members)} votes\n'
            for member in members:
                full_string += f'{diff}{member}\n'
        return full_string + '```'

#poll
#no choices: defaults to yes/no
#>0 choices: variable
@bot.command()
async def poll(ctx, question, *choices):
    await ctx.message.delete()
    print('called .poll')
    await ctx.send('```' + question + '```', view = PollInterface(ctx, question, choices))

@bot.command()
async def timer(ctx, *args):
    await ctx.message.delete()
    seconds = 0
    try:
        for elem in args:
            #for minutes
            if elem[-1] == 'm':
                seconds += 60 * int(elem[:-1])
            elif elem[-1] == 's':
                seconds += int(elem[:-1])
            elif elem.isdigit():
                seconds += int(elem)
    except Exception as e:
        print('.timer error:', e)
        await ctx.respond('Bad Input', ephemeral=True, delete_after=2)
    
    await ctx.send(f"⌛Starting {ctx.author.mention}'s timer of {seconds} seconds⌛")
    await asyncio.sleep(seconds)
    await ctx.send(f'🔔Your {seconds} seconds is up!🔔')

#run
from dotenv import main
main.load_dotenv()
BLUBOT_API_TOKEN = os.environ.get('BLUBOT_API_TOKEN')
try:
    bot.run(BLUBOT_API_TOKEN)
except:
    print("bot didn't run somehow")