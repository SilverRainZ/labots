# -*- encoding: UTF-8 -*-
# RFC 2812 Incomplete Implement

import re
import socket
import logging
import functools
from ircmagic import *
from enum import Enum
from tornado.ioloop import IOLoop
from tornado.iostream import IOStream

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

hdr = logging.StreamHandler()
hdr.setLevel(logging.INFO)

fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
fmter = logging.Formatter(fmt, None)

hdr.setFormatter(fmt)
logger.addHandler(hdr)


class IRCMsgType(Enum):
    PING = 0
    NOTICE = 1
    ERROR = 2
    MSG = 3
    UNKNOW = 4


class IRCMsg(object):
    # Prefix
    nick = ''
    user = ''
    host = ''

    # Command
    cmd = ''

    # Middle
    args = []

    # Trailing
    msg = ''


class IRC(object):
    # Private
    _sock = None
    _stream = None
    _charset = None
    _ioloop = None
    _after_login = None
    _dispath = None

    # Public
    nick = None
    chans = []
    dispatch = None

    def __init__(self, host, port, nick,
            after_login = None, dispatch = None,
            charset = 'utf-8', ioloop = False):

        logger.info('Connecting to %s:%s', host, port)

        self.nick = nick
        self._after_login = after_login
        self._dispath = dispatch
        self._charset = charset
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self._sock.settimeout(20)
        self._ioloop = ioloop or IOLoop.instance()
        self._stream = IOStream(self._sock, io_loop = self._ioloop)
        self._stream.connect((host, port), self.login)


    def _sock_send(self, data):
        return self._stream.write(bytes(data, self._charset))


    def _sock_recv(self):
        def _recv(data):
            msg = data.decode(self._charset)
            msg = msg[:-2]
            self.recv(msg)

        self._stream.read_until(b'\r\n', _recv)


    def chnick(self, nick):
        self._sock_send('NICK %s\r\n' % nick)


    def login(self):
        logger.info('Try to login as "%s"', self.nick)

        self.chnick(self.nick)
        self._sock_send('USER %s %s %s %s\r\n' % (self.nick, 'labots',
            'localhost', 'lastavengers#outlook.com'))

        self._sock_recv()


    def join(self, chan):
        self._sock_send('JOIN %s\r\n' % chan)
        logger.info('Try to join %s', chan)


    def part(self, chan):
        self._sock_send('PART %s\r\n' % chan)
        logger.info('Try to part %s', chan)


    def pong(self):
        self._sock_send('PONG :labots!\n')
        logger.debug('Pong!')


    def send(self, target, msg):
        self._sock_send('PRIVMSG %s :%s\r\n' % (target, msg))


    def action(self, target, msg):
        self._sock_send('PRIVMSG %s :\1ACTION %s\1\r\n')


    def topic(self, chan, topic):
        self._sock_send('TOPIC %s :%s\r\n' % (chan, topic))


    # IRC message parser, return tuple (IRCMsgType, IRCMsg)
    def _parse(self, msg):
        if msg.startswith('PING :'):
            logger.debug('PING')
            return (IRCMsgType.PING, None)
        elif msg.startswith('NOTICE AUTH :'):
            logger.debug('NOTIC AUTH: "%s"')
            return (IRCMsgType.NOTICE, None)
        elif msg.startswith('ERROR :'):
            logger.debug('ERROR: "%s"', msg)
            return (IRCMsgType.ERROR, None)

        try:
            # <message> ::= [':' <prefix> <SPACE> ] <command> <params> <crlf>
            # <crlf> has been striped by recv()
            tmp = msg.split(' ', maxsplit = 2)

            if len(tmp) != 3:
                raise Exception('Failed when parsing <prefix> <command> <params>')

            prefix, command, params = tmp
            logger.debug('prefix: "%s", command: "%s", params: "%s"',
                    prefix, command, params)

            # <params> ::= <SPACE> [ ':' <trailing> | <middle> <params> ]
            middle, _, trailing = params.partition(' :')
            logger.debug('middle: "%s", trailing: "%s"', middle, trailing)
            if middle.startswith(':'):
                trailing = middle[1:]
                middle = ''

            if not middle and not trailing:
                raise Exception('No <middle> and <trailing>')

            # <middle> ::= <Any *non-empty* sequence of octets not including SPACE
            #              or NUL or CR or LF, the first of which may not be ':'>
            args = middle.split(' ')
            logger.debug('args: "%s"', args)

            # <prefix> ::= <servername> | <nick> [ '!' <user> ] [ '@' <host> ]
            tmp = prefix
            nick, _, tmp = tmp.partition('!')
            user, _, host = tmp.partition('@')
            logger.debug('nick: "%s", user: "%s", host: "%s"', nick, user, host)

        except Exception as err:
            logger.error('Parsing error: %s', err)
            logger.error('    Message: %s', repr(msg))
            return (IRCMsgType.UNKNOW, None)
        else:
            ircmsg = IRCMsg()
            ircmsg.nick = nick[1:]  # strip ':'
            ircmsg.user = user
            ircmsg.host = host
            ircmsg.cmd = command
            ircmsg.args = args
            ircmsg.msg = trailing
            return (IRCMsgType.MSG, ircmsg)


    # Response server message, keep bot alive
    def _resp(self, type_, ircmsg):
        if type_ == IRCMsgType.PING:
            self.pong()
        elif type_ == IRCMsgType.ERROR:
            pass
        elif type_ == IRCMsgType.MSG:
            if ircmsg.cmd == RPL_WELCOME:
                self.nick = ircmsg.args[0]
                if self._after_login:
                    self._after_login(self)
            elif ircmsg.cmd == ERR_NICKNAMEINUSE:
                new_nick = ircmsg.args[1] + '_'
                logger.info('Nick already in use, use "%s"', new_nick)
                self.chnick(new_nick)
            elif ircmsg.cmd == 'JOIN' and ircmsg.nick == self.nick:
                self.chans.append(ircmsg.args[0])
            elif ircmsg.cmd == 'PART' and ircmsg.nick == self.nick:
                self.chans.remove(ircmsg.args[0])


    # Receive irc message from server, return a list of IRCMsg).
    # If None returned, connection should be closed
    def recv(self, msg):
        if msg:
            type_, ircmsg = self._parse(msg)
            self._resp(type_, ircmsg)
            if self._dispath:
                self._dispath(type_, ircmsg)

        self._sock_recv()


    def quit(self, reason = '食饭'):
        self._sock_send('QUIT :%s\r\n' % reason)
        logger.debug('Quit: %s' % reason)


    def stop(self):
        self.quit()
        self._sock.close()
