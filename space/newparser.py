"""
New Parser Plan (Two-Stage, Simple, Intent-First)

Goals
- Keep parsing planning flexible and intellegent
- the text token "ubi" may resolve to a StdObj, or it may not, but it could
  provide us a hint.  in the case of `(words:tuple[str,...], obj:StdObj,
  words:tuple[str,...])`, we could split up at least 3 tokens by realizing one
  can resolve to a `StdObj`.
- We want to do all this argument resolution like once though, no repeat
  resolvers figuring out 'ubi' could be a StdObj
- We should be able to do everything we need in one parse() function without
  much abstraction; which turns quickly into a maintenence nightmare (see
  parser.dot for a rather cautionary tale of fanciful abstraction)

Core Concepts
- if we find a can_ that works, we consider filling the *matching* do function
- if we carefully order our method routing, we can safely select the first
  match rather than scoring from among dozens or hundreds of plans looking for
  a winner
- we score the possible match by saying: str < tuple[str,..] < StdObj < Living < Humanoid < Human
- What does this mean for a Weapon vs a Human? ... well... no plan is perfect

"""

import shlex, inspect, logging
from functools import lru_cache
from collections import namedtuple

from .find import find_verb
from .living import Living
from .stdobj import StdObj

log = logging.getLogger(__name__)


def parse(actor, input_text, parse_only=False):
    input_text = input_text.strip()
    if not input_text:
        return

    vtok, *tokens = shlex.shlex(input_text.strip())
    verbs = find_verb(vtok)
    routes = find_routes(actor, verbs)
    log.debug("-=: parse(%s, %s) verbs=%s", repr(actor), repr(input_text), repr(verbs))
    vmap = actor.location.map.visicalc_submap(me)
    objs = [o for o in self.vmap.objects] + me.inventory

    for route in sorted(routes, key=lambda x: x.score, reverse=True):
        log.debug("    route: %s", repr(route))
        # Here's were we do the needful. Using our available tokens, we try to
        # resolve them into the indicated types. The strategy and conversions
        # may be different from Route to Route though, so we need to leave that
        # list of tokens intact.
        #
        # 0. set_this_body(actor) before parsing and trying can-functions, we
        #    do have to remeber to clear this with set_this_body() though
        # 1. any 'str' we can just dump a token in there. done.
        # 2. tuple[str,...] should greedy fill with tokens, but we can borrow
        #    tokens from it later if we need.
        # 3. Any classes (StdObj, Living, etc) we can resolve using objs can be
        #    resolved with list_match(name, objs)
        # 4. the applicable can function will return (bool,dict)
        #    ok,ctx = route.can(**resolved_kwargs)
        # 5a. if ok is False, and this is the only route, we fall through to
        #     below and raise any exception in ctx['error']. ctx['error'] if
        #     given can be an Exception(), or simple text. otherwise, continue
        # 5b. if ok is True and parse_only is True and we have enough kwargs
        #     for the route.do function: return an ExecutionPlan, and be sure
        #     to clear set_this_body()
        # 5b. if ok is True and the resulting dict has enough kwargs for the
        #     route.do function, then we can execute it directly (be sure
        #     set_this_body(actor) is set and that we didn't clear it already).
        #     though, we do need to clear it again after executing the do fn.

    # end-for
    # 1. if we get here with no execution plan, we'll have to raise an E.ParseError(), probably.


class ExecutionPlan(namedtuple("XP", ["actor", "fn", "kw"])):
    def __call__(self):
        set_this_body(self.actor)
        # normally fn won't return anything, but we should store and return if
        # we can
        ret = fn(**self.kw)
        set_this_body()
        return ret


Route = namedtuple("R", ["verb", "can", "do", "score"])


class FnMap(namedtuple("FM", ["fn", "ihint"])):
    def __repr__(self):
        ihl = ", ".join(str(x) for x in self.ihint)
        return f"FM<{self.fn.__name__}({ihl})>"


class IntroHint(namedtuple("IH", ["aname", "type"])):
    def __repr__(self):
        if self.type in (str, None):
            return f"{self.aname}"
        t = self.type.__name__ if inspect.isclass(self.type) else self.type
        return f"{self.aname}:{t}"


@lru_cache
def introspect_hints(fn, do_mode=False):
    fas = inspect.getfullargspec(fn)
    todo = list(fas.args)
    if inspect.ismethod(fn):
        todo = todo[1:]
    if fas.varargs:
        todo.append(fas.varargs)
    todo += fas.kwonlyargs
    if do_mode:
        return tuple(IntroHint(item, None) for item in todo)
    ret = list()
    for item in todo:
        if item == fas.varargs:
            ret.append(IntroHint(item, tuple))
        if an := fas.annotations.get(item, False):
            ret.append(IntroHint(item, an))
        else:
            ret.append(IntroHint(item, implied_type(item)))
    return tuple(ret)


def list_match(name, objs):
    if isinstance(objs, (types.GeneratorType, list, tuple)):
        s = name.split(".", 1)
        if len(s) not in (1, 2):
            raise ValueError(f"len(name.split(., 1)) not in (1,2)")
        objs = [i for i in objs if i.parse_match(*s)]
        if objs:
            return objs
    return tuple()


def find_routes(actor, verbs):
    for verb in verbs:
        can_name = f"can_{verb.name}"
        for fn in [x for x in dir(actor) if x == can_name or x.startswith(f"{can_name}_")]:
            if do := getattr(actor, f"do_{fn[4:]}", False):
                can = getattr(actor, fn, False)
                can = FnMap(can, introspect_hints(can))
                do = FnMap(do, introspect_hints(do, do_mode=True))
                score = sum(type_rank(t) for a, t in can.ihint)
                yield Route(verb, can, do, score)


def implied_type(name):
    nl = name.lower()
    if nl.startswith("words") or nl.startswith("moves"):
        return tuple[str, ...]
    if nl.startswith("word") or nl.startswith("wrd"):
        return str
    if nl.startswith("liv") or nl.startswith("targ"):
        return Living
    if nl.startswith("obs") or nl.startswith("objs"):
        return tuple[StdObj, ...]
    if nl.startswith("ob"):
        return StdObj
    return str


def type_rank(tp):
    # Any arg counts as 1 in the final scoring, we just want our StdObj items
    # to be worth slightly more
    if issubclass(tp, StdObj):
        return 1 + (tp.sodval / 1000)
    return 1
