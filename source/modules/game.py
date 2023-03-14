import logging as log
log.basicConfig(format='[%(levelname)s] %(funcName)s: %(message)s', level=log.INFO)
myLogger = log.getLogger('myLogger')


import discord
import discord.ext.bridge as bridge
import random


class GameCog(discord.Cog):
    
    def __init__(self, bot):
        self.bot = bot
    
    #event holder: create message with one reaction, create reaction-listener that edits/adds names to the message (and deletes)
    @bridge.bridge_command()
    async def game(self, ctx, role: str, maxsize: int = 5):
        myLogger.debug('called .game')
        
        if maxsize < 1 or maxsize > 20:
            await ctx.send('cmdError: .game team size must be between range 1 ≤ maxsize ≤ 20', delete_after=3)
            return
        
        roster = "1. {}{}".format(ctx.author.mention, "".join([f"\n{i}. " for i in range(2, maxsize+1)]))
        embed = discord.Embed(title='Team Roster', description=roster)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
        
        await ctx.send(role, embed=embed, view = GameInterface(embed, role, ctx.author, maxsize))
    

#View subclass extension
class GameInterface(discord.ui.View):
    
    def __init__(self, embed: discord.Embed, role: str, author: discord.User, max_size: int):
        super().__init__(timeout=None)
        self.embed = embed
        self.role = role
        self.author = author
        self.max_size = max_size
        self.players = [author.mention]
        self.prospectives = []
        
    def update_embed(self):
        roster = ('' if len(self.players) < self.max_size else '**TEAM IS CURRENTLY FULL**\n') \
            + "\n".join([f"{i}. {self.players[i - 1]}" for i in range(1, len(self.players) + 1)]) \
            + "\n" \
            + "\n".join([f"{i}. " for i in range(len(self.players) + 1, self.max_size + 1)])
            
        if len(self.prospectives) > 0:
            roster += "\n\nProspective Members:\n" + "\n".join([f"- {self.prospectives[i]}" for i in range(len(self.prospectives))])
        
        self.embed.description = roster

    @discord.ui.button(emoji='❤️', label="Join", style=discord.ButtonStyle.success)
    async def button1_callback(self, button, interaction):
        myLogger.debug('pressed "Join" button')
        user = interaction.user.mention
        
        # check if roster full
        if len(self.players) == self.max_size: 
            await interaction.response.send_message(content='Sorry, The roster is full!', delete_after=3)
            
        # check if you're already in roster
        elif user in self.players:
            await interaction.response.defer()
            return
        
        # add to roster (and remove from prospective if applicable)
        else:
            if user in self.prospectives:
                del self.prospectives[self.prospectives.index(user)]
            self.players.append(user)
            
        self.update_embed()    
        await interaction.response.edit_message(embed=self.embed)

    @discord.ui.button(emoji='🗑️', label="Leave", style=discord.ButtonStyle.danger)
    async def button2_callback(self, button, interaction):
        myLogger.debug('pressed "Remove" button')
        user = interaction.user.mention
        
        # remove if in roster
        if user in self.players:
            del self.players[self.players.index(user)]
        
        # remove if in prospective
        if user in self.prospectives:
            del self.prospectives[self.prospectives.index(user)]
        
        self.update_embed()
        await interaction.response.edit_message(embed=self.embed)
    
    @discord.ui.button(emoji='❓', label="Maybe", style=discord.ButtonStyle.primary)
    async def button3_callback(self, button, interaction):
        myLogger.debug('pressed "Maybe" button')
        user = interaction.user.mention
        
        # if in roster, delete from list, add to prospective
        if user in self.players:
            del self.players[self.players.index(user)]
            self.prospectives.append(user)
            
        # if already in prospective, remove
        elif user in self.prospectives:
            del self.prospectives[self.prospectives.index(user)]
            
        # add to prospective
        else:
            self.prospectives.append(user)
            
        self.update_embed()
        await interaction.response.edit_message(embed=self.embed)
    
    @discord.ui.button(emoji='🪖', label='Recruit', style=discord.ButtonStyle.secondary, row=2)
    async def recruit(self, button, interaction):
        log.debug('pressed "Recruit" button')
        if len(self.prospectives) == 0:
            await interaction.response.send_message(content='There are no prospective players to recruit!', delete_after=3)
            return
        
        i = random.randint(0, len(self.prospectives)-1)
        recruit = self.prospectives[i]
        del self.prospectives[i]
        self.players.append(recruit)
        
        self.update_embed()
        await interaction.response.edit_message(embed=self.embed)
    
    @discord.ui.button(emoji='🎲', label='Randomize', style=discord.ButtonStyle.secondary, row=2)
    async def randomize(self, button, interaction):
        log.debug('pressed "Randomize" button')
        self.embed.color = discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        
        self.update_embed()
        await interaction.response.edit_message(embed=self.embed)