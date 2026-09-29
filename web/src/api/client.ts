/**
 * API client: fetch + SSE.
 * - baseURL from import.meta.env.VITE_API_BASE_URL (empty = same-origin /api).
 * - When VITE_USE_MOCK=1, all calls are served from local fixtures.
 * - SSE uses fetch ReadableStream parsing (EventSource cannot set headers).
 *
 * Security: credentials / KeyAuth headers are kept in-memory only, never
 * persisted to localStorage. Resource IDs are validated against a whitelist
 * before being sent to the backend.
 */
import type {
  AcceptanceCase,
  AggregateMetricsPanel,
  ConfirmedPoint,
  EvaluationRun,
  GoalCard,
  RuntimeInvokeResponse,
  TraceOverlay,
  Topology,
  ValidationIssue,
} from '@/types';
import {
  MOCK_AGGREGATE,
  MOCK_CASES,
  MOCK_CHAT_SCRIPT,
  MOCK_GOAL,
  MOCK_INTERVIEW_REPLIES,
  MOCK_POINTS,
  MOCK_TOPOLOGY,
  MOCK_TRACE_EMPTY,
  MOCK_TRACE_OVERLAY,
  MOCK_VALIDATION_ISSUES,
} from './mock';

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? '';
export const USE_MOCK = (import.meta.env.VITE_USE_MOCK as string | undefined) === '1';

// --------------------------------------------------------------------------- //
// In-memory only credential store (never localStorage)
// --------------------------------------------------------------------------- //
const runtimeCredentials: Record<string, string> = {};
export function setRuntimeCredential(runtimeId: string, apiKey: string) {
  runtimeCredentials[runtimeId] = apiKey;
}
export function getRuntimeCredential(runtimeId: string): string | undefined {
  return runtimeCredentials[runtimeId];
}
export function clearRuntimeCredential(runtimeId: string) {
  delete runtimeCredentials[runtimeId];
}

/** Whitelist validation for resource IDs (prevent injection via path segments). */
const RESOURCE_ID_RE = /^[a-zA-Z0-9_\-.:]{1,128}$/;
export function isValidResourceId(id: string): boolean {
  return RESOURCE_ID_RE.test(id);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`API ${path} failed: ${res.status} ${text}`);
  }
  return res.json() as Promise<T>;
}

// --------------------------------------------------------------------------- //
// SSE stream reader (fetch ReadableStream)
// --------------------------------------------------------------------------- //
export interface SSEChunk {
  event: string;
  data: string;
}

export async function* sseStream(
  path: string,
  body: unknown,
): AsyncGenerator<SSEChunk, void, void> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok || !res.body) {
    throw new Error(`SSE ${path} failed: ${res.status}`);
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx: number;
    while ((idx = buffer.indexOf('\n\n')) !== -1) {
      const raw = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const lines = raw.split('\n');
      let event = 'message';
      let data = '';
      for (const line of lines) {
        if (line.startsWith('event:')) event = line.slice(6).trim();
        else if (line.startsWith('data:')) data += line.slice(5).trim();
      }
      if (data) yield { event, data };
    }
  }
}

// --------------------------------------------------------------------------- //
// API surface
// --------------------------------------------------------------------------- //
export interface WizardApi {
  getGoal(): Promise<GoalCard>;
  saveGoal(goal: GoalCard): Promise<void>;
  getPoints(): Promise<ConfirmedPoint[]>;
  confirmPoint(id: string, text: string, confirmed: boolean): Promise<void>;
  deletePoint(id: string): Promise<void>;
  chatStream(
    sessionId: string,
    message: string,
    onDelta: (text: string) => void,
  ): Promise<{ points: string[] }>;
  generateQuickGoal(form: {
    name: string;
    description: string;
    target_user: string;
    language: string;
    external_systems: string[];
  }): Promise<GoalCard>;
  generateADR(): Promise<string>;
  generateGlossary(): Promise<string>;

  getCases(): Promise<AcceptanceCase[]>;
  saveCases(cases: AcceptanceCase[]): Promise<void>;
  runEvaluation(runtimeId: string, cases: AcceptanceCase[]): Promise<EvaluationRun>;
  getDatasets(): Promise<{ connected: boolean }>;

  getTopology(): Promise<Topology>;
  saveTopology(topology: Topology): Promise<void>;
  validateTopology(topology: Topology): Promise<ValidationIssue[]>;
  recommendComponents(): Promise<{ component_ids: string[] }>;

  invokeRuntime(req: {
    runtime_id: string;
    input: string;
    user_id: string;
    session_id: string;
    stream: boolean;
  }): Promise<RuntimeInvokeResponse>;
  invokeRuntimeStream(
    req: { runtime_id: string; input: string; user_id: string; session_id: string },
    onDelta: (text: string) => void,
  ): Promise<{ trace_id: string | null }>;

  getTrace(runtimeId: string, traceId: string): Promise<TraceOverlay>;
  getAggregate(runtimeId: string, timeWindow: string): Promise<AggregateMetricsPanel>;
}

