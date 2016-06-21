#!/usr/bin/env python3
# -*- encoding: UTF-8 -*-

import os
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
    targets = None
    cmds = None
    callbacks = None

    def init(self):
        pass

    def finalize(self):
        pass

    def callback(self, func):

        def warpper(*args, **kw):
            pass_, target, msg = func(*args, **kw)
            logger.debug('%s(): pass: %s, target: %s, msg: %s',
                    func.__name__, pass_, target, msg)
            self._irc.send('#lasttest', msg)
            return pass_

        return warpper


# Check if a bot's members meet the requirements of labots
def check_bot(bot):
    if not isinstance(bot.targets, list):
        logger.error('bot.target is no correctly defined')
        return False

    if not isinstance(bot.cmds, list):
        logger.error('bot.cmds is no correctly defined')
        return False

    if not isinstance(bot.callbacks, dict):
        logger.error('bot.callbacks is no correctly defined')
        return False

    if not hasattr(bot.init, '__call__'):
        logger.error('bot.init() is no correctly defined')
        return False

    if not hasattr(bot.finalize, '__call__'):
        logger.error('bot.init() is no correctly defined')
        return False

    # Check callback functions
    for cmd in bot.cmds:
        if not cmd in bot.callbacks \
                or not hasattr(bot.callbacks[cmd], '__call__'):
            logger.error('bot.callbacks["%s"] is no correctly defined', cmd)
            return False

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
        if force:
            bots.remove(bot)
    else:
        logger.info('Bot "%s" unloaded', bot._name)
        bots.remove(bot)


def unload_bots(bots):
    for bot in bots:
        unload_bot(bots, bot)


def main():
    irc = IRC(config.host, config.port)
    irc.login('labots')

    bots = load_bots()

    for bot in bots:
        bot._irc = irc

    for bot in bots:
        for chan in bot.targets:
            irc.join(chan)

    while (True):
        try:
            ircmsgs = irc.recv()

            if not ircmsgs:
                continue

            for ircmsg in ircmsgs:
                if ircmsg.command == 'PRIVMSG':
                    for bot in bots:
                        bot.callbacks['PRIVMSG'](
                                ircmsg.nick, ircmsg.args[0], ircmsg.msg)

        except KeyboardInterrupt:
            unload_bots(bots)
            irc.stop()
            logger.info('Exit.')
            os._exit(0)

if __name__ == '__main__':
    main()
