# coding: utf-8

import pytest

from space.serial import load


def _roundtrip(obj):
    saved = obj.save()
    copy = load(saved)
    assert copy.__class__ is obj.__class__
    assert copy.save() == saved


def test_roundtrip_ubi(objs):
    _roundtrip(objs.ubi)


def test_roundtrip_me(objs):
    _roundtrip(objs.me)
