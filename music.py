'''
This script is the class containing all the commands and the loops handled by the bot.
To get a list of all the available commands and how they work, please either open the commands.txt file or visit my GitHub Repository at https://github.com/theLiuk23/Discord-music-bot.
If you have any question, please write me at ldvcoding@gmail.com
'''


from tabnanny import check
from discord.ext import commands
import youtube_dl


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.volume = None
        self.YDL_OPTIONS = {
            'format': 'bestaudio',
            'ignoreerrors':'True',
            'noplaylist': 'True',
            'quiet': 'True' }



    async def ask_video(self, ctx) -> int:
        await ctx.send("Which video do you want to be played?")
        while True:
            message = await self.bot.wait_for("message", check=lambda m: m.content.isdigit())
            print(type(message.content), message)
            return int(message.content) - 1



    async def search_song_on_yt(self, ctx, query:str, videos_num:int) -> bool:
        video_index = 0
        await ctx.send(rf'I am searching on YouTube the first result with "{query}" query.')
        with youtube_dl.YoutubeDL(self.YDL_OPTIONS) as yt_dl:
            if videos_num > 1:
                video_index = await self.ask_video(ctx)
            video = yt_dl.extract_info("ytsearch:%s" % query, download=False)['entries'][video_index]
            song_info = {'source': video['formats'][0]['url'], 'title': video['title'],
                            'duration': video['duration'], 'channel': video['channel']}
            await ctx.send(f"I found {song_info['title']} by {'channel'}. It lasts {song_info['duration']}.")

    # TEST #
    @commands.command(name="ping")
    async def ping(self, ctx):
        await ctx.send("pong")


    @commands.command(name="p")
    async def play(self, ctx, *args):
        videos_num = '1' # It checks if the user wants to choose among multiple videos (default = 1)
        if len(args) == 0:
            raise AttributeError("No arguments were provided.", "song name")
        # By typing "-m" the user wants to choose among multiple videos 
        if "-m" in args:
            videos_num = args[args.index("-m") + 1] # look for next argument after "-m" in args list
            args[args.index("-m")] = 0
            args[args.index("-m") + 1] = 0
            # args_list = list(args)
            # print(args_list)
            # args_list.pop(args_list.index("-m") + 1)
            # args_list.remove("-m")
        if not videos_num.isdigit():
            raise AttributeError("The argument provided must be a number", videos_num)
        videos_num = int(videos_num)
        if videos_num < 1 or videos_num > 10:
            raise IndexError("The number of videos during the research on YouTube must be between 1 and 10.", str(videos_num))
        query = " ".join(args)
        await self.search_song_on_yt(ctx, query, videos_num)


        # S!p music -m 4
        # ("-m 45 music")