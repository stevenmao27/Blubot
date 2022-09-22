import discord
import asyncio
from discord.ext import commands, tasks
from youtube_dl import YoutubeDL
from datetime import timedelta, datetime
from collections import deque
from random import sample

#difference from main.py due to classes and cogs:
#   @bot.command        -> @commands.command
#   @bot.event          -> @commands.Cog.listener()
#   async def foo(ctx)  -> async def foo(self, ctx)
#   bot                 -> self.bot 

class Song():
    def __init__(self, entry):
        self.title = entry['title']
        self.source = entry['formats'][0]['url']
        self.channel = entry['channel']
        self.url = entry['webpage_url']
        self.duration_seconds = max(1, int(entry['duration']))
        self.duration_string = str(timedelta(seconds=self.duration_seconds))

class MusicPlayer():
    def __init__(self):
        print('MusicPlayer: Creating Music Player')
        self.isPlaying = False #refers to song presence. Can isPlaying == True while player.client.is_paused() == True
        self.currSong = None

        self.queue = deque()
        self.cache = deque()

        self.time_since_song = datetime.now()
        self.time_offset = timedelta(seconds=0)
        self.time_recent_pause = None

        self.recent_ControlPanel = None
    
    async def init_client(self, first_channel):
        print('running init_client')
        self.client = await first_channel.connect()
        print('client connection set!')
    
    def updateControlPanel(self, new_ControlPanel):
        if self.recent_ControlPanel:
            self.recent_ControlPanel.stop()
        self.recent_ControlPanel = new_ControlPanel

    def addCache(self, song: Song):
        self.cache.append(song)
        if len(self.cache) > 5: #size limit
            self.cache.popleft()
    
    def push_currSong_back(self):
        if self.currSong:
            self.queue.appendleft(self.currSong)
            self.currSong = None

    def reset_timestamp(self):
        self.time_since_song = datetime.now()
        self.time_offset = timedelta(seconds=0)
        self.time_recent_pause = None

    def pause_song(self):
        self.time_recent_pause = datetime.now()
        self.client.pause()

    def resume_song(self):
        self.time_offset += datetime.now() - self.time_recent_pause
        self.client.resume()

    #rtype: None
    #preq: Client and Channel connected
    #desc: same as skip + ignores current song, force skips to next

    def play_next(self):
        print('- play_next()')
        self.client.stop()

        #cache finished song
        if self.currSong:
            self.addCache(self.currSong)

        if len(self.queue) > 0:
            print('found Song in queue...')
            self.isPlaying = True
            self.currSong = self.queue.popleft()
            currSong_source = self.currSong.source

            print('NOW PLAYING:', self.currSong.title)
            self.reset_timestamp()
            audio_player = discord.FFmpegPCMAudio(currSong_source, **MCog.FFMPEG_OPTIONS)
            self.client.play(audio_player, after = lambda e: self.play_next)
            print('...play complete')
        else:
            print('nothing left in queue. resetting isPlaying, currSong, client')
            self.isPlaying = False
            self.currSong = None
            self.client.stop()
    
    def back_track(self):
        self.push_currSong_back()
        if len(self.cache) > 0:
            self.queue.appendleft(self.cache.pop())
        self.play_next()



