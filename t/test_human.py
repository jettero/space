# coding: utf-8

from space.living import Human
from space.living.gender import Male, Female
from space.living.stats import HitPoints
from space.item import Sack, Ubi


def test_human():
    for _ in range(20):
        h = Human()
        assert 3 <= h.sci <= 18
        assert 1 <= h.hp <= 100
        assert h.conscious is True

        h.hurt(h.hp)
        assert h.conscious is False
        assert h.dead is False
        assert type(h.hp) == HitPoints  # pylint: disable=unidiomatic-typecheck

        h.hurt(20)
        assert h.conscious is False
        assert h.dead is True

        assert isinstance(h.gender, (Male, Female))

        assert h.height > 0
        assert h.weight > 0


def test_slots():
    h = Human()
    u = Ubi()
    s = Sack()
    h.slots.pack = s

    assert h.slots.pack is s

    h.receive_item(u)
    assert u in s


def test_life_state_boundaries():
    h = Human()

    # Start healthy
    assert h.hp > 0
    assert h.conscious is True
    assert h.unconscious is False
    assert h.alive is True
    assert h.dead is False

    # Reduce to exactly 0 hp
    h.hurt(h.hp)
    assert h.hp == 0
    assert h.conscious is False
    assert h.unconscious is True
    assert h.alive is True
    assert h.dead is False

    # Go to -1 hp (still unconscious, still alive)
    h.hurt(1)
    assert h.hp == -1
    assert h.conscious is False
    assert h.unconscious is True
    assert h.alive is True
    assert h.dead is False

    # Go to exactly -10 hp (edge of alive/unconscious)
    h.hurt(9)
    assert h.hp == -10
    assert h.conscious is False
    assert h.unconscious is True
    assert h.alive is True
    assert h.dead is False

    # Cross boundary to -11 hp (dead)
    h.hurt(1)
    assert h.hp == -11
    assert h.conscious is False
    assert h.unconscious is False
    assert h.alive is False
    assert h.dead is True
