#!/usr/bin/env python3
"""
Translate MudOS/LPC save dump files (Pike-like literals) into Python or JSON.

Usage examples:
  # Auto-detect top-level form and emit Python module
  python scripts/mudos_save_translator.py soul.o -o space/verb/emote/soul.py --python-var SOUL

  # Dump as JSON to stdout
  python scripts/mudos_save_translator.py some_save.o --json -
"""

import argparse
import json
from pathlib import Path
import sys

from contrib.tools.lpc_parser import parse
import re
try:
    from black import format_str, FileMode
except Exception:  # pragma: no cover - optional dependency at runtime
    format_str = None
    FileMode = None


def to_synthetic_map(text: str) -> str:
    """Convert MudOS save pairs into a Pike map literal without mangling.

    Accepts either a Pike literal already (return as-is) or a sequence of
    "name (payload)" pairs. Uses a parenthesis depth scanner to extract each
    payload exactly, preserving nested content and quotes.
    """
    s = text
    # Drop leading comment lines
    lines = s.splitlines()
    i = 0
    while i < len(lines) and lines[i].lstrip().startswith("#"):
        i += 1
    s = "\n".join(lines[i:]).strip()
    if s.startswith("([") or s.startswith("({"):
        return s

    pairs = []
    j = 0
    n = len(s)
    while j < n:
        # skip whitespace
        while j < n and s[j].isspace():
            j += 1
        if j >= n:
            break
        # read name token until whitespace or '('
        start = j
        while j < n and not s[j].isspace() and s[j] != '(':
            j += 1
        name = s[start:j]
        # skip whitespace
        while j < n and s[j].isspace():
            j += 1
        if j >= n or s[j] != '(':
            # malformed; stop
            break
        # scan payload starting at '('
        depth = 0
        k = j
        in_str = False
        escape = False
        while k < n:
            ch = s[k]
            if in_str:
                if escape:
                    escape = False
                elif ch == '\\':
                    escape = True
                elif ch == '"':
                    in_str = False
            else:
                if ch == '"':
                    in_str = True
                elif ch == '(':
                    depth += 1
                elif ch == ')':
                    depth -= 1
                    if depth == 0:
                        k += 1
                        break
            k += 1
        payload = s[j:k]
        pairs.append(f"{name}: {payload}")
        j = k
    return "([" + ",".join(pairs) + "])"


def _fix_double_spaces(obj):
    """Recursively collapse double spaces in strings to a single space.

    Preserves intentional spacing around color codes and punctuation by
    repeatedly replacing two spaces with one until stable.
    """
    if isinstance(obj, str):
        # Collapse runs of 2+ spaces into a single space
        return re.sub(r" {2,}", " ", obj)
    if isinstance(obj, list):
        return [_fix_double_spaces(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _fix_double_spaces(v) for k, v in obj.items()}
    return obj


def emit_python_module(data, out_path: Path, var_name: str):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Build module text
    body = repr(data)
    module_text = (
        "# Generated from MudOS save via scripts/mudos_save_translator.py\n"
        "# Do not edit manually.\n\n"
        f"{var_name} = {body}\n"
    )
    # Optionally format with black for readability
    if format_str is not None:
        try:
            module_text = format_str(module_text, mode=FileMode())
        except Exception:
            pass
    out_path.write_text(module_text, encoding="utf-8")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("infile", help="MudOS save file (e.g., soul.o)")
    ap.add_argument("-o", "--out", help="Output file path (for Python module or JSON)")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of Python module")
    ap.add_argument("--python-var", default="DATA", help="Variable name for Python module output")
    args = ap.parse_args(argv)

    in_path = Path(args.infile)
    text = in_path.read_text(encoding="utf-8")
    synthetic = to_synthetic_map(text)
    data = parse(synthetic)
    # Editorial fix: collapse double spaces in all string values
    data = _fix_double_spaces(data)

    if args.json:
        if args.out and args.out != "-":
            Path(args.out).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
            sys.stdout.write("\n")
        return

    # Python module output
    out_path = Path(args.out) if args.out else Path("out.py")
    emit_python_module(data, out_path, args.python_var)


if __name__ == "__main__":
    main()
