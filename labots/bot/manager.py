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
from ..utils import override
from ..storage import Storage
from ..cache import Cache

# Initialize logging
logger = logging.getLogger(__name__)

class Manager(Event, Singleton):
    _bots_path: str
    _cache_db_path: str
    _bots: Dict[str, Bot] = {}
    _action: Action = None
    _cur_name: str = None # Name of currently registering bot

    _storage: Storage
    _config: Cache

    @property
    def action(self) -> Action:
        return self._action

    @action.setter
    def action(self, action: Action):
        if not isinstance(action, Action):
            raise TypeError()
        self._action = action

    def __init__(self,
            bots_path: str = None,
            config_path: str = None,
            storage: Storage = None,
            cache: Cache = None):
        self._bots_path = bots_path
        self._config_path = config_path
        # Add path to system import path
        sys.path.append(bots_path)

        self._storage = storage
        self._cache = cache

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
            logger.info('Configuration of bot %s is loaded', repr(self._cur_name))
        else:
            cfg = {}

        bot = bot_class(
                name = self._cur_name,
                action = self.action,
                config = cfg,
                storage = self._storage,
                cache = self._cache)

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

    async def load_bot(self, name: str):
        bot = self.get_bot(name)
        if bot:
            raise LoadError('Already loaded', bot = bot)
        self._cur_name = name

        if name in sys.modules:
            raise LoadError('%s can not be used as name of bot' % repr(name),
                    name = name)
        try:
            importlib.import_module(name, None)
        except Exception as e:
            raise LoadError('Failed to import module: %s' % e, name = name)

        if self._cur_name:
            self._cur_name = None
            raise LoadError('Module is imported but not bot is loaded',
                    name = name)

        for _, bot in self._bots.items():
            for t in bot.targets:
                await self.action.join(t)

        logger.info('Bot %s is loaded', repr(name))


    async def unload_bot(self, name, force = False):
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
            await self._action.part(t)

        del self._bots[name]
        del sys.modules[name]

        logger.info('Bot %s is unloaded', repr(bot._name))


    async def load_bots(self):
        logger.info('Loading bots from path %s ...', repr(self._bots_path))
        for f in os.listdir(self._bots_path):
            name = self._file_name_to_module_name(f)
            if not name:
                continue
            try:
                await self.load_bot(name)
            except (LoadError, CheckError) as e:
                logger.error(e)


    async def unload_bots(self):
        logger.info('Unloading all bots...')
        for name in [name for name, _ in self._bots.items()]:
            try:
                # Froce unload
                await self.unload_bot(name, force = True)
            except UnloadError as e:
                logger.error(e)


    def check_bot(self, bot: Bot):
        if not isinstance(bot, Bot):
            raise CheckError('Not an instance of bot', bot = bot)

        can_override = []
        cant_override = []
        for v in dir(Bot):
            attr = getattr(Bot, v)
            if not callable(attr):
                continue
            if not override.is_overridable(attr):
                cant_override.append(v)
            elif not override.is_overridden(attr):
                can_override.append(v)

        for v in cant_override:
            attr = getattr(bot, v)
            if attr == None:
                raise CheckError('Attribute %s should not be None' % repr(v),
                        bot = bot)
            if override.is_overridden(attr):
                raise CheckError('Attribute %s should not be overridden' %
                        repr(v), bot = bot)

        overridden = []
        for v in can_override:
            attr = getattr(bot, v)
            if attr == None:
                raise CheckError('Attribute %s should not be None' % repr(v),
                        bot = bot)
            if override.is_overridden(attr):
                overridden.append(v)

        logger.info('Bot %s overrides: %s', repr(bot._name), overridden)

    """
    Implement ..common.event.Event
    """

    async def on_connect(self):
        for _, bot in self._bots.items():
            try:
                bot.on_connect()
            except Exception as e:
                logger.error(EventError(str(e),
                    bot = bot,
                    event = current_func_name()))

    async def on_raw(self, msg: Message):
        for _, bot in self._bots.items():
            try:
                bot.on_raw(msg)
            except Exception as e:
                logger.error(EventError(str(e),
                    bot = bot,
                    event = current_func_name()))

    async def on_message(self, origin: str, target: str, msg: str):
        for _, bot in self._bots.items():
            if not bot.is_in_targets(target):
                continue
            try:
                bot.on_message(origin, target, msg)
            except Exception as e:
                logger.error(EventError(str(e),
                    bot = bot,
                    event = current_func_name()))

    async def on_channel_message(self, origin: str, channel: str, msg: str):
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
