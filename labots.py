#!/usr/bin/env python3
# -*- encoding: UTF-8 -*-

import logging
import sys
import argparse
from tornado.ioloop import IOLoop

from labots.config import config
from labots.irc import client
from labots.bot import manager
from labots.api import server as apiserver
from labots.api import client as apiclient
from labots.api import common as apicommon
from labots.utils import clogger
from labots.common import meta
from labots.storage import Storage
from labots.cache import Cache

# Initialize logging
logger = logging.getLogger(__name__)

def setup_logging(cfg: config.Config = None):
    lv = logging.ERROR
    hdr = logging.StreamHandler(sys.stdout)
    hdr.setFormatter(clogger.Formatter(True))

    if cfg:
        name2level = {
                'debug': logging.DEBUG,
                'info': logging.INFO,
                'warning': logging.WARNING,
                'error': logging.ERROR,
                }
        name2output = {
                'stdout': sys.stdout,
                'stderr': sys.stderr,
                }

        if cfg.log.level in name2level:
            lv = name2level[cfg.log.level]

        if cfg.log.output in name2output:
            hdr = logging.StreamHandler(name2output[cfg.log.output])
        else:
            hdr = logging.FileHandler(cfg.log.output)

        hdr.setFormatter(clogger.Formatter(cfg.log.color))

    logging.basicConfig(
            level = lv,
            handlers = [hdr])

def labots_server(args: argparse.Namespace):
    with open(args.config, 'r') as f:
        try:
            cfg = config.load_config(f.read())
        except (KeyError, ValueError) as e:
            logger.error(e)
            return

    setup_logging(cfg)

    irc = client.Client(
            host = cfg.irc.host,
            port = cfg.irc.port,
            tls = cfg.irc.tls,
            tls_verify = cfg.irc.tls_verify,
            server_password = cfg.irc.server_password,
            nickname = cfg.irc.nickname,
            username = cfg.irc.username,
            realname = cfg.irc.realname,
            user_password = cfg.irc.user_password)
    storage = Storage(cfg.storage.db)
    cache = Cache(cfg.cache.db)
    mgr = manager.Manager(
            bots_path = cfg.manager.bots,
            config_path = cfg.manager.config,
            storage = storage,
            cache = cache)
    api = apiserver.Server(
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
        api.close()
        irc.disconnect()

def labots_client(args: argparse.Namespace):
    setup_logging()

    def callback():
        api = apiclient.Client(addr = args.addr)
        ret = api.request(args.bot, args.action)
        api.close()
        IOLoop.instance().stop()
        sys.exit(0 if ret else 1)

    IOLoop.instance().add_callback(callback())
    IOLoop.instance().start()


def main():
    parser = argparse.ArgumentParser(description = meta.description)
    parser.add_argument("-v", "--version",
            action = 'version',
            version = meta.pretty_name + ' ' + meta.version)

    subparsers = parser.add_subparsers(title = 'subcommanads')

    # Server argumentes
    srvparser = subparsers.add_parser('server',
            aliases = ['srv', 's'],
            help = 'start the server')
    srvparser.add_argument("-c", "--config",
            default = meta.name + '.yaml',
            type = str,
            help = "specify the path of configuration file")
    srvparser.set_defaults(func = labots_server)

    # Client argumentes
    cliparser = subparsers.add_parser('client',
            aliases = ['cli', 'c'],
            help = 'start the client')
    cliparser.add_argument("-a", "--addr",
            default = meta.default_listen,
            type = str,
            help = 'specify the address that the server listens on')
    cliparser.add_argument('action',
            metavar = 'ACTION',
            choices = [act.value for act in apicommon.Action],
            help = 'specify the action to perform')
    cliparser.add_argument('bot',
            metavar = 'BOT',
            type = str,
            help = 'specify the name of bot')
    cliparser.set_defaults(func = labots_client)

    subparsers.default = cliparser
    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
