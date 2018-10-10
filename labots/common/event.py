from abc import ABC, abstractmethod

from .message import Message

class Event(ABC):
    @abstractmethod
    def on_raw(self, msg: Message):
        raise NotImplementedError

    @abstractmethod
    def on_connect(self):
        raise NotImplementedError

    @abstractmethod
    def on_message(self, origin: str, target: str, msg: str):
        """ Callback called when received a message. """
        raise NotImplementedError

    @abstractmethod
    def on_channel_message(self, origin: str, channel: str, msg: str):
        """ Callback called when received a message in a channel. """
        raise NotImplementedError


    '''
    @abstractmethod
    def on_private_message(self, origin: str, msg: str):
        """ Callback called when received a private message. """
        raise NotImplementedError

    @abstractmethod
    def on_join(self, origin: str, channel: str):
        raise NotImplementedError

    @abstractmethod
    def on_part(self, origin: str, channel: str, reason: str):
        raise NotImplementedError

    @abstractmethod
    def on_quit(self, origin: str, reason: str):
        raise NotImplementedError

    @abstractmethod
    def on_nick_change(self, origin: str, msg: str):
        """ Callback called when received a private message. """
        raise NotImplementedError

    def on_raw_xxx(self, msg: Message):
        """ Callback called when received a private message. """
        pass
    '''
