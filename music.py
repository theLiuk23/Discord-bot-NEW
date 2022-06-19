'''
This script is the class containing all the commands and the loops handled by the bot.
To get a list of all the available commands and how they work, please either open the commands.txt file or visit my GitHub Repository at https://github.com/theLiuk23/Discord-music-bot.
If you have any question, please write me at ldvcoding@gmail.com
'''


from discord.ext import commands


class MusicCog(commands.Cog):
    @commands.command(name="ping")
    async def ping(self, ctx):
        await ctx.send("pong")