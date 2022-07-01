from discord.ext import commands

class TooLongVideo(commands.CheckFailure):
    def __init__(self, title, duration):
        self.title = title
        self.duration = duration
        super().__init__(f'"{self.title}" is more than an hour long. ({self.duration})')


class BotIsNotPlaying(commands.CheckFailure):
    def __init__(self):
        super().__init__(f'The bot is not playing some music at the moment.')


class BotIsAlreadyPlaying(commands.CheckFailure):
    def __init__(self):
        super().__init__(f'The bot is already playing dome music at the moment.')


class QueueIsEmpty(commands.CheckFailure):
    def __init__(self):
        super().__init__(f'There are no songs in the music queue.')


class PlaylistNotFound(commands.CheckFailure):
    def __init__(self, pl_name):
        self.pl_name = pl_name
        super().__init__(f'There is no playlist called {pl_name}')