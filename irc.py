# -*- encoding: UTF-8 -*-

import re
import socket
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

hdr = logging.StreamHandler()
hdr.setLevel(logging.DEBUG)

fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fmter = logging.Formatter(fmt, None)

hdr.setFormatter(fmt)
logger.addHandler(hdr)

class IRC(object):
    sock = None
    chans = []

    def __init__(self, host, port, nick):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.sock.settimeout(20)
        self.sock.connect((host, port))

        self.sock.send(bytes('NICK ' + nick + '\n', 'utf-8'))
        self.sock.send(bytes('USER ' + nick + ' ' + nick + ' ' + nick+ ' :' + nick + '\n', 'utf-8'))

        logger.info('Connecting to %s:%s', host, port)


    def join(self, chan):
        self.sock.send(bytes('JOIN ' + chan + '\n', 'utf-8'))
        self.chans.append(chan)

        logger.info('Try to join %s', chan)


    def ping(self):
        self.sock.send(bytes('PONG :pingis\n', 'utf-8'))


    def send(self, chan, msg):
        try:
            self.sock.send(bytes('PRIVMSG ' + chan + ' :' + msg + '\n','utf-8'))
        except socket.error as err:
            logger.error('Scoket error %s', err)
        else:
            logger.info('Send to %s:%s', chan, msg)


    def recv(self):
        try:
            msg_pattern = re.compile(r':(.*?)!~.*?@.*? PRIVMSG (.*?) :(?u)(.*)')

            data = self.sock.recv(2048)
            data = data.decode('utf-8').strip('\n\r')
            if (data.startswith('PING')):  # keep alive
                self.ping()
            msg_info = msg_pattern.match(data)
            if msg_info:
                man, chan, msg = msg_info.groups()
                logger.info('Receive %s@%s: %s', man, chan, msg)
                return (man, chan, msg)

        except socket.error as err:
            logger.error('Scoket error %s', err)
        except UnicodeDecodeError as err:
            logger.error('Decode error %s', err)
        except re.error as err:
            logger.error('Match error %s', err)

        return (None, None, None)


    def stop(self):
        logger.info('Close socket')
        self.sock.close()
