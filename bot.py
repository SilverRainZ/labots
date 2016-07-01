# -*- encoding: UTF-8 -*-
import logging

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# IRC bot prototype
class Bot(object):
    # Private for subclass
    _name = None
    _filename = None
    _send_handler = None

    # Public for sub class
    targets = []
    trig_cmds = []
    trig_keys = []

    def init(self):
        pass

    def finalize(self):
        pass



# Decorator for callback functions in `Bot`
def echo(func):
    def warpper(self, *args, **kw):
        pass_, target, msg = func(self, *args, **kw)
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
        pass_, targets, msg = func(self, *args, **kw)
        logger.debug('%s(): pass: %s, msg: %s', func.__name__, pass_, msg)
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
    if not isinstance(bot.trig_keys, list):
        logger.error('bot.trig_keys is no correctly defined')
        return False
    if not hasattr(bot.init, '__call__'):
        logger.error('bot.init() is no correctly defined')
        return False
    if not hasattr(bot.finalize, '__call__'):
        logger.error('bot.init() is no correctly defined')
        return False

    return True


if __name__ == '__main__':
    logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
