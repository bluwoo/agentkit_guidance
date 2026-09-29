"""veFaaS Python event-function browser front door.

Only a fixed browser-facing path allowlist is proxied. The AgentKit Runtime
credential is injected server-side and never returned to callers.
"""
from __future__ import annotations

import base64
import os
import urllib.error
import urllib.parse
import urllib.request

UPSTREAM = os.environ["WIZARD_UPSTREAM_ORIGIN"].rstrip("/")
AUTH_HEADER = os.environ.get("WIZARD_UPSTREAM_AUTH_HEADER", "Authorization")
AUTH_VALUE = os.environ["WIZARD_UPSTREAM_AUTH_VALUE"]

PUBLIC_EXACT = {
    "/", "/favicon.ico", "/health", "/api/auth/status",
    "/api/auth/login", "/api/auth/logout",
}
PROTECTED_PREFIXES = ("/api/wizard/", "/wizard/", "/assets/")
BLOCKED_PREFIXES = (
    "/invoke", "/run", "/run_sse", "/sessions", "/mcp",
    "/api/auth/admin/",
)
REQUEST_HEADERS = {
    "accept", "accept-language", "content-type", "cookie", "origin",
    "referer", "user-agent", "traceparent", "tracestate", "x-request-id",
}
RESPONSE_HEADERS = {
    "content-type", "cache-control", "etag", "last-modified", "location",
    "vary", "x-request-id", "trace-id", "set-cookie",
}


def _allowed(path: str) -> bool:
    if any(path == prefix or path.startswith(prefix + "/") for prefix in BLOCKED_PREFIXES):
        return False
    return path in PUBLIC_EXACT or any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES)


def _header_map(event: dict) -> dict[str, str]:
    headers = {
        str(k): str(v) for k, v in (event.get("headers") or {}).items()
        if str(k).lower() in REQUEST_HEADERS
    }
    headers[AUTH_HEADER] = AUTH_VALUE
    host = next((v for k, v in (event.get("headers") or {}).items() if str(k).lower() == "host"), "")
    headers["X-Forwarded-Host"] = str(host)
    headers["X-Forwarded-Proto"] = "https"
    headers["Accept-Encoding"] = "identity"
    return headers


def _response(status: int, headers: dict, body: bytes) -> dict:
    clean = {str(k): str(v) for k, v in headers.items() if str(k).lower() in RESPONSE_HEADERS}
    content_type = clean.get("Content-Type") or clean.get("content-type") or "application/octet-stream"
    textual = content_type.startswith("text/") or any(
        marker in content_type for marker in ("json", "javascript", "xml", "svg")
    )
    if textual:
        return {"statusCode": status, "headers": clean, "body": body.decode("utf-8", errors="replace")}
    return {
        "statusCode": status,
        "headers": clean,
        "body": base64.b64encode(body).decode("ascii"),
        "isBase64Encoded": True,
    }


def handler(event: dict, context) -> dict:
    path = str(event.get("path") or "/")
    if not path.startswith("/"):
        path = "/" + path
    if path == "/healthz":
        return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": '{"status":"ok"}'}
    method = str(event.get("httpMethod") or "GET").upper()
    if method not in {"GET", "HEAD", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"} or not _allowed(path):
        return {"statusCode": 404, "headers": {"Content-Type": "application/json"}, "body": '{"detail":"not found"}'}
    query = event.get("queryStringParameters") or {}
    target = UPSTREAM + path
    if query:
        target += "?" + urllib.parse.urlencode(query, doseq=True)
    raw_body = event.get("body") or b""
    if isinstance(raw_body, str):
        if event.get("isBase64Encoded"):
            raw_body = base64.b64decode(raw_body)
        else:
            raw_body = raw_body.encode()
    request = urllib.request.Request(
        target,
        data=raw_body if method not in {"GET", "HEAD"} else None,
        headers=_header_map(event),
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as upstream:
            return _response(upstream.status, dict(upstream.headers.items()), upstream.read())
    except urllib.error.HTTPError as exc:
        return _response(exc.code, dict(exc.headers.items()), exc.read())
    except Exception:
        return {
            "statusCode": 502,
            "headers": {"Content-Type": "application/json"},
            "body": '{"detail":"upstream unavailable"}',
        }
