# -*- encoding: UTF-8 -*-
import logging

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

hdr = logging.StreamHandler()
hdr.setLevel(logging.INFO)

fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
fmter = logging.Formatter(fmt, None)

hdr.setFormatter(fmt)
logger.addHandler(hdr)


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
                [ self._send_handler(t, msg) for t in targets]
            else:
                logger.error('%s(): "%s"._send_handler is invaild',
                        func.__name__, self._name)
        return pass_
    return warpper
