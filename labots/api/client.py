import logging
import json
from tornado import httpclient

from .common import BOT_API_PATH, Action, Response, Error
from ..utils.singleton import Singleton

logger = logging.getLogger(__name__)

class Client(Singleton):
    _addr: str
    _client: httpclient.HTTPClient

    def __init__(self, addr: str = None):
        self._addr = addr
        self._client = httpclient.HTTPClient()

    def request(self, name: str, action: str) -> bool:
        if not action in [item.value for item in Action]:
            self.print_response(Response(error = Error.INVALID_ACTION))
            return False
        action = Action(action)

        # Join URL paths
        url = '/'.join(s.strip('/') for s in
                [self._addr, BOT_API_PATH, name, action.value])
        if action in [Action.LOAD, Action.UNLOAD]:
            # POST request
            try:
                r = self._client.fetch(url, method = 'POST', body = '')
                resp = Response.from_dict(json.loads(r.body))
            except (ConnectionRefusedError, httpclient.HTTPError) as e:
                resp = Response(error = Error.INTERNAL, message = str(e))
            self.print_response(resp)
            return resp.error == Error.OK
        elif action in [Action.STORAGE, Action.CACHE]:
            # GET request
            try:
                r = self._client.fetch(url, method = 'GET')
                resp = Response.from_dict(json.loads(r.body))
            except (ConnectionRefusedError, httpclient.HTTPError) as e:
                resp = Response(error = Error.INTERNAL, message = str(e))
            self.print_response(resp)
            return resp.error == Error.OK

        # Should not reach
        self.print_response(Response(error = Error.INTERNAL))
        return False

    def close(self):
        self._client.close()

    @staticmethod
    def print_response(resp: Response):
        if resp.error != Error.OK:
            logger.error('Server returns error: %s, message: %s, data: %s',
                    resp.error.value, resp.message, resp.data)
        else:
            logger.info('Server returns OK, message: %s, data: %s',
                    resp.message, resp.data)
