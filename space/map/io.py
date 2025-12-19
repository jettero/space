# coding: utf-8

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Union

from .base import Map
from .cell.blocked import BlockedCell
from .cell.cell import Corridor, Floor
from .cell.wall import Wall

NONE_TYPE = type(None)
TOKEN_POOL = " .#@+*%=:;^~ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
PREFERRED_TOKENS = {NONE_TYPE: " ", Wall: "#", Floor: ".", Corridor: ":", BlockedCell: "+"}


def type_identifier(cell_type: type) -> str:
    """
    Return a fully qualified name for `cell_type`.

    The string is `module.Class` for concrete types and the literal `None`
    when the type represents empty cells.
    """

    if cell_type is NONE_TYPE:
        return "None"
    return f"{cell_type.__module__}.{cell_type.__qualname__}"


def resolve_identifier(identifier: str) -> type:
    """
    Resolve `identifier` produced by `type_identifier` back into a type.

    The literal `None` maps to the singleton empty-cell marker. Other
    identifiers are imported via `importlib`.
    """

    if identifier == "None":
        return NONE_TYPE
    module_name, _, class_name = identifier.rpartition(".")
    if not module_name or not class_name:
        raise ValueError(f"invalid identifier: {identifier}")
    return getattr(importlib.import_module(module_name), class_name)


def assign_token(cell_type: type, type_to_token: dict[type, str], used_tokens: set[str]) -> str:
    """
    Assign and memoize a printable token for `cell_type`.

    Preferred glyphs are reused when available; otherwise the next entry from
    `TOKEN_POOL` is consumed.
    """

    if cell_type in type_to_token:
        return type_to_token[cell_type]
    if cell_type in PREFERRED_TOKENS and PREFERRED_TOKENS[cell_type] not in used_tokens:
        type_to_token[cell_type] = PREFERRED_TOKENS[cell_type]
        used_tokens.add(PREFERRED_TOKENS[cell_type])
        return type_to_token[cell_type]
    for token in TOKEN_POOL:
        if token not in used_tokens:
            type_to_token[cell_type] = token
            used_tokens.add(token)
            return token
    raise ValueError("no available tokens for map export")


def map_to_text(a_map: Map) -> str:
    """
    Serialize `a_map` into a compact text format.

    The layout starts with a magic header, the map size, a legend mapping
    single-character tokens to concrete cell classes, a blank line, and the
    token grid trimmed to the populated bounds.
    """

    min_x = min_y = max_x = max_y = None
    for (x, y), cell in a_map:
        if cell is None:
            continue
        if min_x is None or x < min_x:
            min_x = x
        if max_x is None or x > max_x:
            max_x = x
        if min_y is None or y < min_y:
            min_y = y
        if max_y is None or y > max_y:
            max_y = y
    if min_x is None:
        width = height = 0
        type_to_token: dict[type, str] = dict()
        rows: list[str] = list()
    else:
        width = max_x - min_x + 1
        height = max_y - min_y + 1
        type_to_token = dict()
        used_tokens: set[str] = set()
        rows = list()
        for y in range(min_y, max_y + 1):
            chars = list()
            for x in range(min_x, max_x + 1):
                cell = a_map.get(x, y)
                chars.append(assign_token(NONE_TYPE if cell is None else type(cell), type_to_token, used_tokens))
            rows.append("".join(chars).rstrip())
    lines = ["space.map 1", f"size {width} {height}"]
    for cell_type, token in type_to_token.items():
        lines.append(f'legend "{token}" {type_identifier(cell_type)}')
    lines.append("")
    lines.extend(rows)
    return "\n".join(lines) + "\n"


def export_map_to_path(a_map: Map, path: Union[str, Path]) -> None:
    """
    Write `a_map` to `path` using the text format produced by `map_to_text`.
    """

    Path(path).write_text(map_to_text(a_map), encoding="utf-8")


def text_to_map(text: str) -> Map:
    """
    Deserialize `text` produced by `map_to_text` back into a `Map`.

    Raises `ValueError` when the input is malformed or inconsistent with the
    expected format.
    """

    lines = text.splitlines()
    if not lines:
        raise ValueError("empty map export")
    iter_lines = iter(lines)
    if next(iter_lines).strip() != "space.map 1":
        raise ValueError("missing space.map header")
    size_parts = next(iter_lines).split()
    if len(size_parts) != 3 or size_parts[0] != "size":
        raise ValueError("invalid size line")
    width = int(size_parts[1])
    height = int(size_parts[2])
    token_to_type: dict[str, type] = dict()
    for line in iter_lines:
        if line == "":
            break
        if not line.startswith("legend "):
            raise ValueError("legend section malformed")
        rest = line[len("legend ") :]
        if len(rest) < 3 or rest[0] != '"':
            raise ValueError("legend token must start with quote")
        token_end = rest.find('"', 1)
        if token_end == -1:
            raise ValueError("legend token must end with quote")
        if token_end + 1 >= len(rest) or rest[token_end + 1] != " ":
            raise ValueError("legend token must be followed by a space")
        token = rest[1:token_end]
        identifier = rest[token_end + 2 :]
        if not identifier:
            raise ValueError("legend entry missing identifier")
        if token in token_to_type:
            raise ValueError(f"duplicate legend token: {token}")
        token_to_type[token] = resolve_identifier(identifier)
    data_lines = list(iter_lines)
    if len(data_lines) != height:
        raise ValueError("map data height mismatch")
    result = Map(width, height)
    none_token = next((token for token, cell_type in token_to_type.items() if cell_type is NONE_TYPE), None)
    for y, line in enumerate(data_lines):
        if len(line) > width:
            raise ValueError("map data width mismatch")
        for x in range(width):
            if x < len(line):
                token = line[x]
            else:
                if none_token is None:
                    raise ValueError("map data shorter than width but no None legend provided")
                token = none_token
            cell_type = token_to_type.get(token)
            if cell_type is None:
                raise ValueError(f"unknown legend token: {token}")
            if cell_type is NONE_TYPE:
                continue
            result.insert_mapobj(x, y, cell_type())
    return result


def import_map_from_path(path: Union[str, Path]) -> Map:
    """
    Load a map from `path` that was created by `export_map_to_path`.
    """

    return text_to_map(Path(path).read_text(encoding="utf-8"))
