#!/usr/bin/env python3
# coding: utf-8

import logging
import sys
import lark
import operator

log = logging.getLogger(__name__)

class CallableInt:
    def __init__(self, v):
        if isinstance(v, lark.Token):
            v = int(v)
        self.v = v
    def __call__(self):
        return self.v
    def __repr__(self):
        return f'CI({self.v})'
    def __str__(self):
        return f'{self.v}'

class BinOp:
    _op_dict = {'+': operator.add, '-': operator.sub, '*': operator.mul, '/': operator.truediv}

    def __init__(self, lhs, op_str, rhs):
        self.op_str = op_str.value
        self.op = self._op_dict[ self.op_str ]
        self.lhs = lhs
        self.rhs = rhs

    def __repr__(self):
        return f'[{self.lhs} {self.op_str} {self.rhs}]'
    __str__ = __repr__

    def __call__(self):
        return self.op( self.lhs(), self.rhs() )

class Computer(lark.Transformer):
    grammar = '''
        %import common.WS
        %import common.INT
        %ignore WS
        ?start: expr
        mint: "-" INT
        val: INT | mint | WEIRD
        expr: val op expr | val
        WEIRD: "itsaweirdtoken"
        PLUS: "+"
        MINUS: "-"
        TIMES: "*"
        OVER: "/"
        ?op: PLUS | MINUS | TIMES | OVER
    '''

    def __init__(self):
        cb_table = { 'INT': self.int_cb }
        self.parser = lark.Lark(self.grammar, parser='lalr', debug=True,
            transformer=self, lexer_callbacks=cb_table)

    def parse(self, input):
        return self.parser.parse(input)

    def int_cb(self, tok):
        log.debug('int_cb(%s)', repr(tok))
        v = int(tok)
        if v == 7:
            return lark.Token.new_borrow_pos('WEIRD', v, tok)
        return lark.Token.new_borrow_pos(tok.type, v, tok)

    @lark.v_args(inline=True)
    def mint(self, v):
        log.debug('mint(%s)', v)
        return 0 - v.value

    @lark.v_args(inline=True)
    def val(self, v):
        log.debug('val(%s)', repr(v))
        return CallableInt(v)

    @lark.v_args(inline=True)
    def expr(self, *v):
        log.debug('expr(%s)', v)
        if len(v) == 1:
            return v[0]
        if len(v) == 3:
            return BinOp(*v)
        raise Exception("what do I do here??")

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    input = ' '.join(sys.argv[1:])
    if input:
        log.debug('building computer')
        computer = Computer()
        print(f'input is {input}')
        result = computer.parse(input)
        print(f'result is {result}')
        if callable(result):
            print(f'  result(): {result()}')
