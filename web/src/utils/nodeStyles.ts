import type { NodeKind } from '@/types';

/**
 * Visual encoding per 02 §1: shape / color / icon semantics.
 * Colors are design tokens; shapes are approximated via border-radius / border-style
 * because React Flow custom nodes use rectangles. We encode kind via color + label.
 */
export interface NodeVisual {
  color: string;       // border / accent
  background: string;
  shapeHint: string;   // text label for the kind
  internal: boolean;  // Wizard internal node (badged)
}

const KIND_MAP: Record<NodeKind, NodeVisual> = {
  agent: { color: '#165dff', background: '#e8f3ff', shapeHint: 'Agent', internal: false },
  runtime: { color: '#722ed1', background: '#f5e8ff', shapeHint: 'Runtime', internal: false },
  skill: { color: '#0fc6c2', background: '#e8fffb', shapeHint: 'Skill', internal: false },
  mcp: { color: '#722ed1', background: '#f5e8ff', shapeHint: 'MCP', internal: false },
  gateway: { color: '#86909c', background: '#f2f3f5', shapeHint: 'Gateway', internal: false },
  knowledge_base: { color: '#00b42a', background: '#e8ffea', shapeHint: '知识库', internal: false },
  memory: { color: '#ff7d00', background: '#fff7e8', shapeHint: '记忆', internal: false },
  sandbox: { color: '#0fc6c2', background: '#e8fffb', shapeHint: '沙箱', internal: false },
  model: { color: '#f5319d', background: '#ffece8', shapeHint: '模型', internal: false },
  function: { color: '#4e5969', background: '#f2f3f5', shapeHint: '函数', internal: false },
  identity: { color: '#165dff', background: '#e8f3ff', shapeHint: '身份', internal: false },
  guardrails: { color: '#f53f3f', background: '#ffece8', shapeHint: '围栏', internal: false },
  a2a: { color: '#86909c', background: '#f2f3f5', shapeHint: 'A2A', internal: false },
  observability: { color: '#ffb400', background: '#fff7e8', shapeHint: '观测', internal: false },
  wizard_core: { color: '#722ed1', background: '#f5e8ff', shapeHint: 'Wizard 底座', internal: true },
  self_evolution: { color: '#722ed1', background: '#f5e8ff', shapeHint: '自进化', internal: true },
  observed_unmapped: { color: '#f53f3f', background: '#ffece8', shapeHint: '未映射', internal: false },
};

export function getNodeVisual(kind: NodeKind): NodeVisual {
  return KIND_MAP[kind] ?? KIND_MAP.function;
}

/** Wizard base node annotation text (02 §1.1). */
export const WIZARD_BASE_ANNOTATION =
  'Hermes Agent (AIAgent.run_conversation) + FastAPI Shim (Runtime 协议)';

export const SELF_EVOLUTION_ANNOTATION = '后台审查 Fork → 提案队列 → 人工审批 → 生效';
