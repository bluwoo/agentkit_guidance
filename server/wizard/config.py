"""Runtime configuration for the AgentKit Wizard backend.

Every knob is environment-driven (pydantic-settings style). Nothing secret is
ever printed: ``masked_summary`` redacts any value whose key looks like a key /
secret / token.

Environment variables (all optional unless noted):

  Runtime protocol (layer-1 contract)
    RUNTIME_API_KEY_HEADER   header carrying the inbound API key (default X-Api-Key)
    RUNTIME_API_KEY          expected key; when unset the service runs in open
                             local-dev mode (requests allowed, a warning logged).

  Run mode
    WIZARD_MODE              local | mock | production (default local).
                             local:    auto-fall-back to MockHermesBridge if no LLM env.
                             mock:     force MockHermesBridge (tests / demos).
                             production: fail-closed — require WIZARD_LLM_* and an
                             explicit CORS allowlist; never silently mock.

  CORS
    WIZARD_ALLOWED_ORIGINS   comma-separated origin allowlist. In production the
                             list must be non-empty and must not contain ``*``.
                             In local mode an empty list defaults to ``*`` (warned).

  Hermes bridge
    WIZARD_LLM_BASE_URL      LLM endpoint; when unset RealHermesBridge is disabled
                             and the deterministic MockHermesBridge is used (local only).
    WIZARD_LLM_API_KEY
    WIZARD_LLM_MODEL
    WIZARD_LLM_PROVIDER      passed to AIAgent(provider=...)
    WIZARD_LLM_API_MODE      passed to AIAgent(api_mode=...)

  Persistence
    WIZARD_DATA_DIR          draft/session store root (default ./wizard_data)

  Observability / OTel
    OTEL_EXPORTER_OTLP_ENDPOINT  OTLP http(s) endpoint; unset -> console/no-op
    WIZARD_VERSION               stamped onto every span (default 0.1.0)
    HERMES_VERSION               stamped onto every span

  Runtime proxy (anti-SSRF)
    WIZARD_RUNTIME_ENDPOINTS     JSON object {runtime_id: "https://host/prefix"}.
                                 Only ids present here may be proxied; the target
                                 host is taken from this map, never from the request.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


def _mask(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 4:
        return "****"
    return value[:2] + "****" + value[-2:]


def _looks_sensitive(key: str) -> bool:
    k = key.upper()
    return any(tok in k for tok in ("KEY", "SECRET", "TOKEN", "PASSWORD", "CREDENTIAL", "AK", "SK"))


def _parse_origins(raw: str) -> list[str]:
    return [o.strip() for o in (raw or "").split(",") if o.strip()]


@dataclass
class Settings:
    # --- run mode ---
    mode_raw: str = "local"

    # --- layer-1 runtime auth ---
    runtime_api_key_header: str = "X-Api-Key"
    runtime_api_key: str = ""

    # --- CORS ---
    allowed_origins: list[str] = field(default_factory=list)

    # --- Hermes bridge ---
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_provider: str = ""
    llm_api_mode: str = ""

    # --- persistence ---
    data_dir: str = "./wizard_data"

    # --- OTel ---
    otel_exporter_otlp_endpoint: str = ""
    wizard_version: str = "0.1.0"
    hermes_version: str = "0.21.3"
    service_name: str = "wizard"

    # --- runtime proxy whitelist: runtime_id -> base endpoint ---
    runtime_endpoints: dict[str, str] = field(default_factory=dict)
    # runtime_id -> {"header": "Authorization", "value": "Bearer ..."}
    # This is server-only sensitive configuration and is never serialized to clients.
    runtime_auth: dict[str, dict[str, str]] = field(default_factory=dict)

    # --- browser auth / CSRF ---
    public_origin: str = ""

    # --- vendor hermes source ---
    hermes_vendor_root: str = ""

    @property
    def mode(self) -> str:
        """Lowercase-normalized run mode: local | mock | production."""
        return self.mode_raw.strip().lower()

    @property
    def production(self) -> bool:
        return self.mode == "production"

    @property
    def auth_enabled(self) -> bool:
        """KeyAuth is only enforced when a key is actually configured."""
        return bool(self.runtime_api_key.strip())

    @property
    def real_hermes_enabled(self) -> bool:
        return bool(self.llm_base_url.strip() and self.llm_model.strip())

    def require_prod_ready(self) -> list[str]:
        """Return list of missing required config keys when running in production.

        Called at startup; the caller must refuse to boot if the list is non-empty.
        """
        missing: list[str] = []
        if not self.llm_base_url.strip():
            missing.append("WIZARD_LLM_BASE_URL")
        if not self.llm_model.strip():
            missing.append("WIZARD_LLM_MODEL")
        if not self.llm_api_key.strip():
            missing.append("WIZARD_LLM_API_KEY")
        return missing

    def masked_summary(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for k, v in self.__dict__.items():
            if k == "runtime_auth":
                out[k] = json.dumps({rid: {"header": cfg.get("header", ""), "value": "<redacted>"} for rid, cfg in (v or {}).items()})
                continue
            if k == "runtime_endpoints":
                out[k] = json.dumps({rid: ep for rid, ep in (v or {}).items()})
                continue
            if k == "allowed_origins":
                out[k] = ",".join(v or [])
                continue
            if not isinstance(v, str):
                out[k] = str(v)
                continue
            out[k] = _mask(v) if _looks_sensitive(k) else v
        return out


def _parse_endpoints(raw: str) -> dict[str, str]:
    raw = (raw or "").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k): str(v) for k, v in data.items()}


def _parse_runtime_auth(raw: str) -> dict[str, dict[str, str]]:
    raw = (raw or "").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    parsed: dict[str, dict[str, str]] = {}
    for runtime_id, config in data.items():
        if isinstance(config, dict):
            parsed[str(runtime_id)] = {
                "header": str(config.get("header", "")),
                "value": str(config.get("value", "")),
            }
    return parsed


def load_settings() -> Settings:
    """Build Settings entirely from environment variables."""
    return Settings(
        mode_raw=os.environ.get("WIZARD_MODE", "local"),
        runtime_api_key_header=os.environ.get("RUNTIME_API_KEY_HEADER", "X-Api-Key"),
        runtime_api_key=os.environ.get("RUNTIME_API_KEY", ""),
        allowed_origins=_parse_origins(os.environ.get("WIZARD_ALLOWED_ORIGINS", "")),
        llm_base_url=os.environ.get("WIZARD_LLM_BASE_URL", ""),
        llm_api_key=os.environ.get("WIZARD_LLM_API_KEY", ""),
        llm_model=os.environ.get("WIZARD_LLM_MODEL", ""),
        llm_provider=os.environ.get("WIZARD_LLM_PROVIDER", ""),
        llm_api_mode=os.environ.get("WIZARD_LLM_API_MODE", ""),
        data_dir=os.environ.get("WIZARD_DATA_DIR", "./wizard_data"),
        otel_exporter_otlp_endpoint=os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", ""),
        wizard_version=os.environ.get("WIZARD_VERSION", "0.1.0"),
        hermes_version=os.environ.get("HERMES_VERSION", "0.21.3"),
        service_name=os.environ.get("OTEL_SERVICE_NAME", "wizard"),
        runtime_endpoints=_parse_endpoints(os.environ.get("WIZARD_RUNTIME_ENDPOINTS", "")),
        runtime_auth=_parse_runtime_auth(os.environ.get("WIZARD_RUNTIME_AUTH", "")),
        public_origin=os.environ.get("WIZARD_PUBLIC_ORIGIN", "").strip(),
        hermes_vendor_root=os.environ.get(
            "HERMES_VENDOR_ROOT",
            str(Path(__file__).resolve().parents[2] / "vendor" / "hermes-agent"),
        ),
    )


# Module-level singleton; tests may monkeypatch / rebuild.
_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = load_settings()
    return _settings


def set_settings(settings: Settings) -> None:
    """Allow tests to inject a Settings object."""
    global _settings
    _settings = settings
