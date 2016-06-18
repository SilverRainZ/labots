from labots import Bot

class ExampleBot(Bot):
    targets = ['#lasttest']
    cmds = ['PRIVMSG']
    callbacks = None

    def init():
        pass

    def finalize():
        pass

bot = ExampleBot()

@bot.response
def on_privmsg(sender, target, msg):
    print('[on_privmsg]', sender, target, msg)
    return (False, msg)

bot.callbacks = {'PRIVMSG': on_privmsg}
