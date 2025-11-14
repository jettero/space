import io
from types import SimpleNamespace

from prompt_toolkit.application import create_app_session
from prompt_toolkit.application.current import set_app
from prompt_toolkit.buffer import CompletionState
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document
from prompt_toolkit.keys import Keys
from prompt_toolkit.output.base import ColorDepth, Size
from prompt_toolkit.output.vt100 import Vt100_Output

from space.msg import TextMessage
from space.shell import prompt as prompt_module
from space.shell.prompt import Shell

from t.shellexpect import render_terminal


TERMINAL_WIDTH = 80
TERMINAL_HEIGHT = 25


def build_output(width=TERMINAL_WIDTH, height=TERMINAL_HEIGHT):
    stream = io.StringIO()
    output = Vt100_Output(
        stream,
        lambda: Size(rows=height, columns=width),
        term="xterm-256color",
        default_color_depth=ColorDepth.DEPTH_24_BIT,
        enable_bell=False,
        enable_cpr=False,
    )
    return stream, output


def render_once(shell, stream):
    with set_app(shell.application):
        shell.application.renderer.render(shell.application, shell.application.layout)
    data = stream.getvalue()
    stream.seek(0)
    stream.truncate(0)
    return data


def freeze_history(shell):
    for window in (shell.input_window, shell.message_window):
        window.content.buffer._load_history_task = True


def hiya_numbers(lines):
    return [
        int(line[start + 4 : end])
        for line in lines
        if (start := line.find("Hiya")) != -1 and (end := line.rfind('."')) != -1
    ]


def find_binding(shell, key):
    for binding in shell.application.key_bindings.get_bindings_for_keys((key,)):
        if binding.handler.__qualname__.startswith("Shell.preflight"):
            return binding.handler
    raise AssertionError("binding not found")


def test_message_window_scrolls_half_page():
    stream, output = build_output()
    with create_app_session(output=output):
        shell = Shell()
        freeze_history(shell)
        for i in range(200):
            shell.receive_message(TextMessage(f'You say, "Hiya{i}."'))
        initial = render_once(shell, stream)
        find_binding(shell, Keys.ShiftUp)(None)
        scrolled = render_once(shell, stream)
    initial_lines, _, _ = render_terminal(initial, width=TERMINAL_WIDTH, height=TERMINAL_HEIGHT)
    scrolled_lines, _, _ = render_terminal(initial + scrolled, width=TERMINAL_WIDTH, height=TERMINAL_HEIGHT)
    initial_numbers = hiya_numbers(initial_lines)
    scrolled_numbers = hiya_numbers(scrolled_lines)
    assert initial_numbers and scrolled_numbers
    assert len(initial_numbers) == len(scrolled_numbers)
    assert initial_numbers[0] - scrolled_numbers[0] == 11
    assert initial_numbers[-1] - scrolled_numbers[-1] == 11


def test_completions_menu_renders():
    stream, output = build_output()
    with create_app_session(output=output):
        shell = Shell()
        freeze_history(shell)
        buf = shell.input_window.content.buffer
        doc = Document("lo", 2)
        buf.set_document(doc)
        completions = list(buf.completer.get_completions(doc, CompleteEvent(completion_requested=True)))
        buf.complete_state = CompletionState(doc, completions, complete_index=0)
        text = render_once(shell, stream)
    lines, _, _ = render_terminal(text, width=TERMINAL_WIDTH, height=TERMINAL_HEIGHT)
    assert any("lol - Emote(lol)" in line for line in lines)
    assert any("look - Action(look)" in line for line in lines)
    assert lines[-1] == "/space/ lo"


def test_tab_completion_inserts_common_prefix(monkeypatch):
    monkeypatch.setattr(
        prompt_module,
        "VERBS",
        {"more": "desc", "morn": "desc", "morning": "desc"},
        raising=False,
    )
    stream, output = build_output()
    with create_app_session(output=output):
        shell = Shell()
        freeze_history(shell)
        buf = shell.input_window.content.buffer
        doc = Document("mo", 2)
        buf.set_document(doc)
        completions = list(buf.completer.get_completions(doc, CompleteEvent(completion_requested=True)))
        buf.complete_state = CompletionState(doc, completions)
        with set_app(shell.application):
            find_binding(shell, Keys.Tab)(SimpleNamespace(current_buffer=buf))
        text = render_once(shell, stream)
    assert buf.text == "mor"
    lines, _, _ = render_terminal(text, width=TERMINAL_WIDTH, height=TERMINAL_HEIGHT)
    assert lines[-1] == "/space/ mor"
