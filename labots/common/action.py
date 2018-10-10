from abc import ABC, abstractmethod

from .message import Message

class Action(ABC):

    ''' Send message functions. '''

    @abstractmethod
    def raw(msg : Message):
        raise NotImplementedError

    @abstractmethod
    def message(self, target: str, msg: str):
        raise NotImplementedError

    @abstractmethod
    def join(self, channel: str, password: str = None):
        raise NotImplementedError

    @abstractmethod
    def part(self, channel: str, reason: str = None):
        raise NotImplementedError

    ''' Utils functions. '''

    @abstractmethod
    def is_channel(self, target: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def is_same_target(self, target1: str, target2: str) -> bool:
        raise NotImplementedError

'''
    @abstractmethod
    def kick(target: str, msg: str):
        raise NotImplementedError

    @abstractmethod
    def ban(target: str, msg: str):
        raise NotImplementedError
'''
