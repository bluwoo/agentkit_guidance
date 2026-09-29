"""High-level observability service — the only thing the FastAPI shim calls.

All access goes through the injectable APMPlusClient abstraction, so tests
monkeypatch the client instead of touching the network.
"""
from __future__ import annotations

import time
from typing import Any

from server.wizard.observability.apmplus_client import APMPlusClient
from server.wizard.observability.mapper import (
    aggregate_metrics,
    build_trace_overlay,
)
from server.wizard.schemas import (
    AggregateMetricsPanel,
    LogLine,
    Topology,
    TraceOverlay,
    TraceStatus,
)

# Polling strategy per frontend/03-api-integration.md §4.5.
DEFAULT_POLL_INTERVAL_S = 1.5
DEFAULT_POLL_MAX_ATTEMPTS = 10

_WINDOW_SECONDS = {
    "1h": 3600.0,
    "6h": 21600.0,
    "24h": 86400.0,
    "7d": 604800.0,
}


def _extract_trace_spans(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Return spans from the official or legacy fixture response envelope.

    The APMPlus 2026-01-01 API returns ``Result.Trace.SpanList``.  Early local
    fixtures used ``Trace.SpanList`` directly, so retain that shape for backward
    compatibility while preferring the official envelope.
    """
    result = payload.get("Result") or {}
    trace_data = result.get("Trace") if isinstance(result, dict) else None
    if not isinstance(trace_data, dict):
        trace_data = payload.get("Trace") or {}
    raw_spans = trace_data.get("SpanList") if isinstance(trace_data, dict) else []
    return raw_spans if isinstance(raw_spans, list) else []


def _extract_list_spans(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Return ListSpan records from official and legacy response envelopes."""
    result = payload.get("Result") or {}
    if isinstance(result, dict):
        raw_spans = result.get("SpanList")
        if isinstance(raw_spans, list):
            return raw_spans
    raw_spans = payload.get("SpanList")
    return raw_spans if isinstance(raw_spans, list) else []


def get_trace_overlay(
    runtime_id: str,
    trace_id: str,
    design_topology: Topology,
    client: APMPlusClient | None = None,
    poll_interval: float = DEFAULT_POLL_INTERVAL_S,
    poll_max_attempts: int = DEFAULT_POLL_MAX_ATTEMPTS,
    sleep_fn=time.sleep,
) -> TraceOverlay:
    """Fetch a single trace, poll for eventual consistency, map to overlay.

    Polls up to ``poll_max_attempts`` times every ``poll_interval`` seconds.
    Stops early when:
      * credentials are missing            -> status=not_configured
      * authentication fails              -> status=auth_error
      * spans are returned (non-empty)     -> status=ok, mapped overlay
    After all attempts with no spans       -> status=empty
    """
    client = client or APMPlusClient()

    last_error: str | None = None
    suggest_time = int(time.time())
    for attempt in range(poll_max_attempts):
        resp = client.get_trace_detail(trace_id, suggest_time=suggest_time)

        if resp.status == TraceStatus.not_configured:
            return TraceOverlay(
                trace_id=trace_id,
                status=TraceStatus.not_configured,
                error=resp.error,
            )
        if resp.status == TraceStatus.auth_error:
            return TraceOverlay(
                trace_id=trace_id,
                status=TraceStatus.auth_error,
                error=resp.error,
            )
        if resp.status == TraceStatus.error:
            last_error = resp.error
            # keep polling — transient network errors may resolve
            if attempt < poll_max_attempts - 1:
                sleep_fn(poll_interval)
            continue

        # status == ok — extract spans from the official Result.Trace envelope.
        raw_spans = _extract_trace_spans(resp.payload)
        if raw_spans:
            return build_trace_overlay(
                trace_id=trace_id,
                raw_spans=raw_spans,
                topology=design_topology,
                status=TraceStatus.ok,
            )
        # empty spans — poll again for async ingestion
        if attempt < poll_max_attempts - 1:
            sleep_fn(poll_interval)

    return TraceOverlay(
        trace_id=trace_id,
        status=TraceStatus.empty,
        error=last_error,
    )


def get_aggregate_panel(
    runtime_id: str,
    time_window: str = "1h",
    service: str | None = None,
    operation_name: str | None = None,
    client: APMPlusClient | None = None,
    now_ms: int | None = None,
) -> AggregateMetricsPanel:
    """Fetch a time-window span list and compute the aggregate panel.

    The panel is INDEPENDENT of any single trace.  When APMPlus is not
    configured / fails, returns a panel with ``connected=False``.
    """
    client = client or APMPlusClient()

    now_ms = now_ms or int(time.time() * 1000)
    window_s = _WINDOW_SECONDS.get(time_window, 3600.0)
    end_ms = now_ms
    start_ms = now_ms - int(window_s * 1000)

    filters: list[dict[str, Any]] = []
    if service:
        filters.append({"Key": "service_name", "Op": "=", "Value": service})
    if operation_name:
        filters.append({"Key": "operation_name", "Op": "=", "Value": operation_name})

    resp = client.list_span(
        start_time=start_ms // 1000,
        end_time=end_ms // 1000,
        filters=filters,
    )

    if resp.status != TraceStatus.ok:
        return AggregateMetricsPanel(
            time_window=time_window,  # type: ignore[arg-type]
            note=resp.error or "聚合面板暂不可用",
            connected=False,
        )

    raw_spans = _extract_list_spans(resp.payload)
    return aggregate_metrics(
        spans=raw_spans,
        time_window=time_window,
        window_seconds=window_s,
    )


def get_logs(
    runtime_id: str,
    trace_id: str | None = None,
    service: str | None = None,
    raw_logs: list[dict[str, Any]] | None = None,
) -> list[LogLine]:
    """Convert raw TLS log dicts into normalised LogLine objects.

    The actual log-query transport (apmplus-server-log topic) is injected by
    the caller; this function only normalises the 10 verified fields.
    """
    result: list[LogLine] = []
    for entry in raw_logs or []:
        result.append(LogLine(
            service=entry.get("service", ""),
            message=entry.get("message", ""),
            log_level=entry.get("log_level", ""),
            trace_id=entry.get("trace_id", trace_id or ""),
            attribute=entry.get("attribute", {}) or {},
            resource=entry.get("resource", {}) or {},
            hostname=entry.get("hostname", ""),
            file_name=entry.get("file_name", ""),
            file_line=entry.get("file_line", ""),
            source=entry.get("source", ""),
        ))
    return result
