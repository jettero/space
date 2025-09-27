# coding: utf-8
# pylint: disable=invalid-name

from space.args import introspect_hints as ih
from space.container import Containable
from space.living import Living

def test_hints(objs):
    assert ih(objs.me.can_move_words)     == [('moves', [tuple, str])]
    assert ih(objs.me.can_move_obj_words) == [('obj', [Containable]), ('moves', [tuple, str])]
    assert ih(objs.me.can_attack_living)  == [('living', [Living])]
    assert ih(objs.me.can_open_obj)       == [('obj', [Containable])]
