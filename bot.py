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
    _irc = None
    _name = None
    _filename = None

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
            self._irc.send(target, msg)
        return pass_
    return warpper


# Decorator for callback functions in `Bot`
def broadcast(func):
    def warpper(self, *args, **kw):
        pass_, targets, msg = func(self, *args, **kw)
        logger.debug('%s(): pass: %s, msg: %s', func.__name__, pass_, msg)
        if msg:
            [ self._irc.send(t, msg) for t in targets]
        return pass_
    return warpper
