from __main__ import Bot

class ExampleBot(Bot):
    targets = ['#lasttest']
    cmds = ['PRIVMSG']
    callbacks = None

    def init(self):
        pass

    def finalize(self):
        pass

bot = ExampleBot()

@bot.callback
def on_privmsg(nick, target, msg):
    return (False, target, '{}: {}'.format(nick, msg))

bot.callbacks = {'PRIVMSG': on_privmsg}
