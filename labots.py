#!/usr/bin/env python3
# -*- encoding: UTF-8 -*-

import sys
import logging
import config
from tornado.ioloop import IOLoop
from botbox import BotBox
from irc import IRC

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def main():
    botbox = BotBox(config.path)

    irc = IRC(config.host, config.port, 'labots')

    irc.set_callback(
            login = botbox.start,
            privmsg = botbox.on_privmsg,
            join = botbox.on_join,
            part = botbox.on_part,
            nick = botbox.on_nick,
            quit = botbox.on_quit,
            )

    botbox.set_handler(
            send = irc.send,
            join = irc.join,
            part = irc.part
            )

    try:
        IOLoop.instance().start()
    except KeyboardInterrupt:
        botbox.stop()
        irc.stop()
        IOLoop.instance().stop()
        logger.info('Exit.')
        return 0

if __name__ == '__main__':
    logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
    main()
