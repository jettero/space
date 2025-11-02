# coding: utf-8

import re
import logging
import weakref

log = logging.getLogger(__name__)


# all mud objects get this ancestor
# most objects you can pick up or put in a room should also get Containable
# you're probably looking for space/stdobj.py
class baseobj:  # pylint: disable=invalid-name
    _location = None

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, v):
        if v is not None:
            v = weakref.proxy(v)
        self._location = v

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

    def parse_can(self, method, **kw):
        return MethodNameRouter(self, f"can_{method}")(**kw)

    def parse_do(self, method, **kw):
        MethodNameRouter(self, f"do_{method}")(**kw)

    def parse_match(self, *names):
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

        try:
            tok = self.tokens
        except AttributeError:
            tok = self._tokenize()

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
