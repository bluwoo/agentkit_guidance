"""Layer-1 Runtime protocol shim (design 01 §4.1 / frontend 03 §2.0).

Exposes the surface an AgentKit Runtime expects from a hosted image:
  * POST /invoke            — call entry; maps to HermesBridge.turn()
  * GET  /ping /health      — liveness probes (both, SDK habit)
  * GET  /readiness /liveness
Layer-2 optional routes (ADK/SDK application layer, not Runtime-mandatory):
  * POST /run               — non-streaming (ADK convention)
  * POST /run_sse           — SSE streaming: Hermes stream_callback -> text/event-stream
  * GET/POST /sessions      — session CRUD
NOT implemented: /web/harness-sidecar/status (veADK harness_extension only).

KeyAuth: when ``RUNTIME_API_KEY`` is configured, every route below requires the
header named by ``RUNTIME_API_KEY_HEADER`` to match. Without a configured key
the service runs in open local-dev mode (requests allowed, warn logged).

Production hardening:
  * Blocking ``bridge.turn`` always runs via ``loop.run_in_executor`` — the
    event loop is never blocked.
  * ``/run_sse`` propagates the request's OTel context into the worker thread
    via ``contextvars.copy_context()``; the trace id is captured inside that
    context and passed back as a plain value (never re-read cross-thread).
  * Error events return a generic ``"stream failed"`` to the client; the full
    exception is logged server-side only.
"""
from __future__ import annotations

import asyncio
import contextvars
import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from server.wizard.config import get_settings
from server.wizard.shim.hermes_bridge import get_bridge
from server.wizard.shim.otel_middleware import current_trace_id, start_span

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# KeyAuth dependency
# --------------------------------------------------------------------------- #
class AuthError(Exception):
    def __init__(self, message: str = "unauthorized") -> None:
        self.message = message


async def require_runtime_auth(request: Request) -> None:
    """Validate the inbound API key when auth is enabled.

    Raises 401 via FastAPI exception handler when the header is missing/wrong.
    When no key is configured (local dev), allow through but warn once per req.
    """
    settings = get_settings()
    if not settings.auth_enabled:
        return
    header_name = settings.runtime_api_key_header
    supplied = request.headers.get(header_name, "")
    if not supplied or supplied != settings.runtime_api_key:
        raise AuthError("invalid or missing runtime api key")


# --------------------------------------------------------------------------- #
# Request / response models
# --------------------------------------------------------------------------- #
class InvokeRequest(BaseModel):
    session_id: str = ""
    user_id: str = "wizard-user"
    message: str = ""
    input: str = ""  # some SDK clients send `input`; accept as alias
    stream: bool = False


class InvokeResponse(BaseModel):
    session_id: str
    reply: str
    trace_id: str | None = None
    failed: bool = False
    error: str | None = None


class RunRequest(BaseModel):
    session_id: str = ""
    user_id: str = "wizard-user"
    message: str = ""


class SessionCreateRequest(BaseModel):
    user_id: str = "wizard-user"
    session_id: str = ""


def _effective_message(body: InvokeRequest | RunRequest) -> str:
    return (body.message or body.input or "").strip()


# --------------------------------------------------------------------------- #
# Router
# --------------------------------------------------------------------------- #
def build_health_router() -> APIRouter:
    """Probe endpoints — deliberately NOT behind KeyAuth so the Runtime
    orchestrator / load balancer can reach them before it has a key."""
    health = APIRouter()

    @health.get("/ping")
    async def ping() -> dict[str, str]:
        return {"status": "ok"}

    @health.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    @health.get("/readiness")
    async def readiness() -> dict[str, Any]:
        settings = get_settings()
        return {
            "status": "ok",
            "auth_enabled": settings.auth_enabled,
            "bridge": "real" if settings.real_hermes_enabled else "mock",
            "mode": settings.mode,
        }

    @health.get("/liveness")
    async def liveness() -> dict[str, str]:
        return {"status": "ok"}

    return health


