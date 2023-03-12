import logging as log
log.basicConfig(format='[%(levelname)s] %(funcName)s: %(message)s', level=log.INFO)
myLogger = log.getLogger('myLogger')


import discord
from discord.ext import commands
import asyncio
import random
import datetime


class FunCog(commands.Cog):
    
    TERMINATION_KEYWORDS = ['stop', 'here', 'ok', 'aqui', 'alright', 'coming', 'oi', 'e', 'hi']
    
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author == self.bot.user:
            return
        
        msg_text = msg.content
        
        #for .spam command
        # if msg_text in FunCog.TERMINATION_KEYWORDS:
        #     self.loop_counter = 999

        if msg_text.lower() == 'hi blubot':
            await msg.channel.send(f'Hi {msg.author.name}!')

        # elif msg_text.startswith('gimme') and msg_text.split(' ')[1][0].isnumeric():
        #     minutes = int(msg_text.split(' ')[1]) if 'ish' not in msg_text.split(' ') else int(msg_text.split(' ')[1]) * (1 + random.randint(3,7)/10.)
        #     #get_context() itself is an coroutine obj, but somehow returns as a context obj
        #     context_obj = await self.bot.get_context(msg)
        #     await context_obj.invoke(self.bot.get_command('bombtimer'), user=msg.author, minutes=minutes, seconds=0, custom_message='{} set a timer that will blow at {}:{}')

    #bombtimer
    @commands.command()
    async def bombtimer(self, ctx, user: discord.User, minutes: int, seconds: int = 0, custom_message: str = ''):
        myLogger.debug('called .bombtimer')
        totalTime = minutes * 60 + seconds
        INIT_MSG = '🚨Beginning bomb timer on {} in {} minutes and {} seconds\nReply "stop" to terminate the timer🚨' if custom_message == '' else custom_message
        FAIL_MSG = "{} lied."
        SUCCESS_MSG = 'Welcome back, {}'
        def isStop(m):
            if m.content in self.TERMINATION_KEYWORDS:
                if m.author == user:
                    return True
                else:
                    self.bot.loop.create_task(m.channel.send('not you, dummy'))
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
            msg = await self.bot.wait_for('message', timeout=totalTime, check=isStop)
        except asyncio.TimeoutError:
            await ctx.send(FAIL_MSG.format(user.mention))
            await ctx.send('spamming {} {} times'.format(user.name, 10))
            #spam now
            for i in range(10):
                await ctx.send(user.mention)
                await asyncio.sleep(1.5)
        else:
            await ctx.send(SUCCESS_MSG.format(user.mention))