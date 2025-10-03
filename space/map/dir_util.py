# coding: utf-8

import re
import logging
import lark

log = logging.getLogger(__name__)

DIRS = ("n", "s", "e", "w")
DDIRS = DIRS + ("ne", "nw", "se", "sw")
DTR = {"n": (1, -1), "s": (1, 1), "e": (0, 1), "w": (0, -1)}

R_DIR = {
    "n": "s",
    "s": "n",
    "e": "w",
    "w": "e",
}

O_DIR = {
    "n": "ew",
    "s": "ew",
    "e": "ns",
    "w": "ns",
    "ne": ("nw", "se"),
    "sw": ("nw", "se"),
    "nw": ("ne", "sw"),
    "se": ("ne", "sw"),
}


def reverse_dir(dir_name):
    r = ""
    for i in dir_name:
        r += R_DIR[i]
    return r


def orthoganal_dirs(dir_name):
    return O_DIR[dir_name]


def convert_pos(pos):
    if isinstance(pos, float):
        i, f = str(pos).split(".")
        pos = (int(i), int(f))
    if not isinstance(pos, (tuple, list)):
        pos = [int(pos), 0]
    if len(pos) < 2:
        pos = (int(pos[0]), int(pos[0]))
    return [int(i) for i in pos[0:2]]


def translate_dir(dir_name, pos):
    dir_name = dir_name.lower()
    pos = convert_pos(pos)
    cpos = pos[:]
    for i in dir_name:
        try:
            i, v = DTR[i]
            cpos[i] += v
        except KeyError as e:
            raise ValueError(f"'{dir_name}' is a bad direction") from e
    if cpos == pos:
        raise ValueError(f"'{dir_name}' seems useless")
    return tuple(cpos)


def canonical_dir_token(tok):
    x = tok.lower().strip().replace("-", "")
    if x in DDIRS:
        return lark.Token.new_borrow_pos(tok.type, x, tok)
    # 0123 5
    # north
    # southwest
    try:
        return lark.Token.new_borrow_pos(tok.type, x[0] + x[5], tok)
    except IndexError:
        return lark.Token.new_borrow_pos(tok.type, x[0], tok)


MOVES_PARSER = lark.Lark(
    r"""
%import common.WS
%ignore WS
%ignore ","

start: _cdirs
LMDIR: /[Nn][Oo][Rr][Tt][Hh]/ | /[Ss][Oo][Uu][Tt][Hh]/
LODIR: /[Ee][Aa][Ss][Tt]/ | /[Ww][Ee][Ss][Tt]/
MODIR: LMDIR "-"? LODIR
SDIR: /[nsew]/ | "NE" | "SE" | "NW" | "SW"
COUNT: /\d+/
DIR: MODIR | LMDIR | LODIR | SDIR
_cdir: COUNT? DIR
_cdirs: _cdir _cdirs?
""",
    parser="lalr",
    lexer_callbacks={"DIR": canonical_dir_token},
)


def move_string_to_dirs(moves_str):
    log.debug('trying to parse "%s" as moves', moves_str)
    try:
        moves_tree = MOVES_PARSER.parse(moves_str)
    except lark.UnexpectedInput as lui:
        log.exception(lui)
        raise SyntaxError(f'unable to parse "{moves_str}" as moves')
    log.debug(" … parse result: %s", moves_tree)

    c = 1
    for tok in moves_tree.children:
        if tok.type == "COUNT":
            c = int(tok.value)
            continue
        for _ in range(c):
            yield tok.value
        c = 1


DIR_STRING = re.compile(r"^(?:\d*(NE|SE|NW|SW|[nsewNSEW]|(?i:north|south|east|west))[\s,]*)+$")


def is_direction_string(moves_str):
    return bool(DIR_STRING.match(moves_str))
