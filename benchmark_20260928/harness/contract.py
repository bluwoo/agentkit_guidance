"""AgentKit minimal Harness — shared request/response contract.

This module is the single source of truth for the wire contract described in the
`agentkit-sdk` / `agentkit-runtime` Skills:

  * Header:  ``user_id`` / ``session_id``  (multi-tenant isolation; NOT auth)
  * Body:    ``prompt`` (str) / ``files`` (optional multimodal)
  * Sync response: str ; health check ``/ping`` -> ``"pong!"``

It also carries the ``CloudBoundary`` marker: any capability that would need real
Volcengine credentials (AK/SK, ARK model key, APMPlus signing) is implemented up to
the "needs credential" edge and explicitly flagged, never silently faked as a cloud
call.
"""
from __future__ import annotations

import dataclasses
import time
import uuid
from typing import Any, Optional


class CloudBoundary(RuntimeError):
    """Raised (or documented) when a code path needs real cloud credentials.

    The Harness never reaches out to Volcengine. When a component's real behaviour
    requires AK/SK / an ARK model key / a live MCP endpoint, we stop at the boundary
    and surface this marker so the audit can see exactly where cloud would attach.
    """


@dataclasses.dataclass
class InvokeRequest:
    """The unified AgentKit /invoke request (Header + Body collapsed)."""

    prompt: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    files: list[Any] = dataclasses.field(default_factory=list)
    # inbound authorization header (set by the identity layer, not the caller)
    authorization: Optional[str] = None

    @property
    def has_identity(self) -> bool:
        return bool(self.user_id) and bool(self.session_id)


@dataclasses.dataclass
class InvokeResult:
    text: str
    user_id: str
    session_id: str
    trace_id: str = dataclasses.field(default_factory=lambda: uuid.uuid4().hex)
    blocks: list[str] = dataclasses.field(default_factory=list)  # guardrail hits
    ok: bool = True


class Clock:
    """Monotonic millisecond clock used by the observability layer."""

    @staticmethod
    def ms() -> int:
        return int(time.time() * 1000)
