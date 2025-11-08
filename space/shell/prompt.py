# coding: utf-8

# This is supposed to behave more or less like a readline shell, but with async
# events streaming in and better tab completion.
#
# We have to be very careful here to not re-invent the wheel. prompt-toolkit
# has a lot of built in functionality and options that we should try to use
# before hand-rolling our own stupid shitware.
#
# However, we want to make sure of the following things:
#
#########  Shell Behavior
# 0. EOF and ^D, should exit the shell cleanly.
# 1. SIGINT and SIGTERM should exit the shell cleanly and tell the user
#    "received interrupt signal. see ya" or some such
# 2. The prompt should be allowed to reach the bottom of the terminal window.
#    This is worth mentioning in prompt-toolkit because by default it tries to
#    reserve room for a floating menu and we end up with 3-5 blank lines at the
#    bottom of the terminal window that are never used for anything. ick.
# 3. the main exception to the prompt at the end of the window would be if the
#    user input wraps at the right edge of the terminal; in which case we,
#    should certainly let the prompt move up a line so we can see all the
#    input.
#
#########  Tab Completion
# With respect to completion, the following should also always be true. Assume
# all available tokens for the below assertion are `['override', 'overflow',
# 'overwhelm', 'open', 'smile', 'smirk', 'grin']`
#
# 0. we should be trying to mimic the default completion modes of
#    readline/bash, prompt toolkit wants to do the cycle-through-choices thing
#    by default and it's awful and horrible and we don't want that by default
#    -- although we may add it as a configurable option later
# 1. tab completion should never add characters the user didn't type (besides
#    possibly a space after a full completion)
# 2. never guess for the user if the choice is ambiguous
# 3. if the input is empty and the user issues a '<tab>', nothing should happen
#    since the choice is totally ambiguous and the user typed 'o<tab>'
# 4. if the input is empty (called e-in from now on), 'o<tab>' should still not
#    do anything since we can't guess if the user wants a 'v' or a 'p' or an
#    'm' next.
# 5. however, if we add a 'v' so we're at 'ov' and type a '<tab>' it can and
#    should complete to 'over'
# 6. at e-in if we type 'over<tab>' or if we simply type a '<tab>' after it
#    completes to 'over', nothing should happen since we can't know if they
#    (the user) mean to go with 'w' or 'r' or 'f' next.
#
#########  Choice Display
# 0. in the above scenarios if we ever type '<tab><tab>' without any edits
#    between them -- and to be clear, that's a single '<tab>' followed by
#    another '<tab>' without typing any letters, spaces, arrows, backspaces or
#    any other characters/codes in between; we should (only in this case)
#    display a list of available completions.
# 1. ideally, the list of choices should be some kind of pop-up menu we can use
#    the arrow keys to navigate, but it should update when we type something.
# 2. if it pops up above the prompt, the lower left corner should align with
#    the typed text
# 3. and if it obscures any text, that text should be restored when the menu
#    goes away or shrinks in size
# 4. we would prefer said menu to pop up above the prompt line so we don't have
#    to move the pump up from the bottom of the terminal window
# 5. prompt-toolkit does have built in mechanisms for floating-menu popups
#    relating to tab completion, but by default the spawn below the prompt,
#    which messes up our goal of keeping the prompt as close to the bottom of
#    the screen as possible.
# 6. the CompleteStyle.READLINE sucks and CompleteStyle.MULTI_COLUMN is better,
#    despite the above.

import os
from collections import deque

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.application.current import get_app_or_none
from prompt_toolkit.filters import has_completions, completion_is_selected
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.layout import Layout, HSplit, VSplit, ScrollablePane
from prompt_toolkit.layout.containers import Window, FloatContainer, Float
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.menus import MultiColumnCompletionsMenu
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.key_binding.key_bindings import merge_key_bindings

from .base import BaseShell, IntentionalQuit
from space.verb import VERBS


class ShellCompleter(Completer):
    def __init__(self, shell):
        self.shell = shell

    def get_completions(self, document, complete_event):
        app = get_app_or_none()
        actual_before = document.text_before_cursor if app is None else app.current_buffer.document.text_before_cursor
        if not actual_before.strip():
            return
        fragment = actual_before.split()[-1] if actual_before and not actual_before[-1].isspace() else ""
        if fragment.startswith("/"):
            for name in [x[6:] for x in dir(ps) if x.startswith("slash_")]:
                if name.startswith(fragment[1:]):
                    yield Completion(f"/{name} ", start_position=-len(fragment), display=f"/{name}")
            return
        if fragment and len(actual_before.strip().split()) <= 1:
            for name in sorted(VERBS):
                if name.startswith(fragment):
                    yield Completion(f"{name} ", start_position=-len(fragment), display=f"{name} - {VERBS[name]!r}")
            return
        if fragment.startswith("$"):
            prefix = fragment[1:]
            for token in self.shell.get_std_tokens():
                if not prefix or token.startswith(prefix):
                    yield Completion(f"{token} ", start_position=-len(fragment), display=token)
            return
        if fragment.startswith("@"):
            prefix = fragment[1:]
            for token in self.shell.get_living_tokens():
                if not prefix or token.startswith(prefix):
                    yield Completion(f"{token} ", start_position=-len(fragment), display=token)
            return
        return


