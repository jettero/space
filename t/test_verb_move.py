# coding: utf-8

import pytest
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

    # single step
    xp = me.parse("s")
    assert xp
    assert xp.fn.__name__ == "do_move_words"
    assert xp.kw.get("moves") == ("s",)

    # repeated single via count
    xp = me.parse("3s")
    assert xp
    assert xp.fn.__name__ == "do_move_words"
    assert xp.kw.get("moves") == ("s", "s", "s")

    # concatenated repeated letters
    xp = me.parse("ss")
    assert xp
    assert xp.fn.__name__ == "do_move_words"
    assert xp.kw.get("moves") == ("s", "s")

    # cardinal + diagonal
    xp = me.parse("sSW")
    assert xp
    assert xp.fn.__name__ == "do_move_words"
    assert xp.kw.get("moves") == ("s", "sw")


def test_parser_move_action_preprocess_tokens_expands_moves(e_map, eroom):
    me = eroom.o.me

    # ensure that using explicit 'move' verb with direction string expands via dir_util
    xp = me.parse("move 3s SW")
    assert xp
    assert xp.fn.__name__ == "do_move_words"
    assert xp.kw.get("moves") == ("s", "s", "s", "sw")


def test_parser_multi_concat_and_counts_complex(e_map, eroom):
    me = eroom.o.me

    # complex input combines counts and concatenation; ensure order preserved
    # Note: requested example: '3ssSW' -> ['s','s','s','s','SW']
    # Our lexer canonicalizes 'SW' token value to 'sw' for the diagonal.
    xp = me.parse("3ssSW")
    assert xp
    assert xp.fn.__name__ == "do_move_words"
    assert xp.kw.get("moves") == ("s", "s", "s", "s", "sw")


def test_exec_moves_final_position(e_map, eroom):
    # Use provided empty 20x20 room with me centered from fixtures
    me = eroom.o.me

    # start at (9,9)
    assert me.location.pos == (9, 9)

    # After 's', expect (9,10)
    xp = me.parse("s")
    assert xp
    xp()
    assert me.location.pos == (9, 10)

    # 'ss' -> (9,12)
    xp = me.parse("ss")
    assert xp
    xp()
    assert me.location.pos == (9, 12)

    # '3s' -> (9,15)
    xp = me.parse("3s")
    assert xp
    xp()
    assert me.location.pos == (9, 15)

    # 'SW' diagonal applies 's' then 'w' -> from (9,15) to (8,16)
    xp = me.parse("SW")
    assert xp
    xp()
    assert me.location.pos == (8, 16)

    # 'sSW' -> south to (9,16)->(9,17), then diagonal to (7,18)
    xp = me.parse("sSW")
    assert xp
    xp()
    assert me.location.pos == (7, 18)
