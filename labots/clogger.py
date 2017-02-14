# Ref: https://github.com/lilydjwg/winterpy/blob/master/pylib/nicelogger.py 
import time
import logging
import pkgutil

import labots

internal_mod = [modname for (importer, modname, ispkg)
        in pkgutil.iter_modules(labots.__path__)] + [labots.__name__]

level2name = {
        logging.CRITICAL:   'CRIT',
        logging.ERROR:      'ERR',
        logging.WARNING:    'WARN',
        logging.INFO:       'INFO',
        logging.DEBUG:      'DBG',
        logging.NOTSET:     'NTST',
        }

name2color = {
        'CRIT': '\x1b[31m%s\x1b[0m',
        'ERR':  '\x1b[31m%s\x1b[0m',  
        'WARN': '\x1b[33m%s\x1b[0m',
        'INFO': '\x1b[32m%s\x1b[0m',
        'DBG':  '\x1b[37m%s\x1b[0m',
        'NTST': '%s',
        }

old_factory = logging.getLogRecordFactory()

def record_factory(*args, **kwargs):
    record = old_factory(*args, **kwargs)
    # record.custom_attribute = 0xdecafbad
    record.levelname = level2name.get(args[1])

    # Is internal module
    if record.module not in internal_mod:
        record.module = 'bots.' + record.module

    return record

logging.setLogRecordFactory(record_factory)

class Formatter(logging.Formatter):
    _color = False

    def __init__(self, color, *args, **kwargs):
        super().__init__(self, *args, **kwargs)
        self._color = color

    def format(self, record):
        try:
            record.message = record.getMessage()
        except Exception as e:
            record.message = "Bad message (%r): %r" % (e, record.__dict__)
        record.asctime = time.strftime("%m-%d %H:%M:%S", self.converter(record.created))

        prefix = '[%(levelname)4s %(asctime)s %(module)6s]' % record.__dict__
        prefix = name2color.get(record.levelname) % prefix
        formatted = prefix + ' ' + record.message

        if record.exc_info and not record.exc_text:
                record.exc_text = self.formatException(record.exc_info)

        if record.exc_text:
            formatted = formatted.rstrip() + "\n" + record.exc_text

        return formatted.replace("\n", "\n    ")
