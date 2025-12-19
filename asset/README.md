# Space Station Map Assets

This folder contains text-exported `Map` layouts that can be round-tripped via `space.map.io`.

## Current Maps

- `station1.map` – Wagon-wheel torus with stadium-style rooms sharing the outer ring wall.
- `station2.map` – Torus spokes feeding small circular pods (no shared outer wall).

Both files were generated with the toroid helper added in `space/map/generate/toroid.py`.

### Re-generating

Run from the project root:

```sh
python - <<'PY'
from space.map.generate.toroid import generate_station
from space.map import export_map_to_path

export_map_to_path(generate_station(room_kind="stadium"), "asset/station1.map")
export_map_to_path(generate_station(room_kind="spear"), "asset/station2.map")
PY
```

### Loading Into Code

```python
from space.map import import_map_from_path

station_map = import_map_from_path("asset/station1.map")
# use station_map like any Map, e.g., iterate cells or drop objects
```

To choose the spear layout replace the path with `asset/station2.map`.
