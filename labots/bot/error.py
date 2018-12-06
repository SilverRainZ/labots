from .bot import Bot

class BotError(Exception):
    bot_name: str

    def __init__(self, msg: str, name: str = None, bot: Bot = None, *args, **kwargs):
        self.message = msg
        if name:
            self.bot_name = name
        if bot:
            self.bot_name = bot._name

class LoadError(BotError):
    def __str__(self):
        return 'Failed to load bot %s: %s' % (repr(self.bot_name), self.message)

class UnloadError(BotError):
    def __str__(self):
        return 'Failed to unload bot %s: %s' % (repr(self.bot_name), self.message)

class CheckError(BotError):
    def __str__(self):
        return 'Invalid bot %s: %s' % (repr(self.bot_name), self.message)

class RegisterError(BotError):
    def __str__(self):
        return 'Failed to register bot %s: %s' % (repr(self.bot_name), self.message)

class EventError(BotError):
    event: str

    def __init__(self, msg: str, event: str = None, *args, **kwargs):
        super().__init__(msg, *args, **kwargs)
        self.event = event

    def __str__(self):
        return 'Bot %s returns error on event %s: %s' % (
                repr(self.bot_name), repr(self.event), self.message)
