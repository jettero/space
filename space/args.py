# coding: utf-8

import inspect
import logging
from functools import lru_cache
from collections import namedtuple
import space.exceptions as E

log = logging.getLogger(__name__)


class FAK(namedtuple("FAK", ["filled", "args", "kwargs"])):
    def __bool__(self):
        return self.filled


def filter_annotated_arg(name, item, annotation):  # pylint: disable=unused-argument
    if annotation is None:
        return item
    if inspect.isclass(annotation):
        if isinstance(item, annotation):
            return item
        if isinstance(item, (tuple, list)):
            for x in item:
                if isinstance(x, annotation):
                    return x
        return
    if callable(annotation):
        r = annotation(item)
        if r is True:
            return item
        if r not in (False, None):
            return r
        return
    if hasattr(annotation, "match") and hasattr(annotation, "pattern"):
        m = annotation.match(str(item))
        if m:
            gd = m.groupdict()
            if gd:
                return gd
            g = m.groups()
            if g:
                return g
            return item


class IntroHint(namedtuple("IntroHint", ["aname", "tlist"])):
    def __repr__(self):
        # mimic list-of-pairs form for readability in tests
        tl = ", ".join([x.__name__ for x in self.tlist])
        return f"('{self.aname}', [{tl}])"


@lru_cache
def introspect_hints(fn, add_kwonly=False):
    """try to guess the needed argument types for the given function"""
    # pylint: disable=import-outside-toplevel
    # we lazy import so space.args can be used by the below Living and StdObj
    # types without a loop
    from .living import Living
    from .stdobj import StdObj

    fas = inspect.getfullargspec(fn)
    todo = list(fas.args)
    if inspect.ismethod(fn):
        todo = todo[1:]
    if fas.varargs:
        todo.append(fas.varargs)
    if add_kwonly and fas.kwonlyargs:
        todo += fas.kwonlyargs
    ret = [IntroHint(arg, list()) for arg in todo]
    for ih in ret:
        if ih.aname == fas.varargs:
            ih.tlist.append(tuple)
        an = fas.annotations.get(ih.aname, None)
        if an is not None:
            ih.tlist.append(an)
        else:
            ihal = ih.aname.lower()
            if ihal.startswith("ob"):
                ih.tlist.append(StdObj)
            elif ihal.startswith("liv") or ihal.startswith("targ"):
                ih.tlist.append(Living)
            else:
                ih.tlist.append(str)
    return ret


