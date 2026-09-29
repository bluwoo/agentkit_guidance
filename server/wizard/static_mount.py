"""Optional SPA static hosting for the Wizard.

When the ``SERVE_FRONTEND_DIST`` env var points at a built ``web/dist`` (the
React+Vite production output), the app can serve the frontend from the same
process as the API, so a single container exposes both.

Design notes:
  * This is a *purely optional* mount. With ``SERVE_FRONTEND_DIST`` unset the
    service behaves exactly as before (JSON ``GET /``).
  * API routers (``/api/...``, ``/invoke``, ``/run``, ``/health``, ...) are
    registered in ``main.py`` *before* this catch-all runs, so API paths keep
    matching first.
  * Any path that maps to a real file under the dist dir is served directly
    (hashed JS/CSS/assets); every other non-API path falls back to
    ``index.html`` so client-side routing works on hard refresh.
  * Failures (missing dir / missing index.html) degrade to a logged warning and
    API-only mode — they never crash boot.
"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

logger = logging.getLogger("wizard.static")


def maybe_mount_spa(app: FastAPI, dist_dir: str) -> bool:
    """Mount a built SPA at ``/`` if ``dist_dir`` looks like a Vite build.

    Returns ``True`` when static hosting was enabled, ``False`` when it was
    skipped (missing path / missing index.html).
    """
    root = Path(dist_dir or "").expanduser()
    if not root.is_dir():
        logger.warning("SERVE_FRONTEND_DIST=%r is not a directory; API-only mode", str(root))
        return False

    index_file = root / "index.html"
    if not index_file.is_file():
        logger.warning("index.html not found under %r; API-only mode", str(root))
        return False

    @app.get("/{full_path:path}", include_in_schema=False)
    async def _spa(full_path: str) -> FileResponse:
        # Serve real files (assets, favicon, source maps, ...) directly; for
        # anything else return index.html so the React router takes over.
        candidate = (root / full_path).resolve()
        try:
            # Guard against path traversal outside the dist root.
            candidate.relative_to(root.resolve())
        except ValueError:
            return FileResponse(index_file)
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(index_file)

    logger.info("Serving SPA from %s at '/' (SPA fallback to index.html)", root)
    return True
