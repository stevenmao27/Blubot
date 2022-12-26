import logging as log
log.basicConfig(format='[%(levelname)s] %(funcName)s: %(message)s', level=log.INFO)
myLogger = log.getLogger('myLogger')


import discord
from discord.ext import commands, tasks
import random
import asyncio


class UtilityCog(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    async def helpme(self, ctx):
        myLogger.debug('called .helpme')
        await ctx.message.delete()
        msg = '```Commands (prefix= . ):\n.ping [@user]'
        msg += '\n.spam [@user] [number of times (1/sec)] note: anyone can reply to stop spam'
        msg += '\n.bombtimer [@user] [minutes] [(optional) seconds] ["custom message"] note: only victim can reply to stop timer'
        msg += "\n.weather days=[number of entries] loc=[specific_location] coods=[29.38472,-95.23413]"
        msg += '\n.cf note: flip a coin!'
        msg += '\n.game [@role] [(optional) max_team_size] note: fully functional!```'
        await ctx.send(msg)
    
    @commands.command(aliases=['coinflip'])
    async def cf(self, ctx):
        myLogger.debug('called .cf')
        await ctx.message.delete()
        first_roll = random.randint(0,1)
        heads = 1 if first_roll == 0 else 0
        tails = 1 if first_roll == 1 else 0
        first_result = '🗣️ Heads' if first_roll == 0 else '🪙 Tails'
        message_string = f'You flipped **{first_result}!** `Your head:tail ratio is {heads}:{tails}`'
        await ctx.send(message_string, view=CoinflipView(heads, tails))

    @commands.command()
    async def timer(self, ctx, *args):
        myLogger.debug('called .timer')
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
            myLogger.debug('caught bad input for .timer')
            await ctx.respond('Bad Input', ephemeral=True, delete_after=2)
        
        await ctx.send(f"⌛Starting {ctx.author.mention}'s timer of {seconds} seconds⌛")
        await asyncio.sleep(seconds)
        await ctx.send(f'🔔Your {seconds} seconds is up!🔔')

    @commands.command()
    async def spam(self, ctx, user: discord.User, repeats: int):
        myLogger.debug('called .spam')
        if repeats > 12:
            await ctx.send('abuse is bad, {}'.format(ctx.author.name))
            return
        await ctx.send('spamming {} {} times'.format(user.name, repeats))
        #func
        for i in range(repeats):
            await ctx.send(user.mention, delete_after=3)
            await asyncio.sleep(1.5)







class CoinflipView(discord.ui.View):
    def __init__(self, heads, tails):
        super().__init__()
        self.total_heads = heads
        self.total_tails = tails
        self.vals = {0: '🗣️ Heads', 1: '🪙 Tails'}
        self.recent_result = 0
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

