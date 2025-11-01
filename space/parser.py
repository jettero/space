import shlex, inspect, logging, types
from functools import lru_cache
from collections import namedtuple

from .find import find_verb, set_this_body
import space.exceptions as E
from .living import Living
from .stdobj import StdObj
from .util import get_introspection_hints, get_introspection_names

log = logging.getLogger(__name__)


def parse(actor, input_text, parse_only=False):
    input_text = input_text.strip()
    if not input_text:
        return

    parts = shlex.split(input_text)
    if not parts:
        return
    vtok, *tokens = parts
    verbs = find_verb(vtok)  #    ↓ often a weakproxy, so we call __repr__()
    log.debug("-=: parse(%s, %s) verbs=%s", actor.__repr__(), repr(input_text), repr(verbs))
    vmap = actor.location.map.visicalc_submap(actor)
    objs = [o for o in vmap.objects] + actor.inventory

    pop_to_args = None

    errors = list()
    for route in find_routes(actor, verbs):
        if len(tokens) < len(route.can.ihint):
            log.debug("pre-rejecting %s: not enough tokens to fill all ihints", route)
            filled = False
            continue

        log.debug("considering route=%s", repr(route))
        filled = True
        max_ino = len(route.can.ihint) - 1
        remaining = list(tokens)
        already_filled = set()  # if we steal a token, we skip this ihint in the mainloop
        max_fill = dict()  # and then we limit the earlier variadic to this many tokens
        kw = {}
        if len(remaining) > len(route.can.ihint):
            for i, iih in enumerate(route.can.ihint):
                if iih.multi:
                    for j, jih in [(j, route.can.ihint[j]) for j in range(i + 1, len(route.can.ihint))]:
                        if issubclass(jih.type, StdObj):
                            for k, kih in [(k, route.can.ihint[k]) for k in range(j + 1, len(route.can.ihint))]:
                                if kih.multi:
                                    # if we have more than enough tokens and more than one multi
                                    # hint we can present more than one token choice to any obj
                                    # between them
                                    start = j
                                    stop = start + len(remaining) - len(route.can.ihint) + 1
                                    log.debug(
                                        "early token stealing <%s,%s,%s> // choices=%s[%d:%d] => %s",
                                        iih,
                                        jih,
                                        kih,
                                        remaining,
                                        start,
                                        stop,
                                        remaining[start:stop],
                                    )
                                    for b in range(start, stop):
                                        if m := [o for o in list_match(remaining[b], objs) if isinstance(o, jih.type)]:
                                            log.debug('stealing remaining[%d] token "%s" for %s', b, remaining[b], jih)
                                            kw[jih.name] = m[0]
                                            remaining.pop(b)
                                            already_filled.add(j)
                                            max_fill[i] = b
                                            break
        for ino, ih in enumerate(route.can.ihint):
            if ino in already_filled:
                log.debug("skipping ihint=%s, already filled earlier", ih)
                continue
            log.debug("considering ihint=%s", repr(ih))
            if not remaining:
                # XXX: we shouldn't really need this clause if we just check beforehand to
                # see if we have enough tokens
                log.debug("rejecting %s: unable to fill ihint=%s, ran out of tokens", repr(route), repr(ih))
                filled = False
                break
            if ih.variadic:
                # this pretty much has to be the last arg, so we can just slurp the rest
                # of the tokens
                kw[ih.name] = tuple(remaining)
                pop_to_args = ih.name
                remaining = []
                continue
            if ih.type in (str, None):
                kw[ih.name] = remaining.pop(0)
                continue
            if ih.multi is str:
                if b := max_fill.get(ino):
                    log.debug("filling %s::%s with max_fill endpoint %d", route.name, ih, b)
                    kw[ih.name] = fval = tuple(remaining[:b])
                    remaining = remaining[b:]
                    log.debug("filling result kw=%s remaining=%s", fval, remaining)
                    continue
                ir = max_ino - ino
                if ir > 0:
                    log.debug("filling %s::%s ino=%d/%d ir=%d remaining=%s", route.name, ih, ino, max_ino, ir, remaining)
                    kw[ih.name] = fval = tuple(remaining[:-ir])
                    remaining = remaining[-ir:]
                    log.debug("filling result kw=%s remaining=%s", fval, remaining)
                else:
                    kw[ih.name] = tuple(remaining)
                    remaining = []
                continue

            # XXX: we really need a case here (or maybe the loop above) for
            # tuple[cls,...] where cls is a subclass of StdObj it'd look a lot
            # like the below and a little like tuple[str, ...] above

            if issubclass(ih.type, StdObj):
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

        if remaining:
            log.debug("rejecting %s: failed to use all tokens (remaining: %s)", repr(route), repr(remaining))
            continue

        if not filled:
            log.debug("rejecting %s: unable to fill args with available tokens", repr(route))
            continue

        set_this_body(actor)
        kw = route.verb.preprocess_tokens(actor, **kw)
        args = kw.pop(pop_to_args) if pop_to_args in kw else tuple()
        log.debug("running %s.can.fn(%s, %s)", repr(route), repr(args), repr(kw))
        ok, ctx = route.can.fn(*args, **kw)
        set_this_body()
        log.debug("can.fn result: ok=%s ctx=%s", repr(ok), repr(ctx))
        if ok:
            try:
                merged = {ih.name: ctx[ih.name] for ih in route.do.ihint}
                filled = True
            except KeyError as e:
                log.error("%s is broken, can.fn didn't provide %s arg for do.fn.", repr(route), e)
                filled = False
            if not filled:
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
        # We absolutely must present ExecutionPlan.error so the shell can use it.
        return ExecutionPlan(actor, _parse_error, {"error": msg})
    raise E.ParseError(msg)


def _parse_error(error="unknown", **kw):
    raise E.ParseError(error)


class ExecutionPlan(namedtuple("XP", ["actor", "fn", "kw"])):
    def __call__(self):
        log.debug("running %s", repr(self))
        set_this_body(self.actor)
        # normally fn won't return anything, but we should store and return if we can
        ret = self.fn(**self.kw)
        set_this_body()
        return ret

    def __repr__(self):
        return f"XP<{self.actor}.{self.fn.__name__}({self.kw!r})>"

    @property
    def error(self):
        return self.kw.get("error", "unknown")

    def __bool__(self):
        return not (self.fn is _parse_error)


class Route(namedtuple("R", ["verb", "can", "do", "score"])):
    @property
    def name(self):
        return self.can.fn.__name__[4:]


class FnMap(namedtuple("FM", ["fn", "ihint"])):
    def __repr__(self):
        ihl = ", ".join(str(x) for x in self.ihint)
        return f"FM<{self.fn.__name__}({ihl})>"


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
    return tuple(sorted(_find_routes(actor, verbs), key=lambda x: x.score, reverse=True))


def _find_routes(actor, verbs):
    if isinstance(verbs, str):
        verbs = find_verb(verbs)
    for verb in verbs:
        can_name = f"can_{verb.name}"
        for fn in [x for x in dir(actor) if x == can_name or x.startswith(f"{can_name}_")]:
            if do := getattr(actor, f"do_{fn[4:]}", False):
                can = getattr(actor, fn, False)
                can = FnMap(can, get_introspection_hints(can, imply_type_callback=implied_type))
                do = FnMap(do, get_introspection_names(do))
                score = sum(type_rank(x) for x in can.ihint)
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


def type_rank(ih):
    score = 1.0
    if issubclass(ih.type, StdObj):
        score += ih.type.stdobj_dist_val / 1000
    if ih.multi:
        score -= 0.000_001
    return score
