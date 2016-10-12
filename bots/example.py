# Example irc bot
# ../bot.py is its prototype

import os
import json
from bot import Bot

'''
Bot:
    IRC Bot prototype, you must inherit it and create a instance name `bot`.
    Its constructor requires the path
    of this bot script.

    So, the minimal bot script is:

        class MinBot(Bot):
            pass

        bot = MinBot(__file__)

Bot.config:
    A dict. When creating a Bot object, it will auto read configure from a json
    file which has the same name with your bot script, And save it as a dict in
    `Bot.config`.

        e.g. for `example.py`, its config file is `example.json`,
             **YOU SHOULD CREATE IT MANUALLY**.

Bot.say(target, msg):
    Send a `msg` to `target`, note, you will receive the message you sent.

Bot.on_XXX(...):
    on_XXX() event function will be invoked when XXX message is recevied, for
    available functions and their signatures, see `labots/bot.py`.

    When you return True, it means this message won't be passed to next bot.
'''

class ExampleBot(Bot):
    '''
    Inherit `Bot` class from `bot` module (labots/bot.py),
    so you have some pre-define functions and varibles.
    '''

    '''
    You will auto join the following channels, or receive message
    form the following nicks.
    '''
    targets = ['#lasttest', '#nexttest']

    def init(self):
        '''
        This function will be invoked when bot is loaded, you can do some
        initialize stuff here.

        Usually, you can rewrite `self.targets` here, accroding your config.

            e.g:
                self.targets = self.config['targets']
        '''
        pass

    def finalize(self):
        ''' This function will be invoked when bot is unloaded '''
        pass

    ''' Event handle functions '''
    def on_JOIN(self, chan, nick):
        self.say(chan, '%s -->| %s' % (nick, chan))

    def on_PART(self, chan, nick):
        self.say(chan, '%s |<-- %s' % (nick, chan))

    def on_QUIT(self, chan, nick, reason):
        self.say(chan, '%s |<-- : %s' % (nick, reason))

    def on_NICK(self, chan, old_nick, new_nick):
        self.say(chan, '%s -> %s' % (old_nick, new_nick))

    def on_PRIVMSG(self, target, nick, msg):
        ''' Echo bot, response `'echo xxx` message '''
        # NOTE: If you return message in any case,
        # endless loop will be caused
        cmd = '.echo '
        if msg.startswith(cmd):
            self.say(target, '%s: %s' % (nick, msg[len(cmd):]))

    def on_NOTICE(self, target, nick, msg):
        self.say(target, 'Notice: %s' % msg)

    def on_ACTION(self, target, nick, msg):
        self.say(target, 'Action: %s' % msg)

    def on_LABOTS_MSG(self, target, bot, nick, msg):
        if bot:
            self.say(target, '%s: Youe message is sent by %s' % (nick, bot))


'''
**IMPORTANCE**

You must define a instance of your Bot class and name it as `bot`, then it can
be found by LABots, As described above, you should pass `__file__` to its
constructor.
'''

bot = ExampleBot(__file__)
