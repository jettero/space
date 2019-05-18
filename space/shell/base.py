# coding: utf-8

import re
import logging
import weakref
# note: shell.owner is weakref
# owner.shell is not weakref

from ..verb.quit import IntentionalQuit
from ..parser import Parser
from .message import TextMessage, MapMessage, Message

log = logging.getLogger(__name__)

class BaseShell:
    _owner = None
    _stop = False

    def __init__(self, owner=None, init=None):
        self.owner = owner
        self.parser = Parser()
        self.startup(init=init)

    def startup(self, init=None):
        pass

    @property
    def owner(self):
        return self._owner

    @owner.setter
    def owner(self, v):
        if v is None:
            self._owner = None
        if not hasattr(v, 'tell') or not callable(v.tell):
            raise TypeError(f'{v} cannot be a shell owner')
        self._owner = weakref.proxy(v)
        v.shell = self

    def receive(self, something):
        if isinstance(something, Message):
            return self.receive_message(something)
        if isinstance(something, str):
            return self.receive_text(something)
        from ..map import Map
        if isinstance(something, Map):
            return self.receive_map(something)
        raise TypeError(f'unable to receive({something})')

    def receive_message(self, msg):
        raise NotImplementedError()

    def receive_text(self, fmt, *a, **kw):
        self.receive_message( TextMessage(fmt, *a, **kw) )

    def receive_map(self, a_map):
        self.receive_message( MapMessage(a_map) )

    def step(self):
        raise NotImplementedError()

    def loop(self):
        try:
            while not self._stop:
                self.step()
        except IntentionalQuit:
            pass

    def stop(self, val=True, msg='see ya.'):
        self._stop = val
        self.receive_text(msg)

    def pre_parse_kludges(self, line):
        # XXX: this is supposed to look for a single good match and pretend to
        # use the verb, but it broke with the most recent parser changes
        return line

        # XXX: this fix should probably be configurable from shell to shell
        # maybe by override? depending on the shell?
        v0,*rest = line.split(' ', 1)
        c = set()
        for w in self.parser.verb_words:
            if v0 == w:
                break
            if w.startswith(v0):
                c.add(w)
        if len(c) == 1:
            c = list(c)[0]
            if rest:
                return f'{c} {rest[0]}'
            return c
        return line

    def do(self, input_text):
        input_text = self.pre_parse_kludges(input_text)
        txts = re.split(r'\s*;\s*', input_text)
        for txt in txts:
            if txt:
                try:
                    self.parser.parse(self.owner, txt)
                except IntentionalQuit:
                    raise
                except Exception as e: # pylint: disable=broad-except
                    log.exception('during input: %s', input_text)
                    self.receive_text(f'error: {e}')