class MCog(commands.Cog):
    #universal attributes
    YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': 'True', }
    FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
    MUSIC_DATABASE = {}
    COMMAND_ERROR_MESSAGE = '❌ Contexually Invalid Command: Make Sure You Are Connected and Playing!'

    def __init__(self, bot):
        self.bot = bot

    #checks if interactor is connected and in same channel
    def active_permission_check(self, ctx):
        print('- permission_check()')
        try:
            player = self.MUSIC_DATABASE[ctx.guild.id]
            return player.client.is_connected() and ctx.author.voice.channel == player.client.channel and player.isPlaying
        except:
            print('- active permission check failed, defaulting return to False')
            #Either 1) Author not connected to channel 2) Guild + Player doesn't exist 3) Guild client not initialized
            return False

    #preq: guaranteed author connected to channel
    #rtype: bool
    #only for first initiation, add guild to database
    async def first_connect(self, ctx):
        if ctx.guild.id in self.MUSIC_DATABASE: #guild already added
            return False
        else:
            #dict{str: MusicPlayer()}
            self.MUSIC_DATABASE[ctx.guild.id] = MusicPlayer()
            await self.MUSIC_DATABASE[ctx.guild.id].init_client(ctx.author.voice.channel)
            print('- first_connect: Guild Recorded, MusicPlayer Created, Client Initiated, and Connected to Channel!')
            return True

    #rtype: list[Music]
    #desc: returns list of top x song queries OR a single Song
    #ex: self.search_yt(self, ['cat', 'videos', 'q=5'])
    def search_yt(self, args: tuple, num_results = 3):
        print('called search_yt()')
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            #URL: searches, sends Song
            if args[0].startswith('https://www.youtube.com/watch'):
                try:
                    return Song(ydl.extract_info(args[0], download=False))
                except:
                    print('ERROR: URL search failed. URL =', args[0])

            #query: check for num_results, searches, sends Song/list[]
            else:
                #set num_results (blank)
                
                #search and organize
                search_query = ' '.join(args)
                try:
                    top_results = ydl.extract_info(f"ytsearch{num_results}:{search_query}", download=False)['entries'][:num_results]
                    for i in range(len(top_results)):
                        top_results[i] = Song(top_results[i])
                    
                except Exception as err:
                    print(f'SEARCH_YT ERROR\t search="{search_query}" errorType="{type(err).__name__}"')
                    return False
                
                print('- exiting search_yt()')
                #return
                if len(top_results) == 1:
                    return top_results[0]
                else:
                    return top_results

            raise Exception


