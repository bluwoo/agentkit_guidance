import type { Topology } from '@/types';

export const DEFAULT_TOPOLOGY: Topology = {
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
      label: '客服分流 Agent',
      config: { agent_name: 'support-triage-agent', description: '对企业客服工单进行风险评估与分流' },
      skill_ref: null,
      x: 400,
      y: 180,
    },
    {
      component_id: 'model:doubao',
      kind: 'model',
      label: 'Doubao Pro 32k',
      config: { model_name: 'doubao-pro-32k', temperature: 0 },
      skill_ref: null,
      x: 180,
      y: 320,
    },
    {
      component_id: 'guardrails:safe',
      kind: 'guardrails',
      label: '安全围栏 Guardrails',
      config: { policy: '拦截退款/投诉类高危操作并升级人工' },
      skill_ref: null,
      x: 400,
      y: 320,
    },
    {
      component_id: 'obs:apm',
      kind: 'observability',
      label: 'APMPlus 观测',
      config: { trace_content: 'true' },
      skill_ref: null,
      x: 620,
      y: 320,
    },
  ],
  edges: [
    { edge_id: 'e1', source: 'runtime:hermes', target: 'agent:target', type: 'stream' },
    { edge_id: 'e2', source: 'agent:target', target: 'model:doubao', type: 'sync' },
    { edge_id: 'e3', source: 'agent:target', target: 'guardrails:safe', type: 'config' },
    { edge_id: 'e4', source: 'runtime:hermes', target: 'obs:apm', type: 'data_flow' },
  ],
};
