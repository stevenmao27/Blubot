import logging as log
log.basicConfig(format='[%(levelname)s] %(funcName)s: %(message)s', level=log.INFO)
myLogger = log.getLogger('myLogger')


import discord
import discord.ext.bridge as bridge
import random
import asyncio


class UtilityCog(discord.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        self.spam_targets = {}
        self.active_timers = {}
    
    @discord.Cog.listener()
    async def on_message(self, message):
        if message.author in self.spam_targets:
            self.spam_targets[message.author] = True
    
    @bridge.bridge_command(aliases=['cf'], description='Flips a coin')
    async def coinflip(self, ctx):
        myLogger.debug('called .cf')
        await ctx.message.delete()
        first_roll = random.randint(0,1)
        heads = 1 if first_roll == 0 else 0
        tails = 1 if first_roll == 1 else 0
        first_result = '🗣️ Heads' if first_roll == 0 else '🪙 Tails'
        message_string = f'You flipped **{first_result}!** `Your head:tail ratio is {heads}:{tails}`'
        await ctx.send(message_string, view=CoinflipView(heads, tails))

    @bridge.bridge_command(description='Starts a timer')
    async def timer(self, ctx: bridge.BridgeApplicationContext, minutes: int, seconds: int = 0):
        myLogger.debug('called .timer')
        await ctx.message.delete() # type: ignore
        
        await ctx.send(f"⌛Starting {ctx.author.name}'s timer of {minutes} minutes and {seconds} seconds⌛")
        await asyncio.sleep(seconds)
        await ctx.send(f'🔔{ctx.author.mention}, {minutes}:{seconds} is up!🔔')

    @bridge.bridge_command(description='Spams a user up to 25 times. Target can interrupt by messaging in the chat.')
    async def spam(self, ctx: bridge.BridgeApplicationContext, user: discord.User, message: str = '', repeats: int = 7):
        myLogger.debug('called .spam')
        
        if repeats > 25:
            await ctx.reply('too many repeats')
            return
        
        await ctx.reply(f'spamming {user.name} {repeats} times')
        
        self.spam_targets[user] = False
        for i in range(repeats):
            if self.spam_targets[user]:
                await ctx.send(f'{user.name} has responded. Stopping spam command.')
                break
            await ctx.send(user.mention + ' ' + message, delete_after=2)
            await asyncio.sleep(2)
        del self.spam_targets[user]






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

