"""AgentKit Wizard observability layer.

Public API (import from here for convenience):
  - APMPlusClient            : query client (GetTraceDetail/ListSpan/ListSession)
  - APMPlusResponse          : normalised query result
  - build_trace_overlay      : raw spans + Topology -> TraceOverlay (core)
  - aggregate_metrics       : span window -> AggregateMetricsPanel (independent)
  - get_trace_overlay        : high-level fetch + poll + map
  - get_aggregate_panel      : high-level window panel
  - get_logs                 : raw TLS logs -> [LogLine]
"""
from server.wizard.observability.apmplus_client import (
    APMPlusClient,
    APMPlusResponse,
)
from server.wizard.observability.mapper import (
    aggregate_metrics,
    build_trace_overlay,
    normalize_span,
)
from server.wizard.observability.service import (
    get_aggregate_panel,
    get_logs,
    get_trace_overlay,
)

__all__ = [
    "APMPlusClient",
    "APMPlusResponse",
    "aggregate_metrics",
    "build_trace_overlay",
    "get_aggregate_panel",
    "get_logs",
    "get_trace_overlay",
    "normalize_span",
]
