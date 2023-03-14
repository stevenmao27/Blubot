import logging
from typing import ItemsView
logging.basicConfig(format='[%(levelname)s] %(funcName)s(): %(message)s', level=logging.DEBUG)
log = logging.getLogger('myLogger')

import discord
import discord.ext.bridge as bridge
import openai
import os
from dotenv import main

main.load_dotenv()
openai.api_key = os.environ.get('OPENAI_API_TOKEN')

class ChatGPTCog(discord.Cog):
    
    def __init__(self, bot):
        self.bot = bot
        
    @bridge.bridge_command(description='Send a chat prompt to GPT-3.5-Turbo.')
    async def chatgpt(self, ctx, prompt: str, temperature: float = 1):
        log.debug(f"chatgpt command called by {ctx.author} in {ctx.channel} with prompt: {prompt} and temperature: {temperature}")
        await ctx.defer()
        
        if temperature < 0 or temperature > 2:
            await ctx.edit(content="Temperature represents the randomness of the output. It must be between 0 and 2.")
            return
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{'role': 'user', 'content': prompt}],
                temperature=temperature,
                n=1
            )
        except:
            await ctx.edit(content="OpenAI API Encountered an Error.")
            return
        
        embed = discord.Embed(title="GPT-3 API Response", description=f"```Consumed {response['usage']['total_tokens']} tokens for ${round(0.000002 * int(response['usage']['total_tokens']), 6)}\n\nPrompt: {prompt}```{response['choices'][0]['message']['content']}") # type: ignore
        await ctx.edit(embed=embed)



