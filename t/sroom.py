# coding: utf-8
# pylint: disable=invalid-name


def gen_sroom(barriers="", a=3, b=0, at=None, attenuation=None):
    """
    A one-wide corridor for sound tests: Paul at (1, 1), the corridor runs
    east to (1 + a, 1) then south to Dig Dug at (1 + a, 1 + b), or at `at`
    when given. With b >= 2 the south leg is around the corner and out of
    sight.

    barriers is a string of "D" (closed door), "O" (open door) and "W"
    (wall) placed in the corridor starting next to Paul at (2, 1).
    attenuation, when given, replaces the doors' attenuation (dB).
    """

    from space.map import Room, Wall, BlockedCell
    from space.living import Human
    from space.nico import nico

    a_map = Room(a + 1, b + 1)
    for i in range(1, a + 1):
        for j in range(2, b + 2):
            a_map[i, j] = Wall()
    for x, c in enumerate(barriers, 2):
        a_map[x, 1] = bc = Wall() if c == "W" else BlockedCell()
        if c != "W":
            bc.door.open = c == "O"
            if attenuation is not None:
                bc.door.attenuation = attenuation

    od = dict()
    a_map[1, 1] = od["me"] = Human("Paul Miller", "Paul", gender="male")
    a_map[at or (1 + a, 1 + b)] = od["dig_dug"] = Human("Dig~Dug", gender="female")
    o = nico(**od)

    o.me.active = True

    return a_map, o
