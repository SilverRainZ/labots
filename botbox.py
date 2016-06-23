# -*- encoding: UTF-8 -*-
import os
import sys
import logging
import pyinotify
import importlib
import functools
from bot import Bot, echo, broadcast
from tornado.ioloop import IOLoop

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

hdr = logging.StreamHandler()
hdr.setLevel(logging.DEBUG)

fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
fmter = logging.Formatter(fmt, None)

hdr.setFormatter(fmt)
logger.addHandler(hdr)


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

    return True


class EventHandler(pyinotify.ProcessEvent):
    botbox = None

    def __init__(self, botbox):
        self.botbox = botbox


    def process_IN_CREATE(self, event):
        logger.debug('%s', event)
        if event.path == 'bots' \
                and event.name.endswith('.py') \
                and not event.name.startswith('_'):
            self.botbox._load(event.name)


    def process_IN_DELETE(self, event):
        logger.debug('%s', event)
        if event.path == 'bots' \
                and event.name.endswith('.py') \
                and not event.name.startswith('_'):
            self.botbox._unload(event.name)


    def process_IN_MODIFY(self, event):
        logger.debug('%s', event)
        if event.path == 'bots' \
                and event.name.endswith('.py') \
                and not event.name.startswith('_'):
            self.botbox._unload(event.name)
            self.botbox._load(event.name)



class BotBox(object):
    _ioloop = None
    _notifier = None
    _irc = None

    path = None
    irc = None
    bots = []

    def __init__(self, path, ioloop = None):
        self.path = path
        sys.path.append(path)
        self._ioloop = ioloop or IOLoop.instance()
        

    def _get(self, filename):
        for bot in self.bots:
            if bot._filename == filename:
                return bot
        return None


    def _load(self, filename):
        bot = self._get(filename)
        if bot:
            logger.debug('"%s" has been loaded', bot._name)
            return False

        try:
            modname = filename[:-3]
            if modname in sys.modules:
                mod = importlib.reload(sys.modules[modname])
            else:
                mod = importlib.import_module(modname, None)
            if check_bot(mod.bot):
                try:
                    mod.bot.init()
                except Exception as err:
                    logger.error('Bot "%s" is failed to initialize: %s', modname, err)
                    return False
                else:
                    mod.bot._filename = filename
                    mod.bot._name = modname
                    self.bots.append(mod.bot)
                    if self._irc:
                        mod.bot._irc = self._irc
                        for t in mod.bot.targets:
                            self._irc.join(t)
                    logger.info('Bot "%s" is loaded', modname)
                    return True
        except Exception as err:
            logger.error('Bot "%s" is failed to import: %s', modname, err)
            return False


    def _unload(self, filename):
        bot = self._get(filename)
        if not bot:
            logger.debug('"%s" is not loaded', filename[:-3])
            return False
        try:
            bot.finalize()
        except Exception as err:
            logger.error('Bot "%s" failed to finalize: %s', bot._name, err)

        self.bots.remove(bot)
        logger.info('Bot "%s" is unloaded', bot._name)
        return True

    def start(self, irc):
        self._irc = irc

        for f in os.listdir(self.path):
            if f.endswith('.py') and not f.startswith('_'):
                self._load(f)

        wm = pyinotify.WatchManager()
        wm.add_watch(self.path,
                pyinotify.IN_DELETE |
                pyinotify.IN_CREATE |
                pyinotify.IN_MODIFY ,
                rec = False)

        handle = EventHandler(self)
        self._notifier = pyinotify.TornadoAsyncNotifier(
                wm, self._ioloop, default_proc_fun = handle)


    def stop(self):
        while self.bots:
            self._unload(self.bots[0]._filename)
        self._notifier.stop()



if __name__ == '__main__':
    box = BotBox('bots')
    box.start(None)
    try:
        IOLoop.instance().start()
    except KeyboardInterrupt:
        IOLoop.instance().stop()
