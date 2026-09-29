import type { ComponentDef, NodeKind } from '@/types';

export type { ComponentDef };

/**
 * Component card library grouped by 00-directory.md chapters.
 * Prerequisites / permissions / config schemas are design-time metadata;
 * they point to the corresponding Skill docs (no fabricated content).
 */
export const COMPONENT_GROUPS: ComponentDef['group'][] = [
  'Runtime',
  '沙箱 Sandbox',
  'Skills',
  'A2A Registry',
  '会话与记忆 Session&Memory',
  '知识库 KnowledgeBase',
  '网关 Gateway',
  'MCP 服务与工具集',
  '身份与权限 Identity',
  '安全围栏 Guardrails',
  '观测 Observability',
  '评测 Evaluation',
  '模型服务',
  '函数服务',
];

export const COMPONENT_CATALOG: ComponentDef[] = [
  // Runtime
  {
    kind: 'runtime',
    label: 'Runtime 运行实例',
    purpose: '托管 Agent 代码的运行实例，/invoke 调用入口',
    prerequisites: ['选择框架落点（veADK / Codex / 自定义 / ADK workflow）'],
    permissions: ['出站访问火山资源'],
    group: 'Runtime',
    configSchema: [
      { key: 'framework', label: 'Agent 框架', type: 'select', required: true, options: ['veADK', 'Codex', '自定义', 'ADK workflow'] },
      { key: 'port', label: '监听端口', type: 'number', required: true, defaultValue: '8000' },
      { key: 'entry', label: '启动命令', type: 'text', required: true, placeholder: 'e.g. python -m myagent' },
    ],
  },
  {
    kind: 'agent',
    label: '业务 Agent',
    purpose: '被设计的目标 Agent / 子 Agent',
    prerequisites: ['已定义业务目标'],
    permissions: [],
    group: 'Runtime',
    configSchema: [
      { key: 'agent_name', label: 'Agent 名称', type: 'text', required: true, placeholder: 'e.g. ticket-classifier' },
      { key: 'description', label: '职责描述', type: 'textarea', required: false },
    ],
  },
  // 沙箱
  {
    kind: 'sandbox',
    label: '沙箱 Sandbox (工具)',
    purpose: '代码 / 浏览器沙箱工具执行环境',
    prerequisites: ['需先创建沙箱资源'],
    permissions: ['容器网络出站'],
    group: '沙箱 Sandbox',
    configSchema: [
      { key: 'sandbox_type', label: '沙箱类型', type: 'select', required: true, options: ['code', 'browser'] },
      { key: 'image', label: '镜像', type: 'text', required: false },
    ],
  },
  // Skills
  {
    kind: 'skill',
    label: 'Skill 技能单元',
    purpose: '可复用技能单元（如 grill-with-docs）',
    prerequisites: ['对应 Skill 已安装'],
    permissions: [],
    group: 'Skills',
    configSchema: [
      { key: 'skill_name', label: 'Skill 名称', type: 'text', required: true, placeholder: 'e.g. grill-with-docs' },
      { key: 'auto_invoke', label: '允许隐式调用', type: 'select', required: false, options: ['false', 'true'] },
    ],
  },
  // A2A
  {
    kind: 'a2a',
    label: 'A2A Registry',
    purpose: '跨 Agent 注册 / 发现',
    prerequisites: [],
    permissions: ['A2A 网络可达'],
    group: 'A2A Registry',
    configSchema: [
      { key: 'registry_url', label: 'Registry 地址', type: 'text', required: true },
    ],
  },
  // Memory
  {
    kind: 'memory',
    label: '记忆库 Memory / Session',
    purpose: '长期记忆 + 会话状态',
    prerequisites: [],
    permissions: [],
    group: '会话与记忆 Session&Memory',
    configSchema: [
      { key: 'memory_backend', label: '记忆后端', type: 'select', required: true, options: ['builtin', 'redis', 'vikingdb'] },
    ],
  },
  // KnowledgeBase
  {
    kind: 'knowledge_base',
    label: '知识库 VikingDB RAG',
    purpose: '语义检索切片（RAG）',
    prerequisites: ['需先创建知识库资源'],
    permissions: ['私网域名访问'],
    group: '知识库 KnowledgeBase',
    configSchema: [
      { key: 'kb_id', label: '知识库资源 ID', type: 'text', required: true, placeholder: 'e.g. kb-xxxxxxxx' },
      { key: 'top_k', label: '召回条数', type: 'number', required: false, defaultValue: '5' },
    ],
  },
  // Gateway
  {
    kind: 'gateway',
    label: '网关 Gateway',
    purpose: '统一入口、MCP 请求计数',
    prerequisites: [],
    permissions: ['网关公网/私网入口'],
    group: '网关 Gateway',
    configSchema: [
      { key: 'gateway_mode', label: '网关模式', type: 'select', required: true, options: ['mcp', 'rest'] },
    ],
  },
  // MCP
  {
    kind: 'mcp',
    label: 'MCP 服务 / 工具集',
    purpose: '经网关接入的外部工具能力',
    prerequisites: ['MCP 后端服务已部署'],
    permissions: ['出站访问 MCP 服务', '入站认证配置'],
    group: 'MCP 服务与工具集',
    configSchema: [
      { key: 'mcp_endpoint', label: 'MCP 服务地址', type: 'text', required: true },
      { key: 'auth_mode', label: '入站认证', type: 'select', required: false, options: ['none', 'KeyAuth', 'CustomJwt'] },
    ],
  },
  // Identity
  {
    kind: 'identity',
    label: '身份与权限 Identity/IAM',
    purpose: '入站 / 出站授权',
    prerequisites: [],
    permissions: ['IAM 角色绑定'],
    group: '身份与权限 Identity',
    configSchema: [
      { key: 'iam_role', label: 'IAM 角色', type: 'text', required: true },
    ],
  },
  // Guardrails
  {
    kind: 'guardrails',
    label: '安全围栏 Guardrails',
    purpose: '内容安全 / 攻击拦截',
    prerequisites: [],
    permissions: [],
    group: '安全围栏 Guardrails',
    configSchema: [
      { key: 'policy', label: '围栏策略', type: 'textarea', required: false },
    ],
  },
  // Observability
  {
    kind: 'observability',
    label: '观测 Observability (APMPlus/TLS)',
    purpose: '指标 / 链路 / 日志采集点',
    prerequisites: ['观测开启后需重新发布生效'],
    permissions: ['日志投递至 apmplus-server-log'],
    group: '观测 Observability',
    configSchema: [
      { key: 'trace_content', label: '内容采集开关', type: 'select', required: false, options: ['true', 'false'] },
    ],
  },
  // Evaluation (meta — not a runtime node, listed for completeness)
  {
    kind: 'function',
    label: '评测 Evaluation',
    purpose: '评测集 / 评估器 / 评测实验',
    prerequisites: ['评测服务已连接'],
    permissions: [],
    group: '评测 Evaluation',
    configSchema: [],
  },
  // Model
  {
    kind: 'model',
    label: '模型服务 Model Service',
    purpose: '推理、Token 消耗',
    prerequisites: ['模型服务已开通'],
    permissions: ['模型推理 API 出站'],
    group: '模型服务',
    configSchema: [
      { key: 'model_name', label: '模型', type: 'select', required: true, options: ['doubao-pro-32k', 'doubao-pro-128k', 'doubao-lite-4k'] },
      { key: 'temperature', label: 'Temperature', type: 'number', required: false, defaultValue: '0.7' },
    ],
  },
  // Function
  {
    kind: 'function',
    label: '函数服务 Function',
    purpose: '轻量函数计算',
    prerequisites: [],
    permissions: ['函数服务调用权限'],
    group: '函数服务',
    configSchema: [
      { key: 'func_name', label: '函数名', type: 'text', required: true },
    ],
  },
];

/** Wizard internal nodes (marked with "内部" badge). */
export const WIZARD_INTERNAL_KINDS: NodeKind[] = ['wizard_core', 'self_evolution'];
