#!/usr/bin/env python3
# -*- encoding: UTF-8 -*-

import os
import sys
import logging
import importlib
import config
from irc import IRC

# Initialize logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

hdr = logging.StreamHandler()
hdr.setLevel(logging.DEBUG)

fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fmter = logging.Formatter(fmt, None)

hdr.setFormatter(fmt)
logger.addHandler(hdr)


class Bot(object):
    targets = None
    cmds = None
    cmds_callback = None
    _irc = None

    def init(self):
        logger.info('Default init function')

    def finalize(self):
        logger.info('Default finalize function')

    def callback(self, func):

        def warpper(*args, **kw):
            pass_, target, msg = func(*args, **kw)
            logger.debug('%s(): pass: %s, target: %s, msg: %s',
                    func.__name__, pass_, target, msg)
            self._irc.send('#lasttest', msg)
            return pass_

        return warpper

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
def load_bots():
    bots = []

    for mod_name in config.mods:
        try:
            if mod_name in sys.modules:
                importlib.reload(sys.modules[mod_name])
                logger.info('Module "%s" has been loaded', mod_name)
            else:
                mod = importlib.import_module(mod_name, None)
                if check_bot(mod.bot):
                    bots.append(mod.bot)
                    logger.info('Module "%s" loaded', mod_name)
        except ImportError as err:
            logger.error('Import error "%s": %s', mod_name, err)

    return bots


def main():
    irc = IRC(config.host, config.port, config.nick)

    bots = load_bots()

    for bot in bots:
        bot.init()
        bot._irc = irc

    for bot in bots:
        for chan in bot.targets:
            irc.join(chan)

    while (True):
        try:
            nick, target, msg = irc.recv()
            if (nick, target, msg) == (None, None, None):
                continue

            for bot in bots:
                bot.callbacks['PRIVMSG'](nick, target, msg)

        except KeyboardInterrupt:
            irc.stop()
            logger.info('Exit.')
            os._exit(0)

if __name__ == '__main__':
    main()
