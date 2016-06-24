# -*- encoding: UTF-8 -*-
# RFC 2812 Incomplete Implement

import re
import time
import socket
import logging
import functools
from ircmagic import *
from enum import Enum
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.iostream import IOStream
from threading import Timer

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
    _stream = None
    _charset = None
    _ioloop = None
    _timer = None
    _last_pong = None

    # Public
    host = None
    port = None
    nick = None
    chans = []
    after_login = None
    on_recv = None

    def __init__(self, host, port, nick,
            after_login = None, on_recv = None,
            charset = 'utf-8', ioloop = False):

        logger.info('Connecting to %s:%s', host, port)

        self.host = host
        self.port = port
        self.nick = nick
        self.after_login = after_login
        self.on_recv = on_recv

        self._charset = charset
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # sock.settimeout(20)
        self._ioloop = ioloop or IOLoop.instance()
        self._stream = IOStream(sock, io_loop = self._ioloop)
        self._stream.connect((host, port), self._login)

        self._last_pong = time.time()
        self._timer = PeriodicCallback(self._keep_alive,
                60 * 1000, io_loop=self._ioloop)
        self._timer.start()

    def _sock_send(self, data):
        return self._stream.write(bytes(data, self._charset))


    def _sock_recv(self):
        def _recv(data):
            msg = data.decode(self._charset)
            msg = msg[:-2]  # strip '\r\n'
            self._recv(msg)

        self._stream.read_until(b'\r\n', _recv)


    def _reconnect(self):
        logger.info('Reconnecting...')

        self._stream.close()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._stream = IOStream(sock, io_loop = self._ioloop)
        self._stream.connect((self.host, self.port), self._login)


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


    # Response server message
    def _resp(self, type_, ircmsg):
        if type_ == IRCMsgType.PING:
            self.pong()
        elif type_ == IRCMsgType.ERROR:
            pass
        elif type_ == IRCMsgType.MSG:
            if ircmsg.cmd == RPL_WELCOME:
                self._on_login(ircmsg.args[0])
            elif ircmsg.cmd == ERR_NICKNAMEINUSE:
                new_nick = ircmsg.args[1] + '_'
                logger.info('Nick already in use, use "%s"', new_nick)
                self._chnick(new_nick)
            elif ircmsg.cmd == 'JOIN' and ircmsg.nick == self.nick:
                logger.info('%s has joined %s', self.nick, ircmsg.args[0])
                self.chans.append(ircmsg.args[0])
            elif ircmsg.cmd == 'PART' and ircmsg.nick == self.nick:
                logger.info('%s has left %s', self.nick, ircmsg.args[0])
                self.chans.remove(ircmsg.args[0])


    def _keep_alive(self):
        # Ping time out
        if time.time() - self._last_pong > 360:
            logger.error('Ping time out')

            self._reconnect()
            self._last_pong = time.time()


    def _recv(self, msg):
        if msg:
            type_, ircmsg = self._parse(msg)
            self._resp(type_, ircmsg)
            if self.on_recv:
                self.on_recv(type_, ircmsg)

        self._sock_recv()


    def _chnick(self, nick):
        self._sock_send('NICK %s\r\n' % nick)


    def _on_login(self, nick):
        logger.info('You are logined as %s', nick)

        self.nick = nick

        if self.after_login:
            self.after_login()

        chans = self.chans
        self.chans = []
        [self.join(chan) for chan in chans]


    def _login(self):
        logger.info('Try to login as "%s"', self.nick)

        self._chnick(self.nick)
        self._sock_send('USER %s %s %s %s\r\n' % (self.nick, 'labots',
            'localhost', 'lastavengers#outlook.com'))

        self._sock_recv()


    def _pong(self):
        logger.debug('Pong!')

        self._last_pong = time.time()
        self._sock_send('PONG :labots!\n')


    def join(self, chan):
        logger.debug('Try to join %s', chan)
        self._sock_send('JOIN %s\r\n' % chan)


    def part(self, chan):
        logger.debug('Try to part %s', chan)
        self._sock_send('PART %s\r\n' % chan)


    def send(self, target, msg):
        self._sock_send('PRIVMSG %s :%s\r\n' % (target, msg))


    def action(self, target, msg):
        self._sock_send('PRIVMSG %s :\1ACTION %s\1\r\n')


    def topic(self, chan, topic):
        self._sock_send('TOPIC %s :%s\r\n' % (chan, topic))


    def quit(self, reason = '食饭'):
        self._sock_send('QUIT :%s\r\n' % reason)
        logger.debug('Quit: %s' % reason)


    def stop(self):
        logger.info('Stop')
        self.quit()
        self._stream.close()

if __name__ == '__main__':
    logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
    irc = IRC('irc.freenode.net', 6667, 'labots')
    try:
        IOLoop.instance().start()
    except KeyboardInterrupt:
        irc.stop()
        IOLoop.instance().stop()
