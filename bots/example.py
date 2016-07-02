from bot import Bot, echo, broadcast

class ExampleBot(Bot):
    targets = ['#lasttest', '#nexttest']
    trig_cmds = ['JOIN', 'PART', 'QUIT', 'NICK', 'PRIVMSG', 'TIMER']

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
        # NOTE: if you return message in any case,
        # endless loop will be caused
        if msg.startswith('\'echo '):
            return (True, target, '%s: %s' % (nick, msg[5:]))

    @broadcast
    def on_timer(self):
        return (True, self.targets, '1 minute passed')


bot = ExampleBot()
