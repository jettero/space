# coding: utf-8

import re
import logging
from .util import weakify

log = logging.getLogger(__name__)

class OwnershipError(TypeError):...
class LocationError(TypeError):...

# all mud objects get this ancestor
# most objects you can pick up or put in a room should also get Containable
# you're probably looking for space/stdobj.py
class baseobj:  # pylint: disable=invalid-name
    _owner = _tokens = _location = None

    def strongify(self):
        # XXX: I was having a Heisenbug around ReferenceError where literally
        # every other run of pytest t/test_verb_open_close.py was giving a
        # ReferenceError vs passing normally.
        #
        # NOTE: later, this turned out to be a set_this_body() bug in the
        # parser. if you call the below positional_adjectives and you fail to
        # set_this_body() first, it can sometimes point to a weakref that
        # nolonger exists during a pytest where you repeatedly build and
        # teardown a_map and objs (t.troom.gen_troom)
        #
        # I like having this around for now, so I haven't removed it, but the
        # AI keeps trying to use it inappropriately, so it may be just a matter
        # of time.
        #
        # Hey, talkin' to you codex: stop using this.
        return self

    @property
    def location(self):
        """
        The location of a thing is the object that literally contains it: the
        bag it's in, the hand slot of a Living, the floor, etc.

        It is somewhat related to the owner of the object, but it's not
        necessarily the same thing.

        The location is always stored as a weak-reference. Whatever container
        holds the object has the strong ref.
        """
        return self._location

    @location.setter
    def location(self, v):
        if v is None:
            self._location = None
            return
        from space.container import Container
        if isinstance(v, Container):
            self._location = weakify(v)
        else:
            raise LocationError(f"given {v}, but locations should be containers")
        try:
            if (h := self.haver) is not None:
                self.owner = h
        except OwnershipError:
            pass

    @property
    def haver(self):
        """
        Ownership may not quite follow location, but this does. This is the Living location of the object -- even if nested.
        """
        try:
            from space.living import Living
            o = self._location
            while o is not None:
                if isinstance(o, Living):
                    return o
                o = o._location
        except (ReferenceError, AttributeError):
            pass

    @property
    def owner(self):
        """
        The owner of the object, if set, is the Living that owns the object.
        The owner is always a Living or None.  Owners are always a
        weak-reference, and so-weakened can become None due to a user logging
        out or otherwise vanishing.

        The owner isn't neccissarily the haver, use .haver to see who's
        currently holding it a thing.
        """
        if self._owner is not None:
            return self._owner
        return self.haver

    @owner.setter
    def owner(self, v):
        if v is None:
            self._owner = None
            return
        from space.living import Living
        if isinstance(v, Living):
            self._owner = weakify(v)
        else:
            raise OwnershipError(f"given {v}, but owners should be alive")

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

    @property
    def tokens(self):
        if self._tokens is None:
            self.tokens = self._tokenize()
        return set(self._tokens)

    @tokens.setter
    def tokens(self, v):
        self._tokens = set(v)

    def parse_can(self, method, **kw):
        return MethodNameRouter(self, f"can_{method}")(**kw)

    def parse_do(self, method, **kw):
        MethodNameRouter(self, f"do_{method}")(**kw)

    def parse_match(self, *names, pos_adj=True):
        log.debug("%s.parse_match(%s)", self, names)

        if len(names) == 1 and isinstance(names[0], (list, tuple)):
            names = names[0]
        if not names:
            return False
        if m := re.match(r"^(.+)\.(.+)$", names[0]):
            name[0], id1 = m.groups()
            id2 = self.id
            if not (id2.startswith(id1) or id2.endswith(id1)):
                return False

        tok = self.tokens
        if pos_adj:
            from space.map.dir_util import positional_adjectives

            tok.update(positional_adjectives(self))

        for n in names:
            matched = False
            for t in tok:
                if len(t) == 1 and t == n:
                    matched = True
                    break
                if t.startswith(n.lower()):
                    matched = True
                    break
            if not matched:
                return False

        return True
