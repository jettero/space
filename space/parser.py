# coding: utf-8

import logging
import shlex

from .router import MethodArgsRouter
from .map.dir_util import is_direction_string
from .find import set_this_body, find_verb
from .util import deep_eq
import space.exceptions as E

log = logging.getLogger(__name__)

FILLED_SCORE = 1
CAN_DO_SCORE = 2


class PSNode:
    can_do = do_args = kid = fname = rhint = None

    def __init__(self, verb, *more):
        self.verb = verb
        self.next = self.__class__(*more) if more else None
        self.filled = dict()
        self._score = None

    def verb_state(self, verb):
        cur = self
        while cur.verb is not verb:
            if cur.next is None:
                raise E.InternalParseError(f"{verb} not found in {self}")
            cur = cur.next
        return cur

    def new_kid(self, verb):
        cur = self.verb_state(verb)
        while cur.kid is not None:
            cur = cur.kid
        cur.kid = self.__class__(cur.verb)
        self._score = None
        return cur.kid

    def add_rhint(self, verb, rhint):
        kid = self.new_kid(verb=verb)
        kid.rhint = rhint
        kid.fname = getattr(rhint.func, "__name__", str(rhint.func))
        self._score = None

    @property
    def short(self):
        if self.fname:
            return f"PSN[{self.score:.4f}]<{self.verb}:{self.fname}>"
        return f"PSN[{self.score:.4f}]<{self.verb}>"

    def __repr__(self):
        return self.short

    def __str__(self):
        if self.fname:
            sr = f"PSN[{self.score}]<{self.verb}:{self.fname}>"
            for hli in self.rhint.hlist:
                sr += f"\n  {hli}: {self.rhint.tokens.get(hli.aname)}"
                if hli.aname in self.filled:
                    sr += f" → {self.filled[hli.aname]}"
                else:
                    sr += " → ??"
        else:
            sr = f"PSN[{self.score}]<{self.verb}>"
        if self.kid is not None:
            sr += f"\n↓{str(self.kid)}"
        if self.next is not None:
            sr += f" )( {str(self.next)}"
        return sr

    def fill(self, objs):
        if self.rhint is not None:
            self.filled.update(self.rhint.fill(objs))
        if self.next is not None:
            self.next.fill(objs)
        if self.kid is not None:
            self.kid.fill(objs)
        self._score = None

    def evaluate(self):
        res = self.rhint.evaluate(**self.filled)
        # NOTE: can_do is the results of can_whatever(), which also returns
        # further args for do_whatever(); sometimes the do_args may contain an
        # error if we can't can_whatever()
        self.can_do, tmp_kwargs = res
        self.do_args = dict(**self.filled)
        self.do_args.update(tmp_kwargs)
        log.debug("[PSNode] %s.evaluate() → can_do=%s do_args=%s", self.short, self.can_do, self.do_args)
        self._score = None
        return res

    @property
    def score(self):
        if self._score is None:
            if self.can_do is True:
                self._score = CAN_DO_SCORE + (len(self.do_args) / 100)
                return self._score
            if self.rhint:
                for hli in self.rhint.hlist:
                    if hli.aname not in self.filled:
                        self._score = 0
                        return self.score
                self._score = FILLED_SCORE
                return self._score
            self._score = 0
            # I really want this below sub-scoring, but it's not worth it it
            # takes %prun o.me.shell.parser.parse(o.me, "") from 1.8 seconds to
            # 8 seconds just to get a partial score that's never going to decide a winner anyway
            #
            # self._score = max((x.score for x in self if x is not self), default=0) / 10
        return self._score

    @property
    def winner(self):
        r = self
        rs = r.score
        for item in (self.kid, self.next):
            try:
                w = item.winner
                ws = w.score
                if ws > rs:
                    r = w
            except AttributeError:
                pass
        return r

    @property
    def verbs(self):
        r = set()
        for item in self:
            v = item.verb.name
            if v not in r:
                yield item.verb
                r.add(v)

    def __iter__(self):
        yield self
        if self.kid is not None:
            yield from self.kid
        if self.next is not None:
            yield from self.next


