#!/usr/bin/env python
# coding: utf-8

from functools import lru_cache
from typing import Any, get_args, get_origin, Literal, Annotated, Union, get_type_hints
import inspect


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


@lru_cache
def get_introspection_hints(func, unhinted_assumed_type=str):
    sig = inspect.signature(func)
    ordered = []
    raw = getattr(func, "__annotations__", {})
    resolved = get_type_hints(func, globalns=getattr(func, "__globals__", {}), localns=None)  # type: ignore[attr-defined]
    for name, param in sig.parameters.items():
        if param.kind is inspect.Parameter.VAR_POSITIONAL:
            ordered.append((name, ...))
            continue
        ann = raw.get(name, inspect._empty)
        if ann is inspect._empty:
            ordered.append((name, unhinted_assumed_type))
            continue
        ordered.append((name, resolved.get(name, ann)))
    return ordered


def matches_type_hint(value, annotation):
    origin = get_origin(annotation)
    if origin is Annotated:
        return matches_type(value, get_args(annotation)[0])
    if origin is Literal:
        return any(value == lit for lit in get_args(annotation))
    if origin is None:
        if annotation is Any:
            return True
        return isinstance(value, annotation)
    if origin is tuple:
        if not isinstance(value, tuple):
            return False
        args = get_args(annotation)
        if len(args) == 2 and args[1] is Ellipsis:
            return all(matches_type(v, args[0]) for v in value)
        if len(value) != len(args):
            return False
        return all(matches_type(v, t) for v, t in zip(value, args))
    if origin is list:
        return isinstance(value, list) and all(matches_type(v, get_args(annotation)[0]) for v in value)
    if origin is set:
        return isinstance(value, set) and all(matches_type(v, get_args(annotation)[0]) for v in value)
    if origin is dict:
        if not isinstance(value, dict):
            return False
        kt, vt = get_args(annotation)
        return all(matches_type(k, kt) and matches_type(v, vt) for k, v in value.items())
    if origin is type(None):
        return value is None
    if origin is None and annotation is None:
        return value is None
    if origin is Union or str(origin) in {"types.UnionType"}:
        return any(matches_type(value, t) for t in get_args(annotation))
    return isinstance(value, origin)
