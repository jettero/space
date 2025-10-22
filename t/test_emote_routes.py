# coding: utf-8
# pylint: disable=invalid-name

import pytest

from space.verb.emote.gen import EMOTES
from space.router import MethodArgsRouter


@pytest.mark.parametrize("ename", list(EMOTES))
def test_emote_can_methods_exist(objs, ename):
    mr = MethodArgsRouter(objs.me, f"can_{ename}")
    # Ensure at least one can_* method registered for this emote on Living
    assert any(True for _ in mr), f"no can_* methods found for {ename}"


@pytest.mark.parametrize("ename", list(EMOTES))
def test_emote_can_suffixes_match_patterns(objs, ename):
    # Collect expected suffix variants from patterns
    expected = set()
    patterns = next(e.patterns for e in load_emotes() if e.name == ename)
    for sig in patterns.keys():
        sig = (sig or "").strip()
        if sig == "":
            expected.add(f"can_{ename}")
        else:
            expected.add(f"can_{ename}_" + sig.replace("  ", " ").replace(" ", "_"))

    mr = MethodArgsRouter(objs.me, f"can_{ename}")
    found = set(mr)

    # Router dir yields exact names; ensure all expected are present
    missing = expected - found
    assert not missing, f"missing {missing} for {ename}"
