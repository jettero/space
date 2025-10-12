# coding: utf-8
# pylint: disable=invalid-name

import pytest
from space.roll import Roll, Check


def test_roll():
    r = Roll("1d6+2")
    T = [r.roll() for _ in range(5000)]
    assert min(T) == 3
    assert max(T) == 8

    for x in T:
        if x == 8:
            assert x.crit is True
        if x.crit:
            assert x == 8
        if x == 3:
            assert x.fumb is True
        if x.fumb:
            assert x == 3


def _test_mean_trials(r, rel=0.1, trials=50000):
    bfm = sum([r.roll() for _ in range(trials)]) / trials
    assert pytest.approx(r.mean, rel=rel) == bfm


def test_min_max_mean():
    r = Roll("8d20+7")
    assert r.min == 8 + 7
    assert r.max == 8 * 20 + 7
    _test_mean_trials(r, rel=0.1)


def test_1d82():
    _test_mean_trials(Roll("1d8+2"))


def test_1red7():
    _test_mean_trials(Roll("1 red +7"))


def test_5olive():
    _test_mean_trials(Roll("1 olive"))


def _test_wins(l, r, trials=50000):
    L = Roll(l)
    R = Roll(r)
    l, r = 0, 0
    for _ in range(trials):
        if L.roll() > R.roll():
            l += 1
        else:
            r += 1
    assert l > r


def test_grime_first_cycle():
    """if highest wins, …
    red beats blue
    blue beats olive
    olive beats yellow
    yellow beats magenta
    magenta beats red
    (wtf??)
    """

    _test_wins(
        "red",
        "blue",
    )
    _test_wins(
        "blue",
        "olive",
    )
    _test_wins(
        "olive",
        "yellow",
    )
    _test_wins(
        "yellow",
        "magenta",
    )
    _test_wins(
        "magenta",
        "red",
    )


def test_grime_second_cycle():
    """if highest wins, …
    2 red loses to 2 blue
    2 blue loses to 2 olive
    2 olive loses to 2 yellow
    2 yellow loses to 2 magenta
    2 magenta loses to 2 red
    (wtf??)
    """

    _test_wins(
        "2 blue",
        "2 red",
    )
    _test_wins(
        "2 olive",
        "2 blue",
    )
    _test_wins(
        "2 yellow",
        "2 olive",
    )
    _test_wins(
        "2 magenta",
        "2 yellow",
    )
    _test_wins(
        "2 red",
        "2 magenta",
    )

def test_roll_callable_and_compare():
    r = Roll("1d10")
    v1 = r()
    v2 = r.roll()
    assert 1 <= v1 <= 10
    assert 1 <= v2 <= 10
    # comparisons should be valid and return booleans
    assert isinstance(r == 1, bool)
    assert isinstance(r != 1, bool)
    assert isinstance(r < 5, bool)
    assert isinstance(r <= 5, bool)
    assert isinstance(r > 5, bool)
    assert isinstance(r >= 5, bool)


# Check tests
def test_check_eq():
    rr = Check("1d10=1")
    t = f = 0
    for _ in range(1000):
        if rr:
            t += 1
        else:
            f += 1
    assert t < f
    assert t > 0
    assert f > 0


def test_check_lt():
    rr = Check("1d10<2")
    t = f = 0
    for _ in range(1000):
        if rr:
            t += 1
        else:
            f += 1
    assert t < f
    assert t > 0
    assert f > 0


def test_check_gt():
    rr = Check("1d10>9")
    t = f = 0
    for _ in range(1000):
        if rr:
            t += 1
        else:
            f += 1
    assert t < f
    assert t > 0
    assert f > 0


def test_check_eq_set():
    rr = Check("1d10={3..5,2}")
    t = f = 0
    for _ in range(5000):
        if rr:
            t += 1
        else:
            f += 1
    # Probability of hitting {2,3,4,5} on d10 is 4/10
    # Expect both true and false across many trials
    assert t > 0
    assert f > 0


def test_check_neq_set():
    rr = Check("1d10!={3..5,2}")
    t = f = 0
    for _ in range(5000):
        if rr:
            t += 1
        else:
            f += 1
    # Probability of NOT hitting {2,3,4,5} on d10 is 6/10
    assert t > 0
    assert f > 0


# The old set-selection syntax has been removed as not useful.