def build_router() -> APIRouter:
    router = APIRouter(dependencies=[Depends(require_runtime_auth)])

    @router.post("/invoke", response_model=InvokeResponse)
    async def invoke(body: InvokeRequest) -> InvokeResponse:
        bridge = get_bridge()
        message = _effective_message(body)
        if not message:
            return InvokeResponse(session_id=body.session_id, reply="", error="empty message")

        sid = bridge.new_session(body.session_id, body.user_id)
        loop = asyncio.get_running_loop()
        with start_span(
            "invoke_agent {wizard}",
            **{
                "gen_ai.agent.name": "wizard",
                "gen_ai.operation.name": "invoke_agent",
            },
        ):
            # bridge.turn is blocking; run it in a worker thread.
            turn = await loop.run_in_executor(
                None,
                lambda: bridge.turn(session_id=sid, user_id=body.user_id, message=message),
            )

        return InvokeResponse(
            session_id=turn.get("session_id", sid),
            reply=turn.get("reply", ""),
            trace_id=current_trace_id() or turn.get("trace_id"),
            failed=bool(turn.get("failed")),
            error=turn.get("error"),
        )

    # -- layer-2 (optional): non-streaming / streaming / sessions --
    @router.post("/run")
    async def run(body: RunRequest) -> dict[str, Any]:
        """ADK-convention non-streaming call (SDK MinimalApp does not ship this)."""
        bridge = get_bridge()
        sid = bridge.new_session(body.session_id, body.user_id)
        loop = asyncio.get_running_loop()
        with start_span("invoke_agent {wizard}", **{"gen_ai.agent.name": "wizard"}):
            turn = await loop.run_in_executor(
                None,
                lambda: bridge.turn(session_id=sid, user_id=body.user_id, message=body.message),
            )
        return {
            "session_id": sid,
            "output": turn.get("reply", ""),
            "trace_id": current_trace_id() or turn.get("trace_id"),
        }

    @router.post("/run_sse")
    async def run_sse(body: RunRequest) -> StreamingResponse:
        """SSE streaming. Hermes stream_callback deltas -> text/event-stream.

        Threading / context propagation:
          * The blocking ``bridge.turn`` runs in a ``ThreadPoolExecutor`` worker.
          * The request's OTel context (contextvars) is copied into that worker
            via ``contextvars.copy_context()`` + ``ctx.run(...)`` so that
            ``start_span`` inside the worker is a child of the request's root
            span. The resulting ``trace_id`` is captured inside that context and
            passed back as a plain value on the queue — it is never re-read from
            the async side (which would be in a different contextvars frame).
          * ``on_delta`` fires from the worker thread; it uses
            ``loop.call_soon_threadsafe`` to enqueue deltas without touching
            asyncio primitives off-loop.
          * Client disconnect (``asyncio.CancelledError``) cancels the worker.
          * Errors return a generic ``"stream failed"`` to the client; the
            exception detail is logged server-side only.
        """
        bridge = get_bridge()
        sid = bridge.new_session(body.session_id, body.user_id)
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[tuple[str, Any]] = asyncio.Queue()

        # Capture the current (request) context so the worker thread inherits
        # the OTel trace span.
        req_ctx = contextvars.copy_context()

        def on_delta(text: str) -> None:
            """Called from the worker thread; hand the delta back to the loop."""
            try:
                loop.call_soon_threadsafe(queue.put_nowait, ("delta", text))
            except RuntimeError:  # loop already closing
                pass

        def producer() -> None:
            """Runs in a ThreadPoolExecutor worker; inside req_ctx."""
            def _run() -> None:
                trace_id: str | None = None
                try:
                    with start_span(
                        "invoke_agent {wizard}",
                        **{"gen_ai.agent.name": "wizard"},
                    ):
                        turn = bridge.turn(
                            session_id=sid,
                            user_id=body.user_id,
                            message=body.message,
                            on_delta=on_delta,
                        )
                        trace_id = current_trace_id()
                    loop.call_soon_threadsafe(
                        queue.put_nowait,
                        ("done", {"reply": turn.get("reply", ""), "trace_id": trace_id}),
                    )
                except Exception:
                    # Never leak str(e) / traceback to the client.
                    logger.exception("run_sse producer failed for session=%s", sid)
                    loop.call_soon_threadsafe(queue.put_nowait, ("error", None))

            req_ctx.run(_run)

        async def event_stream():
            fut = loop.run_in_executor(None, producer)
            try:
                while True:
                    kind, payload = await queue.get()
                    if kind == "delta":
                        yield f"event: delta\ndata: {json.dumps({'text': payload})}\n\n"
                    elif kind == "done":
                        yield (
                            f"event: done\n"
                            f"data: {json.dumps({'reply': payload['reply'], 'session_id': sid, 'trace_id': payload['trace_id']})}\n\n"
                        )
                        break
                    elif kind == "error":
                        yield (
                            f"event: error\n"
                            f"data: {json.dumps({'message': 'stream failed'})}\n\n"
                        )
                        break
            except asyncio.CancelledError:
                # Client disconnected: cancel the worker and re-raise.
                fut.cancel()
                raise
            finally:
                # Best-effort: wait briefly for the worker to unwind.
                try:
                    await asyncio.wait_for(asyncio.shield(fut), timeout=0.5)
                except (TimeoutError, asyncio.CancelledError, Exception):
                    pass

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @router.get("/sessions")
    async def list_sessions() -> dict[str, Any]:
        # The bridge owns session state; the shim only exposes a minimal view.
        return {"sessions": [], "note": "session lifecycle owned by bridge; list is stubbed"}

    @router.post("/sessions")
    async def create_session(body: SessionCreateRequest) -> dict[str, str]:
        bridge = get_bridge()
        sid = bridge.new_session(body.session_id, body.user_id)
        return {"session_id": sid, "user_id": body.user_id}

    # Sessions live under the authed router; health probes are separate.
    return router


__all__ = ["AuthError", "build_health_router", "build_router", "require_runtime_auth"]
