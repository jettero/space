# coding: utf-8

import pytest

from space.newparser import parse, ExecutionPlan


@pytest.mark.parametrize(
    "line,fn,kw",
    [
        ("look", "do_look", {}),
        ("say hi", "do_say_words", {"words": "hi"}),  # can_say_words joins the tuple
        ("l", "do_look", {}),
        ("look at room", "do_look", {}),
        # get/drop routing requires exact can/do suffix pairing; skip here
        ("inventory", "do_inventory", {}),
        ("i", "do_inventory", {}),
        ("move south", "do_move_words", {"moves": ("south",)}),
        # attack route discovery not exposed in newparser yet; skip here
    ],
)
def test_look_execution_plan(me, line, fn, kw):
    xp = parse(me, line, parse_only=True)
    assert xp is not None
    assert (xp.fn.__name__, xp.kw) == (fn, kw)
