import logging as log
log.basicConfig(format='[%(levelname)s] %(funcName)s: %(message)s', level=log.INFO)
myLogger = log.getLogger('myLogger')


import discord
from discord.ext import commands, tasks


class SocialCog(commands.Cog):
    
    def __init__(self, bot):
        self.bot = bot
    
    #event holder: create message with one reaction, create reaction-listener that edits/adds names to the message (and deletes)
    @commands.command()
    async def game(ctx, role: discord.Role, maxSize: int = 5):
        await ctx.message.delete()
        myLogger.debug('called .game')
        message_string = f'**{f"{role.mention}" if maxSize != 1 else "TEAM IS NOW FULL"}\n1. {ctx.author.mention}**'
        #input error verification
        if maxSize < 1 or maxSize > 20:
            await ctx.send('cmdError: .game team size must be between range 1 ≤ maxSize ≤ 20', delete_after=3)
            return
        await ctx.send(message_string, view = GameInterface(role, ctx.author, maxSize))
    
    #choice == 0: defaults to yes/no
    #choice > 0: variable
    @commands.command()
    async def poll(ctx, question, *choices):
        myLogger.debug('called .poll')
        await ctx.message.delete()
        await ctx.send('```' + question + '```', view = PollInterface(ctx, question, choices))







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
