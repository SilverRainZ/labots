# -*- encoding: UTF-8 -*-
# RFC 2812 Incompleted Implement

import re
import time
import socket
import logging
import functools
from ircmagic import *
from enum import Enum
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.iostream import IOStream

# Initialize logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def empty_callback(*args, **kw):
    logger.debug("Unimplement callback %s %s" % (args, kw))


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

    host = None
    port = None
    nick = None
    chans = []
    chans_ref = {}
    names = {}

    # External callbacks
    # def raw_callback(IRCMsg)
    raw_callback = None
    # def login_callback()
    login_callback = None
    # def privmsg_callback(nick, chan, msg)
    privmsg_callback = None
    # def join_callback(nick, chan)
    join_callback = None
    # def part_callback(nick, chan, reason)
    part_callback = None
    # def quit_callback(nick, chan, reason)
    quit_callback = None
    # def nick_callback(old_nick, new_nick)
    nick_callback = None

    def __init__(self, host, port, nick, charset = 'utf-8', ioloop = False):

        logger.info('Connecting to %s:%s', host, port)

        self.host = host
        self.port = port
        self.nick = nick

        self._charset = charset
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
            if middle.startswith(':'):
                trailing = middle[1:]
                middle = ''
            logger.debug('middle: "%s", trailing: "%s"', middle, trailing)

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
            self._pong()
        elif type_ == IRCMsgType.ERROR:
            pass
        elif type_ == IRCMsgType.MSG:
            if ircmsg.cmd == RPL_WELCOME:
                self._on_login(ircmsg.args[0])
            elif ircmsg.cmd == ERR_NICKNAMEINUSE:
                new_nick = ircmsg.args[1] + '_'
                logger.info('Nick already in use, use "%s"', new_nick)
                self._chnick(new_nick)
            elif ircmsg.cmd == 'JOIN':
                chan = ircmsg.args[0] or ircmsg.msg
                if ircmsg.nick == self.nick:
                    self.chans.append(chan)
                    self.names[chan] = set()
                    logger.info('%s has joined %s', self.nick, chan)
                self.names[chan].add(self.nick)
            elif ircmsg.cmd == 'PART':
                chan = ircmsg.args[0]
                self.names[chan].remove(self.nick)
                if ircmsg.nick == self.nick:
                    self.chans.remove(chan)
                    self.names[chan].clear()
                    logger.info('%s has left %s', self.nick, ircmsg.args[0])
            elif ircmsg.cmd == 'NICK':
                new_nick, old_nick = ircmsg.msg, ircmsg.nick
                for chan in self.chans:
                    if old_nick in self.names[chan]:
                        self.names[chan].remove(old_nick)
                        self.names[chan].add(new_nick)
                if old_nick == self.nick:
                    self.nick = old_nick
                    logger.info('%s is now known as %s', old_nick, new_nick)
            elif ircmsg.cmd == 'QUIT':
                nick = ircmsg.nick
                for chan in self.chans:
                    if nick in self.names[chan]:
                        self.names[chan].remove(nick)
            elif ircmsg.cmd == RPL_NAMREPLY:
                chan = ircmsg.args[2]
                names_list = [x[1:] if x[0] in ['@', '+'] else x
                        for x in ircmsg.msg.split(' ')]
                self.names[chan].update(names_list)
                logger.debug('NAMES: %s' % names_list)


    def _dispatch(self, type_, ircmsg):
        if type_ != IRCMsgType.MSG:
             return

        self.raw_callback(ircmsg)

        # Error message
        if ircmsg.cmd[0] in ['4', '5']:
            logger.error('Error message: %s', ircmsg.msg)
        elif ircmsg.cmd == 'JOIN':
            nick, chan = ircmsg.nick, ircmsg.args[0] or ircmsg.msg
            self.join_callback(nick, chan)
        elif ircmsg.cmd == 'PART':
            nick, chan, reason = ircmsg.nick, ircmsg.args[0], ircmsg.msg
            self.part_callback(nick, chan, reason)
        elif ircmsg.cmd == 'QUIT':
            nick, reason = ircmsg.nick, ircmsg.msg
            for chan in self.chans:
                if nick in self.names[chan]:
                    self.quit_callback(nick, chan, reason)
        elif ircmsg.cmd == 'NICK':
            new_nick, old_nick = ircmsg.msg, ircmsg.nick
            for chan in self.chans:
                if old_nick in self.names[chan]:
                    self.nick_callback(old_nick, new_nick, chan)
        elif ircmsg.cmd == 'PRIVMSG':
            nick, target, msg = ircmsg.nick, ircmsg.args[0], ircmsg.msg
            self.privmsg_callback(nick, target, msg)


    def _keep_alive(self):
        # Ping time out
        if time.time() - self._last_pong > 360:
            logger.error('Ping time out')

            self._reconnect()
            self._last_pong = time.time()


    def _recv(self, msg):
        if msg:
            type_, ircmsg = self._parse(msg)
            self._dispatch(type_, ircmsg)
            self._resp(type_, ircmsg)

        self._sock_recv()


    def _chnick(self, nick):
        self._sock_send('NICK %s\r\n' % nick)


    def _on_login(self, nick):
        logger.info('You are logined as %s', nick)

        self.nick = nick
        chans = self.chans

        self.login_callback()

        self.chans = []
        [self.join(chan, force = True) for chan in chans]



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


    def set_callback(self,
            on_raw = empty_callback,
            on_login = empty_callback,
            on_privmsg = empty_callback,
            on_join = empty_callback,
            on_part = empty_callback,
            on_quit = empty_callback,
            on_nick = empty_callback):
        self.raw_callback = on_raw
        self.login_callback = on_login
        self.privmsg_callback = on_privmsg
        self.join_callback = on_join
        self.part_callback = on_part
        self.quit_callback = on_quit
        self.nick_callback = on_nick


    def join(self, chan, force = False):
        if chan[0] not in ['#', '&']:
            return

        if not force:
            if chan in self.chans_ref:
                self.chans_ref[chan] += 1
                return
            self.chans_ref[chan] = 1

        logger.debug('Try to join %s', chan)
        self._sock_send('JOIN %s\r\n' % chan)


    def part(self, chan):
        if chan[0] not in ['#', '&']:
            return
        if chan not in self.chans_ref:
            return

        if self.chans_ref[chan] != 1:
            self.chans_ref[chan] -= 1
            return

        self.chans_ref.pop(chan, None)

        logger.debug('Try to part %s', chan)
        self._sock_send('PART %s\r\n' % chan)


    def send(self, target, msg):
        self._sock_send('PRIVMSG %s :%s\r\n' % (target, msg))

        # You will recv the message you sent
        self.privmsg_callback(self.nick, target, msg)


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
    irc.set_callback()
    try:
        IOLoop.instance().start()
    except KeyboardInterrupt:
        irc.stop()
        IOLoop.instance().stop()
