# coding: utf-8

import re
import logging
import lark
import space.exceptions as E
from ..find import this_body

import space.obj

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
            raise E.BadDirection(f"'{dir_name}' is a bad direction") from e
    if cpos == pos:
        raise E.UselessDirection(f"'{dir_name}' seems useless")
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


def moves_to_description(moves):
    """Summarize a sequence of moves into a single descriptive string.

    Heuristics:
    - If only one axis moved: "{n}m north|south|east|west".
    - If both axes moved and magnitudes are close (ratio <= 1.5):
      "about {r}m {diagonal}" where r is rounded length.
    - If both axes moved and magnitudes differ (ratio > 1.5):
      "about {major}m {major_dir} and {minor}m {minor_dir}".
    - If no net movement: "in place".
    """
    from ..vv import VV

    dx = dy = 0
    for m in moves:
        m = str(m).lower()
        if "n" in m:
            dy -= 1
        if "s" in m:
            dy += 1
        if "e" in m:
            dx += 1
        if "w" in m:
            dx -= 1
    v = VV(dx, dy)
    dist = float(v.length)
    if dx == 0 and dy == 0:
        return "in place"
    if dx == 0:
        return f"{abs(dy)}m {('north' if dy < 0 else 'south')}"
    if dy == 0:
        return f"{abs(dx)}m {('east' if dx > 0 else 'west')}"

    ax = abs(dx)
    ay = abs(dy)
    # close magnitudes -> diagonal summary
    major_ratio = max(ax, ay) / max(1, min(ax, ay))
    if major_ratio <= 1.5:
        diag = ("north" if dy < 0 else "south") + ("east" if dx > 0 else "west")
        return f"about {dist:0.0f}m {diag}"

    # different enough -> describe components
    major_is_x = ax >= ay
    major = ax if major_is_x else ay
    minor = ay if major_is_x else ax
    major_dir = ("east" if dx > 0 else "west") if major_is_x else ("north" if dy < 0 else "south")
    minor_dir = ("north" if dy < 0 else "south") if major_is_x else ("east" if dx > 0 else "west")
    desc = f"about {major}m {major_dir} and {minor}m {minor_dir}"
    return desc


def positional_adjectives(obj):
    ret = set()
    dx = dy = None
    try:
        tbx, tby = this_body().location.pos
        ox, oy = obj.location.pos
        dx = ox - tbx
        dy = oy - tby
    except AttributeError:
        return ret
    except ReferenceError as e:
        raise e

    if dx == 0 and dy == 0:
        ret.update(("here", "close", "near"))
    else:
        ax = abs(dx)
        ay = abs(dy)
        if ax and ay:
            if dx > 0 and dy < 0:
                ret.add("northeast")
            elif dx > 0 and dy > 0:
                ret.add("southeast")
            elif dx < 0 and dy < 0:
                ret.add("northwest")
            elif dx < 0 and dy > 0:
                ret.add("southwest")
        if ax >= ay:
            if dx > 0:
                ret.add("east")
            elif dx < 0:
                ret.add("west")
        if ay >= ax:
            if dy > 0:
                ret.add("south")
            elif dy < 0:
                ret.add("north")
        manhattan = ax + ay
        if manhattan <= 2:
            ret.update(("close", "near"))
        elif manhattan >= 5:
            ret.add("far")

    return ret


space.obj.positional_adjectives = positional_adjectives
