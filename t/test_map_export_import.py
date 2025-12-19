# coding: utf-8

import pytest
from pathlib import Path

from t.troom import gen_troom
from space.map import export_map_to_path, import_map_from_path


@pytest.fixture
def tmap_file():
    Path("t/tmp").mkdir(exist_ok=True)
    yield Path("t/tmp/exported-map.map")


def test_troom_round_trip(tmap_file):
    a_map, _ = gen_troom()
    export_map_to_path(a_map, tmap_file)
    imported = import_map_from_path(tmap_file)
    assert imported == a_map
