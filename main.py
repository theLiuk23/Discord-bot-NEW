'''
This is the main python script that will be launched to make the bot online.
Here's a list of the functions it will do:
    - check if ffmpeg is already installed in the machine
    - read some useful varibles in the settings.ini file (hidden from the GitHub repository) like the bot token and the prefix
    - launch the client instance with all the available commands.
Some functions like the one to install ffmpeg are made specifically for Linux; if you're using another OS please be aware of some possible problems.
If you want to get more information, please visit my GitHub Repository at https://github.com/theLiuk23/Discord-music-bot.
If you have any question, please write me at ldvcoding@gmail.com
'''


from discord.ext import commands
import configparser
import subprocess
import discord
import music
import os



# INIZIALITORS
config = configparser.RawConfigParser()
intents = discord.Intents.default()
intents.members = True
intents.guilds = True




def read_settings(filename:str, section:str, option:str) -> str:
    # it reads a variable stored in the "settings.ini" file
    config.read(filename)
    if not config.sections().__contains__(section):
        raise FileNotFoundError(f"Section '{section}' does not exist in file {filename}.")
    if not config.options(section).__contains__(option):
        raise FileNotFoundError(f"Option '{option}' does not exist in section {section} in file {filename}.")
    try:
        return config.get(section, option)
    except:
        return None



### MAIN ###
def main():
    download_ffmpeg()
    prefix = read_settings("settings.ini", "variables", "prefix")
    token = read_settings("settings.ini", "variables", "bot_token")
    volume = read_settings("settings.ini", "variables", "volume")
    if token is None or prefix is None:
        raise TypeError(f"Either the token or the prefix is NoneType.\nToken: {token}\nPrefix: {prefix}")
    activity = discord.Activity(type=discord.ActivityType.listening, name=f"music. {prefix}help")
    client = commands.Bot(command_prefix=prefix, intents=intents, activity=activity, help_command=None)
    client.add_cog(music.MusicCog(client, prefix, float(volume)))
    client.run(token, bot=True)
    



def download_ffmpeg():
    # it checks if ffmpeg is installed and eventually downloads it.
    try:
        subprocess.check_output(['which', 'ffmpeg'])
    except subprocess.CalledProcessError:
        return os.system("sudo apt install ffmpeg -y")




# it does not run the script when it is imported from other scripts
if __name__ == "__main__":
    main()