# slash commands
    @discord.slash_command(description='Sends requested song to the front of the queue')
    async def play(self, ctx, 
        search: discord.Option(str, "Enter Search or URL"), 
        results: discord.Option(int, "Enter number of results", min_value=1, max_value=25, default=1)
        ):
        await ctx.defer()
        await self.play_command(ctx, (search,), 'play', results)
        await ctx.interaction.followup.send('/play successful', ephemeral=True, delete_after=0)

    @discord.slash_command(description='Send requested song to the back of the queue')
    async def queue(self, ctx, 
        search: discord.Option(str, "Enter Search or URL"), 
        results: discord.Option(int, "Enter number of results", min_value=1, max_value=25, default=3)
        ):
        await ctx.defer()
        await self.play_command(ctx, (search,), 'queue', results)
        await ctx.interaction.followup.send('/queue successful', ephemeral=True, delete_after=0)
    
    @discord.slash_command(description='Force skips current song and plays requested song')
    async def playnow(self, ctx, 
        search: discord.Option(str, "Enter Search or URL"), 
        results: discord.Option(int, "Enter number of results", min_value=1, max_value=25, default=3)
        ):
        await ctx.defer()
        await self.play_command(ctx, (search,), 'playnow', results)
        await ctx.interaction.followup.send('/playnow successful', ephemeral=True, delete_after=0)



    @discord.slash_command(description='Resumes paused audio')
    async def resume(self, ctx):
        if self.active_permission_check(ctx) and self.MUSIC_DATABASE[ctx.guild.id].client.is_paused():
            self.MUSIC_DATABASE[ctx.guild.id].resume_song()
            await ctx.respond('/resume successful', delete_after=0)
        else:
            await ctx.respond(self.COMMAND_ERROR_MESSAGE, delete_after=3)

    @discord.slash_command(description='Pauses playing audio')
    async def pause(self, ctx):
        if self.active_permission_check(ctx) and self.MUSIC_DATABASE[ctx.guild.id].client.is_playing():
            self.MUSIC_DATABASE[ctx.guild.id].pause_song()
            await ctx.respond('/pause successful', delete_after=0)
        else:
            await ctx.respond(self.COMMAND_ERROR_MESSAGE, delete_after=3)

    @discord.slash_command(description='Skips current song, if any, and plays next song in queue')
    async def skip(self, ctx):
        if self.active_permission_check(ctx) and self.MUSIC_DATABASE[ctx.guild.id].isPlaying:
            self.MUSIC_DATABASE[ctx.guild.id].play_next()
            await ctx.respond('/skip successful', delete_after=0)
        else:
            await ctx.respond(self.COMMAND_ERROR_MESSAGE, delete_after=3)

    @discord.slash_command(description='Backtracks a song in cache')
    async def back(self, ctx):
        if self.active_permission_check(ctx) and self.MUSIC_DATABASE[ctx.guild.id].isPlaying:
            self.MUSIC_DATABASE[ctx.guild.id].back_track()
            await ctx.respond('/back successful', delete_after=0)
        else:
            await ctx.respond(self.COMMAND_ERROR_MESSAGE, delete_after=3)
    
    @discord.slash_command(description='Clears queue') #desc
    async def clear(self, ctx): #name
        if self.active_permission_check(ctx)and self.MUSIC_DATABASE[ctx.guild.id].isPlaying: #conditional
            self.MUSIC_DATABASE[ctx.guild.id].queue.clear() #command
            await ctx.respond('/clear successful', delete_after=0) #message
        else:
            await ctx.respond(self.COMMAND_ERROR_MESSAGE, delete_after=3)

    @discord.slash_command(description='Restarts currently playing song')
    async def restart(self, ctx):
        if self.active_permission_check(ctx)and self.MUSIC_DATABASE[ctx.guild.id].isPlaying:
            self.MUSIC_DATABASE[ctx.guild.id].currSong = None 
            self.MUSIC_DATABASE[ctx.guild.id].play_next()
            await ctx.respond('/restart successful', delete_after=0) 
        else:
            await ctx.respond(self.COMMAND_ERROR_MESSAGE, delete_after=3)

    @discord.slash_command(description='Leaves the channel. Queue data is preserved.')
    async def leave(self, ctx):
        if ctx.guild.id in self.MUSIC_DATABASE and self.MUSIC_DATABASE[ctx.guild.id].client.is_connected():
            await self.MUSIC_DATABASE[ctx.guild.id].client.disconnect()
            self.MUSIC_DATABASE[ctx.guild.id].isPlaying = False
            await ctx.respond('/leave successful', delete_after=0)
        else:
            await ctx.respond(self.COMMAND_ERROR_MESSAGE, delete_after=3)

    #control panel cmds
    @discord.slash_command(description='Brings up control panel. Must be connected to same VC')
    async def control(self, ctx):
        if self.active_permission_check(ctx):
            #if needed, delete last Panel
            if self.MUSIC_DATABASE[ctx.guild.id].recent_ControlPanel:
                await self.MUSIC_DATABASE[ctx.guild.id].recent_ControlPanel.view_message.delete()

            #create and set Panel
            newView = ControlPanel(self.MUSIC_DATABASE[ctx.guild.id]) #create view
            self.MUSIC_DATABASE[ctx.guild.id].updateControlPanel(newView) #push view to player
            view_message = await ctx.send(newView.update_message(), view=newView) #send msg+view
            newView.view_message = view_message #send msg to view

            #if needed, start task loop
            if not self.task_updateControlPanel.is_running():
                self.task_updateControlPanel.start()

            await ctx.respond('/control successful', delete_after=0)
        else:
            await ctx.respond(self.COMMAND_ERROR_MESSAGE, delete_after=3)

