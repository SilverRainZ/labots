#!/usr/bin/env python3
# -*- encoding: UTF-8 -*-

import argparse
import logging

from labots.config import config
from labots.irc import client
from labots.bot import manager
from labots.api import server
from labots.utils import clogger

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config",
            default = 'labots.yaml',
            type = str,
            help = "specified a config file")
    args = parser.parse_args()
    with open(args.config, 'r') as f:
        try:
            cfg = config.load_config(f.read())
        except (KeyError, ValueError) as e:
            logger.error(e)
            return 1

    irc = client.Client(
            host = cfg.irc.host,
            port = cfg.irc.port,
            tls = cfg.irc.tls,
            tls_verify = cfg.irc.tls_verify,
            nickname = cfg.irc.nickname,
            username = cfg.irc.username,
            realname = cfg.irc.realname)
    mgr = manager.Manager(
            path = cfg.manager.path,
            config_path = cfg.manager.config)
    api = server.Server(
            listen = cfg.server.listen,
            manager = mgr)
    mgr.action = irc
    irc.event = mgr

    try:
        irc.connect()
        mgr.load_bots()
        api.serve()
        irc.handle()
    except KeyboardInterrupt:
        mgr.unload_bots()
        api.stop()
        irc.disconnect()

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
