#!/usr/bin/env python3
# -*- encoding: UTF-8 -*-

import sys
import logging
import config
import functools
from tornado.ioloop import IOLoop
from botbox import BotBox
from irc import IRC, IRCMsg, IRCMsgType

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def dispatch(bots, type_, ircmsg):
    if type_ != IRCMsgType.MSG:
        return

    if ircmsg.cmd[0] in ['4', '5']:
        logger.error('Error message: %s', ircmsg.msg)
    elif ircmsg.cmd == 'JOIN':
        chan = ircmsg.args[0]
        for bot in bots:
            if ircmsg.cmd in bot.trig_cmds and chan in bot.targets:
                try:
                    if not bot.on_join(ircmsg.nick, chan):
                        break
                except Exception as err:
                    logger.error('"%s".on_join() failed: %s', bot._name, err)
    elif ircmsg.cmd == 'PART':
        chan, reason = ircmsg.args[0], ircmsg.msg
        for bot in bots:
            if ircmsg.cmd in bot.trig_cmds and chan in bot.targets:
                try:
                    if not bot.on_part(ircmsg.nick, chan, reason):
                        break
                except Exception as err:
                    logger.error('"%s".on_part() failed: %s',bot._name, err)
    elif ircmsg.cmd == 'QUIT':
        reason = ircmsg.msg
        for bot in bots:
            if ircmsg.cmd in bot.trig_cmds:
                try:
                    if not bot.on_quit(ircmsg.nick, reason):
                        break
                except Exception as err:
                    logger.error('"%s".on_quit() failed: %s', bot._name, err)
    elif ircmsg.cmd == 'NICK':
        new_nick = ircmsg.msg
        for bot in bots:
            if ircmsg.cmd in bot.trig_cmds:
                try:
                    if not bot.on_nick(ircmsg.nick, new_nick):
                        break
                except Exception as err:
                    logger.error('"%s".on_nick() failed: %s', bot._name, err)
    elif ircmsg.cmd == 'PRIVMSG':
        chan = ircmsg.args[0]
        for bot in bots:
            if ircmsg.cmd in bot.trig_cmds and chan in bot.targets:
                try:
                    if not bot.on_privmsg(ircmsg.nick, chan, ircmsg.msg):
                        break
                except Exception as err:
                    logger.error('"%s".on_privmsg() failed: %s', bot._name, err)


def main():
    botbox = BotBox(config.path)

    callback = functools.partial(dispatch, botbox.bots)
    irc = IRC(config.host, config.port, 'labots',
            after_login = botbox.start, on_recv = callback)

    botbox.set_handler(irc.send, irc.join, irc.part)

    try:
        IOLoop.instance().start()
    except KeyboardInterrupt:
        botbox.stop()
        irc.stop()
        IOLoop.instance().stop()
        logger.info('Exit.')
        return 0

if __name__ == '__main__':
    logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
    main()
