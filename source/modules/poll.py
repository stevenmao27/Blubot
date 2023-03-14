import logging as log
log.basicConfig(format='[%(levelname)s] %(funcName)s: %(message)s', level=log.INFO)
myLogger = log.getLogger('myLogger')


import discord
import discord.ext.bridge as bridge


class PollCog(discord.Cog):
    
    def __init__(self, bot):
        self.bot = bot
    
    #choice == 0: defaults to yes/no
    #choice > 0: variable
    @bridge.bridge_command(description='Create a poll.')
    async def poll(self, ctx, question, *choices):
        myLogger.debug('called .poll')
        await ctx.message.delete()
        await ctx.send('```' + question + '```', view = PollInterface(ctx, question, choices))


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
        if len(choices) == 0:
            self.choices = ('yes', 'no')
            self.lengths = (6, 5)
        else:
            self.lengths = tuple([len(choice) + 3 for choice in choices])

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
