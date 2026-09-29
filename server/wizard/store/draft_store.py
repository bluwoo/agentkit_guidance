"""Draft / session persistence for the Wizard four-step flow.

Storage is a single SQLite database (stdlib ``sqlite3``) under
``WIZARD_DATA_DIR`` (default ``./wizard_data``). Tables:

  * ``drafts(kind, key, data_json, updated_at)``
        kind in {goalcard, cases, topology, adr, glossary}
  * ``grill_sessions(session_id, state_json, updated_at)``

Security: the data directory is resolved once at startup and every derived path
is checked to remain inside it. Draft keys are opaque identifiers — they never
become filesystem paths (we use one SQLite file), but we still reject keys that
look like traversal sequences so the API surface stays safe if storage moves to
per-key files later.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

from server.wizard.config import get_settings

_LOCK = threading.RLock()
_DB: sqlite3.Connection | None = None
_DATA_DIR: Path | None = None

_FORBIDDEN_KEY_CHARS = ("/", "\\", "..", "\x00")


class TraversalError(ValueError):
    pass


def _validate_key(key: str) -> str:
    key = (key or "").strip()
    if not key or len(key) > 256:
        raise TraversalError("invalid draft key")
    for bad in _FORBIDDEN_KEY_CHARS:
        if bad in key:
            raise TraversalError("invalid draft key")
    return key


def _resolve_data_dir() -> Path:
    global _DATA_DIR
    if _DATA_DIR is not None:
        return _DATA_DIR
    settings = get_settings()
    base = Path(settings.data_dir).resolve()
    base.mkdir(parents=True, exist_ok=True)
    # Defense in depth: ensure the configured dir resolves to a real, writable
    # location. We never let a request influence this path.
    if not base.exists():  # pragma: no cover
        raise TraversalError("data dir missing")
    _DATA_DIR = base
    return base


def _db_path() -> Path:
    base = _resolve_data_dir()
    p = (base / "wizard_state.db").resolve()
    # The only file we open must live under the resolved data dir.
    if base not in p.parents and p != base:
        raise TraversalError("database path escapes data dir")
    return p


def _connect() -> sqlite3.Connection:
    global _DB
    if _DB is not None:
        return _DB
    conn = sqlite3.connect(str(_db_path()), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS drafts (
               kind TEXT NOT NULL,
               key  TEXT NOT NULL,
               data_json TEXT NOT NULL,
               updated_at REAL NOT NULL,
               PRIMARY KEY (kind, key)
           )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS grill_sessions (
               session_id TEXT PRIMARY KEY,
               state_json TEXT NOT NULL,
               updated_at REAL NOT NULL
           )"""
    )
    conn.commit()
    _DB = conn
    return conn


def reset_store() -> None:
    """Close the connection (used by tests between cases)."""
    global _DB, _DATA_DIR
    with _LOCK:
        if _DB is not None:
            try:
                _DB.close()
            finally:
                _DB = None
        _DATA_DIR = None


# --------------------------------------------------------------------------- #
# Draft API
# --------------------------------------------------------------------------- #
def put_draft(kind: str, key: str, data: dict[str, Any]) -> None:
    key = _validate_key(key)
    with _LOCK:
        conn = _connect()
        conn.execute(
            "INSERT INTO drafts(kind, key, data_json, updated_at) VALUES(?,?,?,?) "
            "ON CONFLICT(kind, key) DO UPDATE SET data_json=excluded.data_json, "
            "updated_at=excluded.updated_at",
            (kind, key, json.dumps(data, ensure_ascii=False), time.time()),
        )
        conn.commit()


def get_draft(kind: str, key: str) -> dict[str, Any] | None:
    key = _validate_key(key)
    with _LOCK:
        conn = _connect()
        row = conn.execute(
            "SELECT data_json FROM drafts WHERE kind=? AND key=?", (kind, key)
        ).fetchone()
    if not row:
        return None
    return json.loads(row["data_json"])


def list_drafts(kind: str) -> list[dict[str, Any]]:
    with _LOCK:
        conn = _connect()
        rows = conn.execute(
            "SELECT key, data_json, updated_at FROM drafts WHERE kind=? ORDER BY updated_at DESC",
            (kind,),
        ).fetchall()
    return [
        {"key": r["key"], "data": json.loads(r["data_json"]), "updated_at": r["updated_at"]}
        for r in rows
    ]


def delete_draft(kind: str, key: str) -> bool:
    key = _validate_key(key)
    with _LOCK:
        conn = _connect()
        cur = conn.execute("DELETE FROM drafts WHERE kind=? AND key=?", (kind, key))
        conn.commit()
        return cur.rowcount > 0


# --------------------------------------------------------------------------- #
# Grill session state API
# --------------------------------------------------------------------------- #
def put_session_state(session_id: str, state: dict[str, Any]) -> None:
    session_id = _validate_key(session_id)
    with _LOCK:
        conn = _connect()
        conn.execute(
            "INSERT INTO grill_sessions(session_id, state_json, updated_at) VALUES(?,?,?) "
            "ON CONFLICT(session_id) DO UPDATE SET state_json=excluded.state_json, "
            "updated_at=excluded.updated_at",
            (session_id, json.dumps(state, ensure_ascii=False), time.time()),
        )
        conn.commit()


def get_session_state(session_id: str) -> dict[str, Any] | None:
    session_id = _validate_key(session_id)
    with _LOCK:
        conn = _connect()
        row = conn.execute(
            "SELECT state_json FROM grill_sessions WHERE session_id=?", (session_id,)
        ).fetchone()
    if not row:
        return None
    return json.loads(row["state_json"])


__all__ = [
    "TraversalError",
    "delete_draft",
    "get_draft",
    "get_session_state",
    "list_drafts",
    "put_draft",
    "put_session_state",
    "reset_store",
]