// --------------------------------------------------------------------------- //
// Mock implementation (VITE_USE_MOCK=1)
// --------------------------------------------------------------------------- //
function delay(ms: number) {
  return new Promise((r) => setTimeout(r, ms));
}

let mockChatIndex = 0;

const mockApi: WizardApi = {
  async getGoal() {
    await delay(50);
    return { ...MOCK_GOAL };
  },
  async saveGoal(goal) {
    await delay(30);
    void goal;
  },
  async getPoints() {
    await delay(30);
    return MOCK_POINTS.map((p) => ({ ...p }));
  },
  async confirmPoint() {
    await delay(10);
  },
  async deletePoint() {
    await delay(10);
  },
  async chatStream(_sessionId, message, onDelta) {
    await delay(200);
    void message;
    const reply = MOCK_INTERVIEW_REPLIES[Math.min(mockChatIndex, MOCK_INTERVIEW_REPLIES.length - 1)];
    mockChatIndex += 1;
    // Simulate streaming tokens
    const words = reply.wizard.split('');
    for (const w of words) {
      await delay(24);
      onDelta(w);
    }
    return { points: reply.points };
  },
  async generateQuickGoal(form) {
    await delay(400);
    return {
      ...MOCK_GOAL,
      name: form.name || MOCK_GOAL.name,
      task: form.description || MOCK_GOAL.task,
      target_user: form.target_user || MOCK_GOAL.target_user,
    };
  },
  async generateADR() {
    await delay(300);
    return '# ADR 草稿\n\n## 上下文\n工单分类 Agent 需要在客服场景下快速路由工单。\n\n## 决策\n采用规则 + LLM 混合分类，高危操作走围栏拦截。\n\n## 后果\n分类准确率依赖评测集覆盖；退款类操作被显式排除。';
  },
  async generateGlossary() {
    await delay(300);
    return '| 术语 | 含义 |\n|---|---|\n| 工单 | 客户提交的一条问题记录 |\n| 路由 | 将工单分发到对应处理组 |\n| 围栏 | 拦截高危操作的安全策略 |';
  },
  async getCases() {
    await delay(30);
    return MOCK_CASES.map((c) => ({ ...c }));
  },
  async saveCases() {
    await delay(20);
  },
  async runEvaluation(runtimeId, cases) {
    await delay(80);
    return {
      run_id: 'mock-eval', runtime_id: runtimeId, trace_id: MOCK_TRACE_OVERLAY.trace_id,
      passed: cases.length, failed: 0,
      results: cases.map((item) => ({
        eval_id: item.eval_id, passed: true, judgment_type: item.judgment_type,
        actual_output: item.expected, evidence: { mock: true }, reason: 'mock evaluation',
      })),
    };
  },
  async getDatasets() {
    await delay(30);
    return { connected: false }; // not connected — show placeholder
  },
  async getTopology() {
    await delay(30);
    return {
      nodes: MOCK_TOPOLOGY.nodes.map((n) => ({ ...n, config: { ...n.config } })),
      edges: MOCK_TOPOLOGY.edges.map((e) => ({ ...e })),
    };
  },
  async saveTopology() {
    await delay(20);
  },
  async validateTopology(topology) {
    void topology;
    await delay(80);
    return MOCK_VALIDATION_ISSUES.map((i) => ({ ...i }));
  },
  async recommendComponents() {
    await delay(100);
    return { component_ids: [] }; // empty → guide text
  },
  async invokeRuntime(req) {
    await delay(800);
    void req;
    return {
      output: '分类结果：发票问题 / 路由：财务组。(mock) 注：工单 MCP 调用失败，已降级为人工指引。',
      trace_id: MOCK_TRACE_OVERLAY.trace_id,
      status_code: 200,
      error: null,
    };
  },
  async invokeRuntimeStream(req, onDelta) {
    void req;
    const text = '分类结果：发票问题 / 路由：财务组。工单 MCP 调用失败，已降级为人工指引。';
    for (const ch of text) {
      await delay(40);
      onDelta(ch);
    }
    return { trace_id: MOCK_TRACE_OVERLAY.trace_id };
  },
  async getTrace(_runtimeId, traceId) {
    void _runtimeId;
    await delay(200);
    // Simulate: a special trace id triggers the "no trace" S3 branch.
    if (traceId === 'trace-empty') {
      return { ...MOCK_TRACE_EMPTY };
    }
    return { ...MOCK_TRACE_OVERLAY };
  },
  async getAggregate(_runtimeId, _timeWindow) {
    void _runtimeId;
    void _timeWindow;
    await delay(120);
    return { ...MOCK_AGGREGATE };
  },
};

