# coding: utf-8

import logging
import weakref
from collections import namedtuple

from .args import safe_execute, introspect_args

log = logging.getLogger(__name__)

class MethodRouter:
    def __init__(self, obj, top, multi=False, callback=None, dne_ok=True):
        self.top   = top
        self.multi = multi
        self.obj = weakref.proxy(obj)
        self.callback = callback
        self.dne_ok = dne_ok
        self.dir = tuple( m for m in dir(obj) if m.startswith(top) )

    def __iter__(self):
        yield from self.dir

    def __getitem__(self, idx):
        if isinstance(idx, (list,tuple,set)):
            return tuple( self[i] for i in idx )
        return self.dir[idx]

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

class MethodArgsRouter(MethodRouter):
    def fill(self, *a, **kw):
        for fname in self.dir:
            fak = introspect_args(getattr(self.obj, fname), *a, **kw)
            if fak.filled:
                yield FFAK(getattr(self.obj, fname), *fak)

    def ordered_fill(self, *a, **kw):
        for ffak in sorted(self.fill(*a, **kw), key=lambda x: x.order):
            yield ffak

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
