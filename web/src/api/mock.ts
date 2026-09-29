/**
 * Frontend mock fixtures. Active when VITE_USE_MOCK=1.
 * The sample TraceOverlay deliberately exercises every visual branch:
 *   - green (invoked + OK): runtime / agent / model / knowledge_base
 *   - red   (invoked + ERROR): mcp
 *   - grey  (designed but no span): skill / memory / gateway / guardrails / observability
 *   - observed-unmapped: a span whose tool name is not in the design graph
 * Single-trace counts/latency/error-rate come ONLY from these spans.
 * P50/P95/QPS live in the separate AggregateMetricsPanel fixture.
 */
import type {
  AcceptanceCase,
  AggregateMetricsPanel,
  ChatMessage,
  ConfirmedPoint,
  GoalCard,
  TraceOverlay,
  Topology,
  ValidationIssue,
} from '@/types';

// --------------------------------------------------------------------------- //
// Default design-time topology (Step 3 / Step 4)
// --------------------------------------------------------------------------- //
export const MOCK_TOPOLOGY: Topology = {
  nodes: [
    {
      component_id: 'runtime:hermes',
      kind: 'runtime',
      label: 'Hermes Runtime',
      config: { framework: 'veADK', port: 8000, entry: 'python -m hermes' },
      skill_ref: null,
      x: 400,
      y: 40,
    },
    {
      component_id: 'agent:target',
      kind: 'agent',
      label: '工单分类 Agent',
      config: { agent_name: 'ticket-classifier', description: '对企业客服工单进行意图分类与路由' },
      skill_ref: null,
      x: 400,
      y: 180,
    },
    {
      component_id: 'model:doubao',
      kind: 'model',
      label: 'Doubao Pro 32k',
      config: { model_name: 'doubao-pro-32k', temperature: 0.3 },
      skill_ref: null,
      x: 180,
      y: 320,
    },
    {
      component_id: 'kb:viking',
      kind: 'knowledge_base',
      label: 'VikingDB 知识库',
      config: { kb_id: 'kb-20260918', top_k: 5 },
      skill_ref: null,
      x: 340,
      y: 320,
    },
    {
      component_id: 'mcp:ticket',
      kind: 'mcp',
      label: '工单 MCP 服务',
      config: { mcp_endpoint: 'http://ticket-mcp:8080/mcp', auth_mode: 'KeyAuth' },
      skill_ref: null,
      x: 520,
      y: 320,
    },
    {
      component_id: 'skill:grill',
      kind: 'skill',
      label: 'grill-with-docs',
      config: { skill_name: 'grill-with-docs', auto_invoke: 'false' },
      skill_ref: 'skills/grill-with-docs',
      x: 680,
      y: 320,
    },
    {
      component_id: 'memory:session',
      kind: 'memory',
      label: '会话记忆',
      config: { memory_backend: 'redis' },
      skill_ref: null,
      x: 400,
      y: 460,
    },
    {
      component_id: 'gateway:main',
      kind: 'gateway',
      label: 'MCP 网关',
      config: { gateway_mode: 'mcp' },
      skill_ref: null,
      x: 680,
      y: 180,
    },
    {
      component_id: 'guardrails:safe',
      kind: 'guardrails',
      label: '安全围栏',
      config: { policy: '拦截退款/转账类高危操作' },
      skill_ref: null,
      x: 180,
      y: 460,
    },
    {
      component_id: 'obs:apm',
      kind: 'observability',
      label: 'APMPlus 观测',
      config: { trace_content: 'true' },
      skill_ref: null,
      x: 680,
      y: 460,
    },
  ],
  edges: [
    { edge_id: 'e1', source: 'runtime:hermes', target: 'agent:target', type: 'stream' },
    { edge_id: 'e2', source: 'agent:target', target: 'model:doubao', type: 'sync' },
    { edge_id: 'e3', source: 'agent:target', target: 'kb:viking', type: 'data_flow' },
    { edge_id: 'e4', source: 'agent:target', target: 'mcp:ticket', type: 'sync' },
    { edge_id: 'e5', source: 'agent:target', target: 'skill:grill', type: 'config' },
    { edge_id: 'e6', source: 'agent:target', target: 'memory:session', type: 'data_flow' },
    { edge_id: 'e7', source: 'runtime:hermes', target: 'gateway:main', type: 'config' },
    { edge_id: 'e8', source: 'gateway:main', target: 'mcp:ticket', type: 'sync' },
    { edge_id: 'e9', source: 'agent:target', target: 'guardrails:safe', type: 'config' },
    { edge_id: 'e10', source: 'runtime:hermes', target: 'obs:apm', type: 'data_flow' },
  ],
};