// --------------------------------------------------------------------------- //
// Real implementation (when not in mock mode)
// --------------------------------------------------------------------------- //
const realApi: WizardApi = {
  async getGoal() {
    return request<GoalCard>('/api/wizard/biz-goal');
  },
  async saveGoal(goal) {
    await request('/api/wizard/biz-goal', { method: 'PUT', body: JSON.stringify(goal) });
  },
  async getPoints() {
    return request<ConfirmedPoint[]>('/api/wizard/biz-goal/points');
  },
  async confirmPoint(id, text, confirmed) {
    await request('/api/wizard/biz-goal/points/confirm', {
      method: 'POST',
      body: JSON.stringify({ id, text, confirmed }),
    });
  },
  async deletePoint(id) {
    await request(`/api/wizard/biz-goal/points/${id}`, { method: 'DELETE' });
  },
  async chatStream(sessionId, message, onDelta) {
    const points: string[] = [];
    for await (const chunk of sseStream('/api/wizard/biz-goal/chat', { session_id: sessionId, message })) {
      let payload: Record<string, unknown> = {};
      try { payload = JSON.parse(chunk.data) as Record<string, unknown>; } catch { payload = { text: chunk.data }; }
      if (chunk.event === 'question') {
        onDelta(`${String(payload.qid ?? '')} · ${String(payload.title ?? '')}\n${String(payload.body ?? '')}\n建议：${String(payload.recommended ?? '')}`);
      } else if (chunk.event === 'point') {
        const text = String(payload.text ?? '');
        if (text) points.push(text);
      } else if (chunk.event === 'round') {
        onDelta(`进入第 ${String(payload.round ?? '')} 轮访谈`);
      } else if (chunk.event === 'done') {
        onDelta(String(payload.message ?? '访谈完成'));
      } else if (chunk.event === 'delta') {
        onDelta(String(payload.text ?? chunk.data));
      }
    }
    return { points };
  },
  async generateQuickGoal(form) {
    const result = await request<{ goal_card: GoalCard }>('/api/wizard/biz-goal/generate', {
      method: 'POST',
      body: JSON.stringify(form),
    });
    return result.goal_card;
  },
  async generateADR() {
    const r = await request<{ markdown: string }>('/api/wizard/biz-goal/adr', { method: 'POST' });
    return r.markdown;
  },
  async generateGlossary() {
    const r = await request<{ markdown: string }>('/api/wizard/biz-goal/glossary', { method: 'POST' });
    return r.markdown;
  },
  async getCases() {
    const result = await request<{ cases: AcceptanceCase[] }>('/api/wizard/evaluation/cases');
    return result.cases;
  },
  async saveCases(cases) {
    await request('/api/wizard/evaluation/cases', { method: 'PUT', body: JSON.stringify(cases) });
  },
  async runEvaluation(runtimeId, cases) {
    if (!isValidResourceId(runtimeId)) throw new Error('invalid runtime_id');
    return request<EvaluationRun>('/api/wizard/evaluation/run', {
      method: 'POST',
      body: JSON.stringify({ runtime_id: runtimeId, cases }),
    });
  },
  async getDatasets() {
    return request<{ connected: boolean }>('/api/wizard/evaluation/datasets');
  },
  async getTopology() {
    return request<Topology>('/api/wizard/architecture');
  },
  async saveTopology(topology) {
    await request('/api/wizard/architecture', { method: 'PUT', body: JSON.stringify(topology) });
  },
  async validateTopology(topology) {
    const result = await request<{ valid: boolean; issues: ValidationIssue[] }>('/api/wizard/architecture/validate', {
      method: 'POST', body: JSON.stringify(topology),
    });
    return result.issues;
  },
  async recommendComponents() {
    const result = await request<{ recommended: Array<{ component_id: string }> }>('/api/wizard/architecture/recommend', {
      method: 'POST',
      body: JSON.stringify({}),
    });
    return { component_ids: result.recommended.map((item) => item.component_id) };
  },
  async invokeRuntime(req) {
    if (!isValidResourceId(req.runtime_id)) {
      throw new Error('invalid runtime_id');
    }
    return request<RuntimeInvokeResponse>('/api/wizard/runtime/invoke', {
      method: 'POST',
      body: JSON.stringify(req),
    });
  },
  async invokeRuntimeStream(req, onDelta) {
    if (!isValidResourceId(req.runtime_id)) {
      throw new Error('invalid runtime_id');
    }
    let traceId: string | null = null;
    for await (const chunk of sseStream('/api/wizard/runtime/invoke', { ...req, stream: true })) {
      if (chunk.event === 'delta') onDelta(chunk.data);
      else if (chunk.event === 'trace_id') traceId = chunk.data;
    }
    return { trace_id: traceId };
  },
  async getTrace(runtimeId, traceId) {
    return request<TraceOverlay>(
      `/api/wizard/observability/trace?runtime_id=${encodeURIComponent(runtimeId)}&trace_id=${encodeURIComponent(traceId)}`,
    );
  },
  async getAggregate(runtimeId, timeWindow) {
    return request<AggregateMetricsPanel>(
      `/api/wizard/observability/metrics/aggregate?runtime_id=${encodeURIComponent(runtimeId)}&time_window=${encodeURIComponent(timeWindow)}`,
    );
  },
};

export const api: WizardApi = USE_MOCK ? mockApi : realApi;

export { MOCK_CHAT_SCRIPT };
