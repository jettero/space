# coding: utf-8

from space.living.msg import ReceivesMessages as MessagesMixin


def test_compose_basic_pronouns_and_verb(a_map,objs):
    m = MessagesMixin()
    who = [objs.me, objs.stupid]
    # $N $vattack $t.
    msg = m.compose(objs.me, "$N $vattack $t.", who)
    assert isinstance(msg, str)
    assert msg == "You attack Stupid."

    others = m.compose(None, "$N $vattack $t.", who)
    assert others == f"{objs.me.a_short} attacks {objs.stupid.a_short}."

def test_compose_objects_variants(a_map,objs):
    from space.living.msg import ReceivesMessages as MessagesMixin

    m = MessagesMixin()
    who = [objs.me]
    obs = [objs.ubi]
    msg_t = m.compose(objs.me, "$N $vlook at $o.", who, *obs)
    assert msg_t == f"You look at {objs.ubi.a_short}."
    msg_t = m.compose(None, "$N $vlook at $o.", who, *obs)
    assert msg_t == f"{objs.me.a_short} looks at {objs.ubi.a_short}."
