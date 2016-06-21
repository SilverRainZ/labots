#!/usr/bin/env python3
# -*- encoding: UTF-8 -*-

import sys
import logging
import importlib
import config
from irc import IRC, IRCMsg, IRCMsgType

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

hdr = logging.StreamHandler()
hdr.setLevel(logging.DEBUG)

fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
fmter = logging.Formatter(fmt, None)

hdr.setFormatter(fmt)
logger.addHandler(hdr)


# IRC bot prototype
class Bot(object):
    # Private
    _irc = None         # irc handle for sending message
    _name = 'ProtoTypeBot'

    # Public
    targets = []
    trig_cmds = []
    trig_keys = []

    def init(self):
        pass

    def finalize(self):
        pass


# Decorator for callback functions in `Bot`
def echo(func):
    def warpper(self, *args, **kw):
        pass_, target, msg = func(self, *args, **kw)
        logger.debug('%s(): pass: %s, target: %s, msg: %s',
                func.__name__, pass_, target, msg)
        if target and msg:
            self._irc.send(target, msg)
        return pass_
    return warpper


# Decorator for callback functions in `Bot`
def broadcast(func):
    def warpper(self, *args, **kw):
        pass_, targets, msg = func(self, *args, **kw)
        logger.debug('%s(): pass: %s, msg: %s', func.__name__, pass_, msg)
        if msg:
            [ self._irc.send(t, msg) for t in targets]
        return pass_
    return warpper


# Check if a bot's members meet the requirements of labots
def check_bot(bot):
    if not isinstance(bot.targets, list):
        logger.error('bot.target is no correctly defined')
        return False

    if not isinstance(bot.trig_cmds, list):
        logger.error('bot.trig_cmds is no correctly defined')
        return False

    if not isinstance(bot.trig_keys, list):
        logger.error('bot.trig_keys is no correctly defined')
        return False

    if not hasattr(bot.init, '__call__'):
        logger.error('bot.init() is no correctly defined')
        return False

    if not hasattr(bot.finalize, '__call__'):
        logger.error('bot.init() is no correctly defined')
        return False

    # TODO: Check callback functions

    return True


# Load all bots from modules in `config.mods`.
# If a module is loaded, ignore it.
# Return a list of bots
def load_bots():
    bots = []

    for mod_name in config.mods:
        try:
            if mod_name in sys.modules:
                logger.info('Bot "%s" has been loaded', mod_name)
            else:
                mod = importlib.import_module(mod_name, None)
                if check_bot(mod.bot):
                    try:
                        mod.bot.init()
                    except Exception as err:
                        logger.error('Bot "%s" failed to initialize: %s', mod_name, err)
                    else:
                        mod.bot._name = mod_name
                        bots.append(mod.bot)
                        logger.info('Bot "%s" loaded', mod_name)
        except ImportError as err:
            logger.error('Import error "%s": %s', mod_name, err)

    return bots


# Unload a specified bot from bots list
# If force = True, remove this bot even if
# it is failed to finalize
def unload_bot(bots, bot, force = False):
    try:
        bot.finalize()
    except Exception as err:
        logger.error('Bot "%s" failed to finalize: %s', bot._name, err)
        if not force:
            return
    bots.remove(bot)
    logger.info('Bot "%s" unloaded', bot._name)


def unload_bots(bots):
    while bots:
        unload_bot(bots, bots[0], force = True)


def dispatch(bots, type_, ircmsg):
    if type_ != IRCMsgType.MSG:
        return

    if ircmsg.cmd[0] in ['4', '5']:
        logger.error('Error message: %s', ircmsg)
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
                    logger.error('"%s".on_privmsg() failed: %s', bot._name, ircmsg.cmd, err)


def main():
    irc = IRC(config.host, config.port)
    irc.login('labots')

    bots = load_bots()

    for bot in bots:
        bot._irc = irc
        for chan in bot.targets:
            irc.join(chan)

    while (True):
        try:
            ircmsgs = irc.recv()

            for type_, ircmsg in ircmsgs:
                dispatch(bots, type_, ircmsg)

        except KeyboardInterrupt:
            unload_bots(bots)
            irc.stop()
            logger.info('Exit.')
            return 0

if __name__ == '__main__':
    main()
