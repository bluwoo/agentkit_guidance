"""Unit tests: draft store CRUD + path-traversal protection."""
from __future__ import annotations

import pytest

from server.wizard.store import draft_store


def test_put_get_roundtrip():
    draft_store.put_draft("goalcard", "current", {"task": "hello"})
    assert draft_store.get_draft("goalcard", "current") == {"task": "hello"}


def test_list_drafts():
    draft_store.put_draft("cases", "a", {"x": 1})
    draft_store.put_draft("cases", "b", {"x": 2})
    items = draft_store.list_drafts("cases")
    assert {i["key"] for i in items} == {"a", "b"}


def test_get_missing_returns_none():
    assert draft_store.get_draft("goalcard", "nope") is None


def test_traversal_keys_rejected():
    with pytest.raises(draft_store.TraversalError):
        draft_store.put_draft("goalcard", "../etc/passwd", {})
    with pytest.raises(draft_store.TraversalError):
        draft_store.get_draft("goalcard", "..")
    with pytest.raises(draft_store.TraversalError):
        draft_store.put_draft("goalcard", "a/b", {})
    with pytest.raises(draft_store.TraversalError):
        draft_store.put_draft("goalcard", "", {})


def test_session_state_roundtrip():
    draft_store.put_session_state("sess1", {"decisions": {"task": "x"}})
    assert draft_store.get_session_state("sess1")["decisions"]["task"] == "x"
