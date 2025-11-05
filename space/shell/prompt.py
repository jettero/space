# coding: utf-8

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

from .base import BaseShell, IntentionalQuit


class Shell(BaseShell):
    color = True

    def startup(self, init=None):
        self._session = PromptSession()
        self._patch = patch_stdout(raw=True)
        self._patch.__enter__()
        if isinstance(init, (tuple, list)):
            for cmd in init:
                self.do_step(cmd)

    def receive_message(self, msg):
        print(msg.render_text(color=self.color))

    def do_step(self, cmd):
        if cmd and not self.internal_command(cmd):
            try:
                self.do(cmd)
            except IntentionalQuit:
                self.stop()

    def internal_command(self, line):
        if line.startswith("/"):
            if line.strip() in ("/quit", "/exit"):
                self.stop()
            return True

    def step(self):
        try:
            line = self._session.prompt("/space/ ").strip()
            self.do_step(line)
        except (EOFError, KeyboardInterrupt):
            self.stop()
