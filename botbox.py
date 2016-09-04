# -*- encoding: UTF-8 -*-
import os
import sys
import logging
import pyinotify
import importlib
import functools
import traceback
from tornado.ioloop import IOLoop, PeriodicCallback
from bot import Bot, echo, broadcast, check_bot
from irc import IRCMsg, IRCMsgType

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def empty_handler(*args, **kw):
    logger.debug("Unimplement handler %s %s" % (args, kw))


def file2mod(fname):
    if not fname.startswith('_') \
            and not fname.startswith('.') \
            and (os.path.splitext(fname)[1] in ['', '.py']):
        return os.path.splitext(fname)[0]
    else:
        return None


class EventHandler(pyinotify.ProcessEvent):
    botbox = None

    def __init__(self, botbox):
        self.botbox = botbox


    def process_IN_CREATE(self, event):
        name = file2mod(event.name)
        if not name:
            return

        logger.debug('%s', event)

        if event.path == self.botbox.path:
            self.botbox._load(name)
        else:
            path, dir_name = os.path.split(event.path)
            while path:
                if path == self.botbox.path \
                        and file2mod(dir_name):
                    self.botbox._unload(dir_name)
                    self.botbox._load(dir_name)
                    break
                else:
                    path, dir_name = os.path.split(path)


    def process_IN_DELETE(self, event):
        name = file2mod(event.name)
        if not name:
            return

        logger.debug('%s', event)

        if event.path == self.botbox.path:
            self.botbox._unload(name)
        else:
            path, dir_name = os.path.split(event.path)
            while path:
                if path == self.botbox.path \
                        and file2mod(dir_name):
                    self.botbox._unload(dir_name)
                    self.botbox._load(dir_name)
                    break
                else:
                    path, dir_name = os.path.split(path)


    def process_IN_MODIFY(self, event):
        name = file2mod(event.name)
        if not name:
            return

        logger.debug('%s', event)

        if event.path == self.botbox.path:
            self.botbox._unload(name)
            self.botbox._load(name)
        # Bot is a package
        else:
            path, dir_name = os.path.split(event.path)
            while path:
                if path == self.botbox.path \
                        and file2mod(dir_name):
                    self.botbox._unload(dir_name)
                    self.botbox._load(dir_name)
                    break
                else:
                    path, dir_name = os.path.split(path)


class BotBox(object):
    _ioloop = None
    _notifier = None
    _timer = None
    _tick = 0

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

        # 1 min
        self._tick = 0
        self._timer = PeriodicCallback(self.on_timer,
                60 * 1000, io_loop=self._ioloop)
        self._timer.start()
        

    def _get(self, modname):
        for bot in self.bots:
            if bot._name == modname:
                return bot
        return None


    def _load(self, modname):
        logger.debug('Load "%s"', modname)
        bot = self._get(modname)
        if bot:
            logger.warn('"%s" has been loaded', bot._name)
            return False

        try:
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
                    mod.bot._name = modname
                    self.bots.append(mod.bot)
                    mod.bot._send_handler = self.send_handler
                    for t in mod.bot.targets:
                        self.join_handler(t)
                    logger.info('Bot "%s" is loaded', modname)
                    return True
        except Exception as err:
            logger.error('Bot "%s" is failed to import: %s', modname, err)
            return False


    def _unload(self, modname):
        logger.debug('Unload "%s"', modname)
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


    def set_handler(self, send = empty_handler,
            join = empty_handler,
            part = empty_handler):
        self.send_handler = send
        self.join_handler = join
        self.part_handler = part


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
                rec = True)

        handle = EventHandler(self)
        self._notifier = pyinotify.TornadoAsyncNotifier(
                wm, self._ioloop, default_proc_fun = handle)


    # TODO: 减少重复代码
    def on_privmsg(self, nick, chan, msg):
        for bot in self.bots:
            if 'PRIVMSG' in bot.trig_cmds and chan in bot.targets:
                try:
                    if not bot.on_privmsg(nick, chan, msg):
                        break
                except Exception as err:
                    logger.error('"%s".on_privmsg() failed: %s', bot._name, err)


    def on_join(self, nick, chan):
        for bot in self.bots:
            if 'JOIN' in bot.trig_cmds and chan in bot.targets:
                try:
                    if not bot.on_join(nick, chan):
                        break
                except Exception as err:
                    logger.error('"%s".on_join() failed: %s', bot._name, err)


    def on_part(self, nick, chan, reason):
        for bot in self.bots:
            if 'PART' in bot.trig_cmds and chan in bot.targets:
                try:
                    if not bot.on_part(nick, chan, reason):
                        break
                except Exception as err:
                        logger.error('"%s".on_part() failed: %s',bot._name, err)


    def on_quit(self, nick, chan, reason):
        for bot in self.bots:
            if 'QUIT' in bot.trig_cmds and chan in bot.targets:
                try:
                    if not bot.on_quit(nick, chan, reason):
                        break
                except Exception as err:
                    logger.error('"%s".on_quit() failed: %s', bot._name, err)


    def on_nick(self, old_nick, new_nick, chan):
        for bot in self.bots:
            if 'NICK' in bot.trig_cmds and chan in bot.targets:
                try:
                    if not bot.on_nick(old_nick, new_nick, chan):
                        break
                except Exception as err:
                    logger.error('"%s".on_nick() failed: %s', bot._name, err)


    def on_timer(self):
        logger.debug('self._tick: %s', self._tick)
        self._tick += 1

        for bot in self.bots:
            if 'TIMER' in bot.trig_cmds:
                try:
                    if not bot.on_timer():
                        break
                except Exception as err:
                    logger.error('"%s".on_timer() failed: %s', bot._name, err)


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
