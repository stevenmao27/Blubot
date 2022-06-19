import discord
import asyncio
from discord.ext import commands
import youtube_dl
from youtube_dl import YoutubeDL
from datetime import datetime
import random

#difference from main.py due to classes and cogs:
#   @bot.command        -> @commands.command
#   @bot.event          -> @commands.Cog.listener()
#   async def foo(ctx)  -> async def foo(self, ctx)
#   bot                 -> self.bot 
class Thing():
    value = 999
class MCog(commands.Cog):
    #universal attributes
    YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': 'True', }
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    Q = {}

    def __init__(self, bot):
        self.bot = bot

    #delete for update
    def addGuildToQueue(self, ctx):
        myGuild = ctx.guild.id
        if myGuild in self.Q:
            return
        else:
            self.Q[myGuild] = {'q': [], 'channel': None, 'client': None, 'playing': None, 'isPlaying': False} 
            #Global_Queue{ myGuild: {queue: [music objects], channel: ChannelOBJ, playing: MusicOBJ, isPlaying: Bool}}

    @commands.command()
    async def join(self, ctx):
        if not ctx.message.author.voice:
            await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
            return
        else:
            channel = ctx.message.author.voice.channel
        await channel.connect()

    @commands.command()
    async def leave(self, ctx):
        voice_client = ctx.message.guild.voice_client
        if voice_client.is_connected():
            await voice_client.disconnect()
        else:
            await ctx.send("The bot is not connected to a voice channel.")
    
    #rtype: list[dict{str:}]
    #params: search string/web URL, top number of results to show
    #returns list of top 5 queries and their information
    def search_yt(self, search_query, num_results = 3):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                top_results = ydl.extract_info(f"ytsearch{num_results}:{search_query}", download=False)['entries'][:num_results]
                print('top_results ready')
                for i in range(len(top_results)):
                    top_results[i] = {
                        'title': top_results[i]['title'],
                        'source': top_results[i]['formats'][0]['url'],
                        'channel': top_results[i]['channel'],
                        'duration': top_results[i]['duration'],
                        'url': top_results[i]['webpage_url']
                    }
                print('top results updated, search_yt complete')
                
            except Exception as err:
                print(f'SEARCH_YT ERROR\t search="{search_query}" errorType="{type(err).__name__}"')
                return False
            return top_results
    
    #rtype: None
    #looks at queue, decides whether to play the next song in queue or stop
    def play_next(self, myGuild):
        print('called play_next... ', end='')
        if len(self.Q[myGuild]['q']) > 0:
            print("there's something in queue... ", end='')
            self.Q[myGuild]['isPlaying'] = True
            #assigns url AND removes from queue
            music_url = self.Q[myGuild]['q'][0]['source']
            print('setting url source, current song, and popping off queue... ', end='')
            curr_song = self.Q[myGuild]['playing'] = self.Q[myGuild]['q'].pop(0)
            print('now playing', curr_song['title'])
            self.Q[myGuild]['client'].play(discord.FFmpegPCMAudio(music_url, **self.FFMPEG_OPTIONS), after = lambda e: self.play_next(myGuild))
        else:
            self.Q[myGuild]['isPlaying'] = False
            self.Q[myGuild]['playing'] = None

    def skip_song(self, myGuild):
        print('running skip...')
        self.Q[myGuild]['playing'] = None
        self.play_next(myGuild)

    def resume_song(self, myGuild):
        print('running resume...', self.Q[myGuild]['client'], '------', not self.Q[myGuild]['isPlaying'], '------', self.Q[myGuild]['client'].is_paused())
        if self.Q[myGuild]['client'] and not self.Q[myGuild]['isPlaying'] and self.Q[myGuild]['client'].is_paused():
            self.Q[myGuild]['client'].resume()
            self.Q[myGuild]['isPlaying'] = True
    
    def pause_song(self, myGuild):
        print('running pause...', self.Q[myGuild]['client'], '------', not self.Q[myGuild]['isPlaying'], '------', self.Q[myGuild]['client'].is_paused())
        if self.Q[myGuild]['client'] and self.Q[myGuild]['isPlaying'] and self.Q[myGuild]['client'].is_playing():
            self.Q[myGuild]['client'].pause()
            self.Q[myGuild]['isPlaying'] = False
    
    
    #rtype: None
    #similar to play_next but optimized for first-time playing
    #checks if a song in queue + checks if bot's connected, then begins to play
    '''
    async def play_now(self, myGuild):
        print('called play_now, queue:', [obj['title'] for obj in self.Q[myGuild]['q']])

        if len(self.Q[myGuild]['q']) > 0:
            self.Q[myGuild]['isPlaying'] = True
            music_url = self.Q[myGuild]['q'][0]['source']
            curr_song = self.Q[myGuild]['playing'] = self.Q[myGuild]['q'].pop(0)
            print('now playing', curr_song['title'])
            audio_source = discord.FFmpegPCMAudio(music_url, **self.FFMPEG_OPTIONS)
            self.Q[myGuild]['client'].play(audio_source, after = lambda e: self.play_next(myGuild))

        else:
            self.Q[myGuild]['isPlaying'] = False
    '''
    @commands.command()
    async def thing(self, ctx):
        newthing = Thing()
        print(newthing.value)
        newthing.value += 1
        print(newthing)
    @commands.command()
    async def skip(self, ctx):
        print('ran .skip')
        myGuild = ctx.guild.id
        await self.skip_song(myGuild)

    @commands.command()
    async def resume(self, ctx):
        print('ran .resume')
        myGuild = ctx.guild.id
        await self.resume_song(myGuild)

    @commands.command()
    async def pause(self, ctx):
        print('ran .pause???')
        myGuild = ctx.guild.id
        await self.pause_song(myGuild)

    @commands.command()
    #dynamically checks for URL link or search query, then attempts to play
    async def p(self, ctx, *args, aliases=('q', 'play', 'queue', 'np')):
        myGuild = ctx.guild.id
        print('called .p...', end='')

        try:
            print('not...', end='')
            author_channel = ctx.author.voice.channel
            self.addGuildToQueue(ctx)
            print('broken...', end='')

        except:
            print('not in a channel')
            await ctx.send('You have to be in a voice channel first')
            return

        else:
            print('yet')
            #if first play OR in wrong channel, set client AND connect to correct channel
            if not ctx.guild.voice_client or self.Q[myGuild]['client'].channel != author_channel: 
                print('setting queue VC to authors current channel')
                if ctx.guild.voice_client and ctx.guild.voice_client.is_connected():
                    print('disconnecting current client')
                    await ctx.guild.voice_client.disconnect()
                    print('done or skip disconnect')
                self.Q[myGuild]['client'] = await author_channel.connect() #connects AND sets client (if first time)
                print('setting up done')
            
            #no arg: print queue, URL arg: search and play, query arg: search, ask for choice, then play
            if len(args) == 0:
                print('showing queue')
                if not self.Q[myGuild]['playing'] or self.Q[myGuild]['isPlaying'] == False:
                    await ctx.send('```Nothing is currently playing at this time```')
                else:
                    full_message = f'```Currently Playing: "{self.Q[myGuild]["playing"]["title"]}" by [{self.Q[myGuild]["playing"]["channel"]}] '
                    full_message += f'Duration: {self.Q[myGuild]["playing"]["duration"]}s\n\nNext Songs Queue: \n'
                    for i, music_obj in enumerate(self.Q[myGuild]['q']):
                        full_message += f"{i+1}: \"{music_obj['title']}\" by [{music_obj['channel']}] Duration: {music_obj['duration']}s\n"
                    await ctx.send(full_message + '```')
                    return
            
            elif args[0].startswith('https://www.youtube.com/watch'): #search URL
                #search web_url directly and send object to music queue
                with YoutubeDL(self.YDL_OPTIONS) as ydl:
                    try:
                        print('attempting to extract URL:', args[0])
                        music_obj = ydl.extract_info(args[0], download=False)
                        music_obj = {
                        'title': music_obj['title'],
                        'source': music_obj['formats'][0]['url'],
                        'channel': music_obj['channel'],
                        'duration': music_obj['duration'],
                        'url': music_obj['webpage_url']
                        }
                        print('found source! appending title: "', music_obj['title'], '" to queue...', end='')
                        self.Q[myGuild]['q'].append(music_obj)
                        print('done')
                    except:
                        print('URL search failed. URL =', args[0])

            else: #search query, display search results, ask for which one, then add to queue
                if args[-1].isdigit():
                    num_results = int(args[-1])
                    if num_results < 1 or num_results > 25:
                        await ctx.send('Too many requested results. Setting to default = 3')
                        num_results = 3
                    args = args[:-1]
                else:
                    num_results = 3

                song_list = self.search_yt(' '.join(args), num_results)
                
                #send song choices
                query_message_content = '```Song Selection: reply with a corresponding number or button click (30s timeout)\n'
                for i in range(len(song_list)):
                    query_message_content += f'{i+1}. "{song_list[i]["title"]}" by [{song_list[i]["channel"]}] ({int(song_list[i]["duration"])//60}:{"0" if len(str(int(song_list[i]["duration"])%60)) == 1 else "" + str(int(song_list[i]["duration"])%60)})\n'
                query_message_content += '```'
                try:
                    query_message = await ctx.send(query_message_content, view=self.SearchQueryView(self, song_list, myGuild, timeout=30))
                except Exception as err:
                    print(err)

                #wait for reply or button press
                def check(msg):
                   return msg.content.isdigit() and int(msg.content) > 0 and int(msg.content) <= num_results
                   
                try:
                    msg = await self.bot.wait_for('message', check = check, timeout = 30)
                except:
                    return
                else:
                    await query_message.delete()
                    await msg.delete()
                    self.Q[myGuild]['q'].append(song_list[int(msg.content)-1])
                
            #now play
            if not self.Q[myGuild]['isPlaying']:
                await self.play_next(myGuild)

    class SearchQueryButton(discord.ui.Button):
        def __init__(self, MCog, view, music_object, guild_id, label, style = discord.ButtonStyle.primary, emoji = None, custom_id = None, row = 0):
            super().__init__(label=label, style=style, custom_id=custom_id, emoji=emoji, row=row)
            self.custom_view = view
            self.music = music_object
            self.myGuild = guild_id
            self.MCogObject = MCog
        
        async def callback(self, interaction):
            MCog.Q[self.myGuild]['q'].append(self.music)
            if not MCog.Q[self.myGuild]['isPlaying']:
                self.MCogObject.play_next(self.myGuild)
                await interaction.response.send_message(content='added to queue!', delete_after=1)
    
    class SearchQueryView(discord.ui.View):
        def __init__(self, MCog, song_list, guild_id, timeout = None):
            super().__init__(timeout = timeout)
            num_buttons = len(song_list)
            for i in range(num_buttons):
                self.add_item(MCog.SearchQueryButton(MCog, self, song_list[i], guild_id, label=str(i+1), row=(i//5)))

def setup(bot):
    bot.add_cog(MCog(bot))