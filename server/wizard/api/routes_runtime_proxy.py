"""Runtime test-invoke proxy (frontend/03 §3 path one).

Wizard forwards a test call to the user-designed target Runtime. To prevent
SSRF:
  * The request supplies a ``runtime_id``; the actual target host is taken from
    the server-side whitelist ``WIZARD_RUNTIME_ENDPOINTS`` (env JSON map). The
    request can never supply an arbitrary URL.
  * An unknown runtime_id is rejected.
  * The outbound traceparent is injected so Step4 can pull the same trace.
  * The response echoes the ``trace_id``.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException

from server.wizard.config import get_settings
from server.wizard.schemas import RuntimeInvokeRequest, RuntimeInvokeResponse
from server.wizard.shim.otel_middleware import (
    current_trace_id,
    inject_traceparent_headers,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/runtime", tags=["runtime-proxy"])


@router.post("/invoke", response_model=RuntimeInvokeResponse)
async def proxy_invoke(req: RuntimeInvokeRequest) -> RuntimeInvokeResponse:
    settings = get_settings()
    base = settings.runtime_endpoints.get(req.runtime_id)
    if not base:
        # Resource-ID whitelist: unknown ids are a 400, never a guess.
        raise HTTPException(
            status_code=400,
            detail=f"runtime_id '{req.runtime_id}' is not in the configured allowlist",
        )

    # SSRF guard: only http(s) targets from the whitelist are reachable.
    if not base.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="allowlisted endpoint must be http(s)")

    target = base.rstrip("/") + "/invoke"
    headers = inject_traceparent_headers({"content-type": "application/json"})
    auth = settings.runtime_auth.get(req.runtime_id) or {}
    auth_header = str(auth.get("header") or "").strip()
    auth_value = str(auth.get("value") or "").strip()
    if settings.production and (not auth_header or not auth_value):
        raise HTTPException(status_code=503, detail="target runtime authentication is not configured")
    if auth_header and auth_value:
        headers[auth_header] = auth_value
    body: dict[str, Any] = {
        "input": req.input,
        "user_id": req.user_id,
        "session_id": req.session_id,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(target, json=body, headers=headers)
    except httpx.HTTPError as e:
        # Do not leak the target URL or a stack trace to the client.
        logger.warning("runtime proxy call failed: %s", e)
        return RuntimeInvokeResponse(output="", trace_id=current_trace_id(),
                                      status_code=502, error="upstream runtime unreachable")

    trace_id = resp.headers.get("trace-id") or current_trace_id()
    try:
        payload = resp.json()
    except ValueError:
        payload = {}
    output = payload.get("reply") or payload.get("output") or resp.text

    if resp.is_error:
        return RuntimeInvokeResponse(
            output=output, trace_id=trace_id, status_code=resp.status_code,
            error="upstream runtime returned an error",
        )
    return RuntimeInvokeResponse(
        output=output, trace_id=trace_id, status_code=resp.status_code, error=None
    )


__all__ = ["router"]
