# Example irc bot
# ../bot.py is its prototype

import os
import json
from bot import Bot, echo, broadcast, read_config

'''
Bot:
    IRC Bot prototype, you must inherit it.

echo:
    Use it to decorate your callback functions(see below `targets`),

    In the functions decorate by `echo`,
    You should return `None` or a tuple `(pass, target, msg)`,

    `pass`: if false, DO NOT pass this callback to next bots.
    `target`: the string `msg` will sent to `target`, can be None
    `msg`: ...

    If you return `None`, it is equal to return `(True, None, None)`

broadcast:
    Like `echo`, `target` is a list, used to broadcast message.

read_config:
    It will read configure from a json file which has the same name with
    your bot script, and return a dict.
    configure file is not necessary.

        e.g. for `example.py`, its config file is `example.json`, you should
            create it manually.

'''

class ExampleBot(Bot):
    '''
    Inherit `Bot` class from `bot` module (../bot.py),
    so you have some pre-define functions and varibles.
    '''

    ''' You will auto join the following channels '''
    targets = ['#lasttest', '#nexttest']

    '''
    If you received a JOIN message sent by someone in `targets`,
    function `on_join` will be call, you must define it by youself.
    and so on ...

    Here are all commands support by LABots, `TIMEER` is a timing message
    toggle every 1 min.
    '''
    trig_cmds = ['JOIN', 'PART', 'QUIT', 'NICK', 'PRIVMSG', 'TIMER']

    def init(self):
        '''
        This function will be invoked before bot is loaded, you can read config
        file here, using `bot.read_config(__file__)`, usually, you can reset
        `self.targets` here.

            e.g:
                config = read_config(__file__)
                print(config)
                self.targets = config['targets']
        '''
        pass

    def finalize(self):
        ''' This function will be invoked before bot is unloaded '''
        pass

    ''' Callback functions :) '''
    @echo
    def on_join(self, nick, chan):
        return (True, chan, '%s -->| %s' % (nick, chan))

    @echo
    def on_part(self, nick, chan, reason):
        return (True, chan, '%s |<-- %s: %s' % (nick, chan, reason))

    @echo
    def on_quit(self, nick, chan, reason):
        return (True, chan, '%s |<-- : %s' % (nick, reason))

    @echo
    def on_nick(self, nick, new_nick, chan):
        return (True, chan, '%s -> %s' % (nick, new_nick))

    @echo
    def on_privmsg(self, nick, target, msg):
        ''' Echo bot, response `'echo xxx` message '''
        # NOTE: if you return message in any case,
        # endless loop will be caused
        if msg.startswith('\'echo '):
            return (True, target, '%s: %s' % (nick, msg[5:]))

    @broadcast
    def on_timer(self):
        return (True, self.targets, '1 minute passed')


'''
**IMPORTANCE**

You must define a instance of your Bot class and name it as `bot`, then it can
be found by LABots.
'''
bot = ExampleBot()
