import labots

class ExampleBot(labots.Bot):
    targets = ['#srain']

    def init(self):
        self.logger.info(self.config)

    def on_message(self, origin: str, target: str, msg: str):
        if self.action.is_channel(target):
            self.action.message(target, '%s: I received %s' % (origin, msg))
        else:
            self.action.message(origin, 'I received %s' %  msg)

labots.register(ExampleBot)

# from labots import bot

# class ExampleBot(bot.Bot):
#     '''
#     An example bot implement.
# 
#     You **MUST** inherit ``Bot`` class from ``labots.bot`` module,
#     and declare some key necessary attributes and functions.
#     '''
# 
#     '''
#     targets is a list of target.
# 
#     A target should be a string or dict, represents a nickname or channel.
# 
#     Bot only receives message from targets.
# 
#     If one of targets is channel, bot will auto join this channel when is loaed.
# 
#     If you want to join channel with password, use the full notation of targets.
#     '''
#     targets = ['labots', '#test', {'target': '#test', 'password': '<pa5sw0rd>'}]
# 
#     '''
#     Usage message of bot.
#     '''
#     usage = '''.echo <msg>: Echo a message;
#     When somebody join, part, quit, change his nick, sent a message;
#     When somebody sends a ACTION or NOTICE message, sent a message;
#     When somebody mentions my nick and saying 'poi', reply him with 'Poi~'
#     '''
# 
#     '''
#     Set `allow_reload` to False can prevent the bot from being restarted.
#     '''
#     allow_reload = True
# 
#     def init(self):
#         '''
#         This function will be invoked when bot is loaded, you can do some
#         initialize stuff here.
# 
#         Usually, user can rewrite ``self.targets`` here. For example:
# 
#         .. code-block::
# 
#                 self.targets = self.config['targets']
#         '''
#         pass
# 
#     def finalize(self):
#         ''' This function will be invoked when bot is unloaded '''
#         pass
# 
#     '''
#     Event handle functions.
#     User should implement them to achieve the function they want.
#     '''
#     def on_JOIN(self, chan, nick):
#         self.say(chan, '%s -->| %s' % (nick, chan))
# 
#     def on_PART(self, chan, nick):
#         self.say(chan, '%s |<-- %s' % (nick, chan))
# 
#     def on_QUIT(self, chan, nick, reason):
#         self.say(chan, '%s |<-- : %s' % (nick, reason))
# 
#     def on_NICK(self, chan, old_nick, new_nick):
#         self.say(chan, '%s -> %s' % (old_nick, new_nick))
# 
#     def on_PRIVMSG(self, target, nick, msg):
#         ''' Echo bot, response `'echo xxx` message '''
#         # NOTE: If you return message in any case,
#         # endless loop will be caused
#         cmd = '.echo '
#         if msg.startswith(cmd):
#             self.say(target, '%s: %s' % (nick, msg[len(cmd):]))
# 
#     ''' [v1.1] '''
#     def on_NOTICE(self, target, nick, msg):
#         self.say(target, 'Notice: %s' % msg)
# 
#     ''' [v1.1] '''
#     def on_ACTION(self, target, nick, msg):
#         self.say(target, 'Action: %s' % msg)
# 
#     ''' [v1.1] '''
#     def on_LABOTS_MSG(self, target, bot, nick, msg):
#         if bot:
#             self.say(target, '%s: Youe message is sent by %s' % (nick, bot))
# 
#     ''' [v1.1] '''
#     def on_LABOTS_MENTION_MSG(self, target, bot, nick, msg):
#         if msg == 'poi':
#             self.say(target, '%s: Poi~' % nick)
# 
# 
# '''
# **IMPORTANCE**
# 
# You must define a instance of your Bot class and name it as `bot`, then it can
# be found by LABots, As described above, you should pass `__file__` to its
# constructor.
# '''
# 
# bot = ExampleBot(__file__)