class Shell(BaseShell):
    color = True

    def startup(self, init=None):
        completer = ShellCompleter(self)
        custom_bindings = KeyBindings()

        @custom_bindings.add("tab", filter=has_completions & ~completion_is_selected)
        def _(event):
            b = event.current_buffer
            word = b.document.get_word_before_cursor()
            comps = [c.text for c in b.complete_state.completions]

            # only if every completion still starts with the current word
            if all(c.startswith(word) for c in comps):
                prefix = os.path.commonprefix([c[len(word) :] for c in comps])
                b.insert_text(prefix)

        bindings = merge_key_bindings([load_key_bindings(), custom_bindings])

        self._prompt_text = "/space/ "
        self._message_chunks = deque(maxlen=800)
        self._message_formatted = ""

        self.message_control = FormattedTextControl(lambda: self._message_formatted or "")
        self._message_window = Window(
            content=self.message_control,
            wrap_lines=True,
            always_hide_cursor=True,
        )
        self._message_pane = ScrollablePane(self._message_window, show_scrollbar=False)

        self.input_buffer = Buffer(
            completer=completer,
            complete_while_typing=False,
            multiline=False,
            accept_handler=self._accept_input,
        )
        self.input_control = BufferControl(buffer=self.input_buffer, focus_on_click=True)
        prompt_window = Window(
            content=FormattedTextControl(lambda: self._prompt_text),
            dont_extend_height=True,
            width=len(self._prompt_text),
            always_hide_cursor=True,
        )
        self._input_window = Window(
            content=self.input_control,
            dont_extend_height=True,
        )

        bottom = VSplit(
            [
                prompt_window,
                self._input_window,
            ],
            height=Dimension.exact(1),
        )

        body = HSplit(
            [
                self._message_pane,
                Window(height=Dimension.exact(1), char="─"),
                bottom,
            ],
            padding=0,
        )

        root = FloatContainer(
            content=body,
            floats=[
                Float(
                    content=MultiColumnCompletionsMenu(),
                    attach_to_window=self._input_window,
                    xcursor=True,
                    ycursor=True,
                )
            ],
        )

        self.application = Application(
            layout=Layout(root, focused_element=self._input_window),
            key_bindings=bindings,
            full_screen=True,
            editing_mode=EditingMode.VI,
        )

        # wtf is this for?
        self._patch = patch_stdout(raw=True)
        self._patch.__enter__()

        if isinstance(init, (tuple, list)):
            for cmd in init:
                self.do_step(cmd)

    def receive_message(self, msg):
        self._append_message( msg.render_text(color=self.color) )

    def do_step(self, cmd):
        if cmd and not self.internal_command(cmd):
            try:
                self.do(cmd)
            except IntentionalQuit:
                self.stop()

    def slash_quit(self):
        self.stop()

    slash_exit = slash_quit

    def internal_command(self, line):
        if line.startswith("/"):
            if f := getattr(self, f"slash_{line[1:]}", None):
                f()
                return
            self.owner.tell(f"unknown shell command: {line}")
            return True

    def step(self):
        pass

    def loop(self):
        try:
            self.application.run()
        except (EOFError, KeyboardInterrupt, IntentionalQuit):
            self.stop()

    def get_std_tokens(self):
        """
        tokens to complete words prefixed with '$'
        if the tokens are (e.g.) `["useless", "bauble"]`, `"$us"` could complete to `"useless"`
        """
        owner = self.owner
        if owner is None:
            return []
        return sorted({t for o in owner.nearby_objects for t in o.tokens})

    def get_living_tokens(self):
        """
        tokens to complete words prefixed with '@'
        if the tokens are (e.g.) `["stupid", "skellyman"]`, `"@st"` could complete to `"stupid"`
        """
        owner = self.owner
        if owner is None:
            return []
        return sorted({t for l in owner.nearby_livings for t in l.tokens})

    def stop(self, val=True, msg="see ya."):
        if not self._stop:
            super().stop(val, msg)
        if hasattr(self, "application") and self.application is not None:
            self.application.exit()

    def _append_message(self, text):
        if self._message_chunks:
            self._message_chunks.append("")
        self._message_chunks.append("" if text is None else text)
        joined = "\n".join(self._message_chunks)
        self._message_formatted = ANSI(joined) if self.color else joined
        self._scroll_messages_to_bottom()
        self._invalidate()

    def _accept_input(self, buff):
        line = buff.text.strip()
        buff.set_document(Document("", 0))
        if line:
            self.do_step(line)
        return True

    def _invalidate(self):
        if hasattr(self, "application") and self.application is not None:
            self.application.invalidate()

    def _scroll_messages_to_bottom(self):
        self._message_window.vertical_scroll = 10**6
        self._message_pane.vertical_scroll = 10**6