def introspect_args(fn, *iargs, **ikwargs):
    # pylint: disable=too-many-statements
    # you know what? it *is* too many statements, but this is complicated and
    # more functions won't make it better
    """given a function, zero or more args and zero or more kwargs

    Try to determine a relatively safe set of args from those given
    that fit the given function.

    Return a boolean indicating whether the given args/kwargs fill the
    required args for the given function, the modified args and the
    modified kwargs.

    In [1]: from space.args import introspect_args
       ...: def f(x):
       ...:     return x+1
       ...: fak = introspect_args(f, x=3, y=4, z=5)
       ...: (fak, f(*fak.args, **fak.kwargs))
    Out[1]: (FAK(filled=True, args=(3,), kwargs={}), 4)

    If there's an odered arg named 'x' and a kwarg named 'x' — which would
    normally be a TypeError, introspecting_args will simply choose the
    kwarg over the ordered arg.
    """

    # In [14]: def f(x,y, z=3):
    #     ...:     pass
    #     ...: inspect.getfullargspec(f)
    # Out[14]: FullArgSpec(args=['x', 'y', 'z'], varargs=None, varkw=None,
    #     defaults=(3,), kwonlyargs=[], kwonlydefaults=None, annotations={})
    #
    # In [15]: def g(*a, x=3):
    #     ...:     pass
    #     ...: inspect.getfullargspec(g)
    # Out[15]: FullArgSpec(args=[], varargs='a', varkw=None, defaults=None,
    #     kwonlyargs=['x'], kwonlydefaults={'x': 3}, annotations={})

    log.debug("introspecting_args(%s, *%s, **%s)", fn, iargs, ikwargs)
    fas = inspect.getfullargspec(fn)

    log.debug(" … %s:", fas.__class__.__name__)
    for k, v in fas._asdict().items():
        log.debug("   … %s: %s", k, v)

    # Stage-0: if this is a method, the first arg is 'self' and get
    # automatically passed in during the call; don't populate it
    if inspect.ismethod(fn):
        del fas.args[0]

    # NOTE: The reason python simply raises an exception for some of these
    # forms of ambiguity is that there's no definitely right way to do the
    # below. We make some decisions and just roll with it, preferring to
    # complete the safe execute with some possible arg populations if it's
    # possible and sorta makes sense. (Making sense is defined below and may
    # not actually make sense.)

    # Stage-1: try to complete any positional args
    def generate_args():
        for i, k in enumerate(fas.args):
            annotation = fas.annotations.get(k)
            if k in ikwargs:
                faa = filter_annotated_arg(k, ikwargs.pop(k), annotation)
                if faa is not None:
                    yield faa  # prefer a named arg from ikwargs over the next position arg
                    continue
            if i < len(iargs):
                faa = filter_annotated_arg(k, iargs[i], annotation)
                if faa is not None:
                    yield faa  # use the next positional arg if we have it
                    continue
            # quit trying to consume positionals, leave them as kwargs
            # remember, calling fn(x,y,z) as fn(**{'x':1,'y':2,'z':3}) works
            # just fine
            break

    ra = tuple(generate_args())
    # consume any positional args we might have used in tuple(generate_args())
    # ignoring the fact that we may have used kwargs *instead*.
    # This means if we have fn(x,y,z) and iargs=(1,2,3,4,5,6) and ikwargs={'z':7}
    # we choose the ikwargs['z'], assume we consumed iargs[0:2] and set:
    #   ra=(1,2,7), iargs=(5,6), ikwargs={}
    iargs = iargs[len(ra) :]
    log.debug(" … stage-1 ra=%s iargs=%s ikwargs=%s", ra, iargs, ikwargs)

    filled = len(ra) >= len(fas.args)
    log.debug(" … positional args filled: len(ra)=%d >= len(fas.args)=%d = %s", len(ra), len(fas.args), filled)

    # Stage-2: try to finish completing any varargs
    # If we have a kwarg of that name, we try to consume it (converting as
    # necessary to append to ra). Only if we have no named kwarg do we bother
    # looking at the remaining positional args.
    if fas.varargs and filled:
        faa = ikwargs.pop(fas.varargs) if fas.varargs in ikwargs else iargs
        log.debug(" … stage-2 varargs=%s, trying to fill with: %s", fas.varargs, faa)
        faa = filter_annotated_arg(fas.varargs, faa, fas.annotations.get(fas.varargs))
        if faa is not None:
            if isinstance(faa, list):
                log.debug(" … convert ikwargs[%s] (list) to tuple", fas.varargs)
                faa = tuple(faa)
                filled = True
            elif not isinstance(faa, tuple):
                log.debug(" … convert ikwargs[%s] (%s) to tuple", fas.varargs, type(faa))
                faa = (faa,)
                filled = True
            else:
                log.debug(" … consume ikwargs[%s]", fas.varargs)
        if faa:
            log.debug(" … stage-2 ra += %s", iargs)
            ra += faa
        else:
            log.debug(" … marking unfilled due to not consuming a value for the varargs=%s", fas.varargs)
            filled = False

    # Stage-4: try to fill any kwargs, or just throw the remaining kwargs at any varkw
    rkw = ikwargs if fas.varkw else {k: v for k, v in ikwargs.items() if k in fas.kwonlyargs}
    if rkw:
        for k in list(rkw):
            faa = filter_annotated_arg(k, rkw[k], fas.annotations.get(k))
            if faa is None:
                del rkw[k]
            else:
                rkw[k] = faa
        log.debug(" … stage-3 convert remaining kwargs: %s", rkw)

    return FAK(filled, ra, rkw)


def safe_execute(fn, *a, **kw):
    filled, a, kw = introspect_args(fn, *a, **kw)
    log.debug(" … filled=%s safe_execute(%s, *%s, **kw=%s)", filled, fn, a, kw)
    try:
        return fn(*a, **kw)
    except TypeError as e:
        if not filled:
            # we should probably use raise UTE() from e here, but we want the
            # missing vars in the error for testing if nothing else
            raise E.UnfilledArgumentError(f"safe_execute args failed to fill fn={fn}: {e}")
        raise
