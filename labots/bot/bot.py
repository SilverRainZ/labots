# -*- encoding: UTF-8 -*-
import logging
from typing import List, Dict, Any

from ..common.message import Message
from ..common.event import Event
from ..common.action import Action

# Initialize logging
logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)

def is_covered(func) -> bool:
    return hasattr(func, '_uncoverd')

def uncovered(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    wrapper._uncoverd = None
    return wrapper

class Bot(Event):
    _name = None

    targets: List[Any] = {} # TODO: str or dict?
    config: Dict = {}
    allow_reload: bool = True
    logger: logging.Logger = None
    action: Action = None

    @uncovered
    def __init__(self,
            name: str = '<unknown>',
            action: Action = None,
            config: Dict = {}):
        self._name = name
        self.logger = logging.getLogger(__name__ + ':' + name)
        self.action = action
        self.config = config

    """
    Bot phase callbacks
    """

    @uncovered
    def init(self):
        pass

    @uncovered
    def finalize(self):
        pass

    """
    Implement ..common.event.Event
    """

    @uncovered
    def on_raw(self, msg: Message):
        pass

    @uncovered
    def on_connect(self):
        pass

    @uncovered
    def on_message(self, origin: str, target: str, msg: str):
        pass

    @uncovered
    def on_channel_message(self, origin: str, channel: str, msg: str):
        pass

    """
    Utils functions
    """
    @uncovered
    def is_in_targets(self, target: str) -> bool:
        for t in self.targets:
            if isinstance(t, str):
                if self.action.is_same_target(target, t):
                    return True
            elif isinstance(t, dict) and 'targets' in t:
                if self.action.is_same_target(target, t['target']):
                    return True
        return False
