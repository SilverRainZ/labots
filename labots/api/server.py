import logging
import tornado.web
import tornado.httpserver
from http import HTTPStatus
from urllib.parse import urlparse

from .common import BOT_API_PATH, Action, Response, Error
from ..bot.manager import Manager
from ..bot.error import LoadError, UnloadError
from ..utils import current_func_name
from ..utils.singleton import Singleton

logger = logging.getLogger(__name__)

"""
Server provides:

- /bots/<bot_name>/load
- /bots/<bot_name>/unload
- /bots/<bot_name>/reaload
- /bots/<bot_name>/storage
- /bots/<bot_name>/cache
- ...

"""

class BotHandler(tornado.web.RequestHandler):
    _manager: Manager

    def initialize(self):
        self._manager = self.application._manager

    def get(self, name: str, action: str):
        if not action in [item.value for item in Action]:
            self.set_status(HTTPStatus.BAD_REQUEST)
            self.write(Response(error = Error.INVALID_ACTION).to_dict())
            return
        action = Action(action)

        if action == Action.STORAGE:
            b = self._manager.get_bot(name)
            if b:
                d = {}
                d.update(b.storage)
                self.write(Response(error = Error.OK, data = d).to_dict())
            else:
                self.write(Response(error = Error.NOT_FOUND).to_dict())
            return
        elif action == Action.CACHE:
            b = self._manager.get_bot(name)
            if b:
                d = {}
                d.update(b.cache)
                self.write(Response(error = Error.OK, data = d).to_dict())
            else:
                self.write(Response(error = Error.NOT_FOUND).to_dict())
            return
        else:
            self.set_status(HTTPStatus.METHOD_NOT_ALLOWED)
            self.write(Response(error = Error.NOT_ALLOWED,
                message = 'Action %s is not allowed for method %s' %(
                    repr(action.value), repr(current_func_name()))).to_dict())
            return

        # Should not reach
        self.write(Response(error = Error.INTERNAL).to_dict())

    def post(self, name: str, action: str):
        if not action in [item.value for item in Action]:
            self.set_status(HTTPStatus.BAD_REQUEST)
            self.write(Response(error = Error.INVALID_ACTION).to_dict())
            return
        action = Action(action)

        if action == Action.LOAD:
            try:
                self._manager.load_bot(name)
            except LoadError as e:
                self.write(Response(error = Error.LOAD, message = str(e)).to_dict())
            else:
                self.write(Response(error = Error.OK).to_dict())
            return
        elif action == Action.UNLOAD:
            try:
                self._manager.unload_bot(name)
            except UnloadError as e:
                self.write(Response(error = Error.UNLOAD, message = str(e)).to_dict())
            else:
                self.write(Response(error = Error.OK).to_dict())
            return
        else:
            self.set_status(HTTPStatus.METHOD_NOT_ALLOWED)
            self.write(Response(error = Error.NOT_ALLOWED,
                message = 'Action %s is not allowed for method %s' %(
                    repr(action.value), repr(current_func_name()))).to_dict())
            return

        # Should not reach
        self.write(Response(error = Error.INTERNAL).to_dict())


class Server(tornado.web.Application, Singleton):
    _listen: str
    _manager: Manager
    _server = None

    def __init__(self,
            listen: str = None,
            manager: Manager = None):
        hdrs = [
                (BOT_API_PATH + '/(.+)/(.+)', BotHandler),
                ]
        super().__init__(hdrs)

        self._listen = listen
        self._manager = manager
        self._server = tornado.httpserver.HTTPServer(self)

    def serve(self):
        logger.info('Starting the API server, listening on %s ...', self._listen)
        url = urlparse(self._listen)
        if url.scheme in ['', 'http']:
            self._server.listen(url.port, address = url.hostname)
        else:
            raise NotImplementedError('Unsupported scheme %s' % repr(url.scheme))

    def close(self):
        logger.info('Stopping the API server...')
        self._server.stop()