class PState:
    winner = states = tokens = None

    def __init__(self, me, text_input):
        self.me = me
        self.orig = text_input
        self.tokens = shlex.split(text_input)
        self.vtok = self.tokens.pop(0) if text_input else ""
        fv = find_verb(self.vtok)
        if fv:
            self.states = PSNode(*fv)
        log.debug("[PState] new PState() vtok=%s (verbs=%s) tokens=%s", self.vtok, fv, self.tokens)
        self.filled = False
        self.vmap = me.location.map.visicalc_submap(me)
        self.objs = [o for o in self.vmap.objects] + me.inventory
        self.filled = False

    @property
    def high_score_state(self):
        return self.states.winner

    @property
    def high_score_verb(self):
        try:
            return self.high_score_state.verb
        except AttributeError:
            pass

    @property
    def high_score_args(self):
        try:
            return self.high_score_state.do_args
        except AttributeError:
            pass

    @property
    def error(self):
        try:
            if e := self.high_score_args.get("error"):
                return f'unable to "{self.orig}": {e}'
        except AttributeError:
            pass  # high_score_args is None probably
        return f'unable to understand "{self.orig}"'

    @property
    def short(self):
        r = f"{bool(self)}"
        hss = self.high_score_state
        if hss:
            r += f"/{hss.short}"
        return r

    def __repr__(self):
        return f"PState({self.short})"

    def __str__(self):
        self.fill()
        st = str(self.states).splitlines()
        st = "\n          ".join(st)
        kv = [
            f"PState:",
            f"me:     {self.me}",
            f"tokens: {self.tokens}",
            f"objs:   {self.objs}",
            f"states: {st}",
            f"bool:   {bool(self)}",
            f"winner: {self.winner.verb} → {self.winner.do_args}" if self.winner else "winner: no",
        ]
        return "\n  ".join(kv)

    def add_rhint(self, verb, rhint):
        log.debug("[PState] add_rhint(%s, %s)", verb.name, rhint)
        self.states.add_rhint(verb, rhint)
        self.filled = False

    def fill(self):
        if self.states is not None:
            if self.filled or not self.states:
                return
            log.debug("[PState] filling PState")
            self.filled = True
            self.states.fill(self.objs)

    def __iter__(self):
        if self.states is not None:
            self.fill()
            if self.states:
                for item in self.states:
                    yield item

    def iter_lb(self, lower_bound=1):
        for item in self:
            if item.score >= lower_bound:
                yield item

    @property
    def iter_filled(self):
        yield from self.iter_lb(lower_bound=1)

    @property
    def iter_can_do(self):
        yield from self.iter_lb(lower_bound=2)

    @property
    def iter_verbs(self):
        yield from self.states.verbs

    def __bool__(self):
        # XXX: we shouldn't be true when there's more than one winner with the high score
        # XXX: we shouldn't parse true when we have remaining unused tokens; we
        #      don't really track which self.tokens are consumed though
        # XXX: if we get an error (eg, attack stupid when stupid is too far away)
        #      then the parse should be true, but with an error
        return self.winner is not None and self.winner.can_do

    def __call__(self):
        if self:
            mr = MethodArgsRouter(self.me, f"do_{self.winner.verb.name}")
            set_this_body(self.me)  # we're active when we active the op-tree
            log.debug("[PState] invoking %s(**%s) with active living %s", mr, self.winner.do_args, self.me)
            mr(**self.winner.do_args)
            set_this_body()  # now we go back to sleep again
        else:
            log.error("tried to invoke an untrue pstate: %s", self)
            e = self.error
            if isinstance(e, Exception):
                raise E.ParseError(e) from e
            raise E.ParseError(e)


