# coding: utf-8

import logging
import re
import threading
from typing import List

from .base import BaseShell, IntentionalQuit

log = logging.getLogger(__name__)

from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.completion import Completer, Completion


class _WordCompleter(Completer):
    """Top-level and internal command completer.

    Mirrors readline.py's minimal completion behavior:
      - At start of line, complete from parser.words
      - If first char is '/', complete internal commands
    """

    def __init__(self, get_words, get_line_start: callable):
        self.get_words = get_words
        self.get_line_start = get_line_start

    def get_completions(self, document, complete_event):  # noqa: D401
        # prompt_toolkit calls this during completion; yield Completion
        text = document.text_before_cursor
        # Determine current token to complete
        # Split on whitespace; complete the last fragment
        parts = re.split(r"\s+", text)
        frag = parts[-1] if parts else ""

        # Internal commands start with '/'
        if self.get_line_start(text) == "/":
            words = ["debug", "logfile", "quit", "help"]
            for w in words:
                if w.startswith(frag):
                    yield Completion(w, start_position=-len(frag))
            return

        # Top-level words come from the parser
        for w in self.get_words():
            if w.startswith(frag):
                yield Completion(w + " ", start_position=-len(frag))


class Shell(BaseShell):
    """prompt_toolkit-powered interactive shell.

    - Keeps the same public behavior as readline Shell.
    - Uses patch_stdout() to safely print async messages while prompting.
    - Minimal completion parity with space/shell/readline.py.
    """

    _session = None
    _patch_cm = None
    _printing_lock = threading.Lock()
    color = True

    def startup(self, init=None):
        # Build session with our completer
        def get_words():
            try:
                return list(self.parser.words)
            except Exception:  # pylint: disable=broad-except
                return []

        def get_line_start(txt):
            # strip leading spaces to emulate beginning-of-line behavior
            txt = txt.lstrip()
            return txt[:1] if txt else ""

        completer = _WordCompleter(get_words, get_line_start)
        self._session = PromptSession()
        self._completer = completer

        # Install stdout patching so prints during prompts render cleanly
        self._patch_cm = patch_stdout(raw=True)
        self._patch_cm.__enter__()

        if isinstance(init, (tuple, list)):
            for cmd in init:
                self.do_step(cmd)

    def shutdown(self):
        # Best-effort cleanup of patch_stdout context
        if self._patch_cm is not None:
            try:
                self._patch_cm.__exit__(None, None, None)
            finally:
                self._patch_cm = None

    def _finalize(self):  # explicit finalizer for cleanup
        try:
            self.shutdown()
        except Exception:  # pylint: disable=broad-except
            pass

    # Messages arriving asynchronously while prompting are safely printed
    def receive_message(self, msg):
        with self._printing_lock:
            # patch_stdout ensures clean line handling during prompts
            print(msg.render_text(color=self.color))

    def internal_command(self, line):
        if line.startswith("/"):
            cmd, *args = line[1:].split()
            if cmd == "debug":
                # Toggle debug/info by reusing logging.root level
                cl = logging.getLogger().level
                nl = logging.INFO if cl == logging.DEBUG else logging.DEBUG
                logging.getLogger().setLevel(nl)
            elif cmd == "logfile":
                # Delegate to base behavior by sending owner a help text
                if not args or args[0] in ("off", "0", "false"):
                    # Users of prompt_toolkit shell likely rely on external logging
                    # Keep semantics minimal: disable FileHandlers if present
                    root = logging.getLogger()
                    for h in list(root.handlers):
                        if getattr(h, "baseFilename", None):
                            root.removeHandler(h)
                else:
                    fn = args[0]
                    root = logging.getLogger()
                    fh = logging.FileHandler(fn)
                    fmt = logging.Formatter("%(asctime)s %(name)17s %(levelname)5s %(message)s")
                    fh.setFormatter(fmt)
                    root.addHandler(fh)
            elif cmd in ("exit", "quit"):
                self.stop()
            else:
                self.owner.tell("/debug    toggle log debug (default: on)")
                self.owner.tell("/logfile  set the logfile location (default: shell.log)")
                self.owner.tell("/quit     exit the shell")
            return True

    def do_step(self, cmd):
        if cmd and not self.internal_command(cmd):
            try:
                self.do(cmd)
            except IntentionalQuit:
                self.stop()

    def step(self):
        try:
            # Avoid re-entrant prompts (e.g., MCP stepping other shells)
            app = getattr(self._session, "app", None)
            if app is not None and getattr(app, "_is_running", False):
                return
            # Provide completer each prompt to honor dynamic parser.words
            line = self._session.prompt("ssr> ", completer=self._completer).strip()
            self.do_step(line)
        except (EOFError, KeyboardInterrupt):
            self.stop()
