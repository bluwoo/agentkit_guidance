"""Trace mapper — the single source of truth for span→topology overlay.

IRON RULES (do not violate without changing the design docs):
  * duration_ms = DurationMicroseconds / 1000   (span start→end delta)
    NEVER use Histogram P50/P95.
  * error  = Status == "ERROR" OR ErrorInfoList non-empty
    NEVER use error_type cross-call aggregate counts.
  * node call count = span occurrences within THIS trace (incl. retries)
    NEVER use the `_count` Counter.
  * P50/P95/QPS live ONLY in AggregateMetricsPanel — never written back
    onto a single TraceOverlay.
  * Spans that cannot map to a design component_id go to
    observed_unmapped — never force-fit, never silently drop.
"""
from __future__ import annotations

from typing import Any

from server.wizard.schemas import (
    AggregateMetricsPanel,
    LogLine,
    NodeKind,
    ObservedSpan,
    SpanStatus,
    Topology,
    TraceOverlay,
    TraceStatus,
    TraceSummary,
)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
AGGREGATE_NOTE = "近 N 小时聚合统计，不关联到任何单次调用"

OP_INVOCATION = "invocation"
OP_INVOKE_AGENT = "invoke_agent"
OP_CALL_LLM = "call_llm"
OP_EXECUTE_TOOL = "execute_tool"


# --------------------------------------------------------------------------- #
# Span normalisation: APMPlus raw dict -> ObservedSpan
# --------------------------------------------------------------------------- #
def _extract_error_info(error_list: list[dict[str, Any]]) -> tuple[str | None, str | None, str | None]:
    """Return (error_kind, error_message, error_stack) from first entry."""
    if not error_list:
        return None, None, None
    first = error_list[0] or {}
    return (
        first.get("ErrorKind"),
        first.get("ErrorMessage"),
        first.get("ErrorStack"),
    )


def is_span_error(raw: dict[str, Any]) -> bool:
    """True when the raw span is an error span (Status=ERROR or ErrorInfoList)."""
    status = str(raw.get("Status", "")).upper()
    err_list = raw.get("ErrorInfoList") or []
    return status == "ERROR" or len(err_list) > 0


def normalize_span(raw: dict[str, Any]) -> ObservedSpan:
    """Convert one raw APMPlus span dict into a normalised ObservedSpan."""
    span_id = raw.get("SpanId", "")
    parent_id = raw.get("ParentSpanId") or None
    op = raw.get("OperationName", "")
    service = raw.get("ServiceName", "")
    duration_us = raw.get("DurationMicroseconds", 0) or 0
    start_ms = raw.get("StartTimeMillisecond", 0) or 0

    err_kind, err_msg, err_stack = _extract_error_info(raw.get("ErrorInfoList") or [])
    status_code = "ERROR" if is_span_error(raw) else "OK"
    status = SpanStatus(
        code=status_code,
        error_kind=err_kind,
        error_message=err_msg,
        error_stack=err_stack,
    )

    attrs = raw.get("Attributes") or {}
    if not isinstance(attrs, dict):
        attrs = {}

    total_tokens = raw.get("TotalTokens")
    output_tokens = raw.get("OutputTokens")

    return ObservedSpan(
        span_id=span_id,
        parent_span_id=parent_id,
        name=op,
        start_time_ms=float(start_ms),
        duration_ms=float(duration_us) / 1000.0,
        status=status,
        genai_span_kind=raw.get("GenAISpanKind"),
        service_name=service or None,
        operation_name=op or None,
        call_service_name=raw.get("CallServiceName") or None,
        call_service_type=raw.get("CallServiceType") or None,
        call_resource_name=raw.get("CallResourceName") or None,
        attributes=dict(attrs),
        total_tokens=total_tokens,
        output_tokens=output_tokens,
    )


# --------------------------------------------------------------------------- #
# Component index: build a lookup from the design-time Topology
# --------------------------------------------------------------------------- #
def _component_name(component_id: str) -> str:
    """Extract the part after 'kind:' from a component_id like 'agent:foo'."""
    if ":" in component_id:
        return component_id.split(":", 1)[1]
    return component_id


