import logging as log
log.basicConfig(format='[%(levelname)s] %(funcName)s: %(message)s', level=log.INFO)
myLogger = log.getLogger('myLogger')


import discord
import discord.ext.bridge as bridge


class GameCog(discord.Cog):
    
    def __init__(self, bot):
        self.bot = bot
    
    #event holder: create message with one reaction, create reaction-listener that edits/adds names to the message (and deletes)
    @bridge.bridge_command()
    async def game(self, ctx, role: discord.Role, maxsize: int = 5):
        await ctx.message.delete()
        myLogger.debug('called .game')
        message_string = f'**{f"{role.mention}" if maxsize != 1 else "TEAM IS NOW FULL"}\n1. {ctx.author.mention}**'
        #input error verification
        if maxsize < 1 or maxsize > 20:
            await ctx.send('cmdError: .game team size must be between range 1 ≤ maxsize ≤ 20', delete_after=3)
            return
        await ctx.send(message_string, view = GameInterface(role, ctx.author, maxsize))
    

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
        final_string += f'\n{prospective_string}**'
        return final_string

    @discord.ui.button(label="add", style=discord.ButtonStyle.success)
    async def button1_callback(self, button, interaction):
        myLogger.debug('pressed "add" button')
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
        myLogger.debug('pressed "remove" button')
        #check if you're in the roster, if so, delete, if not, don't say much
        if interaction.user.mention in self.players:
            del self.players[self.players.index(interaction.user.mention)]
        if interaction.user.mention in self.prospectives:
            del self.prospectives[self.prospectives.index(interaction.user.mention)]
        await interaction.response.edit_message(content=self.update_message())
    
    @discord.ui.button(label="perhaps", style=discord.ButtonStyle.secondary)
    async def button3_callback(self, button, interaction):
        myLogger.debug('pressed "perhaps" button')
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