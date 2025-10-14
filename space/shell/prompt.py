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

        # Top-level words come from the parser words generator
        for w in self.get_words():
            if w.startswith(frag):
                yield Completion(w + " ", start_position=-len(frag))


class KeywordFilter(logging.Filter):
    def __init__(self, *name_filters):
        self.name_filters = [re.compile(x) for x in name_filters]

    def filter(self, record):
        for nf in self.name_filters:
            if nf.search(record.name):
                return False
        return True


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
    _logging_opts = None

    def startup(self, init=None):
        def get_words():
            return self.parser.words

        def get_line_start(txt):
            txt = txt.lstrip()
            return txt[:1] if txt else ""

        completer = _WordCompleter(get_words, get_line_start)
        self._session = PromptSession()
        self._completer = completer

        # Install stdout patching so prints during prompts render cleanly
        self._patch_cm = patch_stdout(raw=True)
        self._patch_cm.__enter__()

        # Match readline shell logging setup
        self.reconfigure_logging(
            filename="shell.log",
            format="%(asctime)s %(name)17s %(levelname)5s %(message)s",
            level=logging.DEBUG,
        )

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
        # Always route output through the prompt_toolkit application so the
        # current input line is preserved and the prompt is redrawn.
        rendered = msg.render_text(color=self.color)

        app = getattr(self._session, "app", None) if self._session else None
        if app is not None:
            # run_in_terminal prints outside the prompt area and then restores
            # the prompt, preventing interleaving with user input.
            def _flush():
                with self._printing_lock:
                    # Using print here is safe because run_in_terminal moves
                    # the cursor out of the prompt and restores it afterwards.
                    print(rendered)

            try:
                app.run_in_terminal(_flush)
                app.invalidate()
            except Exception:  # pylint: disable=broad-except
                # As a last resort, fall back to stdout (still under patch_stdout).
                with self._printing_lock:
                    print(rendered)
            return

        # If no session/app yet (early startup), just print.
        with self._printing_lock:
            print(rendered)

    def internal_command(self, line):
        if line.startswith("/"):
            cmd, *args = line[1:].split()
            if cmd == "debug":
                cl = self._logging_opts.get("level")
                nl = logging.INFO if cl == logging.DEBUG else logging.DEBUG
                self.reconfigure_logging(level=nl)
            elif cmd == "logfile":
                if not args or args[0] in ("off", "0", "false"):
                    self.reconfigure_logging(filename=None)
                else:
                    self.reconfigure_logging(filename=args[0])
            elif cmd in ("exit", "quit"):
                self.stop()
            else:
                self.owner.tell("/debug    toggle log debug (default: on)")
                self.owner.tell("/logfile  set the logfile location (default: shell.log)")
                self.owner.tell("/quit     exit the shell")
            return True

    def reconfigure_logging(self, **kw):
        def mydl(*dl):
            norepeat = set()
            for d in dl:
                if isinstance(d, dict):
                    for k, v in d.items():
                        if k not in norepeat:
                            if v is not None:
                                yield k, v
                        norepeat.add(k)

        self._logging_opts = {k: v for k, v in mydl(kw, self._logging_opts)}
        logging.root.handlers = []
        logging.basicConfig(**self._logging_opts)
        kwf = KeywordFilter("space.args")  # XXX: should be configurable
        for handler in logging.root.handlers:
            handler.addFilter(kwf)

    def do_step(self, cmd):
        if cmd and not self.internal_command(cmd):
            try:
                self.do(cmd)
            except IntentionalQuit:
                self.stop()

    def step(self):
        try:
            # Avoid re-entrant prompts (e.g., MCP stepping other shells)
            if self._session.app._is_running:
                return
            # Provide completer each prompt to honor dynamic parser.words
            # Reserve no extra space below the prompt for menus to keep it at bottom.
            line = self._session.prompt("/space/ ", completer=self._completer, reserve_space_for_menu=False).strip()
            self.do_step(line)
        except (EOFError, KeyboardInterrupt):
            self.stop()
