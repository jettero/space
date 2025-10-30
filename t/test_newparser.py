# coding: utf-8

import pytest

from space.newparser import parse, ExecutionPlan

@pytest.mark.parametrize(
    "line,fn,kw",
    [
        ("look", 'do_look', {}),
        ("say hi", 'do_say_words', {"words":'hi'}), # can_say_words joins the tuple
        ("l", 'do_look', {}),
        ("look at room", 'do_look', {}),
        ("get bauble", 'do_get', {"obj": 'bauble'}),
        ("drop bauble", 'do_drop', {"obj": 'bauble'}),
        ("inventory", 'do_inventory', {}),
        ("i", 'do_inventory', {}),
        ("n", 'do_move_words', {"moves": ("north",)}),
        ("south", 'do_move_words', {"moves": ("south",)}),
        ("attack skellyman", 'do_attack', {"target": 'skellyman'}),
    ],
)
def test_look_execution_plan(me, line, fn,kw):
    xp = parse(me, line, parse_only=True)
    assert xp is not None
    assert xp.fn.__name__ == fn
    assert xp.kw == kw
