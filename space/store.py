# coding: utf-8

import json
import os
import sqlite3
from functools import cache
from pathlib import Path


@cache
def db():
    """
    The one sqlite connection: space.db in appserv's data dir
    (APPSERV_DATA_DIR, default ./data), in WAL mode.  The schema is a
    single table that never changes with the mudlib: saves(kind, key, doc)
    where doc is JSONB.
    """

    con = sqlite3.connect(Path(os.environ.get("APPSERV_DATA_DIR", "data")) / "space.db", autocommit=True)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("CREATE TABLE IF NOT EXISTS saves (kind TEXT, key TEXT, doc JSONB, PRIMARY KEY (kind, key))")
    return con


def put(kind: str, key: str, doc) -> None:
    """
    Store the JSON-able `doc` (usually a Serial.save()) under (kind, key),
    replacing whatever was there.
    """

    db().execute("INSERT OR REPLACE INTO saves VALUES (?, ?, jsonb(?))", (kind, key, json.dumps(doc)))


def get(kind: str, key: str):
    """
    The doc stored under (kind, key), or None.
    """

    if row := db().execute("SELECT json(doc) FROM saves WHERE kind = ? AND key = ?", (kind, key)).fetchone():
        return json.loads(row[0])


def keys(kind: str, prefix: str = "") -> list[str]:
    """
    The sorted keys of `kind` that start with `prefix`, prefix removed.
    """

    q = "SELECT key FROM saves WHERE kind = ? AND substr(key, 1, ?) = ? ORDER BY key"
    return [k[len(prefix) :] for (k,) in db().execute(q, (kind, len(prefix), prefix))]
