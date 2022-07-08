'''
This script is the class containing all the commands and the loops handled by the bot.
To get a list of all the available commands and how they work,
please either open the commands.txt file or visit my GitHub Repository at https://github.com/theLiuk23/Discord-music-bot.
If you have any question, please write me at ldvcoding@gmail.com
'''


import asyncio
import inspect
import time
import datetime
import discord
import youtube_dl
import exceptions
import configparser
import pywhatkit
import os, sys
from discord.ext import commands
from discord.ext import tasks


class MusicCog(commands.Cog):
    def __init__(self, bot, prefix, volume):
        self.bot = bot
        self.prefix = prefix
        self.volume = volume
        self.queue = []
        self.now_playing = None
        self.is_playing = False
        self.voice_channel = None
        self.last_song_time = None
        self.count1, self.count2 = 0, 0
        self.playlists = []
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn' }
        self.YDL_OPTIONS = {
            'format': 'bestaudio',
            'ignoreerrors':'True',
            'noplaylist': 'True',
            'nowarnings': 'True',
            'quiet': 'True' }


    @tasks.loop(seconds=5)
    async def check_members(self):
        if self.voice_channel is None:
            return
        if len(self.voice_channel.channel.members) <= 1:
            self.count1 += 1
        else:
            self.count1 = 0
        if self.count1 >= 3:   
            await self.disconnect_from_voice_channel()


    @tasks.loop(seconds=5)
    async def check_is_playing(self):
        if self.voice_channel is None:
            return
        if not self.voice_channel.is_playing() and not self.voice_channel.is_paused():
            self.count2 += 1
        else:
            self.count2 = 0
        if self.count2 >= 3:
            await self.disconnect_from_voice_channel()


    async def add_to_error_log(self, error):
        with open("error_log.txt", "a") as file:
            time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            file.write(f"{time} - {str(error)}\n")



    async def connect_to_voice_channel(self, ctx, voice) -> bool:
        try:
            self.voice_channel = await voice.channel.connect()
            await ctx.guild.change_voice_state(channel=self.voice_channel.channel, self_mute=False, self_deaf=True)
            return True
        except:
            return False


    async def disconnect_from_voice_channel(self) -> bool:
        if self.voice_channel is None:
            raise commands.ChannelNotFound("Bot")
        if self.voice_channel.is_connected() is False:
            raise commands.ChannelNotFound("Bot")
        await self.voice_channel.disconnect()
        self.voice_channel = None
        self.queue = []
        self.is_playing = False



    async def ask_video(self, ctx) -> bool:
        await ctx.send("I found this video. Should I go ahead? [y/n]")
        while True:
            try:
                message = await self.bot.wait_for("message", check=lambda m: m.content == "y" or m.content == "n", timeout=10)
                if message.content == "y" or message.content == "yes":
                    return True
                return False
            except asyncio.TimeoutError:
                raise TimeoutError()



    async def send_song_info(self, ctx, query, info):
        embed = discord.Embed(title=f"Search result of: __**{query}**__")
        embed.add_field(name = "Title", value = info['title'])
        embed.add_field(name = "Channel", value = info['channel'])
        embed.add_field(name = "Duration", value = time.strftime('%H:%M:%S', time.gmtime(info['duration'])))
        await ctx.send(embed = embed)


    async def search_song_on_yt(self, ctx, query:str, ask:bool=False, multiple:bool=False) -> bool:
        with youtube_dl.YoutubeDL(self.YDL_OPTIONS) as yt_dl:
            video = yt_dl.extract_info("ytsearch:%s" % query, download=False)['entries'][0]
            song_info = {'source': video['formats'][0]['url'],
                        'title': video['title'],
                        'duration': video['duration'],
                        'channel': video['channel'],
                        'thumbnails': video['thumbnails'],
                        'views': video['view_count'],
                        'url': video['webpage_url'],}
            if song_info['duration'] > 60 * 60 * 2: # limit the duration of the song
                raise exceptions.TooLongVideo(song_info['title'], time.strftime('%H:%M:%S', time.gmtime(song_info['duration'])))
            if multiple:
                await self.choose_video(ctx, query, video)
            await self.send_song_info(ctx, query, song_info)
            if ask:
                if await self.ask_video(ctx) is False:
                    return
            self.queue.append([song_info, ctx.author.voice.channel])
            # await ctx.send("Added to the queue successfully!")
            if self.is_playing is False:
                await self.play()
            return True


    def my_after(self, error=None):
        coro = self.play()
        fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
        try:
            fut.result()
        except:
            fut.cancel()


    async def play(self):
        if len(self.queue) <= 0:
            self.is_playing = False
            self.now_playing = None
            self.queue = []
            return

        source = self.queue[0][0]['source']
        self.now_playing = self.queue[0]
        self.queue.pop(0)
        if self.voice_channel is None or self.voice_channel.is_connected() is False:
            raise commands.ChannelNotFound("Bot")
        if self.voice_channel.is_playing() is False:
            self.voice_channel.play(discord.FFmpegPCMAudio(source, **self.FFMPEG_OPTIONS), after=self.my_after)
            self.last_song_time = datetime.datetime.now()
        self.voice_channel.source = discord.PCMVolumeTransformer(self.voice_channel.source, volume=self.volume)
        self.is_playing = True


    async def reload_bot(self, ctx):
        await ctx.send("The bot is now relaoding.")
        await self.bot.close()
        os.execv(sys.executable, ['python3'] + ['main.py'])


    async def save_playlist(self, ctx, pl_name):
        if self.now_playing is None and len(self.queue) == 0:
            raise exceptions.QueueIsEmpty()
        queue = list(self.queue) # copy of original queue
        queue.insert(0, self.now_playing)
        config = configparser.RawConfigParser()
        config.read(f'playlists/{pl_name}.ini')
        
        with open(f'playlists/{pl_name}.ini', 'w') as file:
            for index, song in enumerate(queue):
                config.add_section(f'song{index}')
                config.set(f'song{index}', 'title', song[0]['title'])
            config.write(file)




    async def load_playlists(self):
        self.playlists = []
        for file in os.listdir("playlists"):
            self.playlists.append(file.replace(".ini", ""))



    async def playlist_to_queue(self, ctx, pl_name):
        config = configparser.RawConfigParser()
        config.read(f'playlists/{pl_name}.ini')
        with open(f'playlists/{pl_name}.ini', 'r'):
            for song in config.sections():
                await self.search_song_on_yt(ctx, config.get(song, 'title'))
                if self.is_playing is False:
                    await self.play()






    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.command(name="p")
    async def p(self, ctx, *args):
        query = " ".join(args)
        ask = False
        multiple = False

        if ctx.author.voice is None:
            raise commands.ChannelNotFound("User")
        elif len(args) <= 0:
            raise commands.MissingRequiredArgument(inspect.Parameter("query", inspect._ParameterKind.KEYWORD_ONLY))
        elif self.voice_channel is None:
            await self.connect_to_voice_channel(ctx, ctx.author.voice)

        # By typing "-a" the user wants to check the video before playing it
        if "-a" in args:
            query = query.replace(" -a", "")
            ask = True

        await self.search_song_on_yt(ctx, query, ask, multiple)


    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.command(name="pl")
    async def pl(self, ctx, *args):
        pl_name = "_".join(args)
        if len(args) <= 0:
            await self.load_playlists()
            await ctx.send("Here's a list of the saved playlists:\n**" + "\n".join(self.playlists) + "**")
            return
        if pl_name not in self.playlists:
            raise exceptions.PlaylistNotFound(pl_name)
        elif ctx.author.voice is None:
            raise commands.ChannelNotFound("User")
        if self.voice_channel is None:
            await self.connect_to_voice_channel(ctx, ctx.author.voice)
        
        await self.playlist_to_queue(ctx, pl_name)

        
    @commands.command(name="skip")
    async def skip(self, ctx):
        if self.voice_channel is None:
            raise commands.ChannelNotFound("Bot")
        if len(self.queue) <= 0:
            await self.disconnect_from_voice_channel()
            await ctx.send("There are no other songs in the queue.")
            return
        self.voice_channel.stop()
        await self.play()


    @commands.command(name="np")
    async def np(self, ctx):
        if self.last_song_time is None:
            raise exceptions.BotIsNotPlaying()
        if self.now_playing is None:
            raise exceptions.BotIsNotPlaying()
        now = datetime.datetime.now()
        song = self.now_playing[0]
        time_stamp = time.strftime("%H:%M:%S", time.gmtime((now - self.last_song_time).total_seconds()))
        percentage = round((now - self.last_song_time).total_seconds() / song['duration'] * 100, 1)
        embed = discord.Embed(title="__**Now playing**__")
        embed.set_image(url=song['thumbnails'][-1]['url'])
        embed.add_field(name="Title", value=song['title'], inline = True)
        embed.add_field(name="Channel", value=song['channel'], inline = True)
        embed.add_field(name="Views", value=f"{song['views']:,}", inline = True)
        embed.add_field(name="Time Stamp", value=f'{time_stamp} ({percentage}%)', inline = True)
        embed.add_field(name="Duration", value=time.strftime('%H:%M:%S', time.gmtime(song['duration'])), inline = True)
        embed.add_field(name="Link", value=f"[YouTube]({song['url']})")
        await ctx.send(embed=embed)


    @commands.command(name="next")
    async def next(self, ctx):
        if len(self.queue) <= 0:
            raise exceptions.QueueIsEmpty()
        songs = []
        for i, song in enumerate(self.queue):
            songs.append(song[0]['title'])
        await ctx.send("Here's a list of the songs in the music queue:\n" + "\n".join(songs))


    @commands.command(name="stop")
    async def stop(self, ctx):
        if self.voice_channel is not None:
            await ctx.send(f'Disconnecting from "{self.voice_channel.channel}" voice channel')
            await self.disconnect_from_voice_channel()
        else:
            raise exceptions.BotIsNotPlaying()


    @commands.command(name="offline")
    @commands.is_owner()
    async def offline(self, ctx):
        await ctx.send("Going offline! See ya later.")
        if self.voice_channel is not None:
            await self.disconnect_from_voice_channel()
        await self.bot.close()


    @commands.command(name="pause")
    async def pause(self, ctx):
        if self.voice_channel is None:
            raise commands.ChannelNotFound("Bot")
        if not self.voice_channel.is_playing():
            raise exceptions.BotIsNotPlaying()
        self.voice_channel.pause()
        await ctx.send('Music paused.')


    @commands.command(name="resume")
    async def resume(self, ctx):
        if self.voice_channel is None:
            raise commands.ChannelNotFound("Bot")
        if self.voice_channel.is_playing():
            raise exceptions.BotIsAlreadyPlaying()
        self.voice_channel.resume()
        await ctx.send('Music resumed.')


    @commands.command(name="prefix")
    async def change_prefix(self, ctx, *args):
        if len(args) <= 0:
            raise commands.MissingRequiredArgument(inspect.Parameter("prefix", inspect._ParameterKind.KEYWORD_ONLY))
        if len(args) >= 2:
            raise commands.BadArgument("This function needs only one argument.")
        new_prefix = "".join(args)
        if len(new_prefix) >= 2:
            raise commands.BadArgument("The prefix must be a single character.")
        if new_prefix == self.prefix:
            raise commands.BadArgument("New prefix is the same as the old one.")
        cp = configparser.RawConfigParser()
        cp.read("settings.ini")
        cp.set("variables", "prefix", new_prefix)
        with open("settings.ini", "w") as save:
            cp.write(save)
        await ctx.send(f'I changed the bot prefix to {new_prefix}.')
        await self.reload_bot(ctx)


    @commands.command(name="newpl")
    async def newpl(self, ctx, *args):
        if len(args) <= 0:
            raise commands.MissingRequiredArgument(inspect.Parameter("playlist_name", inspect._ParameterKind.KEYWORD_ONLY))
        await self.save_playlist(ctx, "_".join(args))
        await self.load_playlists()


    @commands.command(name="help")
    async def help(self, ctx, *args):
        embed = discord.Embed(color= discord.Colour.dark_teal())
        embed.add_field(name='Here\'s a github page containing all the "Music From YT!" bot info:', value='[Music From YT! - github.com](https://github.com/theLiuk23/Discord-bot-NEW)', inline=False)
        await ctx.send(embed=embed)


    @commands.command(name="vol")
    async def vol(self, ctx, *args):
        if len(args) == 0:
            await ctx.send(f"Volume is now set to {int(self.volume * 100)}")
        else:
            if not str.isdigit(args[0]):
                raise commands.BadArgument()
            volume = int(args[0])
            if volume < 0 or volume > 200:
                raise commands.BadArgument()
            self.volume = float(volume / 100)
            await ctx.send(f"Volume is now set to {volume}%")
            if self.voice_channel is not None:
                self.voice_channel.source.volume = float(volume / 100)
        config = configparser.RawConfigParser()
        config.read("settings.ini")
        with open("settings.ini", "w") as file:
            config.set("variables", "volume", str(float(volume / 100)))
            config.write(file)





    @commands.Cog.listener()
    async def on_ready(self):
        await self.load_playlists()
        if not self.check_is_playing.is_running():
            self.check_is_playing.start()
        if not self.check_members.is_running():
            self.check_members.start()
        print("Bot is now ONLINE", datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'))


    @commands.Cog.listener()
    async def on_disconnect(self):
        print("disconnecting")
        self.count1, self.count2 = 0, 0
        self.voice_channel = None
        self.queue = []
        self.is_playing = False
        self.check_is_playing.stop()
        self.check_members.stop()

    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # if isinstance(error, commands.CommandNotFound):
        #     await ctx.send(f'{ctx.message.content.split(" ")[0]} is not an available command. Type {self.prefix}help to get more information.')
        # elif isinstance(error, commands.CommandOnCooldown):
        #     await ctx.send(f'The command is on cooldown. Wait {error.retry_after:.2f} seconds.')
        # elif isinstance(error, youtube_dl.DownloadError):
        #     await ctx.send(f'There is a unexpected error during the download of the song.')
        # elif isinstance(error, commands.MissingRequiredArgument):
        #     await ctx.send(f'A required argument is missing. ' + error.param.name)
        # elif isinstance(error, commands.ChannelNotFound):
        #     await ctx.send(f"The {error.argument} is not connected to a voice channel.")
        # elif isinstance(error, commands.BadArgument):
        #     await ctx.send(f'The provided arguments are not correct.')
        # elif isinstance(error, exceptions.TooLongVideo):
        #     await ctx.send(f'{error.title} is more than an hour long. ' + error.duration)
        # elif isinstance(error, discord.errors.Forbidden):
        #     await ctx.send("Error 403. The song could not be downloaded. Try again.")
        # elif isinstance(error, exceptions.BotIsAlreadyPlaying):
        #     await ctx.send("Bot is already playing some music.")
        # elif isinstance(error, exceptions.BotIsNotPlaying):
        #     await ctx.send("Bot is not playing some music at the moment.")
        # elif isinstance(error, exceptions.QueueIsEmpty):
        #     await ctx.send(f'There are no songs in the music queue.')
        # elif isinstance(error, exceptions.PlaylistNotFound):
        #     await ctx.send(f'There is no playlist named: {error.pl_name}')
        # elif isinstance(error, TimeoutError):
        #     await ctx.send("Expired [default = No]")
        if True:
            await self.add_to_error_log(error)
            print(str(type(error)) + " - " + str(error))
            await ctx.send('Unexpected error.')
            await self.reload_bot(ctx)