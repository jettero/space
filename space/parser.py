# coding: utf-8

import logging
import shlex

from .verb import load_verbs
from .router import MethodArgsRouter
import space.exceptions as E

log = logging.getLogger(__name__)

VERBS = None
def find_verb(x):
    global VERBS
    if not VERBS:
        VERBS = { v.name: v for v in load_verbs() }
    if not x:
        return VERBS.values()
    x = x.lower()
    v = VERBS.get(x)
    if v:
        return [ v ]
    return [ v for n,v in VERBS.items() if v.match(x) ]

class TargetError(SyntaxError):
    pass

class PSNode:
    can_do = do_args = kid = fname = rhint = None

    def __init__(self, verb, *more):
        self.verb = verb
        self.next = self.__class__(*more) if more else None
        self.filled = dict()

    def verb_state(self, verb):
        cur = self
        while cur.verb is not verb:
            if cur.next is None:
                raise Exception(f'{verb} not found in {self}')
            cur = cur.next
        return cur

    def new_kid(self, verb):
        cur = self.verb_state(verb)
        while cur.kid is not None:
            cur = cur.kid
        cur.kid = self.__class__(cur.verb)
        return cur.kid

    def add_rhint(self, verb, rhint):
        kid = self.new_kid(verb=verb)
        kid.rhint = rhint
        kid.fname = getattr(rhint.func, '__name__', str(rhint.func))

    @property
    def short(self):
        if self.fname:
            return f'PSN[{self.score}]<{self.verb}:{self.fname}>'
        return f'PSN[{self.score}]<{self.verb}>'

    def __repr__(self):
        return self.short

    def __str__(self):
        if self.fname:
            sr = f'PSN[{self.score}]<{self.verb}:{self.fname}>'
            for hli in self.rhint.hlist:
                sr += f'\n  {hli}: {self.rhint.tokens.get(hli.aname)}'
                if hli.aname in self.filled:
                    sr += f' → {self.filled[hli.aname]}'
                else:
                    sr += ' → ??'
        else:
            sr = f'PSN[{self.score}]<{self.verb}>'
        if self.kid is not None:
            sr += f'\n {str(self.kid)}'
        if self.next is not None:
            sr += f'\n{str(self.next)}'
        return sr

    def fill(self, objs):
        if self.rhint is not None:
            self.filled.update(self.rhint.fill(objs))
        if self.next is not None:
            self.next.fill(objs)
        if self.kid is not None:
            self.kid.fill(objs)

    def evaluate(self):
        res = self.rhint.evaluate(**self.filled)
        self.can_do, tmp_kwargs = res
        self.do_args = dict(**self.filled)
        self.do_args.update(tmp_kwargs)
        log.debug('[PSNode] %s.evaluate() → can_do=%s do_args=%s', self.short, self.can_do, self.do_args)
        return res

    @property
    def score(self):
        if self.can_do is True:
            return 2 + (len(self.do_args)/100)
        if self.rhint:
            for hli in self.rhint.hlist:
                if hli.aname not in self.filled:
                    return 0
            return 1
        scores = [ x.score for x in self if x is not self ]
        if scores:
            return max(scores) / 10
        return 0

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
        self.tokens = shlex.split(text_input)
        self.vtok   = self.tokens.pop(0) if text_input else ''
        fv = find_verb(self.vtok)
        if fv:
            self.states = PSNode(*fv)
        log.debug('[PState] new PState() vtok=%s (verbs=%s) tokens=%s', self.vtok, fv, self.tokens)
        self.filled = False
        self.vmap = me.location.map.visicalc_submap(me)
        self.objs = [ o for o in self.vmap.objects ]
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
            return self.high_score_args.get('error')
        except (AttributeError, TypeError):
            pass

    @property
    def short(self):
        r = f'{bool(self)}'
        hss = self.high_score_state
        if hss:
            r += f'/{hss.short}'
        return r

    def __repr__(self):
        return f'PState({self.short})'

    def __str__(self):
        self.fill()
        st = str(self.states).splitlines()
        st = '\n          '.join(st)
        kv = [
            f'PState:',
            f'me:     {self.me}',
            f'tokens: {self.tokens}',
            f'objs:   {self.objs}',
            f'states: {st}',
            f'bool:   {bool(self)}',
            f'winner: {self.winner.verb} → {self.winner.do_args}' if self.winner else 'winner: no',
        ]
        return '\n  '.join(kv)

    def add_rhint(self, verb, rhint):
        log.debug('[PState] add_rhint(%s, %s)', verb.name, rhint)
        self.states.add_rhint(verb, rhint)
        self.filled = False

    def fill(self):
        if self.states is not None:
            if self.filled or not self.states:
                return
            log.debug('[PState] filling PState')
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
        # XXX: we shouldn't parse true when we have remaining unused tokens
        # XXX: if we get an error (eg, attack stupid when stupid is too far away)
        #      then the parse should be true, but with an error
        return self.winner is not None and self.winner.can_do

    def __call__(self):
        if self:
            mr = MethodArgsRouter(self.me, f'do_{self.winner.verb.name}')
            self.me.active = True
            log.debug("[PState] invoking %s(**%s) with active living %s", mr, self.winner.do_args, self.me)
            mr(**self.winner.do_args)
            self.me.active = False
        else:
            log.error("tried to invoke an untrue pstate: %s", self)
            e = self.error
            if isinstance(e, Exception):
                raise e

class Parser:
    def parse(self, me, text_input):
        log.debug('[Parser] parsing "%s" for %s', text_input, me)
        pstate = PState(me, text_input)
        if pstate.states is None:
            from space.map.dir_util import is_direction_string
            if is_direction_string(text_input):
                text_input = f'move {text_input}'
                log.debug('[Parser] parsing "%s" instead', text_input)
                pstate = PState(me, text_input)
        if pstate.states is None:
            return pstate
        self.plan(pstate)
        self.evaluate(pstate)
        return pstate

    def next_words(self, me, text_input):
        ''' try to guess what words will fit next '''
        # XXX: we only consider the very first token, needs work
        pstate = self.parse(me, text_input)
        for v in pstate.iter_verbs:
            yield from v.nick

    def plan(self, pstate):
        for verb in pstate.iter_verbs:
            mr = MethodArgsRouter(pstate.me, f'can_{verb.name}')
            for rhint in mr.hints():
                log.debug("[Parser] rhint=%s", rhint)
                tokens = dict()
                pos = 0
                end = len(pstate.tokens)
                for ihint in rhint.hlist:
                    if ihint.aname not in tokens:
                        tokens[ihint.aname] = list()
                    if pos < end:
                        if ihint.tlist[0] == tuple:
                            tokens[ihint.aname] += pstate.tokens[pos:]
                            pos = end
                        elif pos < end:
                            tokens[ihint.aname].append(pstate.tokens[pos])
                            pos += 1
                pp_tok = verb.preprocess_tokens(pstate.me, **tokens)
                log.debug('[Parser] preprocess tokens for %s; %s --> %s', rhint, tokens, pp_tok)
                rhint.tokens = pp_tok
                pstate.add_rhint(verb, rhint)

    def evaluate(self, pstate):
        log.debug('[Parser] evaluating pstate')
        for item in pstate.iter_filled:
            log.debug('[Parser] %s.evaluate()', item)
            item.evaluate()

        for item in sorted(pstate.iter_can_do, key=lambda x: 0 - x.score):
            log.debug('[Parser] %s is the winner', item)
            pstate.winner = item
            break
        log.debug('[Parser] pstate evaluation result:\n%s', pstate)
