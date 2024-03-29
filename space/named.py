# coding: utf-8

import re
import logging

from .serial import Serial
from .obj import baseobj

FORMAT_RE = re.compile(r'^(.*?)(?:\b|[~])?(a|s|l|d|abbr|short|long|desc)?$')
log = logging.getLogger(__name__)

class Named(Serial, baseobj):
    a = s = l = ''
    a = s = l = ''

    d = 'an object with names and descriptions'

    a_fmt = '{a:{fmt}}'
    s_fmt = '{s:{fmt}}'
    l_fmt = '{l:{fmt}}'
    d_fmt = '{l:{fmt}} :- {d}'
    r_fmt = '{c}({l})'

    class Meta:
        save = 'asld'

    def __init__(self, short=None, abbr=None, long=None):
        super().__init__()
        self.tokens = set()
        if abbr:  self.abbr  = abbr
        if short: self.short = short
        if long:  self.long  = long

    def __format__(self, spec):
        if spec in ('abbr','a'):
            return self.abbr
        if spec in ('short','s'):
            return self.short
        if spec in ('long','l'):
            return self.long
        if spec in ('desc','d'):
            return self.desc
        m = FORMAT_RE.match(spec)
        if m:
            fmt, m_select = m.groups()
            if not m_select:
                m_select = 's'
            return self._m_fmt(m_select, fmt=fmt)
        return super().__format__(spec)

    def _m_fmt(self, var_name, fmt='', **kw):
        m = var_name.lower().strip()[0]
        return getattr(self, f'{m}_fmt').format(**self.as_dict(fmt=fmt, **kw))

    @property
    def abbr(self):
        return self._m_fmt('a')

    @property
    def short(self):
        return self._m_fmt('s')

    @property
    def long(self):
        return self._m_fmt('l')

    @property
    def desc(self):
        return self._m_fmt('d')

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
    def __init__(self, *a, can=None):
        self._a = { str(i) for i in a }
        self._c = None if can is None else Tags(*can)

    def clone(self):
        n = self.__class__.__new__(self.__class__)
        n._a = set(self._a) # pylint: disable=protected-access
        n._c = None if self._c is None else set(self._c) # pylint: disable=protected-access
        return n

    def clear(self):
        self._a.clear()

    def add(self, tag):
        tag = str(tag)
        if self._c is not None:
            if tag not in self._c:
                raise ValueError(f'{tag} not allowed (allowed: {str(self)})')
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
            return '{ }'
        return repr(self._a)

    def __repr__(self):
        return f'{self.__class__.__name__}{str(self)}'

    def __eq__(self, other):
        if isinstance(other, Tags):
            return self._a == other._a # pylint: disable=protected-access
        if not isinstance(other, set):
            other = set(other)
        return self._a == other
