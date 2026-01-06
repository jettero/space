# coding: utf-8

from space.map import Wall


def test_uberfast_matches_fast_diagonal(vroom):
    m = vroom.v_map
    pairs = [((2, 2), (4, 4)), ((1, 1), (3, 3)), ((4, 4), (2, 2))]
    for pos1, pos2 in pairs:
        fast = list(m.fast_voxel(pos1, pos2, bad_type=Wall))
        uber = list(m.uberfast_voxel(pos1, pos2, bad_type=Wall))
        assert fast == uber, f"{pos1}->{pos2}: fast={[c.pos for c in fast]} uber={[c.pos for c in uber]}"


def test_uberfast_matches_fast_horizontal(vroom):
    m = vroom.v_map
    pairs = [((1, 3), (4, 3)), ((3, 3), (1, 3))]
    for pos1, pos2 in pairs:
        fast = list(m.fast_voxel(pos1, pos2, bad_type=Wall))
        uber = list(m.uberfast_voxel(pos1, pos2, bad_type=Wall))
        assert fast == uber, f"{pos1}->{pos2}: fast={[c.pos for c in fast]} uber={[c.pos for c in uber]}"


def test_uberfast_matches_fast_vertical(vroom):
    m = vroom.v_map
    pairs = [((3, 1), (3, 4)), ((3, 4), (3, 1))]
    for pos1, pos2 in pairs:
        fast = list(m.fast_voxel(pos1, pos2, bad_type=Wall))
        uber = list(m.uberfast_voxel(pos1, pos2, bad_type=Wall))
        assert fast == uber, f"{pos1}->{pos2}: fast={[c.pos for c in fast]} uber={[c.pos for c in uber]}"


def test_uberfast_matches_fast_exhaustive(vroom):
    m = vroom.v_map
    cells = [c for c in m.iter_cells() if c.pos[0] < 6 and c.pos[1] < 6]
    mismatches = []
    for c1 in cells:
        for c2 in cells:
            if c1.pos == c2.pos:
                continue
            fast = list(m.fast_voxel(c1.pos, c2.pos, bad_type=Wall))
            uber = list(m.uberfast_voxel(c1.pos, c2.pos, bad_type=Wall))
            if fast != uber:
                mismatches.append((c1.pos, c2.pos, [c.pos for c in fast], [c.pos for c in uber]))
    assert not mismatches, f"{len(mismatches)} mismatches, first: {mismatches[0]}"
