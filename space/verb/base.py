# coding: utf-8

import re
import logging
from ..parser import TargetError

log = logging.getLogger(__name__)

class VerbError(TargetError):
    pass

class Verb:
    name = 'verb'
    form = None
    nick = None

    def __init__(self):
        self.grammars = list()
        if not self.nick:
            self.nick = [ self.name ]
        if self.name not in self.nick:
            self.nick.insert(0, self.name)
        if isinstance(self.form, str):
            self.form = [ self.form ]
        if len(self.nick) == 1:
            self.vword = f'"{self.nick[0]}"'
        else:
            vnames = ' | '.join([ f'"{n}"' for n in self.nick ])
            self.vword = f'_{self.name}_word'
            self.grammars.append( f'!{self.vword}: {vnames}' )
        verb_re = '|'.join(['verb'] + self.nick)
        verb_re = re.compile(rf'^(?:{verb_re})\b')
        self.form = ' | '.join([ verb_re.sub(self.vword, f) for f in self.form ])
        self.rule_name = f'{self.name}'
        self.grammars.append(f'!{self.rule_name}: {self.form}')

    def __repr__(self):
        return f'Verb({self.name})'

    def __str__(self):
        return self.name

    def __eq__(self, other):
        if other is self:
            return True
        try:
            if other.lower() == self.name:
                return True
        except AttributeError:
            pass
        try:
            if other.name == self.name:
                return True
        except AttributeError:
            pass

    def target_error(self, target=None, more=None, sep=' '):
        if isinstance(target, (list,tuple)):
            # NOTE: if target is an empty list, it'll join to ''
            # and if not target will fire
            target = target[0] if len(target) == 1 else ', or '.join(target)
        if not target:
            error = f'could not find {self} target' # could not find attack target
        else:
            error = f'could not {self} {target}' # could not attack human#1234, or human#345, or human#9
        if more:
            error += sep + more
        raise TargetError(error)

    def error(self, msg=None):
        if msg is None:
            msg = f'cannot {self}'
        if isinstance(msg, Exception):
            raise msg
        raise VerbError(msg)

    def _test_pcr(self, pcr):
        if isinstance(pcr, tuple) and len(pcr) == 2:
            if isinstance(pcr[0], bool) and isinstance(pcr[1], dict):
                return pcr
        raise TypeError(f'me.parse_can() error: return should be (bool, dict)')

    def do(self, me, **kw):
        me.parse_do(self.name, **kw)

    def can(self, me, **kw):
        res, kw = self._test_pcr( me.parse_can(self.name, **kw) )
        if res:
            return kw
        self.error(kw.get('error'))
