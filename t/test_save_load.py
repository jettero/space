# coding: utf-8

import pytest

from space.serial import load


def test_save_load_roundtrip_ubi(objs):
    saved = objs.ubi.save()
    copy = load(saved)
    assert copy.__class__ is objs.ubi.__class__
    assert copy.save() == saved


def test_save_load_roundtrip_me(objs):
    saved = objs.me.save()
    copy = load(saved)
    assert copy.__class__ is objs.me.__class__
    assert copy.save() == saved
