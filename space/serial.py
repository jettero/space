# coding: utf-8

import inspect
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

    def save(self, hide_class=False, unfiltered=False, recurse=True, inject=None, override=None):
        cls = self.__class__
        nam = f"{cls.__module__}.{cls.__name__}"

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


PASS_FILTER = (*PASS_FILTER, Serial)
