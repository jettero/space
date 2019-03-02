# coding: utf-8
# pylint: disable=invalid-name

from space.args import introspect_hints
from space.container import Containable
from space.living import Living

def lih(fn):
    return list(introspect_hints(fn).items())

def test_hints(objs):
    assert lih(objs.me.can_move_words)     == [('moves', str)]
    assert lih(objs.me.can_move_obj_words) == [('obj', Containable), ('moves', str)]
    assert lih(objs.me.can_attack_living)  == [('living', Living)]
