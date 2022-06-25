'''
This script is the class containing all the commands and the loops handled by the bot.
To get a list of all the available commands and how they work, please either open the commands.txt file or visit my GitHub Repository at https://github.com/theLiuk23/Discord-music-bot.
If you have any question, please write me at ldvcoding@gmail.com
'''


import asyncio
import json
import datetime
import discord
import youtube_dl
from discord.ext import commands


class MusicCog(commands.Cog):
    def __init__(self, bot, prefix):
        self.bot = bot
        self.prefix = prefix
        self.volume = 1.0
        self.queue = []
        self.is_playing = False
        self.voice_channel = None
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn' }
        self.YDL_OPTIONS = {
            'format': 'bestaudio',
            'ignoreerrors':'True',
            'noplaylist': 'True',
            'nowarnings': 'True',
            'quiet': 'True' }


    async def connect_to_voice_channel(self, ctx, voice) -> bool:
        try:
            self.voice_channel = await voice.channel.connect()
            await ctx.guild.change_voice_state(channel=self.voice_channel.channel, self_mute=False, self_deaf=True)
            return True
        except:
            return False


    async def disconnect_from_voice_channel(self) -> bool:
        if self.voice_channel is None:
            raise commands.ChannelNotFound("Bot is not connected to a voice channel.")
        if self.voice_channel.is_connected() is False:
            raise commands.ChannelNotFound("Bot is not connected to a voice channel.")
        await self.voice_channel.disconnect()
        self.voice_channel = None
        self.queue = []
        self.is_playing = False



    async def ask_video(self, ctx) -> bool:
        await ctx.send("I found this video. Should I go ahead? [y/n]")
        while True:
            message = await self.bot.wait_for("message", check=lambda m: m.content == "y" or m.content == "n")
            if message.content == "y":
                return True
            return False


    async def send_song_info(self, ctx, info):
        embed = discord.Embed(title="Search result")
        embed.add_field(name = "Title", value = info['title'])
        embed.add_field(name = "Channel", value = info['channel'])
        embed.add_field(name = "Duration", value = str(info['duration']) + ' seconds') # TODO: convert in minutes
        await ctx.send(embed=embed)


    async def choose_video(self, ctx, query, video):
        videos = []
        with youtube_dl.YoutubeDL(self.YDL_OPTIONS) as yt_dl:
            for i in range(0, 5):
                videos.append(yt_dl.extract_info("ytsearch:%s" % query, download=False)['entries'][0])
        # for video in videos:
        #     title = video['title']
        #     channel = video['channel']
        #     await ctx.send(f'{title} by {channel}')


    async def search_song_on_yt(self, ctx, query:str, ask:bool, multiple:bool) -> bool:
        with youtube_dl.YoutubeDL(self.YDL_OPTIONS) as yt_dl:
            video = yt_dl.extract_info("ytsearch:%s" % query, download=False)['entries'][0]
            song_info = {'source': video['formats'][0]['url'],
                        'title': video['title'],
                        'duration': video['duration'],
                        'channel': video['channel']}
            if multiple:
                await self.choose_video(ctx, query)
            await self.send_song_info(ctx, song_info)
            if ask:
                if await self.ask_video(ctx, song_info) is False:
                    return
            self.queue.append([song_info, ctx.author.voice.channel])
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
            # raise discord.errors.DiscordServerError("There was a problem playing next song.", "message")


    async def play(self):
        if len(self.queue) <= 0:
            self.is_playing = False
            return

        source = self.queue[0][0]['source']
        self.queue.pop(0)
        if self.voice_channel is None or self.voice_channel.is_connected() is False:
            raise discord.errors.ClientException("The bot is not connected to a voice channel.")
        if self.voice_channel.is_playing() is False:
            self.voice_channel.play(discord.FFmpegPCMAudio(source, **self.FFMPEG_OPTIONS), after = self.my_after)
        self.voice_channel.source = discord.PCMVolumeTransformer(self.voice_channel.source, volume=self.volume)
        self.is_playing = True



    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.command(name="p")
    async def p(self, ctx, *args):
        query = " ".join(args)
        ask = False
        multiple = False

        if ctx.author.voice is None:
            raise commands.ChannelNotFound("User not connected to a voice channel", ctx.author.voice)
        if self.voice_channel is None:
            await self.connect_to_voice_channel(ctx, ctx.author.voice)
        if len(args) == 0:
            raise discord.errors.InvalidArgument("No arguments were provided.", "song name")

        # By typing "-a" the user wants to check the video before playing it
        if "-a" in args:
            query = query.replace(" -a", "")
            ask = True

        # By typing "-m" the user wants to choose among 5 results
        if "-m" in args:
            query = query.replace(" -m", "")
            multiple = True

        await self.search_song_on_yt(ctx, query, ask, multiple)


    @commands.command(name="skip")
    async def skip(self, ctx):
        if self.voice_channel is None:
            raise commands.ChannelNotFound("The bot is not connected to a voice channel.")
        if len(self.queue) <= 0:
            await self.disconnect_from_voice_channel()
            await ctx.send("There are no other songs in the queue.")
            return
        self.voice_channel.stop()
        await self.play()


    @commands.command(name="next")
    async def next(self, ctx):
        songs = []
        for i, song in enumerate(self.queue):
            songs.append(song[i]['title'])
        await ctx.send("Here's a list of the songs in the music queue:\n" + "\n".join(songs))


    @commands.command(name="stop")
    async def stop(self, ctx):
        await ctx.send(f'Disconnecting from "{self.voice_channel.channel}" voice channel')
        await self.disconnect_from_voice_channel()


    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot is now ONLINE", datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'))


    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f'{ctx.message.content.split(" ")[0]} is not an available command. Type {self.prefix}help to get more information.')
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f'The command is on cooldown. Wait {error.retry_after:.2f} seconds.')
        elif isinstance(error, youtube_dl.DownloadError):
            await ctx.send(f'There is a unexpected error during the download of the song.')
        elif isinstance(error, discord.errors.InvalidArgument):
            await ctx.send(f'The input of the argument is invalid.')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f'A required argument is missing.')
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send("The bot is not connected to a voice channel.")
        else:
            print(error)
            await ctx.send('Unexpected error.')