def build_node_index(topology: Topology) -> dict[tuple, str]:
    """Build {semantic_key: component_id} from the design-time topology.

    The semantic key is a tuple whose first element is the span-kind string
    ("runtime" / "agent" / "model" / "skill" / "mcp").  The remaining
    elements are the identifying values extracted from the node's config
    (or inferred from the component_id suffix).
    """
    index: dict[tuple, str] = {}
    for node in topology.nodes:
        name = _component_name(node.component_id)
        kind = node.kind

        if kind == NodeKind.runtime:
            key = ("runtime", node.config.get("service_name", name))
        elif kind == NodeKind.agent:
            key = ("agent", node.config.get("agent_name", name))
        elif kind == NodeKind.model:
            key = ("model", node.config.get("model", name))
        elif kind == NodeKind.skill:
            key = ("skill", node.config.get("tool_name") or node.skill_ref or name)
        elif kind == NodeKind.mcp:
            svc = node.config.get("call_service_name", name)
            res = node.config.get("call_resource_name", "")
            key = ("mcp", svc, res)
        else:
            continue  # gateway / knowledge_base / memory / sandbox / etc.

        index[key] = node.component_id
    return index


def span_semantic_key(span: ObservedSpan) -> tuple | None:
    """Compute the lookup key for a normalised span.

    Returns None when the span has no recognised operation semantics
    (it will be surfaced as observed_unmapped).
    """
    op = span.operation_name or ""
    attrs = span.attributes

    if op == OP_INVOCATION:
        return ("runtime", span.service_name or "")
    if op == OP_INVOKE_AGENT:
        return ("agent", attrs.get("gen_ai.agent.name", ""))
    if op == OP_CALL_LLM:
        return ("model", attrs.get("gen_ai.request.model", ""))
    if op == OP_EXECUTE_TOOL:
        return ("skill", attrs.get("gen_ai.tool.name", ""))
    if span.call_service_name:
        return ("mcp", span.call_service_name, span.call_resource_name or "")
    return None


