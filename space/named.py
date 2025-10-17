# coding: utf-8

import re
import logging

from .serial import Serial
from .obj import baseobj

FORMAT_RE = re.compile(r"^(.*?)(?:\b|[~])?(a|s|l|d|abbr|short|long|desc)?$")
log = logging.getLogger(__name__)


class Named(Serial, baseobj):
    # "unique" means we refer to the object as "the thingy" rather than "a thingy."
    # proper_name means we refer to the thing as thing.short, never thing.a_short or thing.the_short.
    a = "~"
    s = "object"
    l = "named object"
    d = "an object with names and descriptions"

    a_fmt = "{a:{fmt}}"
    s_fmt = "{s:{fmt}}"
    l_fmt = "{l:{fmt}}"
    d_fmt = "{l:{fmt}} :- {d}"
    r_fmt = "{c}({l})"

    unique = False
    plural = False

    class Meta:
        save = "asld"

    def __init__(self, short=None, abbr=None, long=None, proper_name=None, unique=None, plural=None, **kw):
        super().__init__(**kw)  # if Serial and baseobj had __init__, they'd both get called via MRO/super()
        if abbr is not None:
            self.a = abbr
        self.proper_name = False
        if long is not None:
            self.l = long
        if short is not None:
            self.s = short
        if unique is not None:
            self.unique = bool(unique)
        if plural is not None:
            self.plural = bool(plural)
        if proper_name:
            name = str(proper_name)
            if "~" in name:
                self.s = self.l = name.replace("~", " ")
            else:
                self.l = name
                self.s = name.split()[0]
            self.unique = True
            self.proper_name = True
        self.tokens = self._tokenize()

    def __format__(self, spec):
        if spec in ("abbr", "a"):
            return self.abbr
        if spec in ("short", "s"):
            return self.short
        if spec in ("long", "l"):
            return self.long
        if spec in ("desc", "d"):
            return self.desc
        m = FORMAT_RE.match(spec)
        if m:
            fmt, m_select = m.groups()
            if not m_select:
                m_select = "s"
            return self._m_fmt(m_select, fmt=fmt)
        return super().__format__(spec)

    # proper_name is a boolean; set during init when a proper name string is provided.

    @property
    def a_short(self):
        s = self.short
        if not s:
            return s
        if self.proper_name or self.unique or self.plural:
            return self.the_short
        first = s[:1].lower()
        return f"an {s}" if first in "aeiou" else f"a {s}"

    @property
    def the_short(self):
        s = self.short
        if not s:
            return s
        if self.proper_name:
            return s
        return f"the {s}"

    def _m_fmt(self, var_name, fmt="", **kw):
        m = var_name.lower().strip()[0]
        return getattr(self, f"{m}_fmt").format(**self.as_dict(fmt=fmt, **kw))

    @property
    def abbr(self):
        return self._m_fmt("a")

    @property
    def short(self):
        return self._m_fmt("s")

    @property
    def long(self):
        return self._m_fmt("l")

    @property
    def desc(self):
        return self._m_fmt("d")

    @abbr.setter
    def abbr(self, v):
        self.a = v
        self.tokens = self._tokenize()

    @short.setter
    def short(self, v):
        self.s = v
        self.tokens = self._tokenize()

    @long.setter
    def long(self, v):
        self.l = v
        self.tokens = self._tokenize()


class Tags(Serial):
    def __init__(self, *a, can=None, **kw):
        super().__init__(**kw)
        self._a = {str(i) for i in a}
        self._c = None if can is None else Tags(*can)

    def clone(self):  # pylint: disable=protected-access
        n = self.__class__.__new__(self.__class__)
        n._a = set(self._a)
        n._c = None if self._c is None else set(self._c)
        return n

    def clear(self):
        self._a.clear()

    def add(self, tag):
        tag = str(tag)
        if self._c is not None:
            if tag not in self._c:
                raise ValueError(f"{tag} not allowed (allowed: {str(self)})")
        self._a.add(tag)

    def remove(self, tag):
        tag = str(tag)
        try:
            self._a.remove(tag)
        except KeyError:
            pass

    def __add__(self, tag):
        n = self.clone()
        n.add(tag)
        return n

    def __sub__(self, tag):
        n = self.clone()
        n.remove(tag)
        return n

    def __iter__(self):
        yield from self._a

    def __str__(self):
        if not self._a:
            return "{ }"
        return repr(self._a)

    def __repr__(self):
        return f"{self.__class__.__name__}{str(self)}"

    def __eq__(self, other):
        if isinstance(other, Tags):
            return self._a == other._a  # pylint: disable=protected-access
        if not isinstance(other, set):
            other = set(other)
        return self._a == other
