# coding: utf-8

import os
import sys

from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.filters import Condition, has_completions, completion_is_selected
from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.formatted_text.utils import to_formatted_text, to_plain_text
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.defaults import load_key_bindings
from prompt_toolkit.key_binding.key_bindings import merge_key_bindings
from prompt_toolkit.layout import Layout, HSplit, VSplit
from prompt_toolkit.layout.containers import Window, FloatContainer, Float
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl, UIControl, UIContent
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.menus import MultiColumnCompletionsMenu

import logging, re

from .base import BaseShell, IntentionalQuit
from .minimap import Minimap
from .pane import Record, anchor_step, clip_fragments, drop_fragments, layout_rows, splice_fragments
from space.find import set_this_body, this_body
from space.msg import MapMessage
from space.verb import VERBS

log = logging.getLogger(__name__)


class SpaceMessageLog:
    """
    The shell's scrollback, stored as one Record per physical line.

    Ephemeral records (map drawings) are superseded by the next map that
    arrives and are dropped once `linger` lines from later messages have
    piled up under them -- nobody scrolls back to a map they walked away from.
    """

    def __init__(self, limit=1000, color=True, linger=8):
        self.limit = limit
        self.color = color
        self.linger = linger
        self.records = list()
        self.seq = 0

    def __len__(self):
        return len(self.records)

    def __bool__(self):
        return bool(self.records)

    def __getitem__(self, i):
        return self.records[i]

    def make_record(self, text, rigid, ephemeral):
        fragments = to_formatted_text(ANSI(text)) if self.color else [("", text)]
        return Record(fragments, to_plain_text(fragments), rigid, ephemeral, self.seq)

    def append(self, msg, drawings=True):
        self.seq += 1
        new = [self.make_record(*x) for x in msg.render_lines(color=self.color, drawings=drawings)]
        if any(r.ephemeral for r in new):
            self.records = [r for r in self.records if not r.ephemeral]
        self.records += new
        self.expire()
        if (d := len(self.records) - self.limit) > 0:
            self.records = self.records[d:]
        log.debug("SpaceMessageLog.append() len(records)=%d", len(self.records))

    def expire(self):
        if not (eph := [r for r in self.records if r.ephemeral]):
            return
        if sum(1 for r in self.records if r.seq > eph[-1].seq) >= self.linger:
            log.debug("SpaceMessageLog.expire() dropping map block seq=%d", eph[-1].seq)
            self.records = [r for r in self.records if not r.ephemeral]


class MessagePaneControl(UIControl):
    """
    The message pane.  create_content() is handed the window's exact geometry
    by the renderer, which is the only place that geometry is knowable without
    a tty, so all the wrapping and minimap splicing happens right here.
    """

    def __init__(self, shell):
        self.shell = shell
        self.width = 80
        self.height = 24

    def create_content(self, width, height):
        self.width, self.height = width, height
        rows = self.shell.render_pane(width, height) or [[]]
        return UIContent(get_line=lambda i: rows[i], line_count=len(rows), show_cursor=False)


class FullMapControl(UIControl):
    """The `/map` pane: a full-window pannable view of what the owner can see."""

    def __init__(self, shell):
        self.shell = shell

    def create_content(self, width, height):
        rows = self.shell.render_full_map(width, height) or [[]]
        return UIContent(get_line=lambda i: rows[i], line_count=len(rows), show_cursor=False)


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


def input_is_empty(shell):
    return Condition(lambda: not get_app().current_buffer.text)


def showing_full_map(shell):
    return Condition(lambda: shell.full_map)


TRUTHY = {"on": True, "true": True, "yes": True, "off": False, "false": False, "no": False}


def flag(text, default=None):
    """A slash-command on/off argument; `default` when it says neither."""

    return TRUTHY.get(text.strip().lower(), default)


def config_value(text):
    """A /config right-hand side: on/off/true/false/yes/no, an int, or a string."""

    if (found := flag(text)) is not None:
        return found
    if (stripped := text.strip()).lstrip("-").isdigit():
        return int(stripped)
    return stripped


