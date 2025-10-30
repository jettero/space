# coding: utf-8

import pytest

from space.newparser import parse


def test_look_execution_plan(me):
    xp = parse(me, "look", parse_only=True)
    assert xp is not None
    assert xp.fn.__name__ == "do_look"
    assert xp.actor is me
    assert xp.kw == {}


def test_look_executes_when_called(me):
    xp = parse(me, "look", parse_only=True)
    assert xp is not None
    assert xp() is None


@pytest.mark.parametrize(
    "line",
    [
        "say hi",
        "say hello world",
        "take ubi",
        "give ubi stupid",
    ],
)
def test_complex_verbs_currently_not_ready(me, line):
    assert parse(me, line, parse_only=True) is None
