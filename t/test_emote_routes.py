# coding: utf-8
# pylint: disable=invalid-name

import pytest

from space.verb.emote.gen import EMOTES, SAFE_TOKEN


@pytest.mark.parametrize("ename", list(EMOTES))
def test_emote_can_count_matches_patterns(objs, ename):
    fname = ename.replace("-", "X")
    emote = EMOTES[ename]
    expected_count = len(emote.rule_db)

    can_fn = f"can_{fname}"

    found = tuple(n for n in dir(objs.me) if (n == can_fn or n.startswith(f"{can_fn}_")))
    assert len(found) == expected_count, f"can_* count mismatch for {ename}: found {len(found)} != expected {expected_count}"
