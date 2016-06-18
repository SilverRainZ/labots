# -*- encoding: UTF-8 -*-

import re
import socket

class IRC(object):
    sock = None
    chans = []

    def __init__(self, host, port, nick):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.sock.settimeout(20)
        self.sock.connect((host, port))

        self.sock.send(bytes('NICK ' + nick + '\n', 'utf-8'))
        self.sock.send(bytes('USER ' + nick + ' ' + nick + ' ' + nick+ ' :' + nick + '\n', 'utf-8'))

        print('[IRC]', 'connect to {0}:{1}'.format(host, port))


    def join(self, chan):
        self.sock.send(bytes('JOIN ' + chan + '\n', 'utf-8'))
        self.chans.append(chan)
        print('[IRC]', 'join', chan)


    def ping(self):
        print('[IRC]', 'ping!')
        self.sock.send(bytes('PONG :pingis\n', 'utf-8'))


    def send(self, chan, msg):
        try:
            self.sock.send(bytes('PRIVMSG ' + chan + ' :' + msg + '\n','utf-8'))
        except socket.error as err:
            print('[IRC]', 'err: ', 'SOCKET ERROR', err)
        else:
            print('[IRC]', 'send to {0}: {1}'.format(chan, msg))


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
                print('[IRC]', 'recv msg: {0}@{1}: {2}'.format(man, chan, msg))
                return (man, chan, msg)

        except socket.error as err:
            print('[IRC]', 'err: ', 'SOCKET ERROR', err)
        except UnicodeDecodeError as err:
            print('[IRC]', 'err: ', 'DECODE ERROR', err)
        except re.error as err:
            print('[IRC]', 'err: ', 'MATCH ERROR', err)

        return (None, None, None)


    def stop(self):
        print('[IRC]', 'stop')
        self.sock.close()
