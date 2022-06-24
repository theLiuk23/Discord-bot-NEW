'''
This script is the class containing all the commands and the loops handled by the bot.
To get a list of all the available commands and how they work, please either open the commands.txt file or visit my GitHub Repository at https://github.com/theLiuk23/Discord-music-bot.
If you have any question, please write me at ldvcoding@gmail.com
'''


import asyncio
import datetime
import discord
from discord.ext import commands
import youtube_dl


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
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
        except Exception as e:
            print(e)
            return False



    async def ask_video(self, ctx) -> bool:
        await ctx.send("I found this video. Should I go ahead? [y/n]")
        while True:
            message = await self.bot.wait_for("message", check=lambda m: m.content == "y" or m.content == "n")
            if message.content == "y":
                return True
            return False


    async def search_song_on_yt(self, ctx, query:str, ask:bool) -> bool:
        await ctx.send(rf'I am searching on YouTube the first result with "{query}" query.')
        with youtube_dl.YoutubeDL(self.YDL_OPTIONS) as yt_dl:
            video = yt_dl.extract_info("ytsearch:%s" % query, download=False)['entries'][0]
            song_info = {'source': video['formats'][0]['url'], 'title': video['title'],
                            'duration': video['duration'], 'channel': video['channel']}
            await ctx.send(f"I found **{song_info['title']}**\nBy **{song_info['channel']}**\nIt lasts **{song_info['duration']} seconds**.") # TODO: seconds to minutes!
            if ask:
                if await self.ask_video(ctx) is False:
                    return
            self.queue.append([song_info, ctx.author.voice.channel])
            if self.is_playing is False:
                await self.play()
            return True


    def my_after(self, error):
        next_song = self.queue[0][0]['title']
        coro = self.play()
        fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
        try:
            fut.result()
        except:
            raise discord.errors.DiscordServerError("There was a problem playing next song.")


    async def play(self):
        if len(self.queue) <= 0:
            self.is_playing = False
            return

        source = self.queue[0][0]['source']
        self.queue.pop(0)
        
        if self.voice_channel is None or self.voice_channel.is_connected() is False:
            raise discord.errors.ClientException("The bot is not connected to a voice channel.")
            
        if self.voice_channel.is_playing() is False:
            self.voice_channel.play(discord.FFmpegPCMAudio(source, options=self.FFMPEG_OPTIONS), after = self.my_after)
        self.voice_channel.source = discord.PCMVolumeTransformer(self.voice_channel.source, volume=self.volume)
        self.is_playing = True


    @commands.command(name="p")
    async def p(self, ctx, *args):
        query = " ".join(args)
        ask = False

        if ctx.author.voice is None:
            raise discord.errors.DiscordException("User not connected to a voice channel", ctx.author.voice)
        if self.voice_channel is None:
            await self.connect_to_voice_channel(ctx, ctx.author.voice)
        if len(args) == 0:
            raise discord.errors.InvalidArgument("No arguments were provided.", "song name")

        # By typing "-a" the user wants to check the video before playing it
        if "-a" in args:
            query = query.replace(" -a", "")
            ask = True

        await self.search_song_on_yt(ctx, query, ask)



    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot is now ONLINE", datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'))