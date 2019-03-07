# coding: utf-8

import logging
import shlex

from .verb import load_verbs
from .router import MethodArgsRouter

log = logging.getLogger(__name__)

VERBS = None
def find_verb(x):
    global VERBS
    if not VERBS:
        VERBS = { v.name: v for v in load_verbs() }
    x = x.lower()
    v = VERBS.get(x)
    if v:
        return [ v ]
    return [ v for n,v in VERBS.items() if n.startswith(x) ]

class TargetError(SyntaxError):
    pass

class PSNode:
    kid = fname = rhint = None

    def __init__(self, verb, *more):
        self.verb = verb
        self.next = self.__class__(*more) if more else None
        self.filled = dict()

    def new_kid(self, verb=None):
        cur = self
        if verb is not None:
            while cur.verb is not verb:
                if cur.next is None:
                    raise Exception(f'{verb} not found in {self}')
                cur = cur.next
        while cur.kid is not None:
            cur = cur.kid
        cur.kid = self.__class__(self.verb)
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
        if self.kid  is not None:
            sr += f'\n {repr(self.kid)}'
        if self.next is not None:
            sr += f'\n{repr(self.next)}'
        return sr

    def fill(self, objs):
        if self.rhint is not None:
            self.filled.update(self.rhint.fill(objs))
        if self.next is not None:
            self.next.fill(objs)
        if self.kid is not None:
            self.kid.fill(objs)

    def evaluate(self):
        self.can_do, self.do_args = self.rhint.evaluate(**self.filled)
        log.debug('%s evaluate(): can_do=%s do_args=%s', self.short, self.can_do, self.do_args)

    @property
    def score(self):
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
        for item in (self.kid, self.next):
            try:
                w = item.winner
                if w.score > r.score:
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
    states = tokens = None

    def __init__(self, me, text_input):
        self.me = me
        self.init(text_input)
        self.vmap = me.location.map.visicalc_submap(me)
        self.objs = [ o for o in self.vmap.objects ]
        self.filled = False
        self.eval_ok = list()

    def __repr__(self):
        self.fill()
        st = repr(self.states).splitlines()
        st = '\n          '.join(st)
        kv = [
            f'PState:',
            f'me:     {self.me}',
            f'tokens: {self.tokens}',
            f'objs:   {self.objs}',
            f'states: {st}',
        ]
        return '\n  '.join(kv)

    def init(self, text_input):
        self.tokens = shlex.split(text_input)
        self.states = PSNode(*find_verb(self.tokens.pop(0)))
        self.filled = False

    def add_rhint(self, verb, rhint):
        log.debug('add_rhint(%s, %s)', verb.name, rhint)
        self.states.add_rhint(verb, rhint)
        self.filled = False

    def fill(self):
        if self.filled or not self.states:
            return
        log.debug('filling PState')
        self.filled = True
        self.states.fill(self.objs)

    def __iter__(self):
        self.fill()
        if self.states:
            for item in self.states:
                yield item

    @property
    def final(self):
        self.fill()
        return self.states.winner

    @property
    def verb(self):
        return self.final.verb

class Parser:
    def parse(self, me, text_input):
        pstate = PState(me, text_input)
        if not pstate.verb:
            from space.map.dir_util import is_direction_string
            if is_direction_string(text_input):
                pstate.init(f'move {text_input}')
        log.debug('parse(%s, "%s"): %s', me, text_input, pstate)
        self.plan(pstate)
        log.debug('after plan(): %s', pstate)
        self.evaluate(pstate)
        return pstate

    def evaluate(self, pstate, lower_bound=1):
        for i in pstate:
            if i.score >= lower_bound:
                log.debug('%s passed lower_bound=%d', i.short, lower_bound)
                i.evaluate()

    def plan(self, pstate):
        for verb in pstate.states.verbs:
            log.debug('plan() verb=%s', verb)
            mr = MethodArgsRouter(pstate.me, f'can_{verb.name}')
            for rhint in mr.hints():
                log.debug(" rhint=%s", rhint)
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
                rhint.tokens = verb.preprocess_tokens(pstate.me, **tokens)
                pstate.add_rhint(verb, rhint)
        return pstate
