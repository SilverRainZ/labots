#!/usr/bin/env python3
# -*- encoding: UTF-8 -*-

import sys
import argparse
import logging
import yaml
from tornado.ioloop import IOLoop
from labots.botbox import BotBox
from labots.irc.irc import IRC
from labots import clogger


# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default = 'config.yaml', type = str,
            help = "specified a config file")
    args = parser.parse_args()

    with open(args.config, 'r') as f:
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
    filelog = logging.FileHandler('labots.log')
    filelog.setFormatter(clogger.Formatter(False))
    syslog = logging.StreamHandler()
    syslog.setFormatter(clogger.Formatter(True))

    logging.basicConfig(
            level = logging.INFO,
            handlers = [filelog, syslog],
            )
    main()
