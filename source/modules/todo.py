import logging
from typing import ItemsView
logging.basicConfig(format='[%(levelname)s] %(funcName)s(): %(message)s', level=logging.INFO)
log = logging.getLogger('myLogger')

import discord
import discord.ext.bridge as bridge
from enum import Enum
import random


class TodoCog(discord.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        
    @bridge.bridge_command()
    async def todo(self, ctx, title = "Todo List"):
        embed = discord.Embed(title=title, description="You have initialized a new todo list!", color=discord.Color.brand_green())
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar)
        await ctx.send(embed=embed, view=TodoApp(title, ctx.author))

class TodoApp(discord.ui.View):
    
    def __init__(self, title: str, user: discord.User):
        super().__init__(timeout=None)
        self.title = title
        self.user = user
        
        # holds all item data
        self.embed = discord.Embed(title=self.title)
        self.embed.set_author(name=self.user.display_name, icon_url=self.user.avatar)
        
        # init select menu
        self.select_menu = SelectMenu(self)
        self.add_item(self.select_menu)
    
    # returns index of task in embed, or -1 if not found
    def get_task_index(self, description: str) -> int:
        for i, field in enumerate(self.embed.fields):
            if field.name == description or field.value == description:
                return i
        return -1
    
    # syncs embed with select menu
    async def add_task(self, label: str, value: str):
        self.select_menu.add_item(label, value, Direction.TOP)
        self.embed.fields.insert(0, discord.EmbedField(name=label, value=value, inline=False))
        if self.message:
            await self.message.edit(embed=self.embed, view=self)
    
    async def remove_task(self, description: str):
        i = self.get_task_index(description)
        self.select_menu.remove_item(i)
        self.embed.remove_field(i)
        if self.message:
            await self.message.edit(embed=self.embed, view=self)
    
    async def complete_task(self, description: str):
        i = self.get_task_index(description)
        field_object = self.embed.fields[i]
        
        # remove item
        self.select_menu.remove_item(i)
        self.embed.remove_field(i)
        
        # modify field
        field_object.name = f'✅   ~~{field_object.name[4:]}~~'
        if field_object.value != '':
            field_object.value = f'~~{field_object.value}~~'
        
        # reinsert item
        self.select_menu.add_item(field_object.name, field_object.value, Direction.BOTTOM)
        self.embed.append_field(field_object)
        
        if self.message:
            await self.message.edit(embed=self.embed, view=self)
    
    async def restore_task(self, description: str):
        i = self.get_task_index(description)
        field_object = self.embed.fields[i]
        
        # remove item
        self.select_menu.remove_item(i)
        self.embed.remove_field(i)
        
        # modify field
        field_object.name = f'⬜   {field_object.name[6:-2]}'
        if field_object.value != '':
            field_object.value = field_object.value[2:-2]
        
        # reinsert item
        self.select_menu.add_item(field_object.name, field_object.value, Direction.TOP)
        self.embed.fields.insert(0, field_object)
        
        if self.message:
            await self.message.edit(embed=self.embed, view=self)
    
    
    # sends dialog to add new item
    @discord.ui.button(emoji='➕', label="New Task", style=discord.ButtonStyle.success)
    async def add(self, button, interaction):
        await interaction.response.send_modal(AddItemPrompt(self, title="Add Item"))
    
    @discord.ui.button(emoji='✖️', label='Clear Tasks', style=discord.ButtonStyle.danger)
    async def clear(self, button, interaction):
        # reset embed
        self.embed = discord.Embed(title=self.title, color=discord.Color.brand_green())
        self.embed.set_author(name=self.user.display_name, icon_url=self.user.avatar)
        
        # remove from select menu
        for i in range(len(self.select_menu.options)):
            self.select_menu.remove_item(0)
        
        if self.message:
            await self.message.edit(embed=self.embed, view=self)
        
        await interaction.response.defer()
    
    @discord.ui.button(emoji='❔', label='Randomize', style=discord.ButtonStyle.secondary)
    async def randomize(self, button, interaction):
        self.embed.color = discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        if self.message:
            await self.message.edit(embed=self.embed, view=self)
        await interaction.response.defer()

class Direction(Enum):
    TOP = 0
    BOTTOM = 1

class SelectMenu(discord.ui.Select):
    def __init__(self, view, *args, **kwargs):
        super().__init__(*args, placeholder="Complete or Restore a Task", **kwargs)
        self.options = [discord.SelectOption(label="Null Option")]
        self.parent = view
    
    
    
    def add_item(self, label: str, value: str, direction: Direction = Direction.BOTTOM):
        if self.options[0].label == "Null Option":
            self.options = []
        
        if direction == Direction.BOTTOM:
            self.options.append(discord.SelectOption(label=label, value=value))
        else:
            self.options.insert(0, discord.SelectOption(label=label, value=value))
    
    def remove_item(self, i: int):
        if i < 0 or i >= len(self.options):
            return
        elif len(self.options) == 1:
            self.options = [discord.SelectOption(label="Null Option")]
        else:
            self.options.pop(i)
    
    async def callback(self, interaction: discord.Interaction):
        description = f'{self.values[0]}'
        if description[-2:] == '~~':
            await self.parent.restore_task(self.values[0])
        elif description != 'Null Option':
            await self.parent.complete_task(self.values[0])
        await interaction.response.defer()

class AddItemPrompt(discord.ui.Modal):
    
    def __init__(self, view: TodoApp, *args, **kwargs):
        super().__init__(timeout=None, *args, **kwargs)
        self.view = view
        self.add_item(discord.ui.InputText(
            label="Title", 
            placeholder="Enter item title"
            ))
        self.add_item(discord.ui.InputText(
            label="Description (OPTIONAL)", 
            placeholder="Enter a description for the item", 
            style=discord.InputTextStyle.long,
            required=False
            ))
    
    async def callback(self, interaction: discord.Interaction):
        todo_title = '⬜   ' + self.children[0].value if self.children[0].value else ""
        todo_description = self.children[1].value if self.children[1].value else ""
        await self.view.add_task(todo_title, todo_description)
        await interaction.response.defer()
            
            