class Parser:
    def parse(self, me, text_input):
        log.debug('[Parser] parsing "%s" for %s', text_input, me)
        set_this_body(me)  # we're active when we parse
        if is_direction_string(text_input):
            text_input = f"move {text_input}"
            log.debug('[Parser] parsing "%s" instead', text_input)
        pstate = PState(me, text_input)
        if pstate.states is None:
            return pstate
        self.plan(pstate)
        self.evaluate(pstate)
        set_this_body()  # we're inactive until we execute the op-tree
        return pstate

    def plan(self, pstate):
        for verb in pstate.iter_verbs:
            mn = f"can_{verb.name}"
            mr = MethodArgsRouter(pstate.me, mn)
            log.debug("[Parser] plan(%s)", mn)
            for rhint in mr.hints():
                log.debug("[Parser] rhint=%s", rhint)
                tokens = dict()
                pos = 0
                end = len(pstate.tokens)
                for i, ihint in enumerate(rhint.hlist):
                    tlist0, *tlistr = ihint.tlist
                    log.debug('[Parser] ihint=%s tokens="%s"', ihint, " ".join(pstate.tokens[pos:]))
                    if ihint.aname not in tokens:
                        tokens[ihint.aname] = list()
                    if pos < end:
                        if tlist0 in (tuple, tuple[str, ...]):
                            x = len(rhint.hlist) - (i + 1)
                            l = len(pstate.tokens) - x
                            tokens[ihint.aname] += pstate.tokens[pos:l]
                            log.debug(
                                "XXXXXXXXXXXXX hlist=%s tokens[%s]=%s[%d:%d] => %s",
                                repr(rhint.hlist),
                                ihint.aname,
                                repr(pstate.tokens),
                                pos,
                                l,
                                tokens[ihint.aname],
                            )
                            pos += len(tokens[ihint.aname])
                        elif pos < end:
                            tokens[ihint.aname].append(pstate.tokens[pos])
                            pos += 1
                if pos < end:
                    log.debug("[Parser] rejecting rhint=%s due to extra unmatched tokens=%s", rhint, pstate.tokens[pos:])
                    continue
                rhint.tokens = pp_tok = verb.preprocess_tokens(pstate.me, **tokens)
                if log.isEnabledFor(logging.DEBUG) and not deep_eq(tokens, pp_tok):
                    log.debug("[Parser] preprocess tokens for %s; tokens=%s --> pp_tok=%s", rhint.fname, tokens, pp_tok)
                pstate.add_rhint(verb, rhint)

    def evaluate(self, pstate):
        log.debug("[Parser] evaluating pstate")
        for item in pstate.iter_filled:
            log.debug("[Parser] %s.evaluate()", item)
            item.evaluate()

        best = None
        best_score = None
        tied = set()
        for item in pstate.iter_can_do:
            if best is None or item.score > best_score:
                best = item
                best_score = item.score
                tied.clear()
            elif item.score == best_score:
                tied.add(item)

        if best is not None and not tied:
            log.debug("[Parser] %s is the winner", best)
            pstate.winner = best
        else:
            log.debug("[Parser] there were multiple winners (score: %s), we choose to not select one randomly.", best_score)
            choices = tuple(sorted(set(f"{it.verb.name}" for it in pstate.iter_can_do)))
            if choices:
                hs = pstate.high_score_state
                if hs is not None and not (hs.do_args and hs.do_args.get("error")):
                    msg = f"ambiguous: {', '.join(choices)}"
                    if hs.do_args is None:
                        hs.do_args = {"error": msg}
                    else:
                        hs.do_args["error"] = msg
        log.debug("[Parser] pstate evaluation result:\n%s", pstate)

    @property
    def words(self):
        # XXX: until we fix next words, just return the names of all the verbs we know about
        from space.verb import VERBS

        yield from VERBS.keys()

    def next_words(self, me, text_input):
        """try to guess what words will fit next"""
        # XXX: we only consider the very first token and even that breaks if
        # the word is directions 'sSW3s', needs work
        pstate = self.parse(me, text_input)
        for v in pstate.iter_verbs:
            yield from v.nick
