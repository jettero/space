# coding: utf-8


def test_simple_and_targeted_delivery(a_map):
    from t.troom import o as to
    me = to.me
    them = to.stupid
    from space.living.msg import ReceivesMessages

    # Use the actual Humanoid with mixin already applied
    h = me
    # simple action goes to me and heari neighbors
    h.simple_action("$N $vwave.", range=3)

    # targeted action goes to me, target, others
    h.targeted_action("$N $vattack $t.", them, range=6)
