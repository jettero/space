# coding: utf-8

import gc
import pkgutil
import importlib
import logging

log = logging.getLogger(__name__)

_this_body = None


def set_this_body(b=None):
    from .living import Living

    global _this_body
    if isinstance(_this_body, Living):
        _this_body.active = False
    _this_body = b
    if b is not None:
        _this_body.active = True


def this_body():
    return _this_body


def objects(of_types=None):
    if of_types is None:
        from .stdobj import StdObj

        ob_types = StdObj
    for o in gc.get_objects():
        try:
            if isinstance(o, of_types):
                yield o
        except ReferenceError:
            pass


def find_pkg(namespace):
    sv = importlib.import_module(namespace)
    for item in pkgutil.iter_modules(sv.__path__, f"{namespace}."):
        yield importlib.import_module(item.name)


def find_by_classname(namespace, classname):
    """e.g.,
    find_by_classname('space.shell', 'Shell')
    find_by_classname('space.verb', 'Action')
    """
    r = set()
    for m in find_pkg(namespace):
        try:
            r.add(getattr(m, classname))
        except (TypeError, AttributeError):
            pass
    return r


def find_by_baseclass(namespace, *baseclass):
    """e.g., find_by_baseclass('space.item', Containable)"""
    r = set()
    for m in find_pkg(namespace):
        for n in dir(m):
            if not n.startswith("_"):
                c = getattr(m, n)
                try:
                    if c not in baseclass and issubclass(c, baseclass):
                        r.add(c)
                except TypeError:
                    pass
    return r


def name_classlist_by_mod(classlist, suffix=None, inject=None):
    r = dict()
    for cls in classlist:
        n = cls.__module__.split(".")[-1].capitalize()
        if suffix is not None:
            n += suffix
        r[n] = cls
    if isinstance(inject, dict):
        inject.update(r)
    return r


def name_classlist_by_classname(classlist, suffix=None, inject=None):
    r = dict()
    for cls in classlist:
        n = cls.__name__
        if suffix is not None:
            n += suffix
        r[n] = cls
    if isinstance(inject, dict):
        inject.update(r)
    return r


def find_verb_method(verb, method):
    # XXX might this be more complicated later? for now, verbs are always here
    # XXX should we find_by_classname('space.verb', 'Action') and go through the nics too?
    return getattr(importlib.import_module(f"space.verb.{verb}").Action, method)
