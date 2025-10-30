import shlex, inspect, logging, types
from functools import lru_cache
from collections import namedtuple

from .find import find_verb, set_this_body
import space.exceptions as E
from .living import Living
from .stdobj import StdObj

log = logging.getLogger(__name__)


def parse(actor, input_text, parse_only=False):
    input_text = input_text.strip()
    if not input_text:
        return

    parts = shlex.split(input_text)
    if not parts:
        return
    vtok, *tokens = parts
    verbs = find_verb(vtok)
    routes = find_routes(actor, verbs)
    log.debug("-=: parse(%s, %s) verbs=%s", repr(actor), repr(input_text), repr(verbs))
    vmap = actor.location.map.visicalc_submap(actor)
    objs = [o for o in vmap.objects] + actor.inventory

    errors = list()
    for route in sorted(routes, key=lambda x: x.score, reverse=True):
        log.debug("considering route=%s", repr(route))
        remaining = list(tokens)
        kw = {}
        args = []
        filled = True
        for ih in route.can.ihint:
            log.debug("considering ihint=%s", repr(ih))
            if not remaining:
                log.debug("rejecting %s: unable to fill ihint=%s, ran out of tokens", repr(route), repr(ih))
                filled = False
                break
            if ih.type in (str, None):
                kw[ih.name] = remaining.pop(0)
                continue
            if ih.type is ...:
                args.extend(remaining)
                remaining = []
                continue
            if ih.type is tuple or ih.type == tuple[str, ...]:
                kw[ih.name] = tuple(remaining)
                remaining = []
                continue
            if inspect.isclass(ih.type) and issubclass(ih.type, StdObj):
                if m := [o for o in list_match(remaining[0], objs) if isinstance(o, ih.type)]:
                    kw[ih.name] = m[0]
                    remaining.pop(0)
                    continue
                log.debug("rejecting %s: unable to fill ihint=%s, no obj", repr(route), repr(ih))
                filled = False
                break
            log.debug("rejecting %s: unable to fill ihint=%s due to unknown type", repr(route), repr(ih))
            filled = False
            break
        ####################### end-route-ihint-for

        if not filled:
            log.debug("rejecting %s: unable to fill args with available tokens", repr(route))
            continue

        log.debug("running %s.can.fn(%s, %s)", repr(route), repr(args), repr(kw))
        set_this_body(actor)
        ok, ctx = route.can.fn(*args, **kw)
        set_this_body()
        log.debug("can.fn result: ok=%s ctx=%s", repr(ok), repr(ctx))
        if ok:
            try:
                merged = {a: ctx[a] for a, _ in route.do.ihint}
                filled = True
            except KeyError:
                filled = False
            if not filled:
                log.error("%s is broken (filled=%s).", repr(route), repr(merged))
                raise E.ParseError(f'internal error with "{route.verb.name}" verb')
            if parse_only:
                return ExecutionPlan(actor, route.do.fn, merged)
            set_this_body(actor)
            ret = route.do.fn(**merged)
            set_this_body()
            return ret
        if "error" in ctx:
            errors.append(ctx["error"])
        ############################# end-route-for

    msg = errors[0] if len(errors) == 1 else f"unable to understand {input_text!r}"
    if parse_only:

        def error(error="unknown", **kw):
            raise E.ParseError(error)

        return ExecutionPlan(actor, error, {"error": msg})
    raise E.ParseError(msg)


class ExecutionPlan(namedtuple("XP", ["actor", "fn", "kw"])):
    def __call__(self):
        set_this_body(self.actor)
        # normally fn won't return anything, but we should store and return if we can
        ret = self.fn(**self.kw)
        set_this_body()
        return ret

    def __repr__(self):
        return f"XP<{self.actor}.{self.fn.__name__}({self.kw!r})>"


Route = namedtuple("R", ["verb", "can", "do", "score"])


class FnMap(namedtuple("FM", ["fn", "ihint"])):
    def __repr__(self):
        ihl = ", ".join(str(x) for x in self.ihint)
        return f"FM<{self.fn.__name__}({ihl})>"


class IntroHint(namedtuple("IH", ["name", "type"])):
    def __repr__(self):
        v = "*" if self.type is ... else ""
        if self.type in (str, None):
            return f"{v}{self.name}"
        t = self.type.__name__ if inspect.isclass(self.type) else self.type
        return f"{v}{self.name}:{t}"


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
            ret.append(IntroHint(item, ...))
            continue
        if an := fas.annotations.get(item):
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
    if inspect.isclass(tp) and issubclass(tp, StdObj):
        return 1 + (tp.sodval / 1000)
    return 1
