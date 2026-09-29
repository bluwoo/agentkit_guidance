# AgentKit Wizard 后端

薄 FastAPI shim（讲 AgentKit Runtime **层 1** 协议）+ Hermes 原生主循环桥 +
四步引导业务路由 + grill-with-docs 兼容调度 + 草稿持久化 + 14 组件目录。

## 入口

- **ASGI app**: `server/wizard/main.py` 的 `app`（`create_app()` 工厂）
- 启动：
  ```bash
  uvicorn server.wizard.main:app --host 0.0.0.0 --port 8000
  ```
  （项目根在 `PYTHONPATH` 上；也可直接 `python -m server.wizard.main`）

## 环境变量

| 变量 | 默认 | 说明 |
|---|---|---|
| `RUNTIME_API_KEY_HEADER` | `X-Api-Key` | 入站 KeyAuth 头名 |
| `RUNTIME_API_KEY` | 空 | 配置后启用 KeyAuth；**留空=本地 dev 放行（打 warn）** |
| `WIZARD_LLM_BASE_URL` | 空 | 配置后启用 `RealHermesBridge` |
| `WIZARD_LLM_API_KEY` | 空 | |
| `WIZARD_LLM_MODEL` | 空 | |
| `WIZARD_LLM_PROVIDER` | 空 | 传给 `AIAgent(provider=...)` |
| `WIZARD_LLM_API_MODE` | 空 | 传给 `AIAgent(api_mode=...)` |
| `WIZARD_DATA_DIR` | `./wizard_data` | SQLite 草稿库根目录 |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | 空 | 配置后 OTLP 导出；否则 console/no-op |
| `WIZARD_VERSION` / `HERMES_VERSION` | `0.1.0` / `0.21.3` | 打在每个 span 上 |
| `WIZARD_RUNTIME_ENDPOINTS` | 空 | JSON `{runtime_id: "https://host"}` 白名单（runtime 代理 SSRF 防护） |

打印启动配置时，任何含 `KEY/SECRET/TOKEN/...` 的值都会被 mask。

## Hermes Real / Mock 切换

- **Mock（默认，无凭据）**：`MockHermesBridge` 返回确定性引导式回复，按
  `step1/step2/step3/step4/grill/adr/glossary` 关键词路由不同话术，可离线完整冒烟。
- **Real**：设置 `WIZARD_LLM_BASE_URL` + `WIZARD_LLM_MODEL`（可选 `WIZARD_LLM_API_KEY`/
  `PROVIDER`/`API_MODE`）。`RealHermesBridge` 懒加载 `vendor/hermes-agent` 到 `sys.path`，
  实例化 `run_agent.AIAgent(...)`，调 `agent.conversation_loop.run_conversation(...)`，
  把 `stream_callback` 桥到 SSE。
- 测试用 `server.wizard.shim.hermes_bridge.set_bridge(fake)` 注入假桥。

## 路由清单

### 层 1 Runtime 协议（`server/wizard/shim/runtime_protocol.py`）
- `GET  /ping` `/health` `/readiness` `/liveness`（无鉴权，给探活/LB）
- `POST /invoke`（层 1 调用入口；KeyAuth；-> HermesBridge.turn）
- 层 2 可选：`POST /run`、`POST /run_sse`（SSE）、`GET/POST /sessions`
- 不实现 `/web/harness-sidecar/status`（veADK harness_extension 层，Hermes 主路径不用）

### 业务路由（挂 `/api/wizard`）
- `POST /biz-goal/chat`（SSE grill 访谈）、`/points/confirm`、`/adr`、
  `GET/PUT /biz-goal/glossary`、`/generate`、`GET/PUT /biz-goal`
- `GET/PUT /evaluation/cases`、`/recommend`、`GET /evaluation/datasets`（未连接 `{connected:false}`）、`/import-cases`
- `GET /components`（14 组件卡片）
- `POST /architecture/recommend`（无信息返回空数组，不编造）、`GET/PUT /architecture`、`/validate`
- `POST /runtime/invoke`（白名单 + SSRF 防护，回传 `trace_id`）
- `GET /observability/trace` `/metrics/aggregate` `/logs`（薄转发，缺模块返回 `not_configured`）
- `GET/POST /evolution/proposals`、`POST /evolution/proposals/{id}/approve|reject`（幂等 + 审计）

## 目录结构

```
server/wizard/
  main.py            FastAPI app factory + 异常处理 + lifespan
  config.py          环境变量配置（mask 密钥）
  schemas.py         （已定稿，勿改）GoalCard/Topology/Proposal/...
  shim/              runtime_protocol / hermes_bridge / otel_middleware
  api/               业务路由（biz-goal/evaluation/components/architecture/runtime-proxy/observability/evolution）
  grill/             adapter.py 状态机 + prompts/（grilling/domain-modeling 素材，含 NOTICES 出处）
  store/             draft_store.py（SQLite + 防穿越）
  components/        catalog.py（14 组件静态卡片）
```

## grill-with-docs 适配（"调 Skill 工具两次" 的翻译）

`grill-with-docs/SKILL.md` 要求宿主"调 Skill tool 两次（grilling + domain-modeling）"。
Hermes 没有该工具，`grill/adapter.py` 把它翻译为同一对话轮内的两个子流程：
**先 grilling**（design tree frontier，一轮编号 `Q1/Q2...` 带推荐答案，答后重算 frontier）
**再 domain-modeling**（维护 CONTEXT.md 术语表；ADR 仅在三条件满足时提议）。
入口显式触发（`disable-model-invocation`），结构化事件 `question/point/adr/glossary` 走 SSE。
