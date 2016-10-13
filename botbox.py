# -*- encoding: UTF-8 -*-
import os
import sys
import logging
import pyinotify
import importlib
from tornado.ioloop import IOLoop, PeriodicCallback
from bot import Bot, check_bot

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def empty_handler(*args, **kw):
    logger.debug("Unimplement handler %s %s" % (args, kw))


def file2mod(fname):
    if not fname.startswith('_') \
            and not fname.startswith('.') \
            and os.path.splitext(fname)[1] == '.py':
        return os.path.splitext(fname)[0]
    else:
        return None


class EventHandler(pyinotify.ProcessEvent):
    botbox = None

    def __init__(self, botbox):
        self.botbox = botbox


    def process_IN_CREATE(self, event):
        logger.debug('%s', event)

        name = file2mod(event.name)

        if event.path == self.botbox.path and name:
            self.botbox._load(name)


    def process_IN_DELETE(self, event):
        logger.debug('%s', event)

        name = file2mod(event.name)

        if event.path == self.botbox.path and name:
            self.botbox._unload(name)


    def process_IN_MODIFY(self, event):
        logger.debug('%s', event)

        name = file2mod(event.name)

        # If configure file changed
        if not name and not event.name.startswith('_') \
                and os.path.splitext(event.name)[1] == '.json':
            name = os.path.splitext(event.name)[0]

        if event.path == self.botbox.path and name:
            self.botbox._unload(name)
            self.botbox._load(name)


class BotBox(object):
    _ioloop = None
    _notifier = None

    path = None
    bots = []

    send_handler = None
    join_handler = None
    part_handler = None

    def __init__(self, path, ioloop = None):
        logger.info('Path: "%s"', path)

        self.path = path
        sys.path.append(path)
        self._ioloop = ioloop or IOLoop.instance()


    def _get(self, modname):
        for bot in self.bots:
            if bot._name == modname:
                return bot
        return None


    def _load(self, modname):
        bot = self._get(modname)
        if bot:
            logger.warn('"%s" has been loaded', bot._name)
            return False

        try:
            if modname in sys.modules:
                mod = importlib.reload(sys.modules[modname])
            else:
                mod = importlib.import_module(modname, None)

            mod.bot._name = modname
            if check_bot(mod.bot):
                try:
                    mod.bot.init()
                except Exception as err:
                    logger.error('Bot "%s" is failed to initialize: %s', modname, err)
                    return False
                else:
                    self.bots.append(mod.bot)

                    # Set bot's irc handler
                    mod.bot.say = self.send_handler

                    for t in mod.bot.targets:
                        self.join_handler(t)
                    logger.info('Bot "%s" is loaded', modname)
                    return True
        except Exception as err:
            logger.error('Bot "%s" is failed to import: %s', modname, err)
            return False


    def _unload(self, modname):
        bot = self._get(modname)
        if not bot:
            logger.warn('"%s" is not loaded', modname)
            return False
        try:
            bot.finalize()
        except Exception as err:
            logger.error('Bot "%s" failed to finalize: %s', bot._name, err)

        self.bots.remove(bot)
        for t in bot.targets:
            self.part_handler(t)
        logger.info('Bot "%s" is unloaded', bot._name)
        return True


    def set_handler(self,
            send_handler = empty_handler,
            join_handler = empty_handler,
            part_handler = empty_handler):
        self.send_handler = send_handler
        self.join_handler = join_handler
        self.part_handler = part_handler


    def start(self):
        for f in os.listdir(self.path):
            name = file2mod(f)
            if not name:
                continue
            self._load(name)

        wm = pyinotify.WatchManager()
        wm.add_watch(self.path,
                pyinotify.IN_DELETE |
                pyinotify.IN_CREATE |
                pyinotify.IN_MODIFY ,
                rec = False)

        handle = EventHandler(self)
        self._notifier = pyinotify.TornadoAsyncNotifier(
                wm, self._ioloop, default_proc_fun = handle)


    def on_LABOTS_MENTION_MSG(self, target, bot, nick, msg):
        if msg == 'help':
            for bot in self.bots:
                if target in bot.targets and bot.usage:
                    self.send_handler(target, '[%s] %s' % (bot._name, bot.usage))


    def dispatch(self, event, origin, *args, **kw):
        # Build-in behaviors
        if event == 'LABOTS_MENTION_MSG':
            self.on_LABOTS_MENTION_MSG(origin, *args, **kw)

        func_name = 'on_' + event
        if not origin:
            raise Exception('No origin specified.')
        for bot in self.bots:
            if hasattr(bot, func_name) and origin in bot.targets:
                func = getattr(bot, func_name)
                try:
                    logger.debug('Bot "%s", event: %s, origin: %s, %s, %s',
                            bot._name, event, origin, args, kw)
                    # If bot's event function return True value,
                    # do not pass this message to next bot.
                    if func(origin, *args, **kw):
                        break
                except Exception as err:
                    logger.error('"%s".%s() failed: %s', bot._name, func_name, err)


    def stop(self):
        while self.bots:
            self._unload(self.bots[0]._name)
        self._notifier.stop()



if __name__ == '__main__':
    logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
    box = BotBox('bots')
    box.set_handler()
    box.start()
    try:
        IOLoop.instance().start()
    except KeyboardInterrupt:
        box.stop()
        IOLoop.instance().stop()
