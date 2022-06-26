from discord.ext import commands

class TooLongVideo(commands.CheckFailure):
    def __init__(self, title, duration):
        self.title = title
        self.duration = duration
        super().__init__(f'"{self.title}" is more than an hour long. ({self.duration})')


class BotIsNotPlaying(commands.CheckFailure):
    def __init__(self):
        super().__init__(f'The bot is not playing music at the moment.')