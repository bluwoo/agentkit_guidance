"""Unit tests for the trace mapper (the IRON-RULE core)."""
import json
from pathlib import Path

from server.wizard.observability.mapper import (
    aggregate_metrics,
    build_trace_overlay,
    is_span_error,
    normalize_span,
)
from server.wizard.schemas import (
    EdgeType,
    NodeKind,
    Topology,
    TopologyEdge,
    TopologyNode,
)

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# A design-time topology that matches the success fixture
# --------------------------------------------------------------------------- #
def _design_topology() -> Topology:
    return Topology(
        nodes=[
            TopologyNode(
                component_id="runtime:agentkit-runtime",
                kind=NodeKind.runtime,
                label="Runtime",
                config={"service_name": "agentkit-runtime"},
            ),
            TopologyNode(
                component_id="agent:target_agent",
                kind=NodeKind.agent,
                label="Target Agent",
                config={"agent_name": "target_agent"},
            ),
            TopologyNode(
                component_id="model:doubao-pro-32k",
                kind=NodeKind.model,
                label="Doubao Pro",
                config={"model": "doubao-pro-32k"},
            ),
            TopologyNode(
                component_id="skill:search_docs",
                kind=NodeKind.skill,
                label="Search Docs",
                skill_ref="search_docs",
            ),
            # A mounted-but-not-executed skill
            TopologyNode(
                component_id="skill:unused_skill",
                kind=NodeKind.skill,
                label="Unused Skill",
                skill_ref="unused_skill",
            ),
        ],
        edges=[
            TopologyEdge(
                edge_id="e-runtime-agent",
                source="runtime:agentkit-runtime",
                target="agent:target_agent",
                type=EdgeType.sync,
            ),
            TopologyEdge(
                edge_id="e-agent-model",
                source="agent:target_agent",
                target="model:doubao-pro-32k",
                type=EdgeType.sync,
            ),
            TopologyEdge(
                edge_id="e-agent-skill",
                source="agent:target_agent",
                target="skill:search_docs",
                type=EdgeType.sync,
            ),
            TopologyEdge(
                edge_id="e-agent-unused",
                source="agent:target_agent",
                target="skill:unused_skill",
                type=EdgeType.sync,
            ),
        ],
    )


# --------------------------------------------------------------------------- #
# duration calculation — IRON RULE: DurationMicroseconds / 1000
# --------------------------------------------------------------------------- #
class TestDurationCalculation:
    def test_duration_is_microseconds_divided_by_1000(self):
        raw = {"SpanId": "s1", "OperationName": "call_llm",
               "DurationMicroseconds": 1500000, "Status": "OK"}
        span = normalize_span(raw)
        assert span.duration_ms == 1500.0  # 1500000 / 1000

    def test_duration_zero_when_missing(self):
        raw = {"SpanId": "s1", "OperationName": "call_llm", "Status": "OK"}
        span = normalize_span(raw)
        assert span.duration_ms == 0.0

    def test_duration_from_success_fixture(self):
        data = _load("apmplus_trace_success.json")
        spans = data["Trace"]["SpanList"]
        overlay = build_trace_overlay("t1", spans, _design_topology())
        # The llm span had 800000 us = 800 ms
        llm_rt = overlay.node_runtime["model:doubao-pro-32k"]
        assert llm_rt["duration_ms"] == 800.0


# --------------------------------------------------------------------------- #
# error detection — IRON RULE: Status=ERROR or ErrorInfoList non-empty
# --------------------------------------------------------------------------- #
class TestErrorDetection:
    def test_error_from_status(self):
        raw = {"SpanId": "s1", "Status": "ERROR", "ErrorInfoList": []}
        assert is_span_error(raw) is True

    def test_error_from_error_list(self):
        raw = {"SpanId": "s1", "Status": "OK",
               "ErrorInfoList": [{"ErrorKind": "Timeout", "ErrorMessage": "x", "ErrorStack": ""}]}
        assert is_span_error(raw) is True

    def test_ok_span(self):
        raw = {"SpanId": "s1", "Status": "OK", "ErrorInfoList": []}
        assert is_span_error(raw) is False

    def test_error_span_marked_in_overlay(self):
        data = _load("apmplus_trace_error.json")
        spans = data["Trace"]["SpanList"]
        overlay = build_trace_overlay("t2", spans, _design_topology())
        # model node should be in error state
        assert overlay.node_runtime["model:doubao-pro-32k"]["state"] == "error"
        assert "span-llm-error" in overlay.summary.error_span_ids


