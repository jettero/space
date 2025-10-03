# coding: utf-8

import pytest

from space.parser import Parser
from space.map.dir_util import move_string_to_dirs, is_direction_string


def _moves_for(s):
    assert is_direction_string(s)
    return list(move_string_to_dirs(s))


def test_dir_util_parses_repeats_and_diagonals():
    # simple single
    assert _moves_for("s") == ["s"]
    assert _moves_for("SW") == ["sw"]  # canonicalized token value is lowercase 'sw'

    # concatenated different types
    assert _moves_for("sSW") == ["s", "sw"]

    # repeated cardinals
    assert _moves_for("ss") == ["s", "s"]
    assert _moves_for("3s") == ["s", "s", "s"]

    # mixed with count then diagonal
    assert _moves_for("2SW") == ["sw", "sw"]

    # multiple tokens with space/comma
    assert _moves_for("n e") == ["n", "e"]
    assert _moves_for("s,SW") == ["s", "sw"]


def test_dir_util_parses_long_word_forms():
    # long names collapse to first letters; north + west => 'nw'
    assert _moves_for("north") == ["n"]
    assert _moves_for("southwest") == ["sw"]
    # hyphenated long form is not accepted by is_direction_string; ensure parser of dir_util handles words without hyphen
    assert _moves_for("northwest") == ["nw"]


def test_parser_rewrites_bare_direction_to_move(e_map, eroom):
    # Parser should rewrite bare direction strings as 'move …'
    me = eroom.o.me
    p = Parser()

    # single step
    ps = p.parse(me, "s")
    assert ps
    assert ps.winner.verb.name == "move"
    assert ps.winner.do_args.get("moves") == ("s",)

    # repeated single via count
    ps = p.parse(me, "3s")
    assert ps
    assert ps.winner.verb.name == "move"
    assert ps.winner.do_args.get("moves") == ("s", "s", "s")

    # concatenated repeated letters
    ps = p.parse(me, "ss")
    assert ps
    assert ps.winner.verb.name == "move"
    assert ps.winner.do_args.get("moves") == ("s", "s")

    # cardinal + diagonal
    ps = p.parse(me, "sSW")
    assert ps
    assert ps.winner.verb.name == "move"
    assert ps.winner.do_args.get("moves") == ("s", "sw")


def test_parser_move_action_preprocess_tokens_expands_moves(e_map, eroom):
    me = eroom.o.me
    p = Parser()

    # ensure that using explicit 'move' verb with direction string expands via dir_util
    ps = p.parse(me, "move 3s SW")
    assert ps
    assert ps.winner.verb.name == "move"
    assert ps.winner.do_args.get("moves") == ("s", "s", "s", "sw")


def test_parser_multi_concat_and_counts_complex(e_map, eroom):
    me = eroom.o.me
    p = Parser()

    # complex input combines counts and concatenation; ensure order preserved
    # Note: requested example: '3ssSW' -> ['s','s','s','s','SW']
    # Our lexer canonicalizes 'SW' token value to 'sw' for the diagonal.
    ps = p.parse(me, "3ssSW")
    assert ps
    assert ps.winner.verb.name == "move"
    assert ps.winner.do_args.get("moves") == ("s", "s", "s", "s", "sw")


def test_exec_moves_final_position(e_map, eroom):
    # Use provided empty 20x20 room with me centered from fixtures
    me = eroom.o.me
    p = Parser()

    # start at (9,9)
    assert me.location.pos == (9, 9)

    # After 's', expect (9,10)
    ps = p.parse(me, "s")
    assert ps
    ps()
    assert me.location.pos == (9, 10)

    # 'ss' -> (9,12)
    ps = p.parse(me, "ss")
    assert ps
    ps()
    assert me.location.pos == (9, 12)

    # '3s' -> (9,15)
    ps = p.parse(me, "3s")
    assert ps
    ps()
    assert me.location.pos == (9, 15)

    # 'SW' diagonal applies 's' then 'w' -> from (9,15) to (8,16)
    ps = p.parse(me, "SW")
    assert ps
    ps()
    assert me.location.pos == (8, 16)

    # 'sSW' -> south to (9,16)->(9,17), then diagonal to (7,18)
    ps = p.parse(me, "sSW")
    assert ps
    ps()
    assert me.location.pos == (7, 18)
