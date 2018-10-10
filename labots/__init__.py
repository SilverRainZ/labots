from typing import Type

from .bot.bot import Bot
from .bot.manager import Manager

def register(bot_class: Type[Bot]):
    return Manager.get_instance().register_bot(bot_class)
