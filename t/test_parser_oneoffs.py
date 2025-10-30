# coding: utf-8

import pytest

from space.parser import parse, ExecutionPlan


@pytest.mark.parametrize(
    "line,fn,kw",
    [
        ("look", "do_look", {}),
        ("say hi", "do_say_words", {"words": "hi"}),  # can_say_words joins the tuple
        ("l", "do_look", {}),
        ("look at room", "do_look", {}),
        ("inventory", "do_inventory", {}),
        ("i", "do_inventory", {}),
        ("move s", "do_move_words", {"moves": ("s",)}),
        ("move nsew nsew", "do_move_words", {"moves": tuple("n s e w n s e w".split())}),
    ],
)
def test_look_execution_plan(me, line, fn, kw):
    xp = parse(me, line, parse_only=True)
    assert xp is not None
    assert (xp.fn.__name__, xp.kw) == (fn, kw)
