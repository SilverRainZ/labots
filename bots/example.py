# Example irc bot
# labots/bot.py is its prototype
# For LABots 1.1

import os
import json
from labots.bot import Bot

'''
Bot:
    IRC Bot prototype, you must inherit it and create a instance name `bot`.
    Its constructor requires the path
    of this bot script.

    So, the minimal bot script is:

        from labots.bot import Bot

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

    '''
    [v1.1] `usage` will be show when received a "<nick>: help"-like message
    '''
    usage = '''.echo <msg>: Echo a message;
    When somebody join, part, quit, change his nick, sent a message;
    When somebody sends a ACTION or NOTICE message, sent a message;
    When somebody mentions my nick and saying 'poi', reply him with 'Poi~'
    '''

    '''
    [v1.2] Set `reload` to False can prevent the bot from being restarted
    (for some bot has a internal HTTP server)
    '''
    reload = True

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

    ''' [v1.1] '''
    def on_NOTICE(self, target, nick, msg):
        self.say(target, 'Notice: %s' % msg)

    ''' [v1.1] '''
    def on_ACTION(self, target, nick, msg):
        self.say(target, 'Action: %s' % msg)

    ''' [v1.1] '''
    def on_LABOTS_MSG(self, target, bot, nick, msg):
        if bot:
            self.say(target, '%s: Youe message is sent by %s' % (nick, bot))

    ''' [v1.1] '''
    def on_LABOTS_MENTION_MSG(self, target, bot, nick, msg):
        if msg == 'poi':
            self.say(target, '%s: Poi~' % nick)


'''
**IMPORTANCE**

You must define a instance of your Bot class and name it as `bot`, then it can
be found by LABots, As described above, you should pass `__file__` to its
constructor.
'''

bot = ExampleBot(__file__)
