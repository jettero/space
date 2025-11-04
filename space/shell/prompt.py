# coding: utf-8

# This is almost entirely written by AI, but following my framework for a
# readline shell.
#
# This stuff is particularly baffling to the AI cuz it can't see or use a
# shell, so it's hard to even describe what should or shouldn't happen and why.
#
# But we can go over some basics:
#
# 1. ^D and a literall EOF should exit the shell automatically, this allows
#    `./lrun-shell.py < /dev/null` to work, but also, if the user types a
#    literall ^D, the shell should also immediately exit.
# 2. readline was good about trying to use the whole screen. prompt-toolkit
#    seems to want to reserve lines at the bottom of the screen. I find this
#    unacceptable, but forcing the prompt to the bottom of the terminal window
#    has some annoying side effects. namely: if we pop up a floating menu
#    directly above the prompt, we can only see one line of the choices cuz
#    we're likely already at the last line of the terminal window
# 3. '$do<tab>' should complete to 'door', by looping the tokens for each
#    owner.nearby_objects
# 4. '@stu<tab>' should complete to 'stupid', by looping the tokens for each
#    owner.nearby_livings
# 5. whatever completions we do, we have to make sure they're formatted for the
#    parse(), so we can't leave stray leader-symbols in the text we try to
#    parse. iff @stupid is complete, the @ should evaporate automagically
# 6. never add ambiguous characters to a completion. If our choices are
#    'thingus' and 'thingamabob' and we try to complete 'th<tab>'
#    a. we can complete to 'thing' unambiguously and should do so
#    b. we can't really complete aything further until the user types a 'u' or
#       an 'a'. 'thingu<tab>' should give use "thingus" and move on.

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

        # Fallback: use default PromptSession; we will rely on internal menu
        # placement by prompt_toolkit and our Tab handler to show it.
        self._session = PromptSession(completer=self._completer, key_bindings=self._key_bindings, reserve_space_for_menu=False)

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
            line = self._session.prompt("/space/ ", reserve_space_for_menu=False).strip()
            self.do_step(line)
        except (EOFError, KeyboardInterrupt):
            self.stop()
