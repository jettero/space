# coding: utf-8

import inspect
import types
import weakref

# *_FILTER quirks:
# isinstance(True, int) -> True -- (wierd)

PASS_FILTER = (int, str, float, list, tuple)
STOP_FILTER = (property, classmethod, types.FunctionType, types.MethodType, weakref.ProxyType)


class Serial:
    def save(self, hide_class=False, unfiltered=False, recurse=True, inject=None, override=None):
        cls = self.__class__
        nam = f"{cls.__module__}.{cls.__name__}"

        if override:
            if hide_class:
                return override
            return {nam: override}

        obj_d = self.__dict__
        cls_d = cls.__dict__

        first_pass = {k: (cls_d.get(k), obj_v, isinstance(obj_v, Serial)) for k, obj_v in obj_d.items()}
        if unfiltered:
            return first_pass  # this is likely only any good for debugging

        save = {
            k: (obj_v.save() if recurse and isserial else obj_v)
            for k, (cls_v, obj_v, isserial) in first_pass.items()
            if (
                not isinstance(cls_v, STOP_FILTER)
                and not isinstance(obj_v, STOP_FILTER)
                and (isinstance(obj_v, PASS_FILTER) or isserial)
                and cls_v != obj_v  # but we don't want to save any defaults
            )
        }

        if inject:
            # presuambly a child class passed this in via super().save(inject=dict())
            save.update(inject)

        if hide_class:
            return save
        return {nam: save}
