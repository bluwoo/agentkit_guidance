"""Component: **agentkit-observability** (APMPlus + TLS).

Per the Skill:
  * Enabled by toggling observability on the Runtime; VeADK exports via env
    ENABLE_APMPLUS / ENABLE_TLS / ENABLE_COZELOOP.
  * Span attributes follow gen.ai semantic conventions (gen_ai.system, gen_ai.operation.name,
    gen_ai.user.id, gen_ai.session.id, ...).
  * CRITICAL rule: a single trace's duration = span start->end difference; error = span
    Status=ERROR; P50/P95/QPS are *aggregate* window metrics, never attributed to one call.

We run an in-memory span recorder + aggregator that encodes exactly this distinction.
Live APMPlus GetTraceDetail / ListSpan / ListSession need AK/SK signing (CloudBoundary).
"""
from __future__ import annotations

import statistics
import uuid
from dataclasses import dataclass, field

from .contract import Clock


@dataclass
class Span:
    name: str
    trace_id: str
    start: int
    end: int = 0
    status: str = "OK"
    attrs: dict = field(default_factory=dict)

    @property
    def duration_ms(self) -> int:
        return max(0, self.end - self.start)

    @property
    def is_error(self) -> bool:
        return self.status == "ERROR"


class TraceRecorder:
    """In-memory OTel-style recorder following gen.ai attribute conventions."""

    def __init__(self):
        self.spans: list[Span] = []

    def new_trace(self) -> str:
        return uuid.uuid4().hex

    def record(self, name: str, trace_id: str, gen_ai: dict, duration_ms: int = 0,
               status: str = "OK") -> Span:
        start = Clock.ms()
        end = start + duration_ms
        span = Span(name=name, trace_id=trace_id, start=start, end=end,
                    status=status, attrs={"gen_ai.system": "agentkit", **gen_ai})
        self.spans.append(span)
        return span

    def trace_summary(self, trace_id: str) -> dict:
        spans = [s for s in self.spans if s.trace_id == trace_id]
        return {
            "trace_id": trace_id,
            "span_count": len(spans),
            # single-trace duration from span start->end diff (NOT a histogram percentile)
            "total_duration_ms": sum(s.duration_ms for s in spans),
            "error_spans": [s.name for s in spans if s.is_error],
            "operations": [s.attrs.get("gen_ai.operation.name", s.name) for s in spans],
        }

    def aggregate_window(self) -> dict:
        """Aggregate window metrics (P50/P95/QPS) — independent of single traces."""
        durs = [s.duration_ms for s in self.spans]
        if not durs:
            return {"spans": 0, "p50_ms": 0, "p95_ms": 0, "errors": 0}
        ordered = sorted(durs)
        return {
            "spans": len(durs),
            "p50_ms": statistics.median(ordered),
            "p95_ms": ordered[int(0.95 * (len(ordered) - 1))],
            "errors": sum(1 for s in self.spans if s.is_error),
        }
