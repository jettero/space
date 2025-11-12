# coding: utf-8

import asyncio
import os
import sys
from collections import deque

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.filters import has_completions, completion_is_selected
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.layout import Layout, HSplit, VSplit
from prompt_toolkit.layout.containers import Window, FloatContainer, Float
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.menus import MultiColumnCompletionsMenu
from prompt_toolkit.formatted_text.utils import to_formatted_text, split_lines
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.key_binding.bindings.scroll import (
    scroll_half_page_down,
    scroll_half_page_up,
    scroll_page_down,
    scroll_page_up,
)
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.key_binding.key_bindings import merge_key_bindings

import logging, re

from .base import BaseShell, IntentionalQuit
from space.verb import VERBS

log = logging.getLogger(__name__)


class MessageLexer(Lexer):
    def __init__(self, shell):
        self.shell = shell

    def lex_document(self, document):
        lines = self.shell.formatted_lines

        def get_line(i):
            if i < len(lines):
                return list(lines[i])
            return []

        return get_line


class KeywordFilter(logging.Filter):
    def __init__(self, *name_filters):
        self.name_filters = [re.compile(x) for x in name_filters]

    def filter(self, record):
        for nf in self.name_filters:
            if nf.search(record.name):
                return False
        return True


class ShellCompleter(Completer):
    def __init__(self, shell):
        self.shell = shell

    def get_completions(self, document, complete_event):
        before = document.text_before_cursor
        if not before.strip():
            return
        fragment = before.split()[-1] if before and not before[-1].isspace() else ""
        if fragment.startswith("/"):
            for attr in dir(self.shell):
                if attr.startswith("slash_"):
                    name = attr[6:]
                    if name.startswith(fragment[1:]):
                        yield Completion(f"/{name} ", start_position=-len(fragment), display=f"/{name}")
            return
        if fragment and len(before.strip().split()) <= 1:
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
    logging_opts = None
    message_limit = 800

    def startup(self, init=None):
        completer = ShellCompleter(self)
        custom_bindings = KeyBindings()

        self.reconfigure_logging(
            filename="shell.log", format="%(asctime)s %(name)17s %(levelname)5s %(message)s", level=logging.DEBUG
        )

        @custom_bindings.add("tab", filter=has_completions & ~completion_is_selected)
        def _(event):
            b = event.current_buffer
            word = b.document.get_word_before_cursor()
            comps = [c.text for c in b.complete_state.completions]

            # only if every completion still starts with the current word
            if all(c.startswith(word) for c in comps):
                prefix = os.path.commonprefix([c[len(word) :] for c in comps])
                b.insert_text(prefix)

        @custom_bindings.add("s-up")
        def _(event):
            self._scroll_messages_with(scroll_half_page_up, event)

        @custom_bindings.add("s-down")
        def _(event):
            self._scroll_messages_with(scroll_half_page_down, event)

        @custom_bindings.add("pageup")
        def _(event):
            self._scroll_messages_with(scroll_page_up, event)

        @custom_bindings.add("pagedown")
        def _(event):
            self._scroll_messages_with(scroll_page_down, event)

        @custom_bindings.add("c-d")
        def _(event):
            self.stop()

        @custom_bindings.add("c-a")
        def _(event):
            buffer = event.current_buffer
            buffer.cursor_position += buffer.document.get_start_of_line_position()

        @custom_bindings.add("c-e")
        def _(event):
            buffer = event.current_buffer
            buffer.cursor_position += buffer.document.get_end_of_line_position()

        bindings = merge_key_bindings([load_key_bindings(), custom_bindings])

        self.message_queue = deque(maxlen=self.message_limit)
        self.formatted_lines = [[]]
        self.stderr_handler = None

        self.message_window = Window(
            content=BufferControl(
                buffer=Buffer(read_only=True),
                focus_on_click=True,
                include_default_input_processors=False,
                lexer=MessageLexer(self),
            ),
            wrap_lines=True,
            always_hide_cursor=True,
            height=Dimension(weight=1),
        )
        self.message_buffer = self.message_window.content.buffer

        self.input_window = Window(
            content=BufferControl(
                buffer=Buffer(completer=completer, multiline=False, accept_handler=self._accept_input),
                focus_on_click=True,
            ),
            dont_extend_height=True,
        )

        self.application = Application(
            layout=Layout(
                FloatContainer(
                    content=HSplit(
                        [
                            self.message_window,
                            Window(height=Dimension.exact(1), char="─"),
                            VSplit(
                                [
                                    Window(
                                        content=FormattedTextControl(lambda: "/space/ "),
                                        dont_extend_height=True,
                                        width=len("/space/ "),
                                        always_hide_cursor=True,
                                    ),
                                    self.input_window,
                                ],
                                height=Dimension.exact(1),
                            ),
                        ],
                    ),
                    floats=[
                        Float(
                            content=MultiColumnCompletionsMenu(),
                            attach_to_window=self.input_window,
                            xcursor=True,
                            ycursor=True,
                        )
                    ],
                ),
                focused_element=self.input_window,
            ),
            key_bindings=bindings,
            full_screen=True,
            editing_mode=EditingMode.VI,
        )

        if isinstance(init, (tuple, list)):
            for cmd in init:
                self.do_step(cmd)

    def reconfigure_logging(self, **kw):
        opts = {k: v for k, v in kw.items() if v is not None}
        if isinstance(self.logging_opts, dict):
            for key, value in self.logging_opts.items():
                if key not in opts and value is not None:
                    opts[key] = value
        self.logging_opts = opts
        logging.root.handlers = []
        logging.basicConfig(**self.logging_opts)
        kwf = KeywordFilter("space.args")  # XXX: should be configurable
        for handler in logging.root.handlers:
            handler.addFilter(kwf)

    def receive_message(self, msg):
        doc = self.message_buffer.document
        previous_cursor = doc.cursor_position
        at_end = previous_cursor >= len(doc.text)
        colored = msg.render_text(color=True)
        plain = msg.render_text(color=False)
        log.debug("receive_message(%s)", colored)
        self.message_queue.append((colored, plain))
        display_source = plain_text = "\n".join(entry[1] for entry in self.message_queue)
        if self.color:
            display_source = "\n".join(entry[0] for entry in self.message_queue)
            fragments = to_formatted_text(ANSI(display_source))
        else:
            fragments = to_formatted_text(display_source)
        lines = [list(line) for line in split_lines(fragments)]
        self.formatted_lines = lines if lines else [[]]
        self.message_buffer.set_document(
            Document(plain_text, len(plain_text) if at_end else min(previous_cursor, len(plain_text))),
            bypass_readonly=True,
        )
        self.application.invalidate()

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
                return True
            self.owner.tell(f"unknown shell command: {line}")
            return True

    def step(self):
        pass

    def loop(self):
        if not self.application.is_running and not self._stop:
            try:
                self.application.run(
                    pre_run=self._install_exception_handler,
                    set_exception_handler=False,
                )
            except EOFError:
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
        super().stop(val=val, msg=msg)
        if self.application.is_running:
            self.application.exit()

    def _scroll_messages_with(self, handler, event):
        layout = event.app.layout
        previous = layout.current_window
        layout.focus(self.message_window)
        handler(event)
        if previous is not None:
            layout.focus(previous)

    def _accept_input(self, buff):
        line = buff.text.strip()
        buff.set_document(Document("", 0))
        if line:
            self.do_step(line)
        return True

    def _install_exception_handler(self):
        asyncio.get_running_loop().set_exception_handler(self._handle_application_exception)

    def _handle_application_exception(self, loop, context):
        exception = context.get("exception")
        if self.stderr_handler is None:
            self.stderr_handler = logging.StreamHandler(sys.stderr)
            if isinstance(self.logging_opts, dict) and "format" in self.logging_opts:
                self.stderr_handler.setFormatter(logging.Formatter(self.logging_opts["format"]))
            logging.getLogger().addHandler(self.stderr_handler)
        if exception is None:
            msg = context.get("message", "unknown application error")
            log.error("unhandled application exception: %s", msg)
        else:
            msg = context.get("message", str(exception))
            log.exception("unhandled application exception: %s", msg, exc_info=exception)
        self.stop()
