# 技术选型建议（04）

> 文档性质：**选型建议与理由**，不做实现。当前所有对接均为设计状态；**Wizard 后端为 Hermes 原生主循环 + 薄 FastAPI shim，不是 veADK Agent**（据 `docs/hermes-veadk/05-hermes-as-base-verification.md`），本阶段未执行云联调，火山引擎凭据可用性尚未核验。

---

## 1. 前端框架

**建议：React 18+ + TypeScript + Vite。**

理由：
- 本前端核心是**可交互拓扑图 + 流式对话 + 多面板状态**，React 的组件化与生态最成熟。
- 图可视化、SSE 流式、拖拽等关键能力在 React 生态有现成库。
- 若团队现有技术栈为 Vue，可对应 Vue 3 + Pinia + Vite，架构图库换 AntV X6（见 §2）。

UI 组件库：建议 **Ant Design / Arco Design**（企业后台风格，组件卡片、表单、Stepper、抽屉、表格齐全，契合 01 的三栏工作区与验收用例表）。

---

## 2. 图可视化库（架构图关键选型）

**建议：AntV X6 或 React Flow（二选一）。**

| 维度 | React Flow (reactflow) | AntV X6 |
|---|---|---|
| 定位 | React 生态轻量节点编辑器 | 蚂蚁企业级图编辑，能力全 |
| 拖拽连线/缩放/框选 | 开箱即用 | 开箱即用 |
| 自定义节点形状/颜色/边类型 | 容易 | 非常灵活（适合 §1 十四类节点视觉编码） |
| 覆盖层着色/边徽章 | 易做 | 易做 |
| 与 React 集成 | 原生 | 需适配 |

**推荐优先级**：若前端选 React 且追求开发效率 → **React Flow**；若需要更强的企业级图定制（分层布局算法、复杂边徽章、大屏）→ **AntV X6**。
布局算法用库自带 dagre（分层/DAG）+ 力导向（d3-force），与 `02` §5 的"分层默认 + 力导向辅助 + 手动覆盖"对应。

---

## 3. 状态管理

**建议：Zustand / Redux Toolkit（按团队偏好）。**

理由：
- 跨步骤共享"业务目标 / 验收用例 / 拓扑草稿"全局状态，需要单一数据源。
- 配合"草稿持久化到后端"（`03` §2），状态层负责本地状态与后端同步的一致性。
- 测试流程的 5 态状态机（01 §6）建议用显式 finite state（可用 XState 或自实现 reducer），避免 UI 状态散落。

---

## 4. 与 Wizard 后端的通信方式

Wizard 后端 = Hermes + 薄 FastAPI shim（见 `03` §2）。按数据特性分通道：

| 通道 | 技术 | 用途 |
|---|---|---|
| 普通 CRUD / 草稿 | **REST（JSON）** | 业务目标、用例、拓扑、校验（`03` A/D） |
| 引导式对话、测试响应 | **SSE（Server-Sent Events）** | grill-with-docs 流式追问（shim `/run_sse` 语义）、目标 Runtime `/run_sse` 流式测试响应 |
| trace/日志就绪通知（可选演进） | **WebSocket** | 当前先用 REST 有限轮询（`03` §4.2）；后续若需实时可升级 WS |

理由：SSE 天然适配"一问一答流式"与"逐 token 渲染"，与 Runtime 协议的 `/run_sse` 端点语义对齐；观测数据拉取是低频按需，REST 轮询足够，避免常驻连接成本。

---

## 5. 部署方式

**建议：静态托管为主，嵌入 AgentKit Studio 为目标形态。**

- **现阶段**：前端为纯静态资源（Vite build 产物），CDN/对象存储托管，通过反向代理把 `/api/*` 与 Runtime 协议端点（`/run`/`/run_sse`/`/invoke`/`/ping`）转发到 Wizard 后端——即 **Hermes 进程 + 薄 FastAPI shim**（容器形态，监听约定端口，讲 Runtime HTTP 协议，见 `03` §1/§2）。
- **目标形态**：作为 **AgentKit Studio 的一个内嵌向导模块**（iframe / 微前端 qiankun），复用 Studio 登录态与云资源上下文。
- 不建议把凭证直连云资源；所有云调用经 Wizard 后端代理签名（`03` §6）。
- 备选适配路径（05 核验 §7）：若直接复用 veADK 已实现好的 Runtime 协议更省事，也可把 Hermes 包成"类 `BaseAgent`" wrapper（方案 B）；起步推荐方案 A（Hermes 原生进程 + 自写薄 shim），二者对前端透明，前端只面对 `/api/*` 与 Runtime 协议端点。

---

## 6. 选型汇总

| 层 | 建议 | 备选 |
|---|---|---|
| 框架 | React + TS + Vite | Vue 3 + Vite |
| UI 库 | Ant Design / Arco | — |
| 图可视化 | React Flow | AntV X6 |
| 状态 | Zustand / RTK | XState（状态机） |
| 通信 | REST + SSE | WebSocket（trace 推送演进） |
| 部署 | 静态托管 → 嵌入 Studio | 独立部署 |

---

## 7. 证据引用

- Wizard 后端形态（Hermes `AIAgent.run_conversation` + 薄 FastAPI shim）、Runtime 协议端点、方案 A/B 适配路径：`docs/hermes-veadk/05-hermes-as-base-verification.md`（§1、§3c、§7）。
- 组件/接口边界与目标 Runtime `/invoke`、`/run_sse`：`docs/volcengine-official/shard1-results.md`、`shard2-results.md`、`00-directory.md`。
- 流式与观测（已核验 10 字段 + trace_id）：`docs/volcengine-official/shard4-results.md`、`docs/lark-supplements/doc07.md`。
- 评测：`15-evaluation.md`。

---

## 修订记录

| 日期 | 版本 | 修订内容 |
|---|---|---|
| 2026-09-18 | v1.1 | 依据 Hermes 核验文档纠正：① 头部明确"Wizard 后端为 Hermes 原生主循环 + 薄 FastAPI shim，不是 veADK Agent"，并标注本阶段未执行云联调、火山引擎凭据可用性尚未核验；② §4 标题与通道表改为"Wizard 后端"，SSE 用途对齐 shim `/run_sse` 与目标 Runtime `/run_sse`；③ §5 部署把反向代理目标从"veADK Agent"改为"Hermes 进程 + 薄 FastAPI shim（容器形态）"，并补充方案 A/B 对前端透明的说明；④ §7 证据引用更新。 |
| （初始版） | v1.0 | 首版技术选型建议。 |


---

## 措辞与契约修正记录（2026-09-18）

- 头部与 v1.1 修订记录中「当前无云凭据、未联调/无云凭据未联调」改为「本阶段未执行云联调，火山引擎凭据可用性尚未核验」。
