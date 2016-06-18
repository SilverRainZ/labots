#!/usr/bin/env python3
# -*- encoding: UTF-8 -*-

import sys
import config
from irc import IRC

class Bot(object):
    targets = None
    cmds = None
    cmds_callback = None

    def init():
        print('Default init function')

    def finalize():
        print('Default finalize function')

    def response(self, func):
        def privmsg(*args, **kw):
            r = func(*args, **kw)
            print('%s()' % func.__name__)
            print(r)
            return r

        return privmsg

def main():
    irc = IRC(config.host, config.port, config.nick)
    try:
        mods = list(map(lambda x:__import__(x, fromlist = ['bot']), config.mods))
    except ImportError as err:
        print(err)

    irc.join('#lasttest')
    while (True):
        try:
            man, chan, msg = irc.recv()
            if man == None and chan == None and msg == None:
                continue

            for mod in mods:
                mod.bot.callbacks['PRIVMSG'](chan, msg, man)

        except KeyboardInterrupt:
            irc.stop()
            print('[teebot]', 'exit')
            exit(0)

if __name__ == '__main__':
    main()
