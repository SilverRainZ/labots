#!/usr/bin/env python3
# -*- encoding: UTF-8 -*-

import sys
import yaml
import logging
from tornado.ioloop import IOLoop
from labots.botbox import BotBox
from labots.irc.irc import IRC

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def main():
    with open('labots.yaml', 'r') as f:
        config = yaml.load(f)

    botbox = BotBox(config['path'])
    irc = IRC(config['host'], config['port'], 'labots', relaybots = config['relaybots'])

    irc.set_callback(
            login_callback = botbox.start,
            event_callback = botbox.dispatch
            )

    botbox.set_handler(
            send_handler = irc.send,
            join_handler = irc.join,
            part_handler = irc.part
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
    logging.basicConfig(
            handlers=[logging.FileHandler("labots.log"), logging.StreamHandler()],
            format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
    main()
