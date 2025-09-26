# coding: utf-8

import logging
import weakref
import types
from collections import namedtuple

from .args import safe_execute, introspect_args, introspect_hints
import space.exceptions as E

log = logging.getLogger(__name__)

"""Method routing mechanics (developer notes)

Purpose
- Find and invoke the most appropriate ``can_<verb>_*`` or ``do_<verb>_*``
  method on an object, based on available argument names/values.

Components
- ``MethodRouter``: collects method names with a common prefix.
- ``MethodArgsRouter``: builds ``RouteHint`` entries from function signatures
  and yields filled call candidates (``FFAK``) using ``introspect_args``.
- ``MethodNameRouter``: prefers the longest suffix match from available method
  names using underscore-separated segments.
- ``RouteHint``: signature + tokens + filling logic for object/name
  resolution.
- ``FFAK``: a filled function+args+kwargs tuple with a sortable order.

Selection strategy
- Name variant selection prefers longest suffixes that are satisfied by the
  provided keyword keys (``MethodNameRouter.longest_prefix``).
- Argument filling favors named kwargs over positionals and respects type
  annotations or parameter-name heuristics (see ``space/args.py``).
- When ``multi=True``, multiple candidates may be invoked in order; otherwise
  the first compatible candidate returns.
"""

class MethodRouter:
    def __init__(self, obj, top, multi=False, callback=None, dne_ok=True):
        self.top   = top
        self.multi = multi
        self.obj = obj if isinstance(obj, weakref.ProxyTypes) else weakref.proxy(obj)
        self.callback = callback
        self.dne_ok = dne_ok
        self.dir = tuple( m for m in dir(obj) if m.startswith(top) )

    def __iter__(self):
        yield from self.dir

    def __getitem__(self, idx):
        if isinstance(idx, (list,tuple,set)):
            return tuple( self[i] for i in idx )
        return self.dir[idx]

    @property
    def stringified(self):
        base = self.obj.__repr__() # repr(obj) won't work (weakref.proxy)
        if len(self.dir) == 1:
            return f'{base}.{self.dir[0]}'
        return f'{base}.({"|".join(self.dir)})'

    def __repr__(self):
        return f'MethodRouter{{{self.stringified}}}'
    __str__ = __repr__

class FFAK(namedtuple('FFAK', ['func', 'filled', 'args', 'kwargs'])):
    _base_order = 1000
    def __bool__(self):
        return self.filled

    def __call__(self):
        return self.func(*self.args, **self.kwargs)

    def __str__(self):
        return f'{self.func.__name__}()'

    @property
    def order(self):
        if self.filled:
            return self._base_order - len(self.args) + len(self.kwargs)
        return self._base_order

def list_match(name, objs):
    if isinstance(objs, (types.GeneratorType, list, tuple)):
        s = name.split('.', 1)
        assert len(s) in (1,2,)
        objs = [ i for i in objs if i.parse_match(*s) ]
        if objs:
            return objs
    return tuple()

class RouteHint(namedtuple('RouteHint', ['fname', 'func', 'hlist'])):
    tokens = None
    def __repr__(self):
        hl = '/'.join([ repr(x) for x in self.hlist ])
        return f'RH({self.fname})«{hl}»'

    def fill(self, objs):
        log.debug(' filling %s using objs=%s tok=%s', self, objs, self.tokens)
        ret = dict()
        for aname,tlist in self.hlist:
            type0,*remainder = tlist
            v = self.tokens.get(aname)
            if v is None:
                continue
            if not type0:
                ret[aname] = v
            elif type0 in (list,tuple): # tuple→str, hopefully
                if len(remainder) != 1 or remainder[0] is not str:
                    raise NotImplementedError('TODO')
                ret[aname] = v
            elif remainder: # wtf!??!
                raise NotImplementedError('TODO')
            else:
                applicable_objs = [ o for o in objs if isinstance(o, type0) ]
                if isinstance(v, (list,tuple)):
                    o = list()
                    for x in v:
                        o += list_match(x, applicable_objs)
                else:
                    o = list_match(v, applicable_objs)
                # If nothing matched and expected a str (like a direction word),
                # preserve the original token so can_* handlers can reason on it.
                if not o and isinstance(v, (list,tuple)):
                    ret[aname] = v
                elif not o and isinstance(v, str):
                    ret[aname] = v
                else:
                    ret[aname] = o
        return ret

    def evaluate(self, *a, **kw):
        try:
            return safe_execute(self.func, *a, **kw)
        except E.UnfilledArgumentError:
            return False, {}

class MethodArgsRouter(MethodRouter):
    def hints(self):
        ret = list()
        for fname in self.dir:
            func = getattr(self.obj, fname)
            ret.append(RouteHint(fname, func, introspect_hints(func)))
        return ret

    def fill(self, *a, **kw):
        for fname in self.dir:
            fak = introspect_args(getattr(self.obj, fname), *a, **kw)
            if fak.filled:
                yield FFAK(getattr(self.obj, fname), *fak)

    def ordered_fill(self, *a, **kw):
        for ffak in sorted(self.fill(*a, **kw), key=lambda x: x.order):
            yield ffak

    def __repr__(self):
        return f'MethodArgsRouter{{{self.stringified}}}'
    __str__ = __repr__

    def __call__(self, *a, **kw):
        rr = [True, kw]
        did_something = False
        for ffak in self.ordered_fill(*a, **kw):
            log.debug('MNR invoking %s.%s', self.obj, ffak)
            r = ffak()
            did_something = True
            if isinstance(r, tuple) and len(r) == 2 and r[0]:
                kw.update(r[1])
            cbr = self.callback(fname, r) if callable(self.callback) else True
            if not self.multi:
                return r if r is None else tuple(r)
            if cbr is False:
                break
            rr[0] = rr[0] and r[0]
        if not did_something and not self.dne_ok:
            raise NotImplementedError(f'unable to locate {"_".join(self.top)} methods for ({kw})')
        return tuple(rr)

class MethodNameRouter(MethodRouter):
    def __init__(self, obj, top, multi=False, callback=None, dne_ok=True):
        super().__init__(obj, top, multi=multi, callback=callback, dne_ok=dne_ok)
        self.top   = top.split('_')
        l = len(self.top)
        self.dir = tuple( m.split('_')[l:] for m in self.dir )

    def __getitem__(self, idx):
        if isinstance(idx, (list,tuple,set)):
            return tuple( self[i] for i in idx )
        return '_'.join( self.top + self.dir[idx] )

    def count(self, items, smode=None):
        ret = set()
        for idx,mtpl in enumerate(self):
            missing = tuple( i for i in mtpl if i not in items )
            if not missing:
                ret.add(idx)
        log.debug('MNR counted %s', ret)
        if callable(smode):
            return sorted(self[ret], key=smode)
        return self[ret]

    def longest_prefix(self, items):
        return self.count(items, smode=lambda x: -len(x))

    def __call__(self, *a, **kw):
        k = a + tuple(kw)
        pf = self.longest_prefix(k)
        if not pf and not self.dne_ok:
            raise NotImplementedError(f'unable to locate {"_".join(self.top)} methods for ({kw})')

        rr = [True, kw]
        for fname in pf:
            log.debug('MNR invoking %s.%s()', self.obj, fname)
            r = safe_execute(getattr(self.obj, fname), *a, **kw)
            if isinstance(r, tuple) and len(r) == 2 and r[0]:
                kw.update(r[1])
            cbr = self.callback(fname, r) if callable(self.callback) else True
            if not self.multi:
                return r if r is None else tuple(r)
            if cbr is False:
                break
            rr[0] = rr[0] and r[0]
        return tuple(rr)
