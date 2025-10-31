#!/usr/bin/env python
# coding: utf-8

from functools import lru_cache
from collections import namedtuple
from typing import Any, get_args, get_origin, Literal, Annotated, Union, get_type_hints
import inspect
import logging

log = logging.getLogger(__name__)


def deep_eq(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in a.keys() | b.keys():  # union of keys
            va, vb = a.get(k, None), b.get(k, None)
            if not (va and vb):  # either side missing or falsy
                continue
            if not deep_eq(va, vb):
                return False
        return True
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(deep_eq(x, y) for x, y in zip(a, b))
    return a == b


def iscallable(x):
    return inspect.isfunction(x) or inspect.ismethod(x) or inspect.isbuiltin(x)


class IntroHint(namedtuple("IH", ["name", "type", "variadic"])):
    def __repr__(self):
        v = "*" if self.variadic else ""
        if self.type in (str, None):
            return f"{v}{self.name}"
        t = self.type.__name__ if inspect.isclass(self.type) else self.type
        return f"{v}{self.name}:{t}"

    def match(self, val):
        if self.variadic:
            return isinstance(val, tuple) and all(matches_type_hint(x, self.type) for x in val)
        return matches_type_hint(val, self.type)


@lru_cache
def get_introspection_names(func, assume_type=Any):
    sig = inspect.signature(func)
    ordered = []
    resolved = get_type_hints(func, globalns=getattr(func, "__globals__", {}), localns=None)  # type: ignore[attr-defined]
    return [IntroHint(n, assume_type, p.kind is inspect.Parameter.VAR_POSITIONAL) for n, p in sig.parameters.items()]


@lru_cache
def get_introspection_hints(func, unhinted_assumed_type=str, imply_type_callback=None):
    sig = inspect.signature(func)
    ordered = []
    resolved = get_type_hints(func, globalns=getattr(func, "__globals__", {}), localns=None)  # type: ignore[attr-defined]
    for name, param in sig.parameters.items():
        variadic = param.kind is inspect.Parameter.VAR_POSITIONAL
        if r := resolved.get(name):
            ordered.append(IntroHint(name, r, variadic))
            continue
        if callable(imply_type_callback):
            if r := imply_type_callback(name):
                ordered.append(IntroHint(name, r, variadic))
                continue
        ordered.append(IntroHint(name, unhinted_assumed_type, variadic))
    return ordered


def matches_type_hint(val, ihint):
    origin = get_origin(ihint.type)
    if origin is Annotated:
        return matches_type_hint(val, get_args(ihint.type)[0])
    if origin is Literal:
        return any(val == lit for lit in get_args(ihint.type))
    if origin is None:
        if ihint.type is Any:
            return True
        return isinstance(val, ihint.type)
    if origin is tuple:
        if not isinstance(val, tuple):
            return False
        args = get_args(ihint.type)
        if len(args) == 2 and args[1] is Ellipsis:
            return all(matches_type_hint(v, args[0]) for v in val)
        if len(val) != len(args):
            return False
        return all(matches_type_hint(v, t) for v, t in zip(val, args))
    if origin is list:
        return isinstance(val, list) and all(matches_type_hint(v, get_args(ihint.type)[0]) for v in val)
    if origin is set:
        return isinstance(val, set) and all(matches_type_hint(v, get_args(ihint.type)[0]) for v in val)
    if origin is dict:
        if not isinstance(val, dict):
            return False
        kt, vt = get_args(ihint.type)
        return all(matches_type_hint(k, kt) and matches_type_hint(v, vt) for k, v in val.items())
    if origin is type(None):
        return val is None
    if origin is None and ihint.type is None:
        return val is None
    if origin is Union or str(origin) in {"types.UnionType"}:
        return any(matches_type_hint(val, t) for t in get_args(ihint.type))
    return isinstance(val, origin)
