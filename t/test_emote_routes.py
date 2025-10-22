# coding: utf-8
# pylint: disable=invalid-name

import pytest

from space.verb.emote.gen import EMOTES, SAFE_TOKEN
from space.router import MethodArgsRouter


@pytest.mark.parametrize("ename", list(EMOTES))
def test_emote_can_count_matches_patterns(objs, ename):
    fname = ename.replace("-", "_")
    emote = EMOTES[ename]
    expected_count = len(emote.rule_db)

    mr = MethodArgsRouter(objs.me, f"can_{fname}")
    found = tuple(mr)
    assert len(found) == expected_count, f"can_* count mismatch for {ename}: found {len(found)} != expected {expected_count}"
