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

class PState:
    class Node:
        def __init__(self, verb, *more):
            self.verb = verb
            self.next = self.__class__(*more) if more else None
            self.kid  = None
            self.fname = self.func = self.tokens = None

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

        def add_ftok(self, func, _verb=None, **tokens):
            kid = self.new_kid(verb=_verb)
            kid.fname = getattr(func, '__name__', str(func))
            kid.func = func
            kid.tokens = tokens

        def __repr__(self):
            if self.fname:
                hl = ','.join([f'{k}={v}' for k,v in self.tokens.items()])
                sr = f'PSN<{self.verb}:{self.fname}({hl})>'
            else:
                sr = f'PSN<{self.verb}>'
            if self.kid  is not None:
                sr += f'\n {repr(self.kid)}'
            if self.next is not None:
                sr += f'\n{repr(self.next)}'
            return sr

        @property
        def score(self):
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

    def __repr__(self):
        st = repr(self.states).splitlines()
        st = '\n          '.join(st)
        kv = [
            f'PState:',
            f'me:     {self.me}',
            f'tokens: {self.tokens}',
            f'states: {st}',
        ]
        return '\n  '.join(kv)

    def __init__(self, me, text_input):
        self.me = me
        self.init(text_input)

    def init(self, text_input):
        self.tokens = shlex.split(text_input)
        self.states = self.Node(*find_verb(self.tokens.pop(0)))

    def add_ftok(self, verb, func, **tokens):
        log.debug('add_ftok(%s, %s, %s)', verb.name, func.__name__, tokens)
        self.states.add_ftok(func, _verb=verb, **tokens)

    @property
    def final(self):
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
        return pstate

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
                pstate.add_ftok(verb, rhint.func, **rhint.tokens)
        return pstate
