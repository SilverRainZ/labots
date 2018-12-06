from enum import Enum, unique

BOT_API_PATH = '/bots'

@unique
class Action(Enum):
    LOAD = 'load'
    UNLOAD = 'unload'

@unique
class Error(Enum):
    OK = None
    NOT_FOUND = 'bot-not-found'
    LOAD = 'bot-load-error'
    UNLOAD = 'bot-unload-error'
    INVALID_ACTION = 'invalid-action'
    NOT_ALLOWED = 'not-allowed-action'
    INTERNAL = 'internal-error'

class Response(object):
    """ Response returned by .server.Server. """
    _error_key = 'err'
    _message_key = 'msg'

    error: Error
    message: str

    def __init__(self, error: Error = Error.OK, message: str = None):
        self.error = error
        self.message = message

    def to_dict(self) -> dict:
        return {
                Response._error_key: self.error.value,
                Response._message_key: self.message,
                }

    @classmethod
    def from_dict(cls, d: dict):
        if not Response._error_key in d:
            raise KeyError('Key %s not found in response',
                    repr(Response._error_key))
        err = Error(d[Response._error_key])
        if not Response._message_key in d:
            raise KeyError('Key %s not found in response',
                    repr(Response._message_key))
        msg = d[Response._message_key]
        return Response(error = err, message = msg)
