import logging
logging.basicConfig(format='[%(levelname)s] %(funcName)s(): %(message)s', level=logging.INFO)
log = logging.getLogger('myLogger')

import discord
import discord.ui as UI
import discord.ext.bridge as bridge


class TodoCog(discord.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        
    @bridge.bridge_command()
    async def todo(self, ctx, msg):
        await ctx.send(f'You said: {msg}')

class TodoApp(UI.View):
    
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(label="add", style=discord.ButtonStyle.success))
        self.add_item(discord.ui.Button(label="remove", style=discord.ButtonStyle.danger))
        self.add_item(discord.ui.Button(label="clear", style=discord.ButtonStyle.secondary))
        self.add_item(discord.ui.Button(label="list", style=discord.ButtonStyle.primary))
    
    @UI.button(label="add", style=discord.ButtonStyle.success)
    async def button1_callback(self, button, interaction):
        await interaction.response.send_message('add')

    @UI.button(label="remove", style=discord.ButtonStyle.danger)
    async def button2_callback(self, button, interaction):
        await interaction.response.send_message('remove')

    @UI.button(label="clear", style=discord.ButtonStyle.secondary)
    async def button3_callback(self, button, interaction):
        await interaction.response.send_message('clear')

    @UI.button(label="list", style=discord.ButtonStyle.primary)
    async def button4_callback(self, button, interaction):
        await interaction.response.send_message('list')