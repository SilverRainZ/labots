import logging
import pydle
from typing import Dict

from .wrapper import Wrapper
from ..common.message import Message
from ..common.event import Event
from ..common.action import Action
from ..utils.singleton import Singleton

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class Client(Action, Singleton):
    # Config
    _host: str
    _port: int
    _tls: bool
    _tls_verify: bool
    _nickname: str
    _username: str
    _hostname: str
    _realname: str
    _password: str

    _event: Event = None
    _client: Wrapper = None
    _channels: Dict[str,int] = {} # Channel reference count
    
    def __init__(self,
            host: str = None, 
            port: int = None,
            tls: bool = None,
            tls_verify: bool = None,
            nickname: str = None,
            username: str = None,
            hostname: str = None,
            realname: str = None,
            password: str = None,
            ):
        super().__init__()
        self._host = host
        self._port = port
        self._tls = tls
        self._tls_verify = tls_verify
        self._nickname = nickname
        self._username = username
        self._hostname = hostname
        self._realname = realname
        self._password = password

    @property
    def event(self) -> Event:
        return self._event

    @event.setter
    def event(self, event: Event):
        if not isinstance(event, Event):
            raise TypeError()
        self._event = event

    def connect(self):
        self._client = Wrapper(
                event = self._event,
                nickname = self._nickname,
                username = self._username,
                realname = self._realname,
        )
        self._client.connect(
                hostname = self._host,
                port = self._port,
                tls = self._tls,
                tls_verify = self._tls_verify,
                )

    def handle(self):
        self._client.handle_forever()

    def disconnect(self):
        self._client.disconnect()

    ''' Implement ..common.event.Event '''

    def raw(self, msg: Message):
        pass

    def message(self, target: str, msg: str):
        self._client.message(target, msg)

    def join(self, channel: str, password: str = None):
        # Increase reference count
        if channel in self._channels:
            self._channels[channel] += 1
            return
        self._channels[channel] = 1
        self._client.join(channel, password = password)


    def part(self, channel: str, reason: str = None):
        # Decrease reference count
        if self._channels[channel] >= 1:
            self._channels[channel] -= 1
            return
        del self._channels[channel]
        self._client.part(channel, message = reason)

    def is_channel(self, target: str) -> bool:
        return self._client.is_channel(target)

    def is_same_target(self, target1: str, target2: str) -> bool:
        if self.is_channel(target1):
            return self._client.is_same_channel(target1, target2)
        else:
            return self._client.is_same_nick(target1, target2)
