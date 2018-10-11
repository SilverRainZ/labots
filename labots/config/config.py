import logging
import yaml
import pprint
from typing import Dict

from labots.config import checker
from labots.common import meta

# Initialize logging
logger = logging.getLogger(__name__)

class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self

class Config(AttrDict):
    pass


def load_config(raw: str) -> Config:
    """ Load config from a yaml format string.  """
    d = yaml.load(raw)
    try:
        checker.check(d, [
            checker.Item(key = ['irc', 'host'],
                checkers = [checker.is_str, checker.is_not_empty_str],
                required = True),
            checker.Item(key = ['irc', 'port'],
                checkers = [checker.is_int, checker.is_port],
                default = 6667,
                required = True),
            checker.Item(key = ['irc', 'tls'],
                checkers = [checker.is_bool],
                default = False),
            checker.Item(key = ['irc', 'tls_verify'],
                checkers = [checker.is_bool],
                default = True),
            checker.Item(key = ['irc', 'nickname'],
                checkers = [checker.is_str, checker.is_not_empty_str],
                default = meta.name),
            checker.Item(key = ['irc', 'username'],
                checkers = [checker.is_str, checker.is_not_empty_str],
                default = meta.name),
            checker.Item(key = ['irc', 'realname'],
                checkers = [checker.is_str, checker.is_not_empty_str],
                default = meta.url),
            checker.Item(key = ['irc', 'password'],
                checkers = [checker.is_str],
                default = ''),

            checker.Item(key = ['manager', 'path'],
                checkers = [checker.is_str],
                required = True),
            checker.Item(key = ['manager', 'config'],
                checkers = [checker.is_str]),

            checker.Item(key = ['server', 'listen'],
                checkers = [checker.is_str],
                default = meta.default_listen),
            ])
    except (KeyError, ValueError) as e:
        raise e

    return Config(_build_attr_dict(d))


def _build_attr_dict(d: Dict) -> AttrDict:
    """ Recursively convert all dict to AttrDict. """
    r = {}
    for k, v in d.items():
        if isinstance(v, dict):
            r[k] = _build_attr_dict(v)
        else:
            r[k] = v
    return AttrDict(r)
