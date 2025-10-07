# coding: utf-8
# pylint: disable=abstract-method

from .base import BaseShell


class Shell(BaseShell):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.msgs = list()

    def receive_message(self, msg):
        self.msgs.append(msg.render_text(color=False))
