"""Component: **agentkit-sdk** (AgentkitSimpleApp decorator surface).

Mirrors the Skill contract:
  * ``app = AgentkitSimpleApp()``
  * ``@app.entrypoint`` decorates ``async def run(payload: dict, headers: dict)``
  * ``@app.ping`` decorates a health check returning ``"pong!"``
  * ``app.run(host, port)`` starts the service

Critical security rule from the Skill (§3.2 / §10): when ``user_id`` / ``session_id``
headers are missing, the entrypoint MUST return 400 — it must NOT fall back to a
``"default"`` identity and must NOT mint a random one (that would aggregate users
onto one session / break multi-turn context).
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Optional

from .contract import InvokeRequest, InvokeResult


class HTTPError(Exception):
    def __init__(self, status: int, detail: str):
        self.status = status
        self.detail = detail
        super().__init__(f"{status}: {detail}")


class AgentkitSimpleApp:
    """A local, in-process stand-in for ``agentkit.apps.AgentkitSimpleApp``."""

    def __init__(self) -> None:
        self._entrypoint: Optional[Callable[[dict, dict], Awaitable[Any]]] = None
        self._ping: Optional[Callable[[], str]] = None

    # -- decorators -------------------------------------------------------
    def entrypoint(self, fn: Callable[[dict, dict], Awaitable[Any]]):
        self._entrypoint = fn
        return fn

    def ping(self, fn: Callable[[], str]):
        self._ping = fn
        return fn

    # -- local dispatch (no network) --------------------------------------
    async def invoke(self, req: InvokeRequest) -> InvokeResult:
        # Security: reject missing identity headers with 400.
        if not req.user_id or not req.session_id:
            raise HTTPError(400, "user_id and session_id headers are required")
        if self._entrypoint is None:
            raise HTTPError(500, "no entrypoint registered")
        payload = {"prompt": req.prompt, "files": req.files}
        headers = {"user_id": req.user_id, "session_id": req.session_id}
        out = await self._entrypoint(payload, headers)
        # entrypoint returns str in the sync path (per runner.run -> str contract)
        return InvokeResult(text=str(out), user_id=req.user_id,
                            session_id=req.session_id)

    def ping_now(self) -> str:
        if self._ping is None:
            return "pong!"
        return self._ping()


def default_ping() -> str:
    return "pong!"