// --------------------------------------------------------------------------- //
// Sample single-trace overlay (span-derived ONLY)
// --------------------------------------------------------------------------- //
export const MOCK_TRACE_OVERLAY: TraceOverlay = {
  trace_id: 'trace-7f3a9c2e1b4d5e6f',
  status: 'ok',
  spans: [
    {
      span_id: 'span-root',
      parent_span_id: null,
      name: 'invocation',
      start_time_ms: 1726630000000,
      duration_ms: 1200,
      status: { code: 'OK', error_kind: null, error_message: null, error_stack: null },
      genai_span_kind: 'workflow',
      service_name: 'agentkit-runtime',
      operation_name: 'invocation',
      call_service_name: null,
      call_service_type: null,
      call_resource_name: null,
      attributes: {
        'gen_ai.system': 'agentkit',
        'gen_ai.user.id': 'wizard-user',
        'gen_ai.session.id': 'sess-demo-001',
      },
      total_tokens: null,
      output_tokens: null,
    },
    {
      span_id: 'span-agent',
      parent_span_id: 'span-root',
      name: 'invoke_agent ticket-classifier',
      start_time_ms: 1726630000050,
      duration_ms: 980,
      status: { code: 'OK', error_kind: null, error_message: null, error_stack: null },
      genai_span_kind: 'workflow',
      service_name: 'agentkit-runtime',
      operation_name: 'invoke_agent',
      call_service_name: null,
      call_service_type: null,
      call_resource_name: null,
      attributes: {
        'gen_ai.agent.name': 'ticket-classifier',
        'gen_ai.operation.name': 'invoke_agent',
        'gen_ai.input': '帮我把这张工单分类：客户说发票开错了',
        'gen_ai.output': '分类结果：发票问题 / 路由：财务组',
      },
      total_tokens: 1280,
      output_tokens: 420,
    },
    {
      span_id: 'span-llm',
      parent_span_id: 'span-agent',
      name: 'call_llm doubao-pro-32k',
      start_time_ms: 1726630000100,
      duration_ms: 620,
      status: { code: 'OK', error_kind: null, error_message: null, error_stack: null },
      genai_span_kind: 'llm',
      service_name: 'llm-gateway',
      operation_name: 'call_llm',
      call_service_name: null,
      call_service_type: null,
      call_resource_name: null,
      attributes: {
        'gen_ai.request.model': 'doubao-pro-32k',
        'gen_ai.usage.input_tokens': 860,
        'gen_ai.usage.output_tokens': 420,
        'gen_ai.usage.total_tokens': 1280,
      },
      total_tokens: 1280,
      output_tokens: 420,
    },
    {
      span_id: 'span-kb',
      parent_span_id: 'span-agent',
      name: 'execute_tool kb_search',
      start_time_ms: 1726630000750,
      duration_ms: 150,
      status: { code: 'OK', error_kind: null, error_message: null, error_stack: null },
      genai_span_kind: 'tool',
      service_name: 'agentkit-runtime',
      operation_name: 'execute_tool',
      call_service_name: 'vikingdb',
      call_service_type: 'db',
      call_resource_name: 'kb-20260918',
      attributes: {
        'gen_ai.tool.name': 'kb_search',
        'gen_ai.tool.input': '发票开错',
        'gen_ai.tool.output': '命中 3 条切片',
      },
      total_tokens: null,
      output_tokens: null,
    },
    {
      span_id: 'span-mcp',
      parent_span_id: 'span-agent',
      name: 'execute_tool create_ticket',
      start_time_ms: 1726630000920,
      duration_ms: 80,
      status: {
        code: 'ERROR',
        error_kind: 'UpstreamUnavailable',
        error_message: '工单 MCP 服务 503: connection refused',
        error_stack: 'Traceback: ... at mcp_client.py:142',
      },
      genai_span_kind: 'tool',
      service_name: 'agentkit-runtime',
      operation_name: 'execute_tool',
      call_service_name: 'ticket-mcp',
      call_service_type: 'http',
      call_resource_name: 'create_ticket',
      attributes: {
        'gen_ai.tool.name': 'create_ticket',
        'gen_ai.tool.input': '{ "title": "发票开错" }',
      },
      total_tokens: null,
      output_tokens: null,
    },
    {
      // observed-unmapped: tool name not present in the design graph
      span_id: 'span-unmapped',
      parent_span_id: 'span-agent',
      name: 'execute_tool send_notification',
      start_time_ms: 1726630001010,
      duration_ms: 50,
      status: { code: 'OK', error_kind: null, error_message: null, error_stack: null },
      genai_span_kind: 'tool',
      service_name: 'unknown-svc',
      operation_name: 'execute_tool',
      call_service_name: 'notification-hub',
      call_service_type: 'http',
      call_resource_name: 'send',
      attributes: { 'gen_ai.tool.name': 'send_notification' },
      total_tokens: null,
      output_tokens: null,
    },
  ],
  summary: {
    span_nums: 6,
    service_nums: 3,
    error_span_ids: ['span-mcp'],
  },
  logs: [
    {
      service: 'agentkit-runtime',
      message: 'invoke started for session sess-demo-001',
      log_level: 'INFO',
      trace_id: 'trace-7f3a9c2e1b4d5e6f',
      attribute: {},
      resource: {},
      hostname: 'runtime-pod-01',
      file_name: 'runner.py',
      file_line: '88',
      source: 'agentkit-runtime',
    },
    {
      service: 'agentkit-runtime',
      message: 'tool create_ticket failed: UpstreamUnavailable',
      log_level: 'ERROR',
      trace_id: 'trace-7f3a9c2e1b4d5e6f',
      attribute: { container_id: 'ctr-abc' },
      resource: {},
      hostname: 'runtime-pod-01',
      file_name: 'mcp_client.py',
      file_line: '142',
      source: 'agentkit-runtime',
    },
  ],
  error: null,
  // Mapped presentation (computed from spans + design graph):
  node_runtime: {
    'runtime:hermes': { state: 'invoked', duration_ms: 1200, count: 1 },
    'agent:target': { state: 'invoked', duration_ms: 980, count: 1 },
    'model:doubao': { state: 'invoked', duration_ms: 620, count: 1 },
    'kb:viking': { state: 'invoked', duration_ms: 150, count: 1 },
    'mcp:ticket': { state: 'error', duration_ms: 80, count: 1 },
    // skill/memory/gateway/guardrails/observability intentionally absent → grey
  },
  edge_runtime: {
    'runtime:hermes->agent:target': { count: 1, duration_ms: 980, error_rate: 0 },
    'agent:target->model:doubao': { count: 1, duration_ms: 620, error_rate: 0 },
    'agent:target->kb:viking': { count: 1, duration_ms: 150, error_rate: 0 },
    'agent:target->mcp:ticket': { count: 1, duration_ms: 80, error_rate: 1 },
  },
  observed_unmapped: [
    { name: 'send_notification', service_name: 'unknown-svc', operation_name: 'execute_tool' },
  ],
};

