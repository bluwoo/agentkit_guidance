"""Shared canonical data contracts for the AgentKit Wizard.

This module is the single source of truth for the wire format between the
FastAPI shim (server/wizard/api/*) and the React frontend (web/*). It mirrors
the design contracts in frontend/02-architecture-diagram-spec.md and
frontend/03-api-integration.md.

Hard rules encoded here (do not relax without changing the design docs):
- A single-trace overlay is built ONLY from real span data:
  duration_ms = DurationMicroseconds / 1000; error = Status=ERROR or
  ErrorInfoList non-empty; call counts = span occurrences by operation semantics.
  P50/P95/QPS are NEVER attached to a single trace — they live only in the
  separate AggregateMetricsPanel.
- Spans that cannot be mapped to a design-time component_id are "unknown";
  spans observed but absent from the design graph are surfaced as
  "observed-unmapped" (never silently dropped, never force-fit).
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


# --------------------------------------------------------------------------- #
# Step 1 — Goal card
# --------------------------------------------------------------------------- #
class GoalCard(BaseModel):
    name: str = ""
    target_user: str = ""          # 场景名称 / 目标用户
    task: str = ""                 # 业务任务
    typical_input: str = ""        # 典型输入
    expected_output: str = ""      # 期望产出
    non_goals: list[str] = Field(default_factory=list)  # 非目标
    long_running: bool = False     # 是否长链路任务（需 Sidecar 四件套）
    migration: str | None = None  # None | langchain | langgraph | adk | strd...
    classification: Literal["rag", "tool_call", "code_exec", "multi_agent", "unknown"] | None = None


class ConfirmedPoint(BaseModel):
    id: str
    text: str
    confirmed: bool = True


# --------------------------------------------------------------------------- #
# Step 2 — Acceptance / eval
# --------------------------------------------------------------------------- #
class JudgmentType(str, Enum):
    artifact = "artifact"
    external_state = "external_state"
    llm_judge = "llm_judge"
    rule = "rule"


class AcceptanceCase(BaseModel):
    eval_id: str
    description: str = ""
    input_sample: str = ""
    expected: str = ""
    judgment_type: JudgmentType = JudgmentType.rule
    judgment_detail: dict[str, Any] = Field(default_factory=dict)
    pass_threshold: str = ""
    boundary_case: str = ""
    baseline_locked: bool = True  # 自进化提案不得改写


class EvaluationCaseResult(BaseModel):
    eval_id: str
    passed: bool
    judgment_type: JudgmentType
    actual_output: str = ""
    evidence: dict[str, Any] = Field(default_factory=dict)
    reason: str = ""


class EvaluationRun(BaseModel):
    run_id: str
    runtime_id: str
    trace_id: str | None = None
    passed: int = 0
    failed: int = 0
    results: list[EvaluationCaseResult] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Step 3 — Design-time topology
# --------------------------------------------------------------------------- #
class NodeKind(str, Enum):
    agent = "agent"
    runtime = "runtime"
    skill = "skill"
    mcp = "mcp"
    gateway = "gateway"
    knowledge_base = "knowledge_base"
    memory = "memory"
    sandbox = "sandbox"
    model = "model"
    function = "function"
    identity = "identity"
    guardrails = "guardrails"
    a2a = "a2a"
    observability = "observability"
    wizard_core = "wizard_core"      # Hermes + shim internal node
    self_evolution = "self_evolution"
    observed_unmapped = "observed_unmapped"


class TopologyNode(BaseModel):
    component_id: str               # stable id, e.g. "agent:target"
    kind: NodeKind
    label: str
    config: dict[str, Any] = Field(default_factory=dict)
    skill_ref: str | None = None
    x: float | None = None
    y: float | None = None


class EdgeType(str, Enum):
    sync = "sync"
    stream = "stream"
    data_flow = "data_flow"
    config = "config"


class TopologyEdge(BaseModel):
    edge_id: str
    source: str
    target: str
    type: EdgeType = EdgeType.sync


class Topology(BaseModel):
    nodes: list[TopologyNode] = Field(default_factory=list)
    edges: list[TopologyEdge] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    severity: Literal["error", "warning"]
    code: str
    message: str
    component_id: str | None = None


# --------------------------------------------------------------------------- #
# Step 4 — Runtime trace overlay (single trace, span-derived ONLY)
# --------------------------------------------------------------------------- #
class SpanStatus(BaseModel):
    code: Literal["OK", "ERROR", "UNSET"] = "UNSET"
    error_kind: str | None = None
    error_message: str | None = None
    error_stack: str | None = None


class ObservedSpan(BaseModel):
    span_id: str
    parent_span_id: str | None = None
    name: str                       # OperationName
    start_time_ms: float = 0.0
    duration_ms: float = 0.0        # DurationMicroseconds / 1000
    status: SpanStatus = Field(default_factory=SpanStatus)
    genai_span_kind: str | None = None
    service_name: str | None = None
    operation_name: str | None = None
    call_service_name: str | None = None
    call_service_type: str | None = None
    call_resource_name: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    total_tokens: int | None = None
    output_tokens: int | None = None


class TraceSummary(BaseModel):
    span_nums: int = 0
    service_nums: int = 0
    error_span_ids: list[str] = Field(default_factory=list)


class LogLine(BaseModel):
    service: str = ""
    message: str = ""
    log_level: str = ""
    trace_id: str = ""
    attribute: dict[str, Any] = Field(default_factory=dict)
    resource: dict[str, Any] = Field(default_factory=dict)
    hostname: str = ""
    file_name: str = ""
    file_line: str = ""
    source: str = ""


class TraceStatus(str, Enum):
    ok = "ok"                       # overlay rendered from real spans
    not_configured = "not_configured"
    auth_error = "auth_error"
    error = "error"
    empty = "empty"                 # trace exists but no spans (≠ not invoked)


class TraceOverlay(BaseModel):
    trace_id: str
    status: TraceStatus = TraceStatus.empty
    spans: list[ObservedSpan] = Field(default_factory=list)
    summary: TraceSummary = Field(default_factory=TraceSummary)
    logs: list[LogLine] = Field(default_factory=list)
    error: str | None = None
    # Mapped presentation (computed server-side from spans + design graph):
    #   node_runtime[component_id] = {state: invoked|error|no_span, duration_ms, count}
    node_runtime: dict[str, dict[str, Any]] = Field(default_factory=dict)
    edge_runtime: dict[str, dict[str, Any]] = Field(default_factory=dict)
    observed_unmapped: list[dict[str, Any]] = Field(default_factory=list)


class AggregateMetricsPanel(BaseModel):
    """Independent time-window panel. NEVER attached to a single trace."""
    time_window: Literal["1h", "6h", "24h", "7d"] = "1h"
    p50_latency_ms: float | None = None
    p95_latency_ms: float | None = None
    qps: float | None = None
    error_rate: float | None = None
    total_calls: int | None = None
    note: str = "近 N 小时聚合统计，不关联到任何单次调用"
    connected: bool = False


# --------------------------------------------------------------------------- #
# Self-evolution proposals
# --------------------------------------------------------------------------- #
class ProposalKind(str, Enum):
    memory = "memory"
    skill = "skill"
    eval_reflow = "eval_reflow"


class ProposalState(str, Enum):
    draft = "draft"
    scanned = "scanned"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    staged = "staged"
    regressing = "regressing"
    live = "live"


class Proposal(BaseModel):
    id: str
    kind: ProposalKind
    target: str                     # e.g. "MEMORY.md" or "skills/foo/SKILL.md"
    diff: str = ""
    rationale: str = ""
    state: ProposalState = ProposalState.draft
    scan_result: dict[str, Any] | None = None
    regression_report: dict[str, Any] | None = None
    created_at: str | None = None


# --------------------------------------------------------------------------- #
# Runtime test invocation proxy
# --------------------------------------------------------------------------- #
class RuntimeInvokeRequest(BaseModel):
    runtime_id: str
    input: str
    user_id: str = "wizard-user"
    session_id: str = ""
    stream: bool = False


class RuntimeInvokeResponse(BaseModel):
    output: str = ""
    trace_id: str | None = None
    status_code: int = 200
    error: str | None = None
