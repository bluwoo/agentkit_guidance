# AgentKit Agent 开发 Wizard — 前端

React 18 + TypeScript + Vite + Arco Design + React Flow + Zustand 的引导式 Agent 开发 Wizard 前端。
设计规格见 `../frontend/01-ui-spec.md` ~ `04-tech-stack.md`，数据契约对齐 `../server/wizard/schemas.py`。

## 快速开始

```bash
cd web
npm install        # 安装依赖
npm run dev        # 启动开发服务器 http://localhost:5173
```

## 常用命令

| 命令 | 说明 |
|---|---|
| `npm run dev` | 启动 Vite 开发服务器（默认 5173 端口） |
| `npm run build` | TypeScript 类型检查 + 生产构建到 `dist/` |
| `npm run preview` | 预览生产构建产物 |
| `npm run lint` | ESLint 检查（零 warning 才算通过） |
| `npm run typecheck` | 仅运行 `tsc --noEmit` |

## Mock 模式 vs 对接后端

### Mock 模式（默认）

`.env` 中 `VITE_USE_MOCK=1` 时，所有 API 调用走本地 fixture 数据，无需后端即可完整演示四步流程：

- 一条样例 `TraceOverlay` 故意覆盖绿（成功）/红（失败）/灰（设计但无 span）/observed-unmapped 四种分支
- 聚合面板（P50/P95/QPS）独立展示，不回写单次 trace
- 评测集下拉显示「当前未连接评测服务」占位，不造假数据

### 对接真实后端

1. 复制 `.env.example` 为 `.env`：
   ```bash
   VITE_API_BASE_URL=          # 留空 = 同源，Vite dev 代理 /api 到 :8000
   VITE_USE_MOCK=              # 设为空或 0 关闭 mock
   ```
2. 修改 `vite.config.ts` 中的 `server.proxy['/api'].target` 指向你的 FastAPI shim（默认 `http://localhost:8000`）。
3. 后端需实现 `frontend/03-api-integration.md` 中定义的 `/api/wizard/*` 路由。

## 路由

| URL | 步骤 |
|---|---|
| `/wizard/biz-goal` | ① 业务目标 |
| `/wizard/evaluation` | ② 验收与评测 |
| `/wizard/architecture` | ③ 架构设计 |
| `/wizard/diagram-test` | ④ 架构图 + 测试 |

## 组件清单

```
src/
├── main.tsx                          # 入口
├── App.tsx                           # 路由 + 三栏布局壳
├── types/index.ts                    # TS 类型（对齐 schemas.py）
├── api/
│   ├── client.ts                     # fetch + SSE 客户端，mock/real 双实现
│   └── mock.ts                       # 本地 fixture（含样例 TraceOverlay）
├── store/wizardStore.ts              # Zustand 全局状态（含 S0-S4 状态机）
├── data/componentCatalog.ts          # 14 类组件卡片库元数据
├── utils/nodeStyles.ts               # 节点视觉编码（02 规格）
├── components/
│   ├── Stepper.tsx                   # 顶部 4 步步骤条
│   ├── layout/
│   │   ├── ContextPanel.tsx          # 左栏 Context 摘要
│   │   └── ArtifactPanel.tsx         # 右栏 Artifact 预览
│   ├── graph/CustomNode.tsx         # React Flow 自定义节点
│   └── steps/
│       ├── Step1BizGoal.tsx         # ① 业务目标（grill 访谈 + 快速表单）
│       ├── Step2Evaluation.tsx      # ② 验收用例表 + 评测集占位
│       ├── Step3Architecture.tsx   # ③ 组件库 + React Flow 画布 + 校验
│       └── Step4DiagramTest.tsx     # ④ 拓扑 + 测试面板 + Trace 覆盖层 + 聚合面板
└── styles/global.css                # 全局样式
```

## 安全约束

- 所有外部 trace 内容渲染前经 React 自动转义，不使用 `dangerouslySetInnerHTML`。
- 运行时鉴权 KeyAuth Header 仅存内存（`api/client.ts` 中 `runtimeCredentials`），不落 localStorage。
- 资源 ID 经白名单正则校验（`isValidResourceId`）后才拼入 URL。
- 代码与 `.env.example` 中不含任何密钥。
