# coding: utf-8

import types
from collections.abc import Mapping, Sequence
from weakref import ProxyTypes

PRIMITIVE_TYPES = (str, int, float, bool, type(None))
PASS_FILTER = (int, float, str, bool)
STOP_FILTER = (property, classmethod, staticmethod, types.FunctionType, types.MethodType)


def _type_path(target):
    cls = target if isinstance(target, type) else target.__class__
    return f"{cls.__module__}.{cls.__name__}"


def _merge_directive(base, attr):
    value = getattr(base, attr, ())
    return tuple(value) if isinstance(value, (list, tuple, set)) else ()


def _aggregate(attr, mro):
    merged = []
    for base in mro:
        merged.extend(_merge_directive(base, attr))
    return tuple(dict.fromkeys(merged))


def _filters_for(base):
    pass_filter = getattr(base, "__pass_filter__", PASS_FILTER)
    stop_filter = getattr(base, "__stop_filter__", STOP_FILTER)
    if isinstance(pass_filter, (list, set)):
        pass_filter = tuple(pass_filter)
    if isinstance(stop_filter, (list, set)):
        stop_filter = tuple(stop_filter)
    save = _merge_directive(base, "__save__")
    nosave = _merge_directive(base, "__nosave__")
    return pass_filter, stop_filter, save, nosave


def _register_ref(seen, obj):
    key = id(obj)
    if key in seen:
        return seen[key], True
    ref = f"obj{len(seen)}"
    seen[key] = ref
    return ref, False


def _freeze(value, seen):
    if isinstance(value, PRIMITIVE_TYPES):
        return value
    if isinstance(value, Serial):
        ref, existed = _register_ref(seen, value)
        if existed:
            return {"@ref": ref}
        return value._save_into(seen, ref)
    if isinstance(value, ProxyTypes):
        return {"@proxy": str(value)}
    if isinstance(value, Mapping):
        return {str(k): _freeze(v, seen) for k, v in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_freeze(v, seen) for v in value]
    if hasattr(value, "_asdict") and callable(value._asdict):
        ref, existed = _register_ref(seen, value)
        if existed:
            return {"@ref": ref}
        data = value._asdict()
        return {"@id": ref, "@type": _type_path(value), **{k: _freeze(v, seen) for k, v in data.items()}}
    if hasattr(value, "magnitude") and hasattr(value, "units"):
        ref, existed = _register_ref(seen, value)
        if existed:
            return {"@ref": ref}
        unit = value.units if hasattr(value.units, "__str__") else str(value.units)
        return {"@id": ref, "@type": _type_path(value), "magnitude": value.magnitude, "units": str(unit)}
    if hasattr(value, "__dict__"):
        ref, existed = _register_ref(seen, value)
        if existed:
            return {"@ref": ref}
        data = {k: _freeze(v, seen) for k, v in value.__dict__.items() if not callable(v)}
        return {"@id": ref, "@type": _type_path(value), **data}
    if hasattr(value, "__iter__") and not isinstance(value, (str, bytes, bytearray)):
        return [_freeze(v, seen) for v in list(value)]
    ref, existed = _register_ref(seen, value)
    if existed:
        return {"@ref": ref}
    return str(value)


class Serial:
    __pass_filter__ = PASS_FILTER
    __stop_filter__ = STOP_FILTER
    __save__ = ()
    __nosave__ = ()

    @classmethod
    def default_serial(cls, merge=True, omit_class=True):
        bases = list(reversed(cls.mro()))
        result = dict() if merge else []
        for base in bases:
            pass_filter, stop_filter, save, nosave = _filters_for(base)
            data = {}
            for name, value in base.__dict__.items():
                if name in nosave or name.startswith("__"):
                    continue
                if name in save or isinstance(value, pass_filter):
                    if isinstance(value, stop_filter):
                        continue
                    data[name] = value
            if not data:
                continue
            if merge:
                result.update(data)
            elif omit_class:
                result.append(data)
            else:
                result.append({_type_path(base): data})
        if merge and not omit_class:
            return {_type_path(cls): result}
        return result

    @classmethod
    def _nosave(cls):
        return set(_aggregate("__nosave__", cls.mro()))

    @classmethod
    def _save(cls):
        return set(_aggregate("__save__", cls.mro()))

    def _state_items(self):
        defaults = self.default_serial(merge=True, omit_class=True)
        nosave = self._nosave()
        state = {}
        for name, default in defaults.items():
            if name in nosave:
                continue
            if (current := getattr(self, name, None)) != default:
                state[name] = current
        for name, value in self.__dict__.items():
            if name in nosave or name in state:
                continue
            state[name] = value
        return state

    def _save_into(self, seen, ref):
        payload = {"@id": ref, "@type": _type_path(self.__class__)}
        for name, value in self._state_items().items():
            payload[name] = _freeze(value, seen)
        return payload

    def save(self, seen=None):
        tracker = {} if seen is None else seen
        ref, existed = _register_ref(tracker, self)
        if existed:
            return {"@ref": ref}
        return self._save_into(tracker, ref)


def freeze(value):
    return _freeze(value, {})