################################################## SLASH COMMANDS  ##################################################
################################################## ############### ##################################################
################################################## PREFIX COMMANDS ##################################################

    @commands.command(aliases=['ctl'])
    async def ctrl(self, ctx):
        if self.active_permission_check(ctx):
            newView = ControlPanel(self.MUSIC_DATABASE[ctx.guild.id]) #create view
            self.MUSIC_DATABASE[ctx.guild.id].updateControlPanel(newView) #push view to player
            view_message = await ctx.send(newView.update_message(), view=newView) #send msg+view
            newView.view_message = view_message #send msg to view

            if not self.task_updateControlPanel.is_running():
                self.task_updateControlPanel.start()
        else:
            await ctx.respond(self.COMMAND_ERROR_MESSAGE, delete_after=3) 

    @commands.command(aliases=['l'])
    async def lv(self, ctx):
        if ctx.guild.id in self.MUSIC_DATABASE and self.MUSIC_DATABASE[ctx.guild.id].client.is_connected():
            await self.MUSIC_DATABASE[ctx.guild.id].client.disconnect()
            self.MUSIC_DATABASE[ctx.guild.id].isPlaying = False

    @commands.command()
    async def rst(self, ctx):
        if self.active_permission_check(ctx)and self.MUSIC_DATABASE[ctx.guild.id].isPlaying:
            self.MUSIC_DATABASE[ctx.guild.id].currSong = None 
            self.MUSIC_DATABASE[ctx.guild.id].play_next()
        else:
            await ctx.respond(self.COMMAND_ERROR_MESSAGE, delete_after=3)

    # prefix commands
    @commands.command(aliases=['rs'])
    async def r(self, ctx):
        await ctx.message.delete()
        if self.active_permission_check(ctx) and self.MUSIC_DATABASE[ctx.guild.id].client.is_paused():
            self.MUSIC_DATABASE[ctx.guild.id].resume_song()
        else:
            await ctx.respond(self.COMMAND_ERROR_MESSAGE, delete_after=3)

    @commands.command(aliases=['pa', 'pu'])
    async def ps(self, ctx):
        await ctx.message.delete()
        if self.active_permission_check(ctx) and self.MUSIC_DATABASE[ctx.guild.id].client.is_playing():
            self.MUSIC_DATABASE[ctx.guild.id].pause_song()
        else:
            await ctx.respond(self.COMMAND_ERROR_MESSAGE, delete_after=3)
    
    @commands.command(aliases=['fw', 'sp'])
    async def sk(self, ctx):
        await ctx.message.delete()
        if self.active_permission_check(ctx):
            self.MUSIC_DATABASE[ctx.guild.id].play_next()
        else:
            await ctx.respond(self.COMMAND_ERROR_MESSAGE, delete_after=3)
    
    @commands.command()
    async def bk(self, ctx):
        await ctx.message.delete()
        if self.active_permission_check(ctx):
            self.MUSIC_DATABASE[ctx.guild.id].back_track()
        else:
            await ctx.respond(self.COMMAND_ERROR_MESSAGE, delete_after=3)

    @commands.command(aliases=['cr']) #alias 
    async def cl(self, ctx): #name
        await ctx.message.delete()
        if self.active_permission_check(ctx):
            self.MUSIC_DATABASE[ctx.guild.id].queue.clear() #command
        else:
            await ctx.respond(self.COMMAND_ERROR_MESSAGE, delete_after=3)

    @commands.command(aliases=['q', 'pn'])
    async def p(self, ctx, *args):
        await ctx.message.delete()
        invocation = ctx.invoked_with
        await self.play_command(ctx, args, invocation)

