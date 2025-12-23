# coding: utf-8

import re
import logging
from ..util import weakify

# note: shell.owner is weakref
# owner.shell is not weakref

from ..verb.quit import IntentionalQuit
from ..parser import parse
from ..msg import TextMessage, MapMessage, Message

from ..map.dir_util import is_direction_string
from ..map import Map

log = logging.getLogger(__name__)


class BaseShell:
    _owner = None
    _stop = False

    def __init__(self, owner=None, init=None):
        if owner is not None:
            owner.shell = self
        self.preflight(init=init)

    def preflight(self, init=None):
        pass

    @property
    def owner(self):
        return self._owner

    @owner.setter
    def owner(self, v):
        from ..msg import HasShell

        if v is None:
            self._owner = None
        elif not isinstance(v, HasShell):
            raise TypeError(f"{v!r} cannot be a shell owner")
        if self._owner != v:
            v.shell = self
            self._owner = weakify(v)

    @property
    def terminal_size(self):
        return (80, 25)

    def receive(self, something):
        if isinstance(something, Message):
            return self.receive_message(something)
        if isinstance(something, str):
            return self.receive_text(something)
        if isinstance(something, Map):
            return self.receive_map(something)
        raise TypeError(f"unable to receive({something})")

    def receive_message(self, msg):
        raise NotImplementedError()

    def receive_text(self, fmt, *a, **kw):
        self.receive_message(TextMessage(fmt, *a, **kw))

    def receive_map(self, a_map):
        self.receive_message(MapMessage(a_map))

    def step(self):
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    def stop(self, val=True, msg="see ya."):
        if not self._stop:
            self._stop = val
            self.receive_text(msg)

    def pre_parse_kludges(self, line):
        # this used to try to find tokens like 'l' and make them into 'look'
        # that's all internal to the parser now though.  maybe we could later
        # use it for aliases or something
        return line

    def parse(self, input_text, parse_only=True, reraise=True):
        return self.do(input_text, parse_only=parse_only, reraise=reraise)

    def do(self, input_text, parse_only=False, reraise=False):
        ok = False
        input_text = self.pre_parse_kludges(input_text)
        txts = [f"move {x}" if is_direction_string(x) else x for x in re.split(r"\s*;\s*", input_text)]
        log.debug("SHELL SUBST >>> %s >>> %s", input_text, repr(txts))
        p0 = self.owner.location.pos
        for txt in txts:
            if txt:
                try:
                    xp = parse(self.owner, txt, parse_only=True)
                    if parse_only:
                        return xp
                    if xp:
                        xp()
                        ok = True
                    else:
                        self.receive_text(xp.error)
                except IntentionalQuit:
                    raise
                except Exception as e:  # pylint: disable=broad-except
                    log.exception("during input: %s", input_text)
                    self.receive_text(str(e))
                    if reraise:
                        raise
        if self.owner.location.pos != p0:
            self.owner.do("look")
        return ok

    def handle_application_exception(self, loop, context):
        pass
