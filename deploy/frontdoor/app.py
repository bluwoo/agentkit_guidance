"""Minimal browser front door for the AgentKit Wizard.

The proxy exposes only the browser application surface.  Runtime protocol, MCP
and administrative/bootstrap endpoints remain unavailable.  The upstream
AgentKit credential is injected server-side and never returned to the browser.
"""
from __future__ import annotations

import os
from collections.abc import AsyncIterator

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import Response, StreamingResponse

UPSTREAM = os.environ["WIZARD_UPSTREAM_ORIGIN"].rstrip("/")
UPSTREAM_HEADER = os.environ.get("WIZARD_UPSTREAM_AUTH_HEADER", "Authorization")
UPSTREAM_KEY = os.environ["WIZARD_UPSTREAM_AUTH_VALUE"]

PUBLIC_EXACT = {"/", "/favicon.ico", "/health", "/api/auth/status", "/api/auth/login", "/api/auth/logout"}
PROTECTED_PREFIXES = ("/api/wizard/", "/wizard/", "/assets/")
BLOCKED_PREFIXES = ("/invoke", "/run", "/run_sse", "/sessions", "/mcp", "/api/auth/admin/", "/api/auth/setup")
ALLOWED_METHODS = {"GET", "HEAD", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"}
REQUEST_HEADER_ALLOWLIST = {"accept", "accept-language", "content-type", "cookie", "origin", "referer", "user-agent", "traceparent", "tracestate", "x-request-id"}
RESPONSE_HEADER_ALLOWLIST = {"content-type", "cache-control", "etag", "last-modified", "location", "vary", "x-request-id", "trace-id"}

app = FastAPI(title="AgentKit Wizard Browser Front Door")


def _allowed(path: str) -> bool:
    if any(path == prefix or path.startswith(prefix + "/") for prefix in BLOCKED_PREFIXES):
        return False
    return path in PUBLIC_EXACT or any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES)


def _request_headers(request: Request) -> dict[str, str]:
    headers = {key: value for key, value in request.headers.items() if key.lower() in REQUEST_HEADER_ALLOWLIST}
    # Always overwrite a hostile browser-supplied Authorization header.
    headers[UPSTREAM_HEADER] = UPSTREAM_KEY
    headers["X-Forwarded-Host"] = request.headers.get("host", "")
    headers["X-Forwarded-Proto"] = "https"
    return headers


def _response_headers(response: httpx.Response) -> dict[str, str]:
    return {key: value for key, value in response.headers.items() if key.lower() in RESPONSE_HEADER_ALLOWLIST}


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.api_route("/{path:path}", methods=sorted(ALLOWED_METHODS))
async def proxy(path: str, request: Request) -> Response:
    normalized = "/" + path
    if request.method not in ALLOWED_METHODS or not _allowed(normalized):
        return Response(status_code=404)
    target = UPSTREAM + normalized
    if request.url.query:
        target += "?" + request.url.query
    client = httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=20.0), follow_redirects=False)
    upstream_request = client.build_request(request.method, target, headers=_request_headers(request), content=await request.body())
    upstream_response = await client.send(upstream_request, stream=True)

    async def stream() -> AsyncIterator[bytes]:
        try:
            async for chunk in upstream_response.aiter_raw():
                yield chunk
        finally:
            await upstream_response.aclose()
            await client.aclose()

    forwarded = StreamingResponse(
        stream(), status_code=upstream_response.status_code,
        headers=_response_headers(upstream_response),
        media_type=upstream_response.headers.get("content-type"),
    )
    # Preserve each Set-Cookie line (httpx.headers.items() may coalesce them).
    for value in upstream_response.headers.get_list("set-cookie"):
        forwarded.headers.append("set-cookie", value)
    return forwarded
