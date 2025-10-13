import json
from pathlib import Path

from scripts.mudos_save_translator import to_synthetic_map
from contrib.tools.lpc_parser import parse


def load_expected():
    return json.loads(Path("t/converter_test.json").read_text(encoding="utf-8"))


def load_input_text():
    return Path("t/converter_test.o").read_text(encoding="utf-8")


def _normalize(obj):
    # For this simplified case, just return as-is
    return obj


def test_converter_matches_expected():
    expected = load_expected()
    text = load_input_text()
    syn = to_synthetic_map(text)
    data = parse(syn)
    assert _normalize(data) == expected
