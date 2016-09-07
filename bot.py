# -*- encoding: UTF-8 -*-
import os
import json
import logging

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Supported commands
supp_cmd = [
        'JOIN',
        'PART',
        'PRIVMSG',
        'NICK',
        'QUIT',
        'TIMER',
        ]

# IRC bot prototype
class Bot(object):
    # Private for subclass
    _name = None
    _send_handler = None

    # Public for sub class
    targets = []
    trig_cmds = []
    cmd_params = {}

    def init(self):
        pass

    def finalize(self):
        pass


def read_config(file_):
    config_file = os.path.join(os.path.dirname(file_),
            os.path.splitext(os.path.basename(file_))[0] + '.json')

    try:
        with open(config_file, 'r') as f:
            config = json.loads(f.read())
            return config
    except FileNotFoundError as err:
        logger.error('No such file "%s"', config_file)
    except Exception as err:
        logger.error('Failed to read configure file of "%s": %s',
                file_, err)
    return None


# Decorator for callback functions in `Bot`
def echo(func):
    def warpper(self, *args, **kw):
        res = func(self, *args, **kw)
        if not res:
            return True
        pass_, target, msg = res

        logger.debug('%s(): pass: %s, target: %s, msg: %s',
                func.__name__, pass_, target, msg)
        if target and msg:
            if self._send_handler:
                self._send_handler(target, msg)
            else:
                logger.error('%s(): "%s"._send_handler is invaild',
                        func.__name__, self._name)
        return pass_
    return warpper


# Decorator for callback functions in `Bot`
def broadcast(func):
    def warpper(self, *args, **kw):
        res = func(self, *args, **kw)
        if not res:
            return True
        pass_, targets, msg = res

        logger.debug('%s(): pass: %s, target: %s, msg: %s', func.__name__, pass_, msg)
        if msg:
            if self._send_handler:
                [self._send_handler(t, msg) for t in targets]
            else:
                logger.error('%s(): "%s"._send_handler is invaild',
                        func.__name__, self._name)
        return pass_
    return warpper


def check_bot(bot):
    if not isinstance(bot.targets, list):
        logger.error('bot.target is no correctly defined')
        return False
    if not isinstance(bot.trig_cmds, list):
        logger.error('bot.trig_cmds is no correctly defined')
        return False
    if not isinstance(bot.cmd_params, dict):
        logger.error('bot.cmd_params is no correctly defined')
        return False
    if not hasattr(bot.init, '__call__'):
        logger.error('bot.init() is no correctly defined')
        return False
    if not hasattr(bot.finalize, '__call__'):
        logger.error('bot.init() is no correctly defined')
        return False
    for cmd in bot.trig_cmds:
        if cmd not in supp_cmd:
            logger.error('No supported command "%s"', cmd)
            return False
    return True


if __name__ == '__main__':
    logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
