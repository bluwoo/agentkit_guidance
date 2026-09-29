"""Thin observability routes (frontend/03 §4).

These forward to ``server.wizard.observability.service`` which another module is
still building. We **lazy-import** it: if the module is absent or fails to
import, we return an honest ``not_configured`` payload instead of crashing this
service. Tests monkeypatch the imported functions.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/observability", tags=["observability"])


def _load_service():
    """Return (module, None) or (None, error-reason). Never raises."""
    try:
        from server.wizard.observability import (  # noqa: WPS433 - intentional lazy
            get_aggregate_panel,
            get_logs,
            get_trace_overlay,
        )
        return {
            "get_trace_overlay": get_trace_overlay,
            "get_aggregate_panel": get_aggregate_panel,
            "get_logs": get_logs,
        }, None
    except Exception as e:  # pragma: no cover - depends on sibling module
        return None, f"observability service unavailable: {e}"


class TraceQuery(BaseModel):
    runtime_id: str = ""
    trace_id: str = ""
    service: str | None = None
    user_id: str | None = None
    session_id: str | None = None


@router.get("/trace")
async def trace(q: TraceQuery = Depends()) -> dict[str, Any]:
    svc, err = _load_service()
    if err:
        return {"trace_id": q.trace_id, "status": "not_configured", "error": err}
    # Design topology comes from the saved draft; if empty, an empty Topology.
    from server.wizard.schemas import Topology
    from server.wizard.store import draft_store
    topo_data = draft_store.get_draft("topology", "current") or {}
    topology = Topology(**topo_data) if topo_data else Topology()
    overlay = svc["get_trace_overlay"](runtime_id=q.runtime_id, trace_id=q.trace_id,
                                        design_topology=topology)
    return overlay.model_dump()


class AggregateQuery(BaseModel):
    runtime_id: str = ""
    time_window: str = "1h"
    service: str | None = None
    operation_name: str | None = None


@router.get("/metrics/aggregate")
async def aggregate(q: AggregateQuery = Depends()) -> dict[str, Any]:
    svc, err = _load_service()
    if err:
        return {"time_window": q.time_window, "connected": False, "note": err}
    panel = svc["get_aggregate_panel"](
        runtime_id=q.runtime_id, time_window=q.time_window,
        service=q.service, operation_name=q.operation_name,
    )
    return panel.model_dump() if hasattr(panel, "model_dump") else panel


class LogsQuery(BaseModel):
    runtime_id: str = ""
    trace_id: str | None = None
    service: str | None = None
    time_window: str | None = None
    log_level: str | None = None


@router.get("/logs")
async def logs(q: LogsQuery = Depends()) -> dict[str, Any]:
    svc, err = _load_service()
    if err:
        return {"connected": False, "logs": [], "note": err}
    result = svc["get_logs"](
        runtime_id=q.runtime_id, trace_id=q.trace_id, service=q.service,
        time_window=q.time_window, log_level=q.log_level,
    )
    if hasattr(result, "model_dump"):
        return result.model_dump()
    return {"logs": result}


__all__ = ["router"]
