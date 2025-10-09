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
        self.owner.do_recieve(":EOF:YOUR_TURN:", your_turn=True)
