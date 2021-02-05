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

    def on_connect(self):
        super().on_connect()
        self._event.on_connect()

    def on_raw(self, msg):
        super().on_raw(msg)
        self._event.on_raw(pydle_message_to_message(msg))

    def on_message(self, target, by, message):
        super().on_message(target, by, message)
        self._event.on_message(by, target, message)

    def on_channel_message(self, target, by, message):
        super().on_channel_message(target, by, message)
        self._event.on_channel_message(by, target, message)

    def on_join(self, channel, user):
        super().on_join(channel, user)
        logger.info('%s has joined %s', self.nickname, channel)
        # self._event.on_join(channel, user)

