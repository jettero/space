# coding: utf-8

from space.shell.message import TextMessage


def test_compose_basic_pronouns_and_verb(a_map):
    from t.troom import o as to
    me = to.me
    them = to.stupid
    # import mixin directly
    from space.living.msg import ReceivesMessages as MessagesMixin

    m = MessagesMixin()
    who = [me, them]
    # $N $vattack $t.
    msg = m.compose(me, "$N $vattack $t.", who)
    assert isinstance(msg, str)
    assert msg == "You attack Stupid."

    others = m.compose(None, "$N $vattack $t.", who)
    assert others == f"{me.short} attacks {them.short}."


def test_compose_objects_variants(a_map):
    from t.troom import o as to
    me = to.me
    ubi = to.ubi
    from space.living.msg import ReceivesMessages as MessagesMixin

    m = MessagesMixin()
    who = [me]
    obs = [None, ubi]
    msg_t = m.compose(me, "$N look at $o1t.", who, *obs)
    assert msg_t == f"You look at the {ubi.short}."
    msg_a = m.compose(None, "$N look at $o1a.", who, *obs)
    assert msg_a.startswith(me.short)