#command function for play, queue, and playnow
    async def play_command(self, ctx, args: tuple, invocation, num_results = 3):
        print('called play function')

        #check connection,set guild
        if not ctx.author.voice:
            await ctx.send("You aren't connected to a voice channel right now!", delete_after=2)
            return
        
        #guaranteed author connected, setup if first time OR wrong channel
        try:
            if not await self.first_connect(ctx) and ctx.author.voice.channel != self.MUSIC_DATABASE[ctx.guild.id].client.channel:
                await self.MUSIC_DATABASE[ctx.guild.id].client.move_to(ctx.author.voice.channel)
                print('- moved to new channel!')
        except Exception as err:
            print('problem is,', err)
        
        player = self.MUSIC_DATABASE[ctx.guild.id]

        #if no args, bring up controls/queue, return
        #if play/playnow/queue, search and perform
        if len(args) == 0:
            return

            '''
            if not player.isPlaying:
                await ctx.send('```Nothing is currently playing at this time```')
            else:
                full_message = f'```Currently Playing: "{player.currSong.title}" by [{player.currSong.channel}] ({player.currSong.duration_string})\n\nNext Songs Queue: \n'
                for i, song in enumerate(player.queue):
                    full_message += f"{i+1}: \"{song.title}\" by [{song.channel}] Duration: {song.duration_string}\n"
                await ctx.send(full_message + '```')
            return
            '''

        #format options num_results, q= overrides num_results slash command
        while '-' in args[-1] and len(args[-1]) <= 3:
            option = args[-1][1:]
            args = args[:-1]

            #num_results option
            if option.isdigit(): # -3 = 3 results
                if int(option) > 0 and int(option) <= 25:
                    num_results = int(option)
                else: #already defaulted, but need edge case checking
                    num_results = 3

        #search query
        #note: finalSong is technically a list right now, but will become a Song instance
        finalSong = self.search_yt(args, num_results)

        
        #if finalSong has multiple choices, query it up
        if type(finalSong) == list:
            #create and send message + View
            query_message_content = f'```md\n#       Song Selection: reply with corresponding number or buttons       #\n                            Invoked Command: {invocation}\n\n'
            for i, song in enumerate(finalSong):
                query_message_content += f'{i+1}. "{song.title}" by [{song.channel}] <Length: {song.duration_string}>\n'
            query_message_content += '```'

            try:
                print('WAITING FOR SONG SELECTION TO QUEUE')
                query_message = await ctx.send(query_message_content, view=SearchQueryView(finalSong, player, invocation, timeout=30))
            except Exception as err:
                print(err)

            #wait for reply or button press
            '''
            def check(msg):
                return msg.content.isdigit() and int(msg.content) > 0 and int(msg.content) <= len(finalSong)
            '''

            try:
                msg = await self.bot.wait_for('message', check = lambda msg: msg.content.isdigit() and int(msg.content) > 0 and int(msg.content) <= len(finalSong), timeout = 30)
            except:
                return
            else:
                await msg.delete()
                finalSong = finalSong[int(msg.content) - 1]
                
        #queue and play
        if invocation == 'p' or invocation == 'play':
            player.queue.appendleft(finalSong)
            if not player.isPlaying:
                player.play_next()
        elif invocation == 'q' or invocation == 'queue':
            player.queue.append(finalSong)
        elif invocation == 'pn' or invocation == 'playnow':
            player.queue.appendleft(finalSong)
            player.play_next()

    @tasks.loop(seconds=11, count=20)
    async def task_updateControlPanel(self):
        print('- beginning tasks.loop')
        for guildId, player in self.MUSIC_DATABASE.items(): #for every guild, check for existing controlPanel and edit
            if player.recent_ControlPanel and player.isPlaying: #is_finished() useless because timeout=None
                controlPanel = player.recent_ControlPanel
                await controlPanel.view_message.edit(content=controlPanel.update_message(), view=controlPanel)
                
    @task_updateControlPanel.after_loop
    async def task_databaseCleanup(self):
        #clean up inactive guilds
        for guildId, player in self.MUSIC_DATABASE.items():
            if not (player.isPlaying or player.client.is_connected()):
                print(f'deleting player in guild {guildId}')
                del self.MUSIC_DATABASE[guildId]

        if len(self.MUSIC_DATABASE) > 0:
            print('restarting tasks.loop')
            self.task_updateControlPanel.restart()
    
    @discord.slash_command(description='Lists details of Music Cog Module Commands')
    async def help_music(self, ctx):
        message = '`[ Help Commands for Music Controls ]`\n'
        message += "`.p or .q or .pn` to join channel but don't play\n"
        message += '`/leave or .lv or .l` to leave channel\n'
        message += '`/play [search/URL] [results] or .p [search/URL] -[results]` appends song to front of queue\n- `/play Tchaikovsky Barcarolle` searches for top 3 (default) results\n'
        message += '`/queue [search/URL] [results] or .q [search/URL] -[results]` appends song to back of queue\n- `.q Moonlight Sonata -1` automatically queues top result\n'
        message += '`/playnow [search/URL] [results] or .pn [search/URL] -[results]` force play requested song\n- `.p Turkish March -5` searches for top 5 results\n'
        message += '`/control or .ctrl` brings up control panel; only one can be active at a time\n'
        message += '`/pause or .ps or .pa or .pu` pauses if song is playing\n'
        message += '`/resume or .r or .rs` resumes if song is paused\n'
        message += '`/skip or .sk or .sp or .fw` skips current song\n'
        message += '`/back or .bk` moves the queue back by one song\n'
        message += '`/restart or .rst` restarts current song\n'
        message += '`/clear or .cl or .cr` clears the current queue; will not affect current song'
        await ctx.respond(message)








