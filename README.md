# Discord-music-bot
This is a discord bot written with the discord.py API.  
Its main function is to play music from YouTube in a discord voice channel.


## Requirements
To install all the dependencies follow these steps:
1. open a terminal
2. navigate to the directory containing these files
3. type "pip install -r requirements.txt


## Files
- main.py
- music.py
- log.txt
- commands.txt
- exceptions.py
- requirements.txt
- settings.ini (hidden in github)


## Features:
It allows to queue multiple songs and to skip them.  
You can pause and resume them anytime you want.  
You can ask the bot to print lyrics and info about the playing song.  
You can adjust the volume for all the user.  
You can create playlists and play them whenever you want.  
Prefix is editable by the user.  
  
See the avaible commands to know how to use the commands properly.


## AVAILABLE COMMANDS:
1. p [args] --> It plays a song from youtube in to your voice channel (argument needed)
2. next --> It tells the user which are the next songs
3. np --> It tells the user which song is currently playing and a bunch of other information
4. offline --> It offlines the bot (must be the owner)
5. pause --> It pauses the current playing song (bot will reload)
6. pl [args] --> It saves a playlist with the currently playing song and the music queue (argument needed = playlist name, if null it prints the available playlists). Note: if you create a playlist with the same name of an existing one, the bot will delete the older playlist.
7. pl --> shows saved playlists
8. prefix [args] --> It changes the prefix of the bot
9. resume --> It starts playing the song where it was paused
10. stop --> It disconnects the bot from the voice channel
11. skip --> It plays the next song in the queue


## ADDING THE BOT TO A DISCORD SERVER
1. Go to this [link](https://discord.com/oauth2/authorize?client_id=890316639822835712&scope=bot&permissions=8)
2. Select the server
3. Give permissions
4. Enjoy the music!
