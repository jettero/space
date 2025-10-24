# coding: utf-8

import logging
import weakref
import types
from collections import namedtuple

from .args import safe_execute, introspect_args, introspect_hints
import space.exceptions as E

log = logging.getLogger(__name__)

# XXX: This module is a mess. I couldn't make up my mind about how any of this
# should work and the result is a total mess of mostly-thought-out but
# un-written conventions.
#
# XXX: I'd like to get rid of multi-mode, I don't really use it much outside of callbacks
# XXX: I'd like to remove callbacks. They seem to reduplicate some below stuff and aren't really used for anything
#      (see space/obj.py's parse_can to see what I mean. compare to __call__ ... same shit, different error messages)


class MethodRouter:
    def __init__(self, obj, top, multi=False, callback=None, dne_ok=True):
        self.top = top
        self.multi = multi
        self.obj = obj if isinstance(obj, weakref.ProxyTypes) else weakref.proxy(obj)
        self.callback = callback
        self.dne_ok = dne_ok
        self.dir = tuple(m for m in dir(obj) if m == top or m.startswith(f"{top}_"))

    def __iter__(self):
        yield from self.dir

    def __getitem__(self, idx):
        if isinstance(idx, (list, tuple, set)):
            return tuple(self[i] for i in idx)
        return self.dir[idx]

    @property
    def stringified(self):
        base = self.obj.__repr__()  # repr(obj) won't work (weakref.proxy)
        if len(self.dir) == 1:
            return f"{base}.{self.dir[0]}"
        return f'{base}.({"|".join(i if isinstance(i, str) else repr(i) for i in self.dir)})'

    def __repr__(self):
        return f"{self.__class__.__name__}{{{self.stringified}}}"

    __str__ = __repr__


class FFAK(namedtuple("FFAK", ["func", "filled", "args", "kwargs"])):
    _base_order = 1000

    def __bool__(self):
        return self.filled

    def __call__(self):
        return self.func(*self.args, **self.kwargs)

    def __str__(self):
        return f"{self.func.__name__}()"

    @property
    def order(self):
        if self.filled:
            return self._base_order - len(self.args) + len(self.kwargs)
        return self._base_order


def list_match(name, objs):
    if isinstance(objs, (types.GeneratorType, list, tuple)):
        s = name.split(".", 1)
        if len(s) not in (1, 2):
            raise ValueError(f"len(name.split(., 1)) not in (1,2)")
        objs = [i for i in objs if i.parse_match(*s)]
        if objs:
            return objs
    return tuple()


class RouteHint(namedtuple("RouteHint", ["fname", "func", "hlist"])):
    tokens = None

    def __repr__(self):
        hl = "/".join([repr(x) for x in self.hlist])
        return f"RH({self.fname})«{hl}»"

    def fill(self, objs):
        log.debug("%s.fill(%s) tokens=%s", self, objs, self.tokens)
        ret = dict()
        for aname, tlist in self.hlist:
            type0, *remainder = tlist
            v = self.tokens.get(aname)
            log.debug("  aname=%s type0=%s remainder=%s v=%s", aname, type0, remainder, v)
            if v is None:
                continue
            if not type0:
                ret[aname] = v
            elif type0 is str:
                ret[aname] = v[0]
            elif type0 == tuple[str, ...]:
                ret[aname] = v
            elif remainder:
                raise NotImplementedError(f"TODO[unknown(type0={type0!r} remainder={remainder!r})]")
            else:
                applicable_objs = [o for o in objs if isinstance(o, type0)]
                if isinstance(v, (list, tuple)):
                    o = list()
                    for x in v:
                        o += list_match(x, applicable_objs)
                else:
                    o = list_match(v, applicable_objs)
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
        from .stdobj import StdObj

        def _should_sort_by_distance(v):
            if isinstance(v, (list, tuple)) and v and isinstance(v[0], StdObj):
                return True

        kw = {
            k: (tuple(sorted(v, key=lambda o: self.obj.unit_distance_to(o))) if _should_sort_by_distance(v) else v)
            for k, v in kw.items()
        }
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
            log.debug("MAR invoking %s.%s", self.obj, ffak)
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
        self.top = top.split("_")
        l = len(self.top)
        self.dir = tuple(m.split("_")[l:] for m in self.dir)

    def __getitem__(self, idx):
        if isinstance(idx, (list, tuple, set)):
            return tuple(self[i] for i in idx)
        return "_".join(self.top + self.dir[idx])

    def count(self, items, smode=None):
        ret = set()
        for idx, mtpl in enumerate(self):
            missing = tuple(i for i in mtpl if i not in items)
            if not missing:
                ret.add(idx)
        log.debug("MNR counted %s", ret)
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
            log.debug("MNR invoking %s.%s()", self.obj, fname)
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
