# coding: utf-8

from .log import Shell as LogShell
from ..map.dir_util import DDIRS
from ..time import CELLS


class Shell(LogShell):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._queue = []

    def receive_message(self, msg):
        super().receive_message(msg)
        try:
            text = msg.render_text(color=False)
        except AttributeError:
            text = str(msg)
        for line in text.splitlines():
            if line:
                self._queue.append(line)

    def step(self):
        while self._queue:
            self.owner.do_receive(self._queue.pop(0))
        self.owner.do_receive(":EOF:YOUR_TURN:", your_turn=True)

    def round_start(self, n):
        if self.owner.conscious and self.owner.aggro:
            self.owner.simple_action("$N $vgrowl menacingly.")

    def your_turn(self):
        """
        Voice lines, then act through the parser like a player would:
        attack the nearest visible conscious foe from owner.aggro when
        in reach, else move toward it, until the turn is gone or nothing
        makes progress.  Then pass, or disengage when it had aggro but
        couldn't see or get any closer to any of its foes.
        """

        self.step()
        me, acted = self.owner.strongify(), False
        t = me.location.map.time
        while t.current is me and (foe := self.nearest_foe()):
            if me.unit_distance_to(foe) <= me.reach:
                cmd = f"attack {foe.short}"
            elif moves := self.steps_toward(foe):
                cmd = f"move {' '.join(moves)}"
            else:
                break
            if not me.do(cmd):
                break
            acted = True
        if t.current is me:
            me.do("disengage" if me.aggro and not acted else "pass")

    def nearest_foe(self):
        me = self.owner
        return min(
            (f for f, v in me.aggro.items() if v > 0 and f.conscious and me.can_see(f)), key=me.unit_distance_to, default=None
        )

    def steps_toward(self, foe):
        """
        Up to CELLS directions that greedily close the Chebyshev gap to
        foe, stopping when adjacent or when no step gets closer.
        """

        # ponytail: greedy, a wall between mob and foe stalls it; pathfind when maps get twisty
        me, moves = self.owner, []
        fx, fy = foe.location.pos
        gap = lambda c: max(abs(c.pos[0] - fx), abs(c.pos[1] - fy))
        here = me.location
        while len(moves) < CELLS and gap(here) > 1:
            steps = [(gap(c), d, c) for d in DDIRS if (r := me.path_for(me, [*moves, d]))[0] and (c := r[1]["cells"][-1])]
            if not steps or (best := min(steps))[0] >= gap(here):
                break
            moves.append(best[1])
            here = best[2]
        return tuple(moves)
