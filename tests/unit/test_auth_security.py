"""Security regression: bootstrap, corrupt state, logout replay, CSRF, persistence."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def boot(tmp_path, monkeypatch):
    monkeypatch.setenv("WIZARD_DATA_DIR", str(tmp_path / "d"))
    monkeypatch.setenv("WIZARD_OWNER_SETUP_TOKEN", "bootstrap-secret")
    monkeypatch.setenv("WIZARD_MODE", "mock")
    from server.wizard import config
    from server.wizard.auth import set_store
    from server.wizard.shim import hermes_bridge
    from server.wizard.store import draft_store
    config._settings = None
    hermes_bridge.reset_bridge()
    draft_store.reset_store()
    set_store(None)
    from server.wizard.main import create_app
    return create_app


def test_setup_without_token_rejected(boot):
    c = TestClient(boot())
    r = c.post("/api/auth/setup", json={"password": "long-enough-1"})
    assert r.status_code == 403


def test_setup_wrong_token_rejected(boot):
    c = TestClient(boot())
    r = c.post("/api/auth/setup", json={"password": "long-enough-1", "setup_token": "wrong"})
    assert r.status_code == 403


def test_setup_twice_rejected(boot):
    c = TestClient(boot())
    c.post("/api/auth/setup", json={"password": "long-enough-1", "setup_token": "bootstrap-secret"})
    r = c.post("/api/auth/setup", json={"password": "long-enough-2", "setup_token": "bootstrap-secret"})
    assert r.status_code == 403


def test_logout_invalidates_token(boot):
    c = TestClient(boot())
    c.post("/api/auth/setup", json={"password": "long-enough-1", "setup_token": "bootstrap-secret"})
    r = c.get("/api/wizard/components")
    assert r.status_code == 200
    c.post("/api/auth/logout")
    r = c.get("/api/wizard/components")
    assert r.status_code == 401


def test_corrupt_state_fails_closed(boot, tmp_path):
    d = tmp_path / "d"
    d.mkdir()
    (d / "auth.json").write_text("{not json")
    import pytest as pt

    from server.wizard.auth import AuthErrorState, get_store
    with pt.raises(AuthErrorState):
        get_store(str(d))


def test_persistence_across_restart(boot, tmp_path):
    c = TestClient(boot())
    c.post("/api/auth/setup", json={"password": "long-enough-1", "setup_token": "bootstrap-secret"})
    # reload store (simulate restart)
    from server.wizard.auth import get_store, set_store
    set_store(None)
    s = get_store(str(tmp_path / "d"))
    assert s.owner_bound
    assert s.verify("owner", "long-enough-1")


def test_temporary_user_is_separate_and_disable_revokes_sessions(boot):
    client = TestClient(boot())
    admin_headers = {"X-Wizard-Admin-Token": "bootstrap-secret"}
    created = client.post(
        "/api/auth/admin/test-users",
        headers=admin_headers,
        json={"username": "test-e2e", "password": "temporary-pass-123"},
    )
    assert created.status_code == 200
    login = client.post(
        "/api/auth/login",
        json={"username": "test-e2e", "password": "temporary-pass-123"},
    )
    assert login.status_code == 200
    token = client.cookies.get("wizard_session")
    assert token
    assert client.get("/api/wizard/components").status_code == 200

    disabled = client.post(
        "/api/auth/admin/test-users/test-e2e/disable",
        headers=admin_headers,
    )
    assert disabled.status_code == 200
    replay = TestClient(boot())
    replay.cookies.set("wizard_session", token)
    assert replay.get("/api/wizard/components").status_code == 401
    relogin = replay.post(
        "/api/auth/login",
        json={"username": "test-e2e", "password": "temporary-pass-123"},
    )
    assert relogin.status_code == 401


def test_csrf_no_origin_in_prod_rejects(monkeypatch, tmp_path):
    monkeypatch.setenv("WIZARD_MODE", "production")
    from server.wizard import config
    config._settings = None
    from server.wizard.auth import _csrf_ok
    class Req:
        method = "POST"

        def __init__(self, headers):
            self.headers = headers

    assert _csrf_ok(Req({"Host": "example.com"})) is False
    assert _csrf_ok(Req({"Host": "example.com", "Origin": "https://example.com"})) is True
