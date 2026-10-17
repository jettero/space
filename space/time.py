# coding: utf-8

from math import ceil

MCP = None  # injected by space.master.load_mcp()
MAIN, SMALL, CELLS = 2, 1, 6


class Time:
    """
    The Time daemon for one map: passive bookkeeping, never a driver.

    Every map has one.  Outside a fight my_turn() always says yes and
    charge() does nothing.  start() rolls initiative for every Living on
    the map and runs turns: each grants MAIN main actions and SMALL
    small ones; a small with none left trades down a main, and a move
    action is CELLS cells of direction commands that stays open until
    spent or a main action closes it.

    Shell events (round_start, your_turn, round_end and the private
    status lines) are handed off with MCP.call_out(..., 0), so no fight
    code ever runs inside anyone's command.  The fight ends when
    fighting goes false: nobody conscious here has aggro toward anybody
    conscious here.
    """

    actors = ()
    round = turn = main = small = cells = 0
    spent = False

    def __init__(self, a_map):
        self.map = a_map

    def __repr__(self):
        return f"Time<round {self.round}, {self.current!r}, {self.main} main, {self.small} small, {self.cells} cells>"

    @property
    def livings(self) -> list:
        from .living import Living  # pylint: disable=import-outside-toplevel

        return list(self.map.objects_of_type(Living))

    @property
    def conscious(self) -> list:
        return [x for x in self.livings if x.conscious]

    @property
    def fighting(self) -> bool:
        here = self.conscious
        return any(v > 0 and t in here for a in here for t, v in a.aggro.items())

    @property
    def current(self):
        return self.actors[self.turn] if self.actors else None

    def tell(self, bodies, pick, *a):
        for b in bodies:
            MCP.call_out(pick(b.shell), 0, *a)

    def start(self):
        """
        Roll initiative for every Living on the map, tell each of them
        the order, and start round 1.
        """

        rolls = {a: a.initiative.roll() for a in self.conscious}
        self.actors = sorted(rolls, key=rolls.get, reverse=True)
        self.tell(
            self.actors, lambda s: s.receive_text, "Initiative: {}", ", ".join(f"{a.short} {rolls[a]}" for a in self.actors)
        )
        self.round, self.turn = 1, -1
        self.next_turn()

    def my_turn(self, body, main=0, small=0, cells=0) -> tuple[bool, dict]:
        """
        Whether body can spend main/small actions and move cells right
        now, as a can_* result: always ok outside a fight, otherwise
        only on body's turn and within what the turn has left.
        """

        if not self.round:
            return True, {}
        if body is not self.current:
            return False, {"error": "It's not your turn."}
        if main + max(0, small - self.small) + ceil(max(0, cells - self.cells) / CELLS) <= self.main:
            return True, {}
        return False, {"error": "You can't move that far." if cells else "You have no actions left this turn."}

    def charge(self, body, main=0, small=0, cells=0):
        """
        Spend body's actions after (or as) a verb runs.  Cells use the
        open move action first and spill into a new one per main; a
        small with none left costs a main; a main closes the open move
        action.  Then the fight may end, and the turn ends when nothing
        is left.  No-op outside a fight or off turn.
        """

        if not self.round or body is not self.current:
            return
        while cells:
            if not self.cells:
                self.main, self.cells = self.main - 1, CELLS
            cells, self.cells = max(0, cells - self.cells), max(0, self.cells - cells)
        self.small -= (s := min(small, self.small))
        self.main -= main + small - s
        if main:
            self.cells = 0
        self.spent = True
        self.check(not (self.main or self.small or self.cells))

    def pass_turn(self, body):
        if self.round and body is self.current:
            self.check(True)

    def check(self, over):
        if not self.fighting:
            self.tell(self.actors, lambda s: s.receive_text, "The fight is over.")
            del self.actors, self.round, self.turn, self.main, self.small, self.cells, self.spent
        elif over:
            self.next_turn()

    def next_turn(self):
        here = self.conscious
        for _ in self.actors:  # ponytail: late arrivals never join the order; add them on arrival when maps get busy
            self.turn += 1
            if self.turn == len(self.actors):
                self.tell(self.actors, lambda s: s.round_end, self.round)
                self.round, self.turn = self.round + 1, 0
            if self.turn == 0:
                self.tell(self.actors, lambda s: s.round_start, self.round)
            if self.current in here:
                break
        self.main, self.small, self.cells, self.spent = MAIN, SMALL, 0, False
        self.tell([self.current], lambda s: s.your_turn)
