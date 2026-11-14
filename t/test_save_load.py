# coding: utf-8
# pylint: disable=redefined-outer-name

import json

import pytest

from space import store
from space.item import Katana, Sack, Ubi
from space.living import Human
from space.map import import_map_from_path
from space.map.io import drop_floor_items, floor_items
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


@pytest.fixture
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("APPSERV_USERS_DIR", str(tmp_path / "appserv" / "users"))
    store.db.cache_clear()
    yield store
    store.db.cache_clear()


def test_store_roundtrip(db):
    db.put("character", "acct/Bob", doc := Human("Bob").save())
    db.put("character", "other/Al", {})
    assert db.get("character", "acct/Bob") == json.loads(json.dumps(doc))
    assert db.get("character", "acct/nobody") is None
    assert db.keys("character", "acct/") == ["Bob"]


def test_fresh_human_saves_no_slots():
    assert "slots" not in next(iter(Human("Bob").save().values()))


def test_katana_in_hand_roundtrips_through_json():
    bob = Human("Bob")
    bob.slots.right_hand = Katana()
    bob.slots.pack = Sack()
    bob.slots.pack.add_item(Ubi())
    bob.credits = 5

    copy = load(json.loads(json.dumps(bob.save())))
    assert isinstance(k := copy.slots.right_hand, Katana) and k.haver is copy
    assert isinstance(u := next(iter(copy.slots.pack)), Ubi) and u.haver is copy
    assert copy.credits == 5 and "bob" in copy.tokens and copy.hp == bob.hp


def test_ship_items_survive_save_load(db):
    ship = import_map_from_path("asset/ship1.map")
    ship.get(6, 2).add_item(Katana())
    db.put("ship", "acct/Bob", {"map": "asset/ship1.map", "items": floor_items(ship)})

    doc = db.get("ship", "acct/Bob")
    assert list(doc["items"]) == ["6,2"]
    drop_floor_items(ship := import_map_from_path(doc["map"]), doc["items"])
    assert [type(i) for i in ship.get(6, 2)] == [Katana]
