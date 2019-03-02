# coding: utf-8

import types
import logging
import lark

from .verb import load_verbs

log = logging.getLogger(__name__)

class TargetError(SyntaxError):
    pass

def list_match(name, objs, text_input=None):
    if isinstance(objs, (types.GeneratorType, list, tuple)):
        s = name.split('.', 1)
        assert len(s) in (1,2,)
        objs = [ i for i in objs if i.parse_match(*s) ]
        if objs:
            return objs

def squash_list_of_dict_args(*a, **kw):
    def _k(k):
        if k in kw:
            n = 2
            tk = f'{k}{n}'
            while tk in kw:
                n += 1
                tk = f'{k}{n}'
            return tk
        return k
    for d in a:
        for k,v in d.items():
            kw[_k(k)] = v
    return kw

class Transformer(lark.Transformer):
    @lark.v_args(inline=True)
    def action(self, v):
        items = list(self.cfilter(v.children))
        verb = items.pop(0).value
        items = [ { item.type.lower(): item.value } for item in items ]
        return verb, squash_list_of_dict_args(*items)

    @lark.v_args(inline=True)
    def words(self, *o):
        return lark.Token('WORDS', ' '.join(o))

    def cfilter(self, children):
        for item in children:
            if hasattr(item, 'children'):
                yield from self.cfilter(item.children)
            else:
                yield item

class Parser:
    text_input = me = vmap = vmap_objs = vmap_living = None

    def grammar_txt(self, sep='\n'):
        return sep.join( self.grammar.split('\n') )

    def __str__(self):
        return self.grammar_txt()

    def __repr__(self):
        t = '\n  ' + self.grammar_txt(sep='\n  ')
        return f'{self.__class__.__name__}:{t}'

    @property
    def verb_words(self):
        return sorted([ v.name for v in self.verbs ])

    @property
    def verb_rule_names(self):
        for v in self.verbs:
            yield v.rule_name

    @property
    def verb_grammars(self):
        for v in self.verbs:
            yield from v.grammars

    def _reWORD_token(self, v):
        sv = str(v)
        log.debug(' … demoting %s to WORD(%s)', v.type, sv)
        return lark.Token.new_borrow_pos('WORD', sv, v)

    def living_token(self, v):
        log.debug('living_token(%s)', v)
        objs = list_match(v, self.vmap_living, self.text_input)
        if objs:
            log.debug(' … returning %s(%s)', v.type, objs)
            return lark.Token.new_borrow_pos(v.type, objs, v)
        return self._reWORD_token(v)

    def obj_token(self, v):
        log.debug('obj_token(%s)', v)
        objs = list_match(v, self.vmap_objs, self.text_input)
        if objs:
            log.debug(' … returning %s(%s)', v.type, objs)
            return lark.Token.new_borrow_pos(v.type, objs, v)
        return self._reWORD_token(v)

    def __init__(self):
        self.verbs = load_verbs()
        actions = ' | '.join(self.verb_rule_names)
        grammars = '\n'.join(self.verb_grammars)
        self.grammar = '\n'.join([
            '%import common.WS',
            '%ignore WS',
            '?start: action',
            'LIVING: WORD',
            'OBJ: WORD',
           r'WORD: /[\w_#.-]+/',
            'words: WORD /[;,]+/ words?',
            '     | WORD words?',
            "string: \"\\\"\" /[^\"]+/ \"\\\"\"",
            "      | \"'\" /[^']+/ \"'\"",
            "      | \"\\\"\" \"\\\"\"",
            "      | \"'\" \"'\"",
           f'action: {actions}',
           f'{grammars}',
        ])

        def token_helper(vo, type_=None):
            def inner(tok):
                return lark.Token.new_borrow_pos(type_ or tok.type, vo, tok)
            return inner

        lexer_callbacks = { 'LIVING': self.living_token, 'OBJ': self.obj_token }
        for vo in self.verbs:
            lexer_callbacks[ vo.name.upper() ] = token_helper(vo)

        try:
            self.lark = lark.Lark(self.grammar, parser='lalr', debug=True,
                transformer=Transformer(), lexer_callbacks=lexer_callbacks)
        except:
            log.error('failed grammar:\n%s', self.grammar)
            raise

    def pre_parse(self, me, text_input):
        from .living import Living
        self.me = me
        self.vmap = me.location.map.visicalc_submap(me)
        self.vmap_objs = [ o for o in self.vmap.objects ]
        self.vmap_living = [ o for o in self.vmap.objects_of_type(Living) ]
        self.text_input = text_input
        return text_input

    def parse(self, me, text_input, verb_exec=True, post_parse=True):
        text_input = self.pre_parse(me, text_input)

        try:
            verb, kw = self.lark.parse(text_input)
        except lark.UnexpectedInput as lui:
            still_fail = True
            from space.map.dir_util import is_direction_string
            if is_direction_string(text_input):
                try:
                    verb, kw = self.lark.parse('move ' + text_input)
                    still_fail = False
                except lark.UnexpectedInput:
                    pass
            if still_fail:
                c = lui.column-1 # pylint: disable=no-member
                if c > 0:
                    text_input = text_input[:c] + '→' + text_input[c:]
                else:
                    text_input = '→' + text_input
                raise SyntaxError(f'unable to parse "{text_input}" (\'→\' added before error)')

        if not post_parse:
            return (verb, kw)
        return self.post_parse(verb, kw, verb_exec=verb_exec)

    def post_parse(self, verb, kw, verb_exec=True):
        # verb.can() must raise exception for parse to fail here. Otherwise, it
        # is expected to return args formatted for verb.execute() — e.g.,
        # attack.can(self.me, **kw) should return kw
        kw = verb.can(self.me, **kw)
        if not isinstance(kw, dict):
            raise TypeError(f'{verb}.can() error: return should be a dict')
        if not verb_exec:
            return (verb, kw)
        self.me.active = True
        verb.do(self.me, **kw)
        self.me.active = False
