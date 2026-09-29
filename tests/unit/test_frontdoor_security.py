from __future__ import annotations

import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient

MODULE = Path(__file__).resolve().parents[2] / "deploy" / "frontdoor" / "app.py"


def load(monkeypatch):
    monkeypatch.setenv("WIZARD_UPSTREAM_ORIGIN", "https://runtime.example")
    monkeypatch.setenv("WIZARD_UPSTREAM_AUTH_HEADER", "Authorization")
    monkeypatch.setenv("WIZARD_UPSTREAM_AUTH_VALUE", "redacted-test")
    spec = importlib.util.spec_from_file_location("wizard_frontdoor", MODULE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def test_machine_paths_are_not_exposed(monkeypatch):
    module = load(monkeypatch)
    client = TestClient(module.app)
    for path in ("/invoke", "/mcp", "/sessions", "/api/auth/setup", "/api/auth/admin/test-users"):
        assert client.get(path).status_code == 404


def test_only_allowlisted_browser_paths(monkeypatch):
    module = load(monkeypatch)
    assert module._allowed("/")
    assert module._allowed("/api/auth/login")
    assert module._allowed("/api/wizard/biz-goal")
    assert module._allowed("/assets/app.js")
    assert not module._allowed("/docs")
    assert not module._allowed("/api/auth/admin/test-users")


def test_runtime_key_is_added_server_side(monkeypatch):
    module = load(monkeypatch)
    class Request:
        def __init__(self):
            self.headers = {"host": "human.example", "cookie": "wizard_session=x", "authorization": "attacker"}

    headers = module._request_headers(Request())
    assert headers["Authorization"] == "redacted-test"
    assert headers["X-Forwarded-Host"] == "human.example"
    assert "attacker" not in headers.values()
