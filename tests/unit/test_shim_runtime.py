"""Unit tests: layer-1 runtime protocol routes + KeyAuth behavior."""
from __future__ import annotations

from fastapi.testclient import TestClient


def _make_client(monkeypatch, api_key: str = "", header_name: str = "X-Api-Key"):
    if api_key:
        monkeypatch.setenv("RUNTIME_API_KEY", api_key)
    else:
        monkeypatch.delenv("RUNTIME_API_KEY", raising=False)
    monkeypatch.setenv("RUNTIME_API_KEY_HEADER", header_name)
    from server.wizard import config
    config._settings = None
    from server.wizard.main import create_app
    return TestClient(create_app())


def test_health_probes_open(client):
    # Auth disabled by default -> probes reachable.
    assert client.get("/ping").json() == {"status": "ok"}
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/readiness").status_code == 200
    assert client.get("/liveness").json() == {"status": "ok"}


def test_invoke_uses_mock_bridge(client):
    r = client.post("/invoke", json={"session_id": "s1", "user_id": "u", "message": "step1 hi"})
    assert r.status_code == 200
    body = r.json()
    assert body["session_id"] == "s1"
    assert "Step1" in body["reply"]
    assert body["failed"] is False


def test_invoke_empty_message(client):
    r = client.post("/invoke", json={"session_id": "s1", "message": ""})
    assert r.status_code == 200
    assert r.json()["error"] == "empty message"


def test_keyauth_rejects_missing_header(monkeypatch):
    c = _make_client(monkeypatch, api_key="s3cr3t")
    r = c.post("/invoke", json={"message": "hi"})
    assert r.status_code == 401


def test_keyauth_rejects_wrong_key(monkeypatch):
    c = _make_client(monkeypatch, api_key="s3cr3t")
    r = c.post("/invoke", headers={"X-Api-Key": "wrong"}, json={"message": "hi"})
    assert r.status_code == 401


def test_keyauth_accepts_correct_key(monkeypatch):
    c = _make_client(monkeypatch, api_key="s3cr3t")
    r = c.post("/invoke", headers={"X-Api-Key": "s3cr3t"},
               json={"session_id": "s9", "message": "step2"})
    assert r.status_code == 200
    assert "Step2" in r.json()["reply"]


def test_keyauth_custom_header_name(monkeypatch):
    c = _make_client(monkeypatch, api_key="k", header_name="ApiKeyName")
    assert c.post("/invoke", json={"message": "hi"}).status_code == 401
    assert c.post("/invoke", headers={"ApiKeyName": "k"},
                  json={"message": "hi"}).status_code == 200


def test_health_probes_stay_open_when_auth_enabled(monkeypatch):
    c = _make_client(monkeypatch, api_key="s3cr3t")
    # Probes must NOT require the key (orchestrator/LB reach them first).
    assert c.get("/ping").status_code == 200
    assert c.get("/health").status_code == 200


def test_sessions_create_and_list(client):
    r = client.post("/sessions", json={"user_id": "u1"})
    assert r.status_code == 200
    assert r.json()["user_id"] == "u1"
    assert client.get("/sessions").status_code == 200
