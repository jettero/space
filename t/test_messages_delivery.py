# coding: utf-8

from space.living.msg import ReceivesMessages

def test_simple_and_targeted_delivery(a_map, objs):
    objs.me.simple_action("$N $vwave.", range=3)
    objs.me.targeted_action("$N $vattack $t.", objs.stupid, range=6)
