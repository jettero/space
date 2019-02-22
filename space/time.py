# coding: utf-8

from collections import deque

class Time:
    def __init__(self, *actors):
        self._actors = deque()
        for actor in actors:
            self.add_actor(actor)

    def step(self):
        for a in self:
            a.shell.round_start()

        for a in self:
            if a.alive:
                a.shell.your_turn()

        for a in self:
            a.shell.round_start()

    def add_actor(self, a):
        self._actors.append(a)

    def remove_actor(self, a):
        self._actors.pop(a)

    def __iter__(self):
        for a in sorted(self.actors, key=lambda x: 0-x.initiative.roll()):
            yield a
