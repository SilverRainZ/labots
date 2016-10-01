# -*- encoding: UTF-8 -*-
import os
import json
import logging

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# IRC bot prototype
class Bot(object):
    # Private for subclass
    _name = None
    _file = None

    # Public for sub class
    targets = []
    config = {}

    # IRC handler functions
    # def say(target, msg)
    say = None

    def __init__(self, file_):
        self._file = file_
        self.read_config()

    def init(self):
        pass

    def finalize(self):
        pass

    def read_config(self):
        config_file = os.path.join(os.path.dirname(self._file),
                os.path.splitext(os.path.basename(self._file))[0] + '.json')

        try:
            with open(config_file, 'r') as f:
                self.config = json.loads(f.read())
        except FileNotFoundError as err:
            logger.error('No such file "%s"', config_file)
        except json.JSONDecodeError as err:
            logger.error('"%s", json decode error: %s', config_file, err)
        except Exception as err:
            logger.error('Failed to read configure file of "%s": %s', self._file, err)

    '''
    User implemented function, origin of message must be the first argument,
    if function return True, this event won't pass to next bot:

    def on_PRIVMSG(target, nick, msg):
        pass
    def on_ACTION(target, nick, msg):
        pass
    def on_NOTICE(target, nick, msg):
        pass
    def on_JOIN(chan, nick):
        pass
    def on_PART(chan, nick):
        pass
    def on_QUIT(chan, nick, reason):
        pass
    def on_NICK(chan, old_nick, new_nick):
        pass
    '''



events = [ 'PRIVMSG', 'ACTION', 'NOTICE', 'JOIN', 'PART', 'QUIT', 'NICK', ]

def check_bot(bot):
    if not isinstance(bot.targets, list):
        logger.error('"%s".targets is not correctly defined', bot._name)
        return False
    if not hasattr(bot.init, '__call__'):
        logger.error('"%s".init() is not correctly defined', bot._name)
        return False
    if not hasattr(bot.finalize, '__call__'):
        logger.error('"%s".init() is not correctly defined', bot._name)
        return False

    func_names = []
    for event in events:
        func_name = 'on_' + event
        if hasattr(bot, func_name):
            attr = getattr(bot, func_name)
            if hasattr(attr, '__call__'):
                func_names.append(func_name)
            else:
                logger.error('"%s".%s() is not callable', bot._name, func_name)

    logger.info('Bot "%s" provides: %s', bot._name, func_names)
    return True


if __name__ == '__main__':
    logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
