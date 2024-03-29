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
        # this used to try to find tokens like 'l' and make them into 'look'
        # that's all internal to the parser now though
        return line

    def do(self, input_text):
        input_text = self.pre_parse_kludges(input_text)
        txts = re.split(r'\s*;\s*', input_text)
        p0 = self.owner.location.pos
        for txt in txts:
            if txt:
                try:
                    pstate = self.parser.parse(self.owner, txt)
                    if pstate:
                        pstate()
                    else:
                        self.receive_text(f'error: {pstate.error}')
                except IntentionalQuit:
                    raise
                except Exception as e: # pylint: disable=broad-except
                    log.exception('during input: %s', input_text)
                    self.receive_text(f'error: {e}')
        if self.owner.location.pos != p0:
            self.owner.do('look')
