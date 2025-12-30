import time
import pytest
from pathlib import Path


def test_visicalc_benchmark_small(e_map, eroom):
    """Benchmark visicalc on small eroom map."""
    from space.living import Human

    m = e_map
    center_x = m.bounds.X // 2
    center_y = m.bounds.Y // 2
    human = Human("Benchmark Tester")
    m[center_x, center_y] = human

    print(f"\n\n=== Small map ({m.bounds}) ===")
    _run_benchmark(m, human, iterations=50)


def test_visicalc_benchmark_large():
    """Benchmark visicalc on large station1 map."""
    from space.map import import_map_from_path
    from space.living import Human

    map_path = Path(__file__).parent.parent / "asset" / "station1.map"
    if not map_path.exists():
        pytest.skip("station1.map not found")

    m = import_map_from_path(map_path)
    center_x = m.bounds.X // 2
    center_y = m.bounds.Y // 2
    human = Human("Benchmark Tester")
    m[center_x, center_y] = human

    print(f"\n\n=== Large map ({m.bounds}) ===")
    _run_benchmark(m, human, iterations=10)


def _run_benchmark(m, human, iterations):
    maxdist_values = [None, 30, 50]

    for maxdist in maxdist_values:
        start = time.perf_counter()
        for _ in range(iterations):
            m.visicalc(human, maxdist=maxdist)
        elapsed = time.perf_counter() - start

        per_call_ms = (elapsed / iterations) * 1000
        label = f"maxdist={maxdist}" if maxdist else "maxdist=None (full map)"
        print(f"{label}: {per_call_ms:.2f}ms/call ({iterations} iterations)")

    assert True