# --------------------------------------------------------------------------- #
# call count — IRON RULE: span occurrences in THIS trace (incl retries)
# --------------------------------------------------------------------------- #
class TestCallCounting:
    def test_retry_counts_as_two_calls(self):
        data = _load("apmplus_trace_success.json")
        spans = data["Trace"]["SpanList"]
        overlay = build_trace_overlay("t1", spans, _design_topology())
        # search_docs appears twice (retry1 + retry2)
        assert overlay.node_runtime["skill:search_docs"]["count"] == 2

    def test_edge_call_count_includes_retry(self):
        data = _load("apmplus_trace_success.json")
        spans = data["Trace"]["SpanList"]
        overlay = build_trace_overlay("t1", spans, _design_topology())
        edge_key = "agent:target_agent->skill:search_docs"
        assert overlay.edge_runtime[edge_key]["count"] == 2

    def test_edge_error_rate(self):
        data = _load("apmplus_trace_error.json")
        spans = data["Trace"]["SpanList"]
        overlay = build_trace_overlay("t2", spans, _design_topology())
        edge_key = "agent:target_agent->model:doubao-pro-32k"
        # 1 out of 1 child span is ERROR → error_rate = 1.0
        assert overlay.edge_runtime[edge_key]["error_rate"] == 1.0


# --------------------------------------------------------------------------- #
# observed-unmapped — never force-fit, never drop
# --------------------------------------------------------------------------- #
class TestObservedUnmapped:
    def test_unmapped_span_goes_to_observed_unmapped(self):
        data = _load("apmplus_trace_error.json")
        spans = data["Trace"]["SpanList"]
        overlay = build_trace_overlay("t2", spans, _design_topology())
        # unplanned_external_plugin is not in the design topology
        unmapped_ids = {u["span_id"] for u in overlay.observed_unmapped}
        assert "span-tool-unmapped" in unmapped_ids
        # MCP service also unmapped
        assert "span-mcp-unmapped" in unmapped_ids

    def test_unmapped_not_in_node_runtime(self):
        data = _load("apmplus_trace_error.json")
        spans = data["Trace"]["SpanList"]
        overlay = build_trace_overlay("t2", spans, _design_topology())
        # The unmapped skill should NOT appear in node_runtime
        assert "skill:unplanned_external_plugin" not in overlay.node_runtime


# --------------------------------------------------------------------------- #
# Skill mounted-but-not-executed
# --------------------------------------------------------------------------- #
class TestMountedNotExecuted:
    def test_mounted_no_span_marked_no_span(self):
        data = _load("apmplus_trace_success.json")
        spans = data["Trace"]["SpanList"]
        overlay = build_trace_overlay("t1", spans, _design_topology())
        entry = overlay.node_runtime["skill:unused_skill"]
        assert entry["state"] == "no_span"
        assert entry.get("sub_state") == "mounted_not_executed"


# --------------------------------------------------------------------------- #
# aggregate panel — IRON RULE: independent, note always set
# --------------------------------------------------------------------------- #
class TestAggregatePanel:
    def test_panel_fields_and_note(self):
        data = _load("apmplus_list_span.json")
        spans = data["SpanList"]
        panel = aggregate_metrics(spans, time_window="1h")
        assert panel.total_calls == 4
        assert panel.p50_latency_ms is not None
        assert panel.p95_latency_ms is not None
        assert panel.error_rate == 0.25  # 1 of 4 is ERROR
        assert panel.qps is not None
        # IRON RULE: note is always the canonical disclaimer
        assert panel.note == "近 N 小时聚合统计，不关联到任何单次调用"
        assert panel.connected is True

    def test_empty_window(self):
        panel = aggregate_metrics([], time_window="1h")
        assert panel.total_calls == 0
        assert panel.error_rate is None
        assert panel.p50_latency_ms is None

    def test_panel_never_attached_to_trace(self):
        """P50/P95 must never appear in node_runtime or edge_runtime."""
        data = _load("apmplus_trace_success.json")
        spans = data["Trace"]["SpanList"]
        overlay = build_trace_overlay("t1", spans, _design_topology())
        for entry in overlay.node_runtime.values():
            assert "p50" not in entry
            assert "p95" not in entry
            assert "qps" not in entry
