# coding: utf-8

import inspect
import types

# def dig_class(base, pass_filter=(int,str,float), stop_filter=(property, classmethod, types.FunctionType, types.MethodType, )):
#     if not inspect.isclass(base):
#         base = base.__class__
#     ret = dict()
#     for c in base.mro():
#         ret.update({ k:v for k,v in c.__dict__.items() if not k.startswith('__') and isinstance(v, pass_filter) and not isinstance(v, stop_filter) })
#     return ret

# dig_class(o.me)

PASS_FILTER = (int, str, float)
STOP_FILTER = (property, classmethod, types.FunctionType, types.MethodType)


class Serial:
    @classmethod
    def get_filters(cls):
        try:
            pass_filter = c.__pass_filter__
        except:
            pass_filter = PASS_FILTER
        try:
            stop_filter = c.__stop_filter__
        except:
            stop_filter = STOP_FILTER
        try:
            save = c.__save__
        except:
            save = list()
        try:
            nosave = c.__nosave__
        except:
            nosave = list()
        return pass_filter, stop_filter, save, nosave

    @classmethod
    def default_serial(cls, merge=True, omit_class=True):
        """
        enumerate all the fields we need to save. by default, we merge one big
        list of k,v pairs together and return a dict. specifying merge=False
        triggers a list return and specifying omit_class=False causes the
        return data to be labled by origin-class (although, in the merge case,
        this will just be the top level class name).
        """
        s = set()
        ret = dict() if merge else list()
        for c in reversed(cls.mro()):
            pass_filter, stop_filter, save, nosave = cls.get_filters()
            dat = {
                k: v
                for k, v in c.__dict__.items()
                if k in save
                or (
                    k not in nosave
                    and not k.startswith("__")
                    and isinstance(v, pass_filter)
                    and not isinstance(v, stop_filter)
                )
            }
            if dat:
                if merge:
                    ret.update(dat)
                elif omit_class:
                    ret.append(dat)
                else:
                    ret.append({f"{c.__module__}.{c.__name__}": dat})
        if merge and not omit_class:
            return {f"{cls.__module__}.{cls.__name__}": ret}
        return ret

    def save(self):
        ret = dict()
        for k, v in self.default_serial(merge=True, omit_class=True).items():
            if (ga := getattr(self, k, None)) != v:
                ret[k] = ga
        cls = self.__class__
        return {f"{cls.__module__}.{cls.__name__}": ret}
