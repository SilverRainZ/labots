from bot import Bot, echo, broadcast

class ExampleBot(Bot):
    targets = ['#lasttest', '#nexttest']
    trig_cmds = ['JOIN', 'PART', 'QUIT', 'NICK', 'PRIVMSG']

    def init(self):
        pass

    def finalize(self):
        pass

    @echo
    def on_join(self, nick, chan):
        return (True, chan, '%s -->| %s' % (nick, chan))

    @echo
    def on_part(self, nick, chan, reason):
        return (True, chan, '%s |<-- %s: %s' % (nick, chan, reason))

    @broadcast
    def on_quit(self, nick, reason):
        return (True, self.targets, '%s |<-- : %s' % (nick, reason))

    @broadcast
    def on_nick(self, nick, new_nick):
        return (True, self.targets, '%s -> %s' % (nick, new_nick))

    @echo
    def on_privmsg(self, nick, target, msg):
        return (True, target, '%s: %s' % (nick, msg))


bot = ExampleBot()
