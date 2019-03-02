# coding: utf-8

import logging
import shlex

from .verb import load_verbs

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
    def __repr__(self):
        kv = [
            f'PState:',
            f'me:     {self.me}',
            f'tokens: {self.tokens}',
            f'verb:   {self.verb}',
            f'opt:    verb_exec={self.verb_exec} parse_can={self.parse_can}',
            f'states: {self.states}',
        ]
        return '\n  '.join(kv)

    def __init__(self, me, text_input, verb_exec=True, parse_can=True):
        self.me = me
        self.verb_exec = verb_exec
        self.parse_can = parse_can
        self.init(text_input)

    def init(self, text_input):
        self.tokens = shlex.split(text_input)
        self.states = [ find_verb(self.tokens[0]) ]
        self.verb = self.states[0][0] if len(self.states[0]) == 1 else None

class Parser:
    def parse(self, me, text_input, verb_exec=True, parse_can=True):
        pstate = PState(me=me, verb_exec=verb_exec, parse_can=parse_can, text_input=text_input)
        if not pstate.verb:
            from space.map.dir_util import is_direction_string
            if is_direction_string(text_input):
                pstate.init(f'move {text_input}')
        log.debug('parsing "%s" for %s: %s', text_input, me, pstate)
        if pstate.parse_can:
            return self.parse_can(pstate)
        return pstate

    def parse_can(self, pstate):
        nstate = list()
        pstate.states.append(nstate)
        kw = { 'words': ' '.join(pstate.tokens[1:]) }
        for v in pstate.states[0]:
            nstate.append( v.can(pstate.me, **kw) )
        return pstate