# --------------------------------------------------------------------------- #
# Core overlay builder
# --------------------------------------------------------------------------- #
def build_trace_overlay(
    trace_id: str,
    raw_spans: list[dict[str, Any]],
    topology: Topology,
    status: TraceStatus = TraceStatus.ok,
    error: str | None = None,
    logs: list[LogLine] | None = None,
) -> TraceOverlay:
    """Build a TraceOverlay from raw APMPlus spans + design-time topology.

    This is the IRON-RULE core: every number on the overlay comes from the
    span tree of THIS trace only.
    """
    normalized = [normalize_span(s) for s in raw_spans]
    index = build_node_index(topology)

    # -- node_runtime accumulation ------------------------------------------
    # node_runtime[component_id] = {state, duration_ms, count, span_ids}
    node_runtime: dict[str, dict[str, Any]] = {}
    # span_id -> component_id (for edge building)
    span_to_component: dict[str, str] = {}
    observed_unmapped: list[dict[str, Any]] = []

    for span in normalized:
        key = span_semantic_key(span)
        component_id: str | None = None
        if key is not None:
            component_id = index.get(key)

        if component_id is None:
            observed_unmapped.append({
                "span_id": span.span_id,
                "operation_name": span.operation_name,
                "service_name": span.service_name,
                "semantic_key": list(key) if key else None,
                "reason": "observed_unmapped",
            })
            continue

        span_to_component[span.span_id] = component_id
        entry = node_runtime.setdefault(component_id, {
            "state": "invoked",
            "duration_ms": 0.0,
            "count": 0,
            "span_ids": [],
        })
        entry["count"] += 1
        entry["duration_ms"] += span.duration_ms
        entry["span_ids"].append(span.span_id)
        if span.status.code == "ERROR":
            entry["state"] = "error"

    # -- edge_runtime accumulation (parent→child chains) --------------------
    # edge_runtime["src->tgt"] = {count, duration_ms, error_count, error_rate}
    edge_runtime: dict[str, dict[str, Any]] = {}
    for span in normalized:
        if span.span_id not in span_to_component:
            continue
        child_comp = span_to_component[span.span_id]
        parent_id = span.parent_span_id
        if not parent_id or parent_id not in span_to_component:
            continue
        parent_comp = span_to_component[parent_id]
        edge_key = f"{parent_comp}->{child_comp}"
        er = edge_runtime.setdefault(edge_key, {
            "source": parent_comp,
            "target": child_comp,
            "count": 0,
            "duration_ms": 0.0,
            "error_count": 0,
            "error_rate": 0.0,
        })
        er["count"] += 1
        er["duration_ms"] += span.duration_ms
        if span.status.code == "ERROR":
            er["error_count"] += 1

    # Finalise error_rate per edge.
    for er in edge_runtime.values():
        er["error_rate"] = (
            er["error_count"] / er["count"] if er["count"] else 0.0
        )

    # -- Skill mounted-but-not-executed ------------------------------------
    # Skill nodes that have an edge in the design graph but zero execute_tool
    # spans in this trace -> state="no_span" with sub-flag mounted_not_executed.
    mounted_components = {
        e.source for e in topology.edges
    } | {e.target for e in topology.edges}
    for node in topology.nodes:
        if node.kind != NodeKind.skill:
            continue
        if node.component_id in node_runtime:
            continue  # has spans -> already invoked/error
        if node.component_id in mounted_components:
            node_runtime[node.component_id] = {
                "state": "no_span",
                "sub_state": "mounted_not_executed",
                "duration_ms": 0.0,
                "count": 0,
                "span_ids": [],
            }

    # -- summary -----------------------------------------------------------
    service_set = {s.service_name for s in normalized if s.service_name}
    error_span_ids = [s.span_id for s in normalized if s.status.code == "ERROR"]
    summary = TraceSummary(
        span_nums=len(normalized),
        service_nums=len(service_set),
        error_span_ids=error_span_ids,
    )

    return TraceOverlay(
        trace_id=trace_id,
        status=status,
        spans=normalized,
        summary=summary,
        logs=logs or [],
        error=error,
        node_runtime=node_runtime,
        edge_runtime=edge_runtime,
        observed_unmapped=observed_unmapped,
    )


# --------------------------------------------------------------------------- #
# Aggregate metrics panel (independent time window — NEVER on a trace)
# --------------------------------------------------------------------------- #
def _percentile(sorted_vals: list[float], pct: float) -> float | None:
    """Linear-interpolation percentile. Returns None for empty input."""
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * pct
    lo = int(k)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = k - lo
    return sorted_vals[lo] * (1 - frac) + sorted_vals[hi] * frac


def aggregate_metrics(
    spans: list[dict[str, Any]],
    time_window: str = "1h",
    window_seconds: float | None = None,
) -> AggregateMetricsPanel:
    """Compute P50/P95/QPS/error_rate/total_calls from a span window.

    This function NEVER writes values back onto a TraceOverlay.  The note
    field is always set to the canonical disclaimer.
    """
    durations: list[float] = []
    error_count = 0
    for raw in spans:
        dur_us = raw.get("DurationMicroseconds", 0) or 0
        durations.append(float(dur_us) / 1000.0)
        if is_span_error(raw):
            error_count += 1

    total = len(durations)
    durations.sort()
    p50 = _percentile(durations, 0.50)
    p95 = _percentile(durations, 0.95)

    # window_seconds default from time_window label
    if window_seconds is None:
        _window_map = {"1h": 3600.0, "6h": 21600.0, "24h": 86400.0, "7d": 604800.0}
        window_seconds = _window_map.get(time_window, 3600.0)

    qps = (total / window_seconds) if window_seconds > 0 else None
    error_rate = (error_count / total) if total > 0 else None

    return AggregateMetricsPanel(
        time_window=time_window,  # type: ignore[arg-type]
        p50_latency_ms=p50,
        p95_latency_ms=p95,
        qps=qps,
        error_rate=error_rate,
        total_calls=max(0, total),
        note=AGGREGATE_NOTE,
        connected=True,
    )
