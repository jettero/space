# coding: utf-8

import re
import readline
import logging

from .base import BaseShell, IntentionalQuit

log = logging.getLogger(__name__)

class KeywordFilter(logging.Filter):
    def __init__(self, *name_filters):
        self.name_filters = [ re.compile(x) for x in name_filters ]

    def filter(self, record):
        for nf in self.name_filters:
            if nf.search( record.name ):
                return False
        return True

class Shell(BaseShell):
    _logging_opts = None
    at_prompt = False
    color = True

    def startup(self, init=None):
        readline.parse_and_bind('tab: complete')
        readline.set_completer(self.complete)
        self.reconfigure_logging(filename='shell.log',
            format='%(asctime)s %(name)17s %(levelname)5s %(message)s',
            level=logging.DEBUG)

        if isinstance(init, (tuple,list)):
            for cmd in init:
                self.do_step(cmd)

    def receive_message(self, msg):
        if self.at_prompt:
            print('')
            self.at_prompt = False
        print( msg.render_text(color=self.color) )

    def complete(self, text, state):
        bidx = readline.get_begidx()
        lbuf = readline.get_line_buffer()
        if bidx == 0:
            # state starts at 0, and increases until we return None or there's
            # an exception
            words = self.parser.words
            results = [x for x in words if x.startswith(text)]
            return results[state] + ' '
        if bidx == 1 and lbuf[0] == '/':
            words = ['debug', 'logfile', 'quit', 'help']
            results = [x for x in words if x.startswith(text)]
            return results[state] + ' '

        # line = readline.get_line_buffer()
        # XXX:
        # consider what the next word should complete from ... attack living,
        # look obj ... hrm how do we ask the parser for a partial parse or how
        # do we ask the verb what its next word should be and how do we decide
        # what part of the line we're looking at? get_begidx() and get_endidx()?
        # hrm hrm hrm

    def reconfigure_logging(self, **kw):
        def mydl(*dl):
            norepeat = set()
            for d in dl:
                if isinstance(d, dict):
                    for k,v in d.items():
                        if k not in norepeat:
                            if v is not None:
                                yield k,v
                        norepeat.add(k)
        self._logging_opts = { k:v for k,v in mydl(kw, self._logging_opts) }
        logging.root.handlers = []
        logging.basicConfig(**self._logging_opts)
        kwf = KeywordFilter('space.args') # XXX: should be configurable
        for handler in logging.root.handlers:
            handler.addFilter(kwf)

    def internal_command(self, line):
        if line.startswith('/'):
            cmd, *args = line[1:].split()
            if cmd == 'debug':
                cl = self._logging_opts.get('level')
                nl = logging.INFO if cl == logging.DEBUG else logging.DEBUG
                self.reconfigure_logging(level=nl)
            elif cmd == 'logfile':
                if not args or args[0] in ('off', '0', 'false'):
                    self.reconfigure_logging(filename=None)
                else:
                    self.reconfigure_logging(filename=args[0])
            elif cmd in ('exit','quit',):
                self.stop()
            else:
                self.owner.tell('/debug    toggle log debug (default: on)')
                self.owner.tell('/logfile  set the logfile location (default: shell.log)')
                self.owner.tell('/quit     exit the shell')
            return True

    def do_step(self, cmd):
        if cmd and not self.internal_command(cmd):
            try:
                self.do(cmd)
            except IntentionalQuit:
                self.stop()

    def step(self):
        self.at_prompt = True
        try:
            cmd = input('ssr> ').strip()
            self.at_prompt = False
            self.do_step(cmd)
        except (EOFError, KeyboardInterrupt):
            self.stop()
        self.at_prompt = False
