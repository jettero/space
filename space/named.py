# coding: utf-8

import re
import logging

from .serial import Serial
from .obj import baseobj

FORMAT_RE = re.compile(r"^(.*?)(?:\b|[~])?(a|s|l|d|abbr|short|long|desc)?$")
log = logging.getLogger(__name__)


class Named(Serial, baseobj):
    a = "~"
    s = "object"
    l = "named object"
    d = "normally, you put your names in here"

    unique = False  # uniques are "the thing" rather than "a thing"
    plural = False  # Inherently plural noun (no a/an); e.g., "scissors", "pants".
    proper = False  # properly named things are never "the Paul" or "a Paul", always "Paul"

    pair_word = "pair"  # word used for pluralia tantum: used in "a pair of X"

    poessive = "its"
    reflexive = "itself"
    subjective = objective = "it"

    class Meta:
        save = "asld"

    def __init__(
        self, short=None, abbr=None, long=None, proper=None, proper_name=None, unique=None, plural=None, pair_word=None, **kw
    ):
        super().__init__(**kw)  # if Serial and baseobj had __init__, they'd both get called via MRO/super()
        if abbr is not None:
            if not isinstance(abbr, str):
                raise TypeError(f"wtf is this? ({abbr!r})")
            self.a = abbr
        if long is not None:
            if not isinstance(long, str):
                raise TypeError(f"wtf is this? ({long!r})")
            self.l = long
        if short is not None:
            if not isinstance(short, str):
                raise TypeError(f"wtf is this? ({short!r})")
            self.s = short
        if unique is not None:
            self.unique = bool(unique)
        if plural is not None:
            self.plural = bool(plural)
        if proper is not None:
            self.proper = bool(proper)
        if pair_word is not None:
            self.pair_word = pair_word
        if proper_name:
            self.proper_name = proper_name
        self.tokens = self._tokenize()

    @property
    def proper_name(self):
        if self.proper:
            return self.l

    @proper_name.setter
    def proper_name(self, v):
        if v:
            if "~" in v:
                self.s = self.l = v.replace("~", " ")
            else:
                self.l = v
                self.s = v.split()[0]
            self.proper = True
        else:
            self.proper = False

    @property
    def p_short(self):
        return self.a_short + "'s"

    @property
    def a_short(self):
        if self.proper or self.unique:
            return self.the_short
        if self.plural and self.pair_word:
            first = self.pair_word[:1].lower()
            return f"an {self.pair_word} of {self.l}" if first in aeiou else f"an {self.pair_word} of {self.l}"
        if self.plural:
            return self.the_short
        first = self.s[:1].lower()
        return f"an {self.s}" if first in "aeiou" else f"a {self.s}"

    @property
    def the_short(self):
        if self.proper:
            return self.s
        return f"the {self.s}"

    @property
    def a_long(self):
        if self.proper or self.unique:
            return self.the_long
        if self.plural and self.pair_word:
            first = self.pair_word[:1].lower()
            return f"an {self.pair_word} of {self.l}" if first in aeiou else f"an {self.pair_word} of {self.l}"
        if self.plural:
            return self.the_long
        first = self.l[:1].lower()
        return f"an {self.l}" if first in "aeiou" else f"a {self.l}"

    @property
    def the_long(self):
        if self.proper:
            return self.l
        return f"the {self.l}"

    @property
    def abbr(self):
        return self.a

    @property
    def short(self):
        return self.s

    @property
    def long(self):
        return self.l

    @property
    def desc(self):
        return self.d

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

    def __format__(self, spec):
        if spec in ("abbr", "a"):
            return self.abbr
        if spec in ("short", "s"):
            return self.short
        if spec in ("long", "l"):
            return self.long
        if spec in ("desc", "d"):
            return self.desc
        if m := FORMAT_RE.match(spec):
            fmt, m_select = m.groups()
            if not m_select:
                m_select = "s"
            if m_select.startswith("a"):
                return f"{self.abbr:{fmt}}" if fmt else self.abbr
            if m_select.startswith("s"):
                return f"{self.short:{fmt}}" if fmt else self.short
            if m_select.startswith("l"):
                return f"{self.long:{fmt}}" if fmt else self.long
            if m_select.startswith("d"):
                return f"{self.desc:{fmt}}" if fmt else self.desc
        return super().__format__(spec)


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
