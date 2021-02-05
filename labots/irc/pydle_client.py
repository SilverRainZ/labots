import logging
import pydle

from ..common.message import Message
from ..common.event import Event

logger = logging.getLogger(__name__)

def pydle_message_to_message(msg) -> Message:
    _msg = Message()
    _msg.command = msg.command
    _msg.params = msg.params
    return _msg

class PydleClient(pydle.Client):
    """
    A simple wrapper of pydle.Client, convert pydle callbacks to
    ..common.event.Event.
    """

    RECONNECT_MAX_ATTEMPTS = 100
    RECONNECT_DELAYS = [d * 5 for d in range(0, RECONNECT_MAX_ATTEMPTS)]

    _event: Event

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def on_connect(self):
        await super().on_connect()
        await self._event.on_connect()

    async def on_raw(self, msg):
        await super().on_raw(msg)
        await self._event.on_raw(pydle_message_to_message(msg))

    async def on_message(self, target, by, message):
        await super().on_message(target, by, message)
        await self._event.on_message(by, target, message)

    async def on_channel_message(self, target, by, message):
        await super().on_channel_message(target, by, message)
        await self._event.on_channel_message(by, target, message)

    async def on_join(self, channel, user):
        await super().on_join(channel, user)
        logger.info('%s has joined %s', self.nickname, channel)
        # FIXME: Why?
        # self._event.on_join(channel, user)
