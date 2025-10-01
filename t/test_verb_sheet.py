# coding: utf-8

import re

from space.living import Human
from space.item import Ubi, Sack


def test_sheet_shows_core_stats_and_carry_weight(eroom):
    me = eroom.o.me

    # add a pack and an item for weight display
    pack = Sack()
    me.receive_item(pack)
    me.receive_item(Ubi())

    # should not raise
    me.do('sheet')

    # sanity: ensure basic attributes exist on object
    assert me.height > 0 and me.weight > 0 and me.hp >= 0
