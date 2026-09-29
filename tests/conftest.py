"""Test fixtures: isolate data dir, reset store + bridge between cases."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Project root on sys.path (also done by root conftest.py; redundant is fine).
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def isolated_data_dir(tmp_path, monkeypatch):
    """Point the store at a temp dir and reset singletons before/after each test."""
    monkeypatch.setenv("WIZARD_DATA_DIR", str(tmp_path / "wizdata"))
    # Clear any cached settings/state so env changes take effect.
    from server.wizard import config
    from server.wizard.shim import hermes_bridge
    from server.wizard.store import draft_store

    config._settings = None
    hermes_bridge.reset_bridge()
    draft_store.reset_store()
    from server.wizard import auth
    auth._store = None
    yield
    draft_store.reset_store()
    hermes_bridge.reset_bridge()
    config._settings = None
    auth._store = None


@pytest.fixture
def client():
    import os
    os.environ["WIZARD_OWNER_SETUP_TOKEN"] = "test-bootstrap-token"
    from fastapi.testclient import TestClient

    from server.wizard.main import create_app
    c = TestClient(create_app())
    c.post("/api/auth/setup", json={"password": "test-password-123", "setup_token": "test-bootstrap-token"})
    return c
