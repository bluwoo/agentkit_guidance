"""APMPlus query client for the AgentKit Wizard observability layer.

Wraps the three verified APMPlus OpenAPI queries (GetTraceDetail / ListSpan /
ListSession) behind a single, injectable HTTP abstraction so that the rest of
the wizard (mapper / service / tests) never touches the network directly.

Contract (see frontend/03-api-integration.md §4.0):
  - Endpoint : https://apmplus-server.cn-beijing.volcengineapi.com
  - Method   : POST  ?Action=<Action>&Version=2026-01-01
  - Service  : apmplus_server   region: cn-beijing
  - Carrier  : BusinessCarrier=agentkit_runtime
  - Auth     : Volcengine Signature V4 (AK/SK HMAC-SHA256), via volcengine SDK.

Degradation rules (frontend/03-api-integration.md §4.6):
  - AK/SK missing            -> status="not_configured"  (never raise)
  - Auth / signature failure -> status="auth_error"
  - Other transport failure   -> status="error"
  - Credentials are NEVER written to logs, error bodies, or exceptions.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

from server.wizard.schemas import TraceStatus

# --------------------------------------------------------------------------- #
# Constants — strictly from the verified API contract
# --------------------------------------------------------------------------- #
APMPLUS_HOST = "apmplus-server.cn-beijing.volcengineapi.com"
APMPLUS_SCHEME = "https"
APMPLUS_SERVICE = "apmplus_server"
APMPLUS_REGION = "cn-beijing"
APMPLUS_API_VERSION = "2026-01-01"
APMPLUS_BUSINESS_CARRIER = "agentkit_runtime"

ENV_ACCESS_KEY = "APMPLUS_ACCESS_KEY"
ENV_SECRET_KEY = "APMPLUS_SECRET_KEY"

# Error codes returned by APMPlus (Volcengine style) that map to auth_error.
_AUTH_ERROR_CODES = {
    "AuthenticationError",
    "SignatureDoesNotMatch",
    "AccessDenied",
    "InvalidAccessKeyId",
    "SecurityTokenExpired",
    "MissingAuthenticationToken",
}


@dataclass
class APMPlusResponse:
    """Normalised result of one APMPlus query.

    Attributes:
        status:   one of TraceStatus.ok / not_configured / auth_error / error.
        payload:  parsed JSON dict from APMPlus (empty dict on failure).
        error:    safe, credential-free error message for the UI layer.
    """

    status: TraceStatus = TraceStatus.error
    payload: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.status == TraceStatus.ok


# --------------------------------------------------------------------------- #
# Internal: Volcengine V4 signing (reuses the installed SDK)
# --------------------------------------------------------------------------- #
def _build_signed_request(
    action: str,
    body: dict[str, Any],
    ak: str,
    sk: str,
    session_token: str = "",
) -> tuple[str, dict[str, str], bytes]:
    """Build a fully-signed (method, url, headers, body) tuple.

    Uses volcengine.auth.SignerV4 so we do not re-implement the canonical
    request.  The signed result is converted to plain httpx primitives.
    """
    from volcengine.auth.SignerV4 import SignerV4
    from volcengine.base.Request import Request
    from volcengine.Credentials import Credentials

    credentials = Credentials(
        ak, sk, APMPLUS_SERVICE, APMPLUS_REGION, session_token=session_token
    )
    raw_body = json.dumps(body).encode("utf-8")

    req = Request()
    req.set_method("POST")
    req.set_host(APMPLUS_HOST)
    req.set_path("/")
    req.set_schema(APMPLUS_SCHEME)
    req.set_query({"Action": action, "Version": APMPLUS_API_VERSION})
    req.set_headers({"Content-Type": "application/json; charset=utf-8"})
    req.body = raw_body

    # SignerV4.sign mutates req.headers in-place (adds X-Date, X-Content-Sha256,
    # Authorization, and Host).
    SignerV4.sign(req, credentials)

    url = f"{APMPLUS_SCHEME}://{APMPLUS_HOST}/?Action={action}&Version={APMPLUS_API_VERSION}"
    headers = dict(req.headers)
    headers["Host"] = APMPLUS_HOST
    return url, headers, raw_body


# --------------------------------------------------------------------------- #
# Public client
# --------------------------------------------------------------------------- #
class APMPlusClient:
    """Thin, testable wrapper around the three APMPlus query APIs.

    Args:
        transport:  httpx transport (or `httpx.MockTransport`) injected by
                    tests.  When ``None`` a default client is created lazily.
        ak / sk:    explicit credentials; when omitted the client first reads
                    ``APMPLUS_ACCESS_KEY`` / ``APMPLUS_SECRET_KEY`` and then
                    falls back to the current Volcengine control-plane
                    ``VOLCENGINE_ACCESS_KEY`` / ``VOLCENGINE_SECRET_KEY``.
                    Passing an explicit empty string keeps the client disabled.
        timeout:    per-request timeout in seconds.
    """

    def __init__(
        self,
        transport: httpx.BaseTransport | None = None,
        ak: str | None = None,
        sk: str | None = None,
        session_token: str | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._transport = transport
        self._timeout = timeout
        self._ak = (
            ak
            if ak is not None
            else os.environ.get(ENV_ACCESS_KEY)
            or os.environ.get("VOLCENGINE_ACCESS_KEY", "")
        )
        self._sk = (
            sk
            if sk is not None
            else os.environ.get(ENV_SECRET_KEY)
            or os.environ.get("VOLCENGINE_SECRET_KEY", "")
        )
        self._session_token = (
            session_token
            if session_token is not None
            else os.environ.get("VOLCENGINE_SESSION_TOKEN")
            or os.environ.get("VOLC_SESSIONTOKEN", "")
        )

        # In AgentKit Runtime the service role is exposed as a short-lived IAM
        # credential file.  Use it only when callers did not explicitly pass
        # credentials (explicit empty strings intentionally keep the client off).
        if ak is None and sk is None and not (self._ak and self._sk):
            try:
                credential_data = json.loads(
                    Path("/var/run/secrets/iam/credential").read_text(encoding="utf-8")
                )
                self._ak = str(credential_data["access_key_id"])
                self._sk = str(credential_data["secret_access_key"])
                self._session_token = str(credential_data.get("session_token", ""))
            except (FileNotFoundError, KeyError, ValueError, OSError, TypeError):
                pass

    # -- credential helpers --------------------------------------------------
    def is_configured(self) -> bool:
        """True when both AK and SK are present (never logs their values)."""
        return bool(self._ak) and bool(self._sk)

    # -- internal dispatch ---------------------------------------------------
    def _post(self, action: str, body: dict[str, Any]) -> APMPlusResponse:
        if not self.is_configured():
            return APMPlusResponse(
                status=TraceStatus.not_configured,
                error="APMPlus credentials not configured",
            )

        try:
            url, headers, raw_body = _build_signed_request(
                action,
                body,
                self._ak,
                self._sk,
                session_token=self._session_token,
            )
        except Exception as exc:  # noqa: BLE001 - signing failure path -> error status
            return APMPlusResponse(
                status=TraceStatus.error,
                error=f"signing failed: {type(exc).__name__}",
            )

        client = httpx.Client(
            transport=self._transport, timeout=self._timeout
        ) if self._transport else httpx.Client(timeout=self._timeout)

        try:
            resp = client.post(url, headers=headers, content=raw_body)
        except httpx.HTTPError as exc:
            return APMPlusResponse(
                status=TraceStatus.error,
                error=f"transport error: {type(exc).__name__}",
            )
        finally:
            if not self._transport:
                client.close()

        return self._interpret(action, resp)

    @staticmethod
    def _interpret(action: str, resp: httpx.Response) -> APMPlusResponse:
        """Convert an httpx.Response into a normalised APMPlusResponse."""
        try:
            data = resp.json()
        except (json.JSONDecodeError, ValueError):
            return APMPlusResponse(
                status=TraceStatus.error,
                error=f"{action}: non-JSON response (HTTP {resp.status_code})",
            )

        # Volcengine style error envelope.
        meta = data.get("ResponseMetadata", {}) or {}
        err = meta.get("Error", {}) or {}
        code = err.get("Code", "")
        msg = err.get("Message", "")

        if resp.status_code in (401, 403) or code in _AUTH_ERROR_CODES:
            return APMPlusResponse(
                status=TraceStatus.auth_error,
                payload=data,
                error=f"auth_error: {code or 'HTTP ' + str(resp.status_code)}",
            )

        if resp.status_code >= 400:
            return APMPlusResponse(
                status=TraceStatus.error,
                payload=data,
                error=f"{action} failed: {code or 'HTTP ' + str(resp.status_code)} {msg}".strip(),
            )

        return APMPlusResponse(status=TraceStatus.ok, payload=data)

    # -- public API: three verified queries ----------------------------------
    def get_trace_detail(self, trace_id: str, suggest_time: int = 0) -> APMPlusResponse:
        """GetTraceDetail — fetch the full span tree for one trace_id."""
        body = {
            "TraceId": trace_id,
            "SuggestTime": suggest_time,
            "BusinessCarrier": APMPLUS_BUSINESS_CARRIER,
        }
        return self._post("GetTraceDetail", body)

    def list_span(
        self,
        start_time: int,
        end_time: int,
        filters: list[dict[str, Any]] | None = None,
        limit: int = 100,
    ) -> APMPlusResponse:
        """ListSpan — browse spans in a time window (aggregate panel source)."""
        body = {
            "StartTime": start_time,
            "EndTime": end_time,
            "Filters": filters or [],
            "Offset": 0,
            "Limit": limit,
            "Order": "DESC",
            "OrderBy": "start_time_millisecond",
            "BusinessCarrier": APMPLUS_BUSINESS_CARRIER,
        }
        return self._post("ListSpan", body)

    def list_session(
        self,
        start_time_ms: int,
        end_time_ms: int,
        page_size: int = 50,
    ) -> APMPlusResponse:
        """ListSession — session-level token statistics."""
        body = {
            "StartTime": start_time_ms,
            "EndTime": end_time_ms,
            "PageNo": 1,
            "PageSize": page_size,
            "BusinessCarrier": APMPLUS_BUSINESS_CARRIER,
        }
        return self._post("ListSession", body)