class SearchQueryView(discord.ui.View):
    def __init__(self, song_list, player, invocation, timeout = None):
        super().__init__(timeout = timeout)
        for i in range(len(song_list)):
            self.add_item(SearchQueryButton(self, song_list[i], player, invocation, label=str(i+1), row=(i//5)))

class SearchQueryButton(discord.ui.Button):
    def __init__(self, view, song: Song, player, invocation, label, style = discord.ButtonStyle.primary, emoji = None, custom_id = None, row = 0):
        super().__init__(label=label, style=style, custom_id=custom_id, emoji=emoji, row=row)
        self.custom_view = view
        self.song = song
        self.player = player
        self.invocation = invocation
    
    async def callback(self, interaction):
        if self.invocation == 'p' or self.invocation == 'play':
                self.player.queue.appendleft(self.song)
                if not self.player.isPlaying:
                    self.player.play_next()
        elif self.invocation == 'q' or self.invocation == 'queue':
            self.player.queue.append(self.song)
        elif self.invocation == 'pn' or self.invocation == 'playnow':
            self.player.queue.appendleft(self.song)
            self.player.play_next()
        await interaction.response.send_message(content='song queued successfully', delete_after=1)
        
        #disable view
        self.view.disable_all_items()



#controls panel
class ControlPanel(discord.ui.View):
    def __init__(self, player):
        super().__init__(timeout=None)
        self.player = player
        #self.view_message = view_message   #set in cmd call
    
    def update_message(self):
        #if updated while isPlaying = False, give error message
        if not self.player.isPlaying:
            return '```Voice Client is inactive, play audio to begin.```'

        #current song
        full_message = f'```autohotkey\nCurrently Playing: "{self.player.currSong.title}" by [{self.player.currSong.channel}] ({self.player.currSong.duration_string})\n\n'
        
        #song progress (time2 - time1) / total_time * 100 * 0.5blocks/percent
        delta_time = datetime.now() - self.player.time_since_song - self.player.time_offset

        minutes, seconds = divmod(delta_time.seconds + delta_time.days * 86400, 60)
        hours, minutes = divmod(minutes, 60)
        timestamp = '{:d}:{:02d}:{:02d}'.format(hours, minutes, seconds)

        circle_position = min(49, int(delta_time.total_seconds() / self.player.currSong.duration_seconds * 100 / 2))
        emoji = '▶️' if self.player.client.is_paused() or not self.player.isPlaying else '⏸️'
        full_message += f'           {emoji} {"▬" * circle_position}ⵔ{"═" * (49 - circle_position)}             '
        full_message += f'\n                                                                     {timestamp}\n```'

        #queue list
        full_message += '```md\nNext Songs Queue: \n----------------------------------------------------------------------------\n'
        for i, song in enumerate(self.player.queue):
            full_message += f"{i+1}. \"{song.title}\" by [{song.channel}] <Length: {song.duration_string}>\n"
        full_message += '```'

        return full_message

    @discord.ui.button(style=discord.ButtonStyle.danger, emoji='⏮')
    async def button1_callback(self, button, interaction):
        if interaction.user.voice and interaction.user.voice.channel == self.player.client.channel and self.player.isPlaying:
            self.player.back_track()
        else:
            print('user either not connected, not in same channel, or isPlaying false')
        await interaction.response.edit_message(content=self.update_message(), view=self)

    @discord.ui.button(style=discord.ButtonStyle.blurple, emoji='⏯')
    async def button2_callback(self, button, interaction):
        if interaction.user.voice and interaction.user.voice.channel == self.player.client.channel and self.player.isPlaying:
            if self.player.client.is_paused():
                self.player.resume_song()
            else:
                self.player.pause_song()
        else:
            print('user either not connected, not in same channel, or isPlaying false')
        await interaction.response.edit_message(content=self.update_message(), view=self)

    @discord.ui.button(style=discord.ButtonStyle.success, emoji='⏭')
    async def button3_callback(self, button, interaction):
        if interaction.user.voice and interaction.user.voice.channel == self.player.client.channel and self.player.isPlaying:
            self.player.play_next()
        else:
            print('user either not connected, not in same channel, or isPlaying false')
        await interaction.response.edit_message(content=self.update_message(), view=self)

    @discord.ui.button(style=discord.ButtonStyle.gray, emoji='🔀')
    async def button4_callback(self, button, interaction):
        if interaction.user.voice and interaction.user.voice.channel == self.player.client.channel and self.player.isPlaying:
            self.player.queue = sample(self.player.queue, k=len(self.player.queue))
        else:
            print('user either not connected, not in same channel, or isPlaying false')
        await interaction.response.edit_message(content=self.update_message(), view=self)

    @discord.ui.button(style=discord.ButtonStyle.gray, emoji='🔁')
    async def button5_callback(self, button, interaction):
        await interaction.response.edit_message(content=self.update_message(), view=self)





def setup(bot):
    bot.add_cog(MCog(bot))