# coding: utf-8

import logging
import weakref

log = logging.getLogger(__name__)


# all mud objects get this ancestor
# most objects you can pick up or put in a room should also get Containable
# you're probably looking for space/stdobj.py
class baseobj:  # pylint: disable=invalid-name
    _location = None

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, v):
        if v is not None:
            v = weakref.proxy(v)
        self._location = v

    @property
    def owner(self):
        try:
            o = self._location
            from space.living import Living

            while o is not None and not isinstance(o, Living):
                o = o._location
            return o
        except AttributeError:
            pass

    @owner.setter
    def owner(self, v):
        from space.living import Living

        if isinstance(v, Living):
            self.location = v
            return
        raise ValueError(f"owners should be alive")

    @property
    def id(self):
        return f"{id(self):02x}"

    @property
    def cname(self):
        return self.__class__.__name__

    def has_shell(self):
        return False

    def __repr__(self):
        r = self.cname
        sf = str(self)
        if sf != r:
            r += f"<{sf}>"
        return f"{r}#{self.id}"

    def __str__(self):
        try:
            l = self.long
            if l:
                return l
        except AttributeError:
            pass
        return self.cname

    short = long = abbr = None

    def _tokenize(self):
        r = set()
        for i in ("short", "long", "cname"):
            if a := getattr(self, i, None):
                for s in a.split():
                    t = s.strip(", ").lower()
                    r.add(t)
        if a := getattr(self, "abbr", None):
            r.add(a)
        return r - set([None, ""])

    # def parse_can(self, method, **kw):
    #     pc_ret = [True, {k: v for k, v in kw.items() if v is not None}]

    #     def cb(fname, ret):
    #         log.debug("parse_can.cb< fname=%s pc_ret=%s >", fname, tuple(pc_ret))
    #         if not isinstance(ret, tuple) or len(ret) != 2:
    #             raise ValueError(f"invalid return parse_can.cb< ({self}).{fname}() >: {ret}")
    #         pc_ret[0] = pc_ret[0] and ret[0]
    #         if isinstance(ret[1], dict):
    #             pc_ret[1].update({k: v for k, v in ret[1].items() if v is not None})
    #         if not pc_ret[0]:
    #             log.debug("denying parse_can.cb< (%s).%s() >", self, fname)
    #             return False
    #         log.debug("  … pc_ret=%s", tuple(pc_ret))

    #     MethodNameRouter(self, f"can_{method}", multi=True, callback=cb)(**kw)
    #     return tuple(pc_ret)

    def parse_can(self, method, **kw):
        return MethodNameRouter(self, f"can_{method}")(**kw)

    def parse_do(self, method, **kw):
        MethodNameRouter(self, f"do_{method}")(**kw)

    def parse_match(self, txt, id_=None):
        log.debug("%s .parse_match(txt=%s, id=%s)", self, txt, id_)
        if id_ is not None:
            id1 = id_.lower()
            id2 = self.id
            if not (id2.startswith(id1) or id2.endswith(id1)):
                return False
        try:
            tok = self.tokens
        except AttributeError:
            tok = self._tokenize()

        for t in tok:
            if len(t) == 1 and t == txt:
                # case sensitive abbr match
                return True
            if t.startswith(txt.lower()):
                return True
        return False
