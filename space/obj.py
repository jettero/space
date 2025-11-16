# coding: utf-8

import re
import logging
from .util import weakify

log = logging.getLogger(__name__)

positional_adjectives = None


# all mud objects get this ancestor
# most objects you can pick up or put in a room should also get Containable
# you're probably looking for space/stdobj.py
class baseobj:  # pylint: disable=invalid-name
    _tokens = _location = None

    def strongify(self):
        # XXX: I was having a Heisenbug around ReferenceError where literally
        # every other run of pytest t/test_verb_open_close.py was giving a
        # ReferenceError vs passing normally.
        #
        # NOTE: later, this turned out to be a set_this_body() bug in the
        # parser. if you call the below positional_adjectives and you fail to
        # set_this_body() first, it can sometimes point to a weakref that
        # nolonger exists during a pytest where you repeatedly build and
        # teardown a_map and objs (t.troom.gen_troom)
        #
        # I like having this around for now, so I haven't removed it, but the
        # AI keeps trying to use it inappropriately, so it may be just a matter
        # of time.
        #
        # Hey, talkin' to you codex: stop using this.
        return self

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, v):
        self._location = weakify(v)

    @property
    def owner(self):
        try:
            o = self._location
            from space.living import Living

            while o is not None and not isinstance(o, Living):
                o = o._location
            return o
        except AttributeError:
            pass

    @owner.setter
    def owner(self, v):
        from space.living import Living

        if isinstance(v, Living):
            self.location = v
            return
        raise ValueError(f"owners should be alive")

    @property
    def id(self):
        return f"{id(self):02x}"

    @property
    def cname(self):
        return self.__class__.__name__

    def has_shell(self):
        return False

    def __repr__(self):
        r = self.cname
        sf = str(self)
        if sf != r:
            r += f"<{sf}>"
        return f"{r}#{self.id}"

    def __str__(self):
        try:
            l = self.long
            if l:
                return l
        except AttributeError:
            pass
        return self.cname

    short = long = abbr = None

    def _tokenize(self):
        r = set()
        for i in ("short", "long", "cname"):
            if a := getattr(self, i, None):
                for s in a.split():
                    t = s.strip(", ").lower()
                    r.add(t)
        if a := getattr(self, "abbr", None):
            r.add(a)
        return r - set([None, ""])

    @property
    def tokens(self):
        if self._tokens is None:
            self.tokens = self._tokenize()
        return set(self._tokens)

    @tokens.setter
    def tokens(self, v):
        self._tokens = set(v)

    def parse_can(self, method, **kw):
        return MethodNameRouter(self, f"can_{method}")(**kw)

    def parse_do(self, method, **kw):
        MethodNameRouter(self, f"do_{method}")(**kw)

    def parse_match(self, *names, pos_adj=True):
        log.debug("%s.parse_match(%s)", self, names)

        if len(names) == 1 and isinstance(names[0], (list, tuple)):
            names = names[0]
        if not names:
            return False
        if m := re.match(r"^(.+)\.(.+)$", names[0]):
            name[0], id1 = m.groups()
            id2 = self.id
            if not (id2.startswith(id1) or id2.endswith(id1)):
                return False

        tok = self.tokens
        if pos_adj:
            global positional_adjectives
            if positional_adjectives is None:
                from space.map.dir_util import positional_adjectives
            tok.update(positional_adjectives(self))

        log.debug(f"WTF names+adjectives: {tok}")
        for n in names:
            matched = False
            for t in tok:
                if len(t) == 1 and t == n:
                    matched = True
                    break
                if t.startswith(n.lower()):
                    matched = True
                    break
            if not matched:
                return False

        return True
