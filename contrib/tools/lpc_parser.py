"""
Minimal parser for LPC/Pike literal data structures using Lark.

Supports a subset needed for parsing MudOS save dumps (e.g., soul.o):
- Maps: ([ key: value, ... ])
- Arrays: ({ value, ... })
- Strings: double-quoted with escapes
- Identifiers: bare names used as map keys (e.g., LIV, STR)
- Numbers: integers (optional, for completeness)
"""

from lark import Lark, Transformer, v_args


GRAMMAR = r"""
?start: value

?value: map
      | array
      | string
      | number
      | identifier

map   : "([" [pair ("," pair)* [","]] "])"
pair  : key ":" value
// Keys in MudOS saves are usually quoted strings; prioritize that.
key   : STRING      -> key_string
      | identifier  -> key_identifier

array : "({" [value ("," value)* [","]] "})"

// tokens
identifier: /[A-Za-z_][A-Za-z0-9_]*/

// Stronger string token to avoid truncation of quoted keys
STRING : /"(\\.|[^"\\])*"/
string : STRING

number : SIGNED_NUMBER

%import common.SIGNED_NUMBER
%import common.WS_INLINE
%ignore WS_INLINE
"""


@v_args(inline=True)
class ToPython(Transformer):
    def identifier(self, token):
        return str(token)

    def string(self, s):
        return s[1:-1].encode('utf-8').decode('unicode_escape')

    def number(self, n):
        text = str(n)
        try:
            return int(text)
        except ValueError:
            return float(text)

    def key_string(self, s):
        text = str(s)
        return bytes(text[1:-1], 'utf-8').decode('unicode_escape')

    def key_identifier(self, token):
        return str(token)

    def pair(self, k, v):
        return (k, v)

    def map(self, *pairs):
        d = {}
        for k, v in pairs:
            d[k] = v
        return d

    def array(self, *values):
        return list(values)


parser = Lark(GRAMMAR, start="start", parser="lalr", maybe_placeholders=False)


def parse(text):
    tree = parser.parse(text)
    return ToPython().transform(tree)
