# -*- encoding: UTF-8 -*-
import os
import sys
import logging
import importlib
from typing import Dict, Type
import yaml

from .bot import Bot
from .error import LoadError, UnloadError, RegisterError, CheckError, EventError
from ..common.message import Message
from ..common.action import Action
from ..common.event import Event
from ..utils.singleton import Singleton
from ..utils import current_func_name

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Manager(Event, Singleton):
    _path: str
    _config_path: str
    _bots: Dict[str, Bot] = {}
    _action: Action = None
    _cur_name: str = None # Name of currently registering bot

    @property
    def action(self) -> Action:
        return self._action

    @action.setter
    def action(self, action: Action):
        if not isinstance(action, Action):
            raise TypeError()
        self._action = action

    def __init__(self, path: str = None, config_path: str = None):
        self._path = path
        self._config_path = config_path
        # Add path to system import path
        sys.path.append(path)

    """
    Bot management functions
    """

    def register_bot(self, bot_class: Type[Bot]):
        # Check class
        if not issubclass(bot_class, Bot):
            raise RegisterError('Class %s is not subclass of class %s' %
                    (bot_class, Bot),
                    name = self._cur_name)

        # Try load bot config
        cfgs = None
        if self._config_path:
            try:
                with open(self._config_path) as f:
                    cfgs = yaml.load(f)
            except Exception as e:
                raise RegisterError('Failed to open bots config file: %s' % e,
                        name = self._cur_name)

        if self._cur_name in cfgs:
            cfg = cfgs[self._cur_name]
            logger.info('Config of bot %s is loaded', repr(self._cur_name))
        else:
            cfg = None

        bot = bot_class(
                name = self._cur_name,
                action = self.action,
                config = cfg,
                )

        try:
            self.check_bot(bot)
        except CheckError as e:
            raise e
        try:
            bot.init()
        except Exception as e:
            raise RegisterError('Failed to initialize: %s' % e, bot = bot)

        self._bots[self._cur_name] = bot
        self._cur_name = None


    def get_bot(self, name: str) -> Bot:
        if name in self._bots:
            return self._bots[name]
        return None

    def load_bot(self, name: str):
        bot = self.get_bot(name)
        if bot:
            raise LoadError('Already loaded', bot = bot)
        try:
            self._cur_name = name
            if name in sys.modules:
                importlib.reload(sys.modules[name])
            else:
                importlib.import_module(name, None)
        except Exception as e:
            raise LoadError('Failed to import module: %s' % e, name = name)

        if self._cur_name:
            self._cur_name = None
            raise LoadError('Module is imported but not bot is loaded',
                    name = name)

        logger.info('Bot %s is loaded', repr(name))


    def unload_bot(self, name, force = False):
        bot = self.get_bot(name)
        if not bot:
            raise UnloadError('Not loaded', name = name)
        if not bot.allow_reload and not force:
            raise UnloadError('Can not be reloaded', bot = bot)
        try:
            bot.finalize()
        except Exception as e:
            raise UnloadError('Failed to finalize: %s' % e, bot = bot)

        for t in bot.targets:
            self._action.part(t)

        del self._bots[name]

        logger.info('Bot "%s" is unloaded', bot._name)


    def load_bots(self):
        for f in os.listdir(self._path):
            name = self._file_name_to_module_name(f)
            if not name:
                continue
            try:
                self.load_bot(name)
            except (LoadError, CheckError) as e:
                logger.error(e)


    def unload_bots(self):
        for name in [name for name, _ in self._bots.items()]:
            try:
                # Froce unload
                self.unload_bot(name, force = True)
            except UnloadError as e:
                logger.error(e)


    def check_bot(self, bot: Bot):
        pass

    """
    Implement ..common.event.Event
    """

    def on_connect(self):
        for _, bot in self._bots.items():
            for t in bot.targets:
                self.action.join(t)
        for _, bot in self._bots.items():
            try:
                bot.on_connect()
            except Exception as e:
                logger.error(EventError(str(e),
                    bot = bot,
                    event = current_func_name()))

    def on_raw(self, msg: Message):
        for _, bot in self._bots.items():
            try:
                bot.on_raw(msg)
            except Exception as e:
                logger.error(EventError(str(e),
                    bot = bot,
                    event = current_func_name()))

    def on_message(self, origin: str, target: str, msg: str):
        for _, bot in self._bots.items():
            if not bot.is_in_targets(target):
                continue
            try:
                bot.on_message(origin, target, msg)
            except Exception as e:
                logger.error(EventError(str(e),
                    bot = bot,
                    event = current_func_name()))

    def on_channel_message(self, origin: str, channel: str, msg: str):
        for _, bot in self._bots.items():
            if not bot.is_in_targets(channel):
                continue
            try:
                bot.on_channel_message(origin, channel, msg)
            except Exception as e:
                logger.error(EventError(str(e),
                    bot = bot,
                    event = current_func_name()))

    """
    Utils functions
    """

    @staticmethod
    def _file_name_to_module_name(f):
        v = os.path.splitext(f)
        base, ext = v[0], v[1]
        # Not a python file
        if ext != '.py':
            return None
        # Ignored
        if base.startswith('_') or base.startswith('.'):
            return None
        return base
