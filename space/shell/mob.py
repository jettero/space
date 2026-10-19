# coding: utf-8

from .log import Shell as LogShell


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
        Voice lines, then the owner's behavior runs its fight turn
        through the parser like a player would (see
        space.living.behavior).
        """

        self.step()
        (me := self.owner.strongify()).behavior.behave(me)