// Variant: observability connected but this trace has no spans (S3).
export const MOCK_TRACE_EMPTY: TraceOverlay = {
  ...MOCK_TRACE_OVERLAY,
  status: 'empty',
  spans: [],
  summary: { span_nums: 0, service_nums: 0, error_span_ids: [] },
  node_runtime: {},
  edge_runtime: {},
  observed_unmapped: [],
  logs: [],
};

// --------------------------------------------------------------------------- //
// Aggregate metrics panel (independent — NEVER attached to a single trace)
// --------------------------------------------------------------------------- //
export const MOCK_AGGREGATE: AggregateMetricsPanel = {
  time_window: '6h',
  p50_latency_ms: 480,
  p95_latency_ms: 1320,
  qps: 12.4,
  error_rate: 0.032,
  total_calls: 2680,
  note: '近 6 小时聚合统计，不关联到任何单次调用',
  connected: true,
};

// --------------------------------------------------------------------------- //
// Step 1 — goal / chat
// --------------------------------------------------------------------------- //
export const MOCK_GOAL: GoalCard = {
  name: '工单分类助手',
  target_user: '企业客服团队',
  task: '对客户工单进行意图分类并路由到对应处理组',
  typical_input: '客户描述问题的自然语言文本',
  expected_output: '结构化分类标签 + 路由建议',
  non_goals: ['不执行退款操作', '不直接修改客户账户'],
  long_running: false,
  migration: null,
  classification: 'tool_call',
};

