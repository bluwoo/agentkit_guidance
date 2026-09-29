/**
 * Canonical wire types. Mirrors server/wizard/schemas.py — do not invent field names.
 * A single-trace overlay is built ONLY from real span data.
 * P50/P95/QPS NEVER attach to a single trace; they live only in AggregateMetricsPanel.
 */

// --------------------------------------------------------------------------- //
// Step 1 — Goal card
// --------------------------------------------------------------------------- //
export interface GoalCard {
  name: string;
  target_user: string;
  task: string;
  typical_input: string;
  expected_output: string;
  non_goals: string[];
  long_running: boolean;
  migration: string | null;
  classification: 'rag' | 'tool_call' | 'code_exec' | 'multi_agent' | 'unknown' | null;
}

export interface ConfirmedPoint {
  id: string;
  text: string;
  confirmed: boolean;
}

export interface ChatMessage {
  id: string;
  role: 'wizard' | 'user';
  text: string;
  pendingPoints?: string[];
}

// --------------------------------------------------------------------------- //
// Step 2 — Acceptance / eval
// --------------------------------------------------------------------------- //
export type JudgmentType = 'artifact' | 'external_state' | 'llm_judge' | 'rule';

export interface AcceptanceCase {
  eval_id: string;
  description: string;
  input_sample: string;
  expected: string;
  judgment_type: JudgmentType;
  judgment_detail: Record<string, unknown>;
  pass_threshold: string;
  boundary_case: string;
  baseline_locked: boolean;
}

export interface EvaluationCaseResult {
  eval_id: string;
  passed: boolean;
  judgment_type: JudgmentType;
  actual_output: string;
  evidence: Record<string, unknown>;
  reason: string;
}

export interface EvaluationRun {
  run_id: string;
  runtime_id: string;
  trace_id: string | null;
  passed: number;
  failed: number;
  results: EvaluationCaseResult[];
}

// --------------------------------------------------------------------------- //
// Step 3 — Design-time topology
// --------------------------------------------------------------------------- //
export type NodeKind =
  | 'agent'
  | 'runtime'
  | 'skill'
  | 'mcp'
  | 'gateway'
  | 'knowledge_base'
  | 'memory'
  | 'sandbox'
  | 'model'
  | 'function'
  | 'identity'
  | 'guardrails'
  | 'a2a'
  | 'observability'
  | 'wizard_core'
  | 'self_evolution'
  | 'observed_unmapped';

export interface TopologyNode {
  component_id: string;
  kind: NodeKind;
  label: string;
  config: Record<string, unknown>;
  skill_ref: string | null;
  x: number | null;
  y: number | null;
}

export type EdgeType = 'sync' | 'stream' | 'data_flow' | 'config';

export interface TopologyEdge {
  edge_id: string;
  source: string;
  target: string;
  type: EdgeType;
}

export interface Topology {
  nodes: TopologyNode[];
  edges: TopologyEdge[];
}

export interface ValidationIssue {
  severity: 'error' | 'warning';
  code: string;
  message: string;
  component_id: string | null;
}

// Component catalog metadata (Step 3 left panel)
export interface ComponentDef {
  kind: NodeKind;
  label: string;
  purpose: string;
  prerequisites: string[];
  permissions: string[];
  configSchema: ConfigField[];
  group: ComponentGroup;
}

export type ComponentGroup =
  | 'Runtime'
  | '沙箱 Sandbox'
  | 'Skills'
  | 'A2A Registry'
  | '会话与记忆 Session&Memory'
  | '知识库 KnowledgeBase'
  | '网关 Gateway'
  | 'MCP 服务与工具集'
  | '身份与权限 Identity'
  | '安全围栏 Guardrails'
  | '观测 Observability'
  | '评测 Evaluation'
  | '模型服务'
  | '函数服务';

export interface ConfigField {
  key: string;
  label: string;
  type: 'text' | 'textarea' | 'select' | 'number';
  required: boolean;
  placeholder?: string;
  options?: string[];
  defaultValue?: string;
}

// --------------------------------------------------------------------------- //
// Step 4 — Runtime trace overlay (single trace, span-derived ONLY)
// --------------------------------------------------------------------------- //
export interface SpanStatus {
  code: 'OK' | 'ERROR' | 'UNSET';
  error_kind: string | null;
  error_message: string | null;
  error_stack: string | null;
}

export interface ObservedSpan {
  span_id: string;
  parent_span_id: string | null;
  name: string;
  start_time_ms: number;
  duration_ms: number;
  status: SpanStatus;
  genai_span_kind: string | null;
  service_name: string | null;
  operation_name: string | null;
  call_service_name: string | null;
  call_service_type: string | null;
  call_resource_name: string | null;
  attributes: Record<string, unknown>;
  total_tokens: number | null;
  output_tokens: number | null;
}

export interface TraceSummary {
  span_nums: number;
  service_nums: number;
  error_span_ids: string[];
}

export interface LogLine {
  service: string;
  message: string;
  log_level: string;
  trace_id: string;
  attribute: Record<string, unknown>;
  resource: Record<string, unknown>;
  hostname: string;
  file_name: string;
  file_line: string;
  source: string;
}

export type TraceStatus = 'ok' | 'not_configured' | 'auth_error' | 'error' | 'empty';

// Per-component runtime state computed from THIS single trace's spans.
export interface NodeRuntimeState {
  state: 'invoked' | 'error' | 'no_span';
  duration_ms: number;
  count: number;
  span_ids?: string[];
  sub_state?: string;
}

export interface EdgeRuntimeState {
  count: number;
  duration_ms: number;
  error_rate: number; // 0..1, computed within this single trace only
}

export interface TraceOverlay {
  trace_id: string;
  status: TraceStatus;
  spans: ObservedSpan[];
  summary: TraceSummary;
  logs: LogLine[];
  error: string | null;
  node_runtime: Record<string, NodeRuntimeState>;
  edge_runtime: Record<string, EdgeRuntimeState>;
  observed_unmapped: Array<{ name: string; service_name: string | null; operation_name: string | null }>;
}

export interface AggregateMetricsPanel {
  time_window: '1h' | '6h' | '24h' | '7d';
  p50_latency_ms: number | null;
  p95_latency_ms: number | null;
  qps: number | null;
  error_rate: number | null;
  total_calls: number | null;
  note: string;
  connected: boolean;
}

// --------------------------------------------------------------------------- //
// Runtime test invocation proxy
// --------------------------------------------------------------------------- //
export interface RuntimeInvokeRequest {
  runtime_id: string;
  input: string;
  user_id: string;
  session_id: string;
  stream: boolean;
}

export interface RuntimeInvokeResponse {
  output: string;
  trace_id: string | null;
  status_code: number;
  error: string | null;
}

// --------------------------------------------------------------------------- //
// Wizard step state machine (S0-S4)
// --------------------------------------------------------------------------- //
export type TestState = 'S0' | 'S1' | 'S2' | 'S3' | 'S4';

export type StepId = 1 | 2 | 3 | 4;
