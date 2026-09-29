"""FastAPI application factory for the AgentKit Wizard backend.

  * Layer-1 Runtime protocol shim (/invoke, /run, /run_sse, /sessions + probes)
  * Wizard business routes under /api/wizard
  * OTel middleware (root span + W3C trace continuation)
  * Safe exception handler (never echo secrets / stack traces)
  * Lifespan: init tracer provider, close the Hermes bridge on shutdown.

Production hardening (WIZARD_MODE=production):
  * ``require_prod_ready()`` must pass — WIZARD_LLM_BASE_URL / WIZARD_LLM_MODEL /
    WIZARD_LLM_API_KEY all present — or the service refuses to start.
  * ``WIZARD_ALLOWED_ORIGINS`` may be empty in production (same-origin SPA, no
    CORS needed); wildcard ``*`` is rejected. Local mode still defaults to ``*``.

Run:
  uvicorn server.wizard.main:app --host 0.0.0.0 --port 8000
(see server/README.md)
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from server.wizard.config import get_settings
from server.wizard.shim.hermes_bridge import reset_bridge
from server.wizard.shim.otel_middleware import (
    init_tracer_provider,
    make_otel_asgi_middleware,
)
from server.wizard.shim.runtime_protocol import (
    AuthError,
    build_health_router,
    build_router,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("wizard.main")


def _resolve_cors_origins(settings) -> list[str]:
    """Pick CORS allow-origins from settings, enforcing production policy.

    * production: empty list is allowed (frontend is served same-origin, no CORS
      needed); wildcard ``*`` is rejected.
    * local / mock: empty list defaults to ``*`` (warned); otherwise use the list.
    """
    origins = list(settings.allowed_origins or [])
    if settings.production:
        # Empty allowlist = same-origin only (no CORS headers). The frontend is
        # served by this same backend (SERVE_FRONTEND_DIST), so no cross-origin
        # allowlist is required. This also avoids the chicken-and-egg problem of
        # needing the runtime endpoint before the runtime exists.
        if "*" in origins:
            raise RuntimeError(
                "WIZARD_MODE=production rejects allow_origins=['*']; set an explicit allowlist"
            )
        return origins
    # local / mock
    if not origins:
        logger.warning("WIZARD_ALLOWED_ORIGINS unset -> CORS allowing '*' (local dev only)")
        return ["*"]
    return origins


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # --- startup ---
        if settings.production:
            missing = settings.require_prod_ready()
            if missing:
                raise RuntimeError(
                    f"production mode is missing required config: {missing}. "
                    "Refusing to start."
                )
        init_tracer_provider(settings)
        logger.info("AgentKit Wizard starting; mode=%s config=%s", settings.mode, settings.masked_summary())
        # Wire the Hermes bridge to the MCP endpoint and run FastMCP's session
        # manager inside this parent lifespan. Mounted sub-app lifespans are not
        # started automatically by Starlette.
        from server.wizard.mcp_endpoint import mcp_lifespan, set_bridge
        from server.wizard.shim.hermes_bridge import get_bridge
        set_bridge(get_bridge(settings))
        from server.wizard.auth import get_store
        app.state.user_store = get_store(settings.data_dir)
        if not settings.auth_enabled:
            logger.warning("RUNTIME_API_KEY unset -> KeyAuth DISABLED (local dev only)")
        async with mcp_lifespan():
            yield
        # --- shutdown ---
        reset_bridge()
        logger.info("AgentKit Wizard shut down cleanly")

    app = FastAPI(title="AgentKit Wizard", version=settings.wizard_version, lifespan=lifespan)

    # CORS: read from settings; production enforces an explicit allowlist.
    cors_origins = _resolve_cors_origins(settings)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # OTel root-span middleware (must wrap requests to build the invocation span).
    app.add_middleware(make_otel_asgi_middleware(settings))

    # Single-user browser login gate (login page + static stay public).
    from server.wizard.auth import auth_middleware
    app.middleware("http")(auth_middleware)

    # --- safe exception handlers: never leak secrets / stack traces ---
    @app.exception_handler(AuthError)
    async def _auth_err(request: Request, exc: AuthError):
        return JSONResponse(status_code=401, content={"detail": exc.message})

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        # Log full detail server-side; return a generic message to the client.
        logger.exception("unhandled error on %s", request.url.path)
        return JSONResponse(status_code=500, content={"detail": "internal server error"})

    # --- routers ---
    # Health probes: unauthenticated (Runtime orchestrator / LB reach them first).
    app.include_router(build_health_router())
    # Layer-1/2 Runtime protocol: KeyAuth applied inside build_router().
    app.include_router(build_router())
    # Wizard business routes.
    from server.wizard.api.router import build_wizard_router
    app.include_router(build_wizard_router(), prefix="/api/wizard")

    # Single-user browser login.
    from server.wizard.api.routes_auth import build_auth_router
    app.include_router(build_auth_router(settings))

    # Native MCP streamable-HTTP endpoint at /mcp (tool: invoke).
    from server.wizard.mcp_endpoint import mount_mcp
    mount_mcp(app)

    # --- optional single-process static hosting --------------------------------
    # When SERVE_FRONTEND_DIST points at a built web/dist, serve the SPA at "/"
    # (with SPA fallback) in the same process as the API. With the env var
    # unset the service keeps its original JSON root (dev / API-only mode).
    serve_dist = os.environ.get("SERVE_FRONTEND_DIST", "").strip()
    if serve_dist:
        from server.wizard.static_mount import maybe_mount_spa
        maybe_mount_spa(app, serve_dist)
    else:
        @app.get("/")
        async def root() -> dict:
            return {"service": "agentkit-wizard", "version": settings.wizard_version,
                    "docs": "/docs"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server.wizard.main:app", host="0.0.0.0", port=8000, reload=False)
