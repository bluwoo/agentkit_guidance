"""Unit tests: production-mode fail-closed behaviour.

Covers:
  * WIZARD_MODE=production refuses to auto-fallback to MockHermesBridge.
  * require_prod_ready() lists missing LLM config keys.
  * create_app() refuses when CORS allowlist is empty or wildcard in production.
  * lifespan refuses to start when LLM config is missing (even with CORS set).
  * mock mode forces MockHermesBridge; local mode falls back to it.
  * MockHermesBridge.new_session generates unique ids (no cross-request crosstalk).
"""
from __future__ import annotations

import pytest

from server.wizard.config import Settings, load_settings

# Import create_app once at module load with the default (local) env so that
# main.py's module-level ``app = create_app()`` runs with safe settings. Tests
# below then call create_app() directly with overridden env.
from server.wizard.main import create_app


def test_prod_require_prod_ready_lists_all_missing():
    s = Settings(mode_raw="production")
    missing = s.require_prod_ready()
    assert "WIZARD_LLM_BASE_URL" in missing
    assert "WIZARD_LLM_MODEL" in missing
    assert "WIZARD_LLM_API_KEY" in missing


def test_prod_require_prod_ready_empty_when_configured():
    s = Settings(
        mode_raw="production",
        llm_base_url="https://llm.example/v1",
        llm_model="gpt-x",
        llm_api_key="sk-x",
    )
    assert s.require_prod_ready() == []


def test_prod_mode_get_bridge_raises_without_llm(monkeypatch):
    monkeypatch.setenv("WIZARD_MODE", "production")
    for var in ("WIZARD_LLM_BASE_URL", "WIZARD_LLM_MODEL", "WIZARD_LLM_API_KEY"):
        monkeypatch.delenv(var, raising=False)

    from server.wizard import config
    config._settings = None
    from server.wizard.shim import hermes_bridge
    hermes_bridge._bridge = None

    with pytest.raises(RuntimeError, match="production mode requires WIZARD_LLM"):
        hermes_bridge.get_bridge()


def test_prod_mode_get_bridge_raises_without_api_key(monkeypatch):
    """Base URL + model present but no API key -> still raise."""
    monkeypatch.setenv("WIZARD_MODE", "production")
    monkeypatch.setenv("WIZARD_LLM_BASE_URL", "https://llm/v1")
    monkeypatch.setenv("WIZARD_LLM_MODEL", "m")
    monkeypatch.delenv("WIZARD_LLM_API_KEY", raising=False)

    from server.wizard import config
    config._settings = None
    from server.wizard.shim import hermes_bridge
    hermes_bridge._bridge = None

    with pytest.raises(RuntimeError, match="production mode requires WIZARD_LLM"):
        hermes_bridge.get_bridge()


def test_prod_create_app_allows_empty_origins(monkeypatch):
    # Empty allowlist in production = same-origin SPA, no CORS needed.
    monkeypatch.setenv("WIZARD_MODE", "production")
    monkeypatch.delenv("WIZARD_ALLOWED_ORIGINS", raising=False)
    # LLM env present so we isolate the CORS check (not the LLM check).
    monkeypatch.setenv("WIZARD_LLM_BASE_URL", "https://llm/v1")
    monkeypatch.setenv("WIZARD_LLM_MODEL", "m")
    monkeypatch.setenv("WIZARD_LLM_API_KEY", "k")

    from server.wizard import config
    config._settings = None

    app = create_app()
    cors = [m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"]
    assert cors and cors[0].kwargs.get("allow_origins", []) == []


def test_prod_create_app_raises_on_wildcard_origin(monkeypatch):
    monkeypatch.setenv("WIZARD_MODE", "production")
    monkeypatch.setenv("WIZARD_ALLOWED_ORIGINS", "*")
    monkeypatch.setenv("WIZARD_LLM_BASE_URL", "https://llm/v1")
    monkeypatch.setenv("WIZARD_LLM_MODEL", "m")
    monkeypatch.setenv("WIZARD_LLM_API_KEY", "k")

    from server.wizard import config
    config._settings = None

    with pytest.raises(RuntimeError, match="rejects allow_origins"):
        create_app()


def test_prod_lifespan_raises_missing_llm(monkeypatch):
    """Valid CORS + missing LLM -> app constructs but lifespan refuses to start."""
    monkeypatch.setenv("WIZARD_MODE", "production")
    monkeypatch.setenv("WIZARD_ALLOWED_ORIGINS", "https://app.example.com")
    for var in ("WIZARD_LLM_BASE_URL", "WIZARD_LLM_MODEL", "WIZARD_LLM_API_KEY"):
        monkeypatch.delenv(var, raising=False)

    from server.wizard import config
    config._settings = None
    from fastapi.testclient import TestClient

    app = create_app()  # CORS passes; app constructs
    with pytest.raises(RuntimeError, match="production mode is missing required config"), TestClient(app):
        # entering context triggers lifespan startup; nothing to do inside.
        pass


def test_mock_mode_forces_mock_bridge(monkeypatch):
    monkeypatch.setenv("WIZARD_MODE", "mock")
    # LLM env present — mock mode must still use MockHermesBridge.
    monkeypatch.setenv("WIZARD_LLM_BASE_URL", "https://llm/v1")
    monkeypatch.setenv("WIZARD_LLM_MODEL", "m")
    monkeypatch.setenv("WIZARD_LLM_API_KEY", "k")

    from server.wizard import config
    config._settings = None
    from server.wizard.shim import hermes_bridge
    hermes_bridge._bridge = None

    bridge = hermes_bridge.get_bridge()
    assert bridge.name == "mock-hermes"


def test_local_mode_falls_back_to_mock(monkeypatch):
    monkeypatch.setenv("WIZARD_MODE", "local")
    for var in ("WIZARD_LLM_BASE_URL", "WIZARD_LLM_MODEL"):
        monkeypatch.delenv(var, raising=False)

    from server.wizard import config
    config._settings = None
    from server.wizard.shim import hermes_bridge
    hermes_bridge._bridge = None

    bridge = hermes_bridge.get_bridge()
    assert bridge.name == "mock-hermes"


def test_mock_new_session_unique_ids():
    from server.wizard.shim.hermes_bridge import MockHermesBridge
    b = MockHermesBridge()
    s1 = b.new_session()
    s2 = b.new_session()
    assert s1.startswith("sess-mock-")
    assert s2.startswith("sess-mock-")
    assert s1 != s2


def test_hermes_version_default_is_0213():
    s = load_settings()
    assert s.hermes_version == "0.21.3"


def test_mode_property_normalizes():
    assert Settings(mode_raw=" Production ").mode == "production"
    assert Settings(mode_raw="local").production is False
    assert Settings(mode_raw="production").production is True


def test_local_mode_allows_wildcard_cors(monkeypatch):
    monkeypatch.setenv("WIZARD_MODE", "local")
    monkeypatch.delenv("WIZARD_ALLOWED_ORIGINS", raising=False)

    from server.wizard import config
    config._settings = None

    # local + empty origins -> ["*"] with warning; constructs fine.
    app = create_app()
    assert app is not None
