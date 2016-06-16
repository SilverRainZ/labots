#!/usr/bin/env python3

import sys
from config import bot_paths 

def main():
    sys.path.append('./bots')
    print(bot_paths)
    try:
        bots = map(lambda x:__import__(x, fromlist = ['main']), bot_paths)
    except ImportError as err:
        print(err)

    for bot in bots:
        bot.main()

if __name__ == '__main__':
    main()
