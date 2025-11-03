# coding: utf-8

import logging
import re
import threading
from typing import List

from .base import BaseShell, IntentionalQuit

log = logging.getLogger(__name__)

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.completion import Completer, Completion
import space.verb as _verbs


class _WordCompleter(Completer):
    """Top-level and internal command completer.

    Minimal completion behavior with sigils:
      - First word: complete from verb names
      - If line starts with '/': complete internal commands
      - After first word: use sigils
        - '$' tokens from StdObj in view
        - '@' tokens from Living in view
    """

    def __init__(self, get_line_start: callable, get_std_tokens: callable, get_living_tokens: callable):
        self.get_line_start = get_line_start
        self.get_std_tokens = get_std_tokens
        self.get_living_tokens = get_living_tokens

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

        # Split words to determine position (first word vs args)
        tokens = [p for p in parts if p]

        # First word: verbs
        if len(tokens) <= 1:
            exact = [w for w in _verbs.VERBS if w == frag]
            if exact:
                yield Completion(exact[0] + " ", start_position=-len(frag))
                return
            for w in _verbs.VERBS:
                if w.startswith(frag):
                    yield Completion(w + " ", start_position=-len(frag))
            return

        # Argument position: sigil-based completion
        if frag.startswith("$"):
            base = frag[1:]
            for t in self.get_std_tokens():
                if t.startswith(base):
                    yield Completion(t + " ", start_position=-len(frag))
            return
        if frag.startswith("@"):
            base = frag[1:]
            for t in self.get_living_tokens():
                if t.startswith(base):
                    yield Completion(t + " ", start_position=-len(frag))
            return


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
    _app = None
    _patch_cm = None
    _printing_lock = threading.Lock()
    color = True
    _logging_opts = None

    def startup(self, init=None):
        def get_line_start(txt):
            txt = txt.lstrip()
            return txt[:1] if txt else ""

        def get_std_tokens():
            return sorted({t for o in self.owner.nearby_objects for t in o.tokens})

        def get_living_tokens():
            return sorted({t for o in self.owner.nearby_livings for t in o.tokens})

        kb = KeyBindings()
        self._key_bindings = kb
        self._completer = _WordCompleter(get_line_start, get_std_tokens, get_living_tokens)

        @kb.add("tab")
        def _(event):
            buf = event.app.current_buffer
            # Probe completions without opening menu
            comps = list(self._completer.get_completions(buf.document, None))
            if not comps:
                buf.complete_state = None
                return
            # First-word special handling: work with verb names (no trailing space)
            text = buf.document.text_before_cursor
            parts = re.split(r"\s+", text)
            frag = parts[-1] if parts else ""
            is_first_word = len([p for p in parts if p]) <= 1 and (not text or not text.startswith("/"))

            if len(comps) == 1:
                if is_first_word:
                    # Insert verb + single trailing space
                    name = comps[0].text.strip()
                    buf.delete_before_cursor(len(frag))
                    buf.insert_text(name + " ")
                else:
                    buf.apply_completion(comps[0])
                buf.complete_state = None
                return
            # Multiple matches: attempt longest common prefix expansion
            # Compute insertion texts normalized
            if is_first_word:
                inserts = [c.text.strip() for c in comps]
            else:
                inserts = [c.text for c in comps]

            # Find longest common prefix among inserts
            def lcp(strs):
                if not strs:
                    return ""
                s1 = min(strs)
                s2 = max(strs)
                i = 0
                n = min(len(s1), len(s2))
                while i < n and s1[i] == s2[i]:
                    i += 1
                return s1[:i]

            common = lcp(inserts)
            # Only expand beyond current fragment; avoid inserting trailing space here
            if common and common.startswith(frag) and len(common) > len(frag):
                buf.insert_text(common[len(frag) :])
                buf.complete_state = None
                return
            # No unambiguous expansion left: open the menu
            buf.start_completion(select_first=False)

        @kb.add("s-tab")
        def _(event):
            st = event.app.current_buffer.complete_state
            if st is not None and st.completions:
                i = (st._selected_completion_index or 0) - 1
                if i >= 0:
                    st._selected_completion_index = i

        @kb.add("down")
        def _(event):
            st = event.app.current_buffer.complete_state
            if st is not None and st.completions:
                i = (st._selected_completion_index or -1) + 1
                if i < len(st.completions):
                    st._selected_completion_index = i

        @kb.add("up")
        def _(event):
            st = event.app.current_buffer.complete_state
            if st is not None and st.completions:
                i = (st._selected_completion_index or 0) - 1
                if i >= 0:
                    st._selected_completion_index = i

        @kb.add("enter")
        def _(event):
            buf = event.app.current_buffer
            st = buf.complete_state
            if st is not None and st.completions:
                if len(st.completions) == 1:
                    buf.apply_completion(st.completions[0])
                    st = None
            text = buf.text
            if text.strip():
                event.app.exit(result=text)
            else:
                # Blank line submits nothing; redraw prompt
                buf.reset()

        @kb.add("c-d")
        def _(event):
            event.app.exit(exception=EOFError)

        # Use simple PromptSession; keep prompt on last line without reserving space
        self._session = PromptSession()

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
            if self._session and self._session.app._is_running:
                return
            line = self._session.prompt(
                "/space/ ", completer=self._completer, reserve_space_for_menu=False, key_bindings=self._key_bindings
            ).strip()
            self.do_step(line)
        except (EOFError, KeyboardInterrupt):
            self.stop()