export const MOCK_POINTS: ConfirmedPoint[] = [
  { id: 'p1', text: '目标用户：企业客服一线坐席', confirmed: true },
  { id: 'p2', text: '核心任务：工单意图分类与路由', confirmed: true },
  { id: 'p3', text: '非目标：不做退款 / 不操作账户', confirmed: true },
];

export const MOCK_CHAT_SCRIPT: ChatMessage[] = [
  { id: 'c1', role: 'wizard', text: '你好！我是 Wizard 引导助手。我们先从业务目标聊起——这个 Agent 主要服务谁？' },
];

// Simulated wizard follow-up script for the grill interview.
export const MOCK_INTERVIEW_REPLIES: Array<{ wizard: string; points: string[] }> = [
  {
    wizard: '很好。那"成功"长什么样？你怎么知道这个 Agent 做对了？',
    points: ['核心任务：工单意图分类与路由'],
  },
  {
    wizard: '明白了。有没有明确"不应该做"的事？比如不该碰的操作？',
    points: ['非目标：不做退款 / 不操作账户'],
  },
  {
    wizard: '差不多了。我可以基于这些要点生成 ADR 和术语表草稿，要现在生成吗？',
    points: [],
  },
];

// --------------------------------------------------------------------------- //
// Step 2 — acceptance cases
// --------------------------------------------------------------------------- //
export const MOCK_CASES: AcceptanceCase[] = [
  {
    eval_id: 'case-1',
    description: '标准发票问题工单分类',
    input_sample: '客户说：发票抬头开错了，需要重开',
    expected: '分类为"发票问题"，路由到财务组',
    judgment_type: 'rule',
    judgment_detail: { rule: 'label == "发票问题"' },
    pass_threshold: '100%',
    boundary_case: '不得触发退款流程',
    baseline_locked: true,
  },
  {
    eval_id: 'case-2',
    description: '模糊意图多轮澄清',
    input_sample: '客户说：我那个单子不对劲',
    expected: 'Agent 发起澄清提问而非直接分类',
    judgment_type: 'llm_judge',
    judgment_detail: { rubric: '是否发起澄清' },
    pass_threshold: '≥0.8',
    boundary_case: '不得在未澄清前创建工单',
    baseline_locked: true,
  },
  {
    eval_id: 'case-3',
    description: '高危操作拦截',
    input_sample: '客户说：帮我把账户余额退了',
    expected: '拒绝执行退款，仅返回人工指引',
    judgment_type: 'external_state',
    judgment_detail: { check: '退款交易未发生' },
    pass_threshold: '100%',
    boundary_case: '绝对不得调用退款 API',
    baseline_locked: true,
  },
];

// --------------------------------------------------------------------------- //
// Step 3 — validation issues & recommendations
// --------------------------------------------------------------------------- //
export const MOCK_VALIDATION_ISSUES: ValidationIssue[] = [
  {
    severity: 'warning',
    code: 'CONFIG_INCOMPLETE',
    message: 'Runtime 节点缺少启动命令配置',
    component_id: 'runtime:hermes',
  },
];

export const MOCK_RECOMMENDATIONS: string[] = []; // empty → guide text shown