def completing(shell):
    return has_completions & ~completion_is_selected


class Shell(BaseShell):
    color = True
    logging_opts = None
    message_limit = 800
    map_linger = 8

    # a minimap and an inline map are the same information twice, so the
    # defaults are mutually exclusive; /config will happily turn both on
    default_config = {"maps.minimap": True, "maps.inline": False}

    # key -> (handler method name, filter factory or None)
    key_table = (
        ("c-l", "key_refresh", None),
        ("c-o", "key_fold_minimap", None),
        ("c-i", "key_fold_minimap", input_is_empty),
        ("tab", "key_complete_common_prefix", completing),
        ("s-up", "key_scroll_up", None),
        ("s-down", "key_scroll_down", None),
        ("c-d", "key_quit", None),
        ("c-a", "key_line_start", None),
        ("c-e", "key_line_end", None),
        ("left", "key_pan_west", showing_full_map),
        ("right", "key_pan_east", showing_full_map),
        ("up", "key_pan_north", showing_full_map),
        ("down", "key_pan_south", showing_full_map),
        ("escape", "key_close_map", showing_full_map),
        ("q", "key_close_map", showing_full_map),
    )

    @property
    def terminal_size(self):
        """
        (columns, rows) of the terminal we are drawing on.

        Asks the application's Output rather than os.get_terminal_size(),
        which raises OSError whenever stdout is not a tty -- under pytest that
        turned every inline map into a swallowed exception.
        """

        size = self.application.output.get_size()
        return size.columns, size.rows

    def preflight(self, init=None):
        completer = ShellCompleter(self)
        custom_bindings = KeyBindings()

        self.reconfigure_logging(
            # XXX: this should require a filename arg and should be invoked by the
            # user we'll leave it for now cuz it's handy for debugging
            filename="shell.log",
            format="%(asctime)s %(name)17s %(levelname)5s %(message)s",
            level=logging.DEBUG,
        )

        for key, name, mkfilter in self.key_table:
            custom_bindings.add(key, filter=True if mkfilter is None else mkfilter(self))(getattr(self, name))

        self.config = dict(self.default_config)
        self.map_view = None
        self.full_map = False
        self.map_buffer = list()
        self.map_pan = (0, 0)
        self.scroll_anchor = None
        self.minimap = Minimap(self)
        self.message_log = SpaceMessageLog(limit=self.message_limit, color=self.color, linger=self.map_linger)
        self.pane_control = MessagePaneControl(self)
        self.map_control = FullMapControl(self)

        self.message_window = Window(
            content=self.pane_control,
            wrap_lines=False,
            always_hide_cursor=True,
            height=Dimension(weight=1),
        )

        self.input_window = Window(
            content=BufferControl(
                buffer=Buffer(name="input buf", completer=completer, multiline=False, accept_handler=self._accept_input),
            ),
            dont_extend_height=True,
            wrap_lines=True,
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
                                        always_hide_cursor=False,
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
            key_bindings=merge_key_bindings([load_key_bindings(), custom_bindings]),
            full_screen=True,
            editing_mode=EditingMode.VI,
        )

        if isinstance(init, (tuple, list)):
            for cmd in init:
                self.do_step(cmd)

    def render_pane(self, width: int, height: int) -> list:
        """
        Lay the scrollback out for a width×height pane and splice the minimap
        into the top-right corner of the result.
        """

        mm = self.minimap.rows(width, height)
        rows = layout_rows(
            self.message_log.records,
            width,
            height,
            band_w=self.minimap.width if mm else 0,
            band_h=len(mm),
            anchor=self.scroll_anchor,
        )
        for r, mrow in enumerate(mm):
            rows[r] = rows[r] + mrow
        return rows

    def draw_map(self, a_map) -> list:
        """
        Render a map the way our owner sees it, one text line per cell row.

        Establishing the viewer matters: Living.abbr resolves to "@" only for
        the active body, and set_this_body() is the only thing that sets that.
        The parser does it around a turn, so a player's own turn leaves them
        active until something else acts -- which means a display cannot
        inherit the flag, it has to declare it.  A display is a player command
        that happens not to go through the parser, so it names its viewpoint
        and puts back whatever it found.
        """

        prior = this_body()
        set_this_body(self.owner)
        drawing = a_map.colorized_text_drawing if self.color else a_map.text_drawing
        set_this_body(prior)
        return drawing.split("\n")

    def build_map_buffer(self):
        """
        Draw the stored map at its full line-of-sight extent, once, into a
        row buffer.  Panning is then a scroll offset into that buffer -- no
        redraw per keypress, per keystroke, or per resize.
        """

        if (owner := self.owner) is None or self.map_view is None:
            self.map_buffer = [[("", "no map yet — look around first")]]
            self.map_pan = (0, 0)
            return
        self.map_buffer = [to_formatted_text(ANSI(x)) for x in self.draw_map(self.map_view)]
        bounds = self.map_view.bounds
        self.map_pan = (
            max(0, owner.location.pos[0] - bounds.x - self.pane_control.width // 2),
            max(0, owner.location.pos[1] - bounds.y - self.pane_control.height // 2),
        )

    def render_full_map(self, width: int, height: int) -> list:
        """
        Blit a width×(height-1) window of the map buffer at self.map_pan,
        with a status row underneath and a chevron on each edge that has more
        buffer beyond it.
        """

        col, row = self.map_pan
        rows = [clip_fragments(drop_fragments(x, col), width) for x in self.map_buffer[row : row + height - 1]]
        rows += [[] for _ in range(height - 1 - len(rows))]

        if col > 0:
            rows[len(rows) // 2] = splice_fragments(rows[len(rows) // 2], 0, "◄")
        if max((sum(len(f[1]) for f in x) for x in self.map_buffer), default=0) > col + width:
            rows[len(rows) // 2] = splice_fragments(rows[len(rows) // 2], width - 1, "►")
        if row > 0:
            rows[0] = splice_fragments(rows[0], width // 2, "▲")
        if len(self.map_buffer) > row + height - 1:
            rows[-1] = splice_fragments(rows[-1], width // 2, "▼")

        where = tuple(self.owner.location.pos) if self.owner is not None else "nowhere"
        return rows + [[("", f" you {where}  view +{col},+{row}  — arrows pan, q/escape closes"[:width])]]

    def reconfigure_logging(self, **kw):
        try:
            # this is not the right way to do this. There's certainly an arg we
            # could provide to trunace the log
            if self.logging_opts and (f := self.logging_opts.get("filename")):
                if os.path.isfile(f):
                    os.unlink(f)
        except FileNotFoundError:
            pass
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
        if isinstance(msg, MapMessage):
            self.map_view = msg.map
        self.message_log.append(msg, drawings=self.config["maps.inline"])
        self.application.invalidate()

    def do_step(self, cmd):
        if cmd and not self.internal_command(cmd):
            try:
                self.do(cmd)
            except IntentionalQuit:
                self.stop()

    @property
    def half_page(self):
        if r := self.message_window.render_info:
            return max(5, r.window_height // 2)
        return 5

    def scroll_pane(self, delta):
        self.scroll_anchor = anchor_step(self.message_log.records, self.scroll_anchor, delta, self.pane_control.width)
        log.debug("scroll_pane(%d) anchor=%s", delta, self.scroll_anchor)
        self.application.invalidate()

    def pan(self, dx, dy):
        self.map_pan = (
            max(0, min(self.map_pan[0] + dx, max((sum(len(f[1]) for f in x) for x in self.map_buffer), default=1) - 1)),
            max(0, min(self.map_pan[1] + dy, len(self.map_buffer) - 1)),
        )
        self.application.invalidate()

    def show_full_map(self, on=None):
        self.full_map = (not self.full_map) if on is None else on
        if self.full_map:
            self.build_map_buffer()
        self.message_window.content = self.map_control if self.full_map else self.pane_control
        self.application.invalidate()

    def key_refresh(self, event):
        self.application.renderer.clear()
        self.application.invalidate()

    def key_fold_minimap(self, event):
        self.slash_mm()

    def key_complete_common_prefix(self, event):
        b = event.current_buffer
        word = b.document.get_word_before_cursor()
        comps = [c.text for c in b.complete_state.completions]

        # only if every completion still starts with the current word
        if all(c.startswith(word) for c in comps):
            b.insert_text(os.path.commonprefix([c[len(word) :] for c in comps]))

    def key_scroll_up(self, event):
        self.scroll_pane(-self.half_page)

    def key_scroll_down(self, event):
        self.scroll_pane(self.half_page)

    def key_quit(self, event):
        self.stop()

    def key_line_start(self, event):
        event.current_buffer.cursor_position += event.current_buffer.document.get_start_of_line_position()

    def key_line_end(self, event):
        event.current_buffer.cursor_position += event.current_buffer.document.get_end_of_line_position()

    def key_pan_north(self, event):
        self.pan(0, -1)

    def key_pan_south(self, event):
        self.pan(0, 1)

    def key_pan_west(self, event):
        self.pan(-1, 0)

    def key_pan_east(self, event):
        self.pan(1, 0)

    def key_close_map(self, event):
        self.show_full_map(False)

    def slash_quit(self, arg=""):
        self.stop()

    slash_exit = slash_quit

    def slash_config(self, arg=""):
        """
        /config                    list every setting
        /config maps.inline        show one setting
        /config maps.inline = off  set one setting
        """

        if not (arg := arg.strip()):
            for key in sorted(self.config):
                self.receive_text(f"{key} = {self.config[key]}")
            return
        key, eq, value = arg.partition("=")
        if (key := key.strip()) not in self.config:
            self.receive_text(f"unknown config key: {key}")
            return
        if eq:
            self.config[key] = config_value(value)
        self.receive_text(f"{key} = {self.config[key]}")
        self.application.invalidate()

    def slash_minimap(self, arg=""):
        self.set_map_mode(minimap=flag(arg, not self.config["maps.minimap"]))

    def slash_inline(self, arg=""):
        self.set_map_mode(inline=flag(arg, not self.config["maps.inline"]))

    def slash_mm(self, arg=""):
        """Swap the map between the minimap band and the message flow."""

        self.set_map_mode(minimap=(on := flag(arg, not self.config["maps.minimap"])), inline=not on)

    def set_map_mode(self, minimap=None, inline=None):
        if minimap is not None:
            self.config["maps.minimap"] = minimap
        if inline is not None:
            self.config["maps.inline"] = inline
        self.application.invalidate()

    def slash_map(self, arg=""):
        self.show_full_map(flag(arg))

    def internal_command(self, line):
        if line.startswith("/"):
            name, _, rest = line[1:].partition(" ")
            if f := getattr(self, f"slash_{name}", None):
                f(rest.strip())
                return True
            self.receive_text(f"unknown shell command: {line}")
            return True

    def step(self):
        pass

    def start(self):
        if not self.application.is_running and not self._stop:
            try:
                self.application.run(set_exception_handler=False)
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

    def _accept_input(self, buff):
        if line := buff.text.strip():
            # buff is the commandline input buffer, so if we got a command, we
            # should do the needful
            self.do_step(line)
        buff.set_document(Document("", 0))
        return True

    def handle_application_exception(self, loop, context):
        exception = context.get("exception")
        stderr_handler = logging.StreamHandler(sys.stderr)
        if isinstance(self.logging_opts, dict) and "format" in self.logging_opts:
            stderr_handler.setFormatter(logging.Formatter(self.logging_opts["format"]))
        logging.getLogger().addHandler(stderr_handler)
        if exception is None:
            msg = context.get("message", "unknown application error")
            log.error("unhandled application exception: %s", msg)
        else:
            msg = context.get("message", str(exception))
            log.exception("unhandled application exception: %s", msg, exc_info=exception)
        self.stop()
