# coding: utf-8

import importlib
import importlib.util
import json
import types
import weakref
from collections import deque

# *_FILTER quirks:
# isinstance(True, int) -> True -- (wierd)

PASS_FILTER = (int, str, float, list, tuple, deque)
STOP_FILTER = (property, classmethod, types.FunctionType, types.MethodType, weakref.ProxyType)


class Serial:
    __save__ = list(
        # this list is *only* names of attributes (e.g. properties) that we try to save
        # despite being ruled out by the filters
    )

    @classmethod
    def save_anyway(cls):
        ret = set()
        for c in cls.mro():
            try:
                ret = ret.union(c.__save__)
            except AttributeError:
                pass
        return ret

    def as_json(self, indent=2, sort_keys=True, filename=None):
        ret = json.dumps(self.save(), indent=indent, sort_keys=sort_keys)
        if filename is not None:
            if not filename.endswith(".json"):
                filename += ".json"
            with open(filename, "w") as fh:
                fh.write(ret)
        return ret

    def save(self, hide_class=False, unfiltered=False, recurse=True, inject=None, override=None):
        cls = self.__class__
        nam = f"\x1f{cls.__module__}.{cls.__qualname__}"

        if override:
            if hide_class:
                return override
            return {nam: override}

        obj_d = self.__dict__
        cls_d = cls.__dict__

        first_pass = {k: (cls_d.get(k), obj_v) for k, obj_v in obj_d.items()}
        if unfiltered:
            return first_pass  # this is likely only any good for debugging

        def handle_value(obj_v):
            if recurse:
                if isinstance(obj_v, Serial):
                    return obj_v.save()
                if isinstance(obj_v, (list, tuple, deque)):
                    return tuple(handle_value(v) for v in obj_v)
            return obj_v

        __save__ = self.save_anyway()
        save = {
            k: handle_value(obj_v)
            for k, (cls_v, obj_v) in first_pass.items()
            if k in __save__
            or (
                not isinstance(cls_v, STOP_FILTER)
                and not isinstance(obj_v, STOP_FILTER)
                and isinstance(obj_v, PASS_FILTER)
                and cls_v != obj_v  # but we don't want to save any defaults
            )
        }

        if inject:
            # presuambly a child class passed this in via super().save(inject=dict())
            save.update(inject)

        if hide_class:
            return save
        return {nam: save}

    @classmethod
    def load(cls, data):
        if not isinstance(data, dict):
            raise TypeError(f"{cls.__qualname__} cannot load {type(data).__name__}")
        inst = cls.__new__(cls)

        def convert(value):
            if isinstance(value, tuple):
                return tuple(convert(v) for v in value)
            if isinstance(value, dict) and len(value) == 1:
                for marker in value:
                    if marker.startswith("\x1f"):
                        return load(value)
            return value

        for name, raw in data.items():
            value = convert(raw)
            if isinstance(default := cls.__dict__.get(name), list):
                value = list(value)
            elif isinstance(default, tuple):
                value = tuple(value)
            elif isinstance(default, deque):
                value = deque(value)
            setattr(inst, name, value)

        return inst


def split_marker(marker):
    parts = marker.split(".")
    for size in range(len(parts), 0, -1):
        module_name = ".".join(parts[:size])
        try:
            spec = importlib.util.find_spec(module_name)
        except ModuleNotFoundError:
            continue
        if spec is not None:
            return module_name, ".".join(parts[size:])
    raise ModuleNotFoundError(marker)


def resolve_marker(marker):
    if marker.startswith("\x1f"):
        marker = marker[1:]
    module_name, qual = split_marker(marker)
    module = importlib.import_module(module_name)
    target = module
    if qual:
        for attr in qual.split("."):
            target = getattr(target, attr)
    return target


def load(dat):
    if isinstance(dat, str):
        dat = json.loads(dat)
    if not isinstance(dat, dict):
        raise TypeError("load expects dict or json string")
    if len(dat) != 1:
        raise ValueError("load expects exactly one root object")

    for marker, payload in dat.items():
        if not marker.startswith("\x1f"):
            raise ValueError("load missing class marker")
        cls = resolve_marker(marker)
        if not issubclass(cls, Serial):
            raise TypeError("load target is not a Serial subclass")
        return cls.load(payload)


PASS_FILTER = (*PASS_FILTER, Serial)
