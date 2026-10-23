# AgentKit — Agent Onboarding & Engineering Guide

> 新 Agent 克隆本仓库后，**从本页最前面开始按顺序执行**。目标是让一个没有历史上下文的 Agent，
> 用仓库自带的 Skills 快速搭出可运行、可验证、可部署的 AgentKit 工程。

## 0. 首读顺序（First Run）

按顺序做，不要跳步：

1. **读 Skills 总入口**：[`skills/README.md`](skills/README.md)
2. 按任务需要读取对应组件 Skill（**不要一次通读全部 14 个 Skill**）：
   - 底座依次读：[`skills/veadk/SKILL.md`](skills/veadk/SKILL.md) →
     [`skills/agentkit-sdk/SKILL.md`](skills/agentkit-sdk/SKILL.md) →
     [`skills/references/runner-entrypoint.md`](skills/references/runner-entrypoint.md)
   - 需要部署时再读 [`skills/agentkit-runtime/SKILL.md`](skills/agentkit-runtime/SKILL.md)
3. 在独立 `<WORKSPACE>` 创建 `execution-journal.md`，持续记录：任务与验收标准、读过的 Skill、
   版本与实际命令、失败根因与复验、证据等级（L1–L4）、云资源与清理状态。
4. 完整协议见 [`AGENTKIT_AGENT_ONBOARDING.md`](AGENTKIT_AGENT_ONBOARDING.md)。

> 不要直接改 `skills/`；业务代码写进独立 `<WORKSPACE>`。只有确认 Skill 本身有误并完成事实核验后，
> 才单独修 Skill 并重跑整套回归。

## 1. 总原则与固定依赖顺序

- 优先用 AgentKit SDK、veADK、Google ADK 原生组件；先证明最小闭环，再按需加组件。
- 依赖顺序：

  ```
  veADK → AgentKit SDK → Google ADK Workflow（有编排时）
        → 按需挂 Memory / Knowledge Base / Sandbox / Skills / MCP / A2A
        → Identity + Guardrails → Runtime → Observability → Evaluation
  ```

- 约束：先开观测再做在线评测；会话标识不是身份授权；`backend="local"` 不等于无外部依赖；
  Runtime / MCP Gateway / A2A Registry 是不同组件不可互替；Google ADK 编排原语从
  `google.adk` / `google.adk.workflow` 导入。

## 2. 环境基线（除非用户要求升级并复验）

```text
Python 3.12 / veadk-python / agentkit-sdk-python / google-adk / mcp / AgentKit CLI
```

在独立工作区建虚拟环境，安装后立即核对 `python --version`、`pip show`、`agentkit --version`
与对应 `--help`；**不要凭 Skill 里的命令名猜 CLI 支持情况**。

## 3. 开发闭环（按阶段）

- **A 定义任务**：把每条需求写成可失败断言（缺 `user_id/session_id` → 400；同用户会话连续；
  异用户记忆隔离；未知 route → 默认路由；错误凭据 → 401；更新后可回滚）。
- **B 最小无云实现**：Agent/Runner 可构造；SDK 入口监听 `0.0.0.0:8000`；`/ping` 可用；
  `/invoke` 严格要求 `user_id`+`session_id`，缺任一返回 400，不回落默认值；覆盖正常/默认/错误/隔离路径。
- **C Workflow 先用无模型节点证明拓扑**：固定拓扑用 Graph，动态控制流用 Dynamic，主管委派用 Collaborative；
  覆盖每个 route、默认路由、Join、退出条件、并发上限、幂等与恢复不重复副作用。
- **D 加入真实模型**：B/C 全过后才引入；验收看业务语义而非仅 HTTP 200。
- **E 逐个接组件**：每次只加一个，按对应 Skill 做正例/负例/隔离/清理验收。
- **F 部署 Runtime**：镜像架构、监听 8000、健康检查、项目与地域回读、Ready、业务输出、错误路径、
  日志关联、发新版本、回滚、清理并回查 NotFound。
- **G 安全/观测/评测闭环**：Identity 四象限、Guardrails 高代码接入、完整 Trace/Span、
  独立 Dataset/Evaluator/Target，阈值不达标不发版。

## 4. 证据等级与安全硬规则

| 等级 | 含义 | 允许表述 |
|---|---|---|
| L1 静态 | import/签名/schema/编译 | 静态检查通过 |
| L2 离线真跑 | 本地真实节点/协议/测试 | 离线行为通过 |
| L3 真实依赖 | 真实模型/MCP/云组件数据面 | 真实依赖调用通过 |
| L4 云端 E2E | 创建→调用→观测/评测→清理 | 端到端通过 |

硬规则：项目/账号/资源/Endpoint/App/Workspace/Trace/用户信息一律用变量或占位符
（`<PROJECT_NAME>`、`<REGION>`、`<RUNTIME_ID>`、`<ENDPOINT>`、`<APP_ID>` 等）；
`.env` 不提交，仓库只保留 `.env.example`；日志只记凭据类别不记值；
云资源用唯一任务前缀写资源账本并逆序清理回查。

## 5. 完成定义（DoD）

输入输出与失败语义明确；只读任务所需 Skill 且遵循其契约；版本与 `--help` 已核对；
非伪实现；单测/错误/隔离测试全过；结论与证据等级一致；更新与回滚通过；
本轮资源已清理或有经批准保留说明；产物无凭据/Cookie/JWT/真实资源标识硬编码；
`execution-journal.md` 如实区分已验证/部分/未验证。

> 若修改了 `skills/`，运行仓库统一验证脚本（见 onboarding 第 8 节），确认正式 Skill 数量与
> 秘密模式/重复 Skill/相对链接检查全部通过。

## 6. 冷启动完整示例

[`examples/cold-start-agent/`](examples/cold-start-agent/) 是只依赖本仓库 README、Onboarding 与按需 Skills 构建的离线示例，覆盖：

- veADK Agent 与 AgentKit SDK 服务入口；
- Google ADK Graph 条件路由和 `DEFAULT_ROUTE`；
- 贯穿 HTTP 请求链的持久化 `ShortTermMemory`，以及 session/user 隔离；
- 缺少 `user_id` / `session_id` 时返回 HTTP 400；
- 真实本地 MCP stdio：initialize → tools/list → tools/call；
- L1 静态与 L2 离线真跑测试、执行日志和机器可读结果。

从该目录的 [`README.md`](examples/cold-start-agent/README.md) 开始；无需云凭据，也不会创建云资源。

---

# 工程入口：构建、运行、测试

以下为该服务本体的通用工程说明。它是一个 FastAPI 垫片，在外置 agent 循环之上运行
“目标 → 验收 → 架构 → 评测” 的业务流程，暴露层-1 Runtime 协议
（`/invoke`、`/run`、`/run_sse`、`/sessions`、`/health`），并可同时构建内置前端单页应用。

> 设计文档见 [`design/`](design/) 与 [`docs/`](docs/)，从
> [`design/01-architecture.md`](design/01-architecture.md) 与
> [`design/architecture.html`](design/architecture.html) 开始。

## 6. Prerequisites

| Need | Version | Notes |
|---|---|---|
| Python | 3.11–3.13（验证 venv 用 3.13；镜像用 3.12-slim） | Hermes 要求 `>=3.11,<3.14` |
| Node | LTS | 仅构建前端（`web/`） |
| Docker | CLI 28.x | `docker buildx --platform linux/amd64` |

## 7. Install

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r deploy/requirements.txt
pip install pytest pytest-asyncio ruff        # dev-only
```

`deploy/requirements.txt` 是真实依赖集合（fastapi/uvicorn/otel 与 Hermes 依赖统一）；
provider 专属 extra 默认不安装。

## 8. Run locally

```bash
bash run_local.sh            # mock bridge, serves web/dist on http://127.0.0.1:8000
```

`APP_MODE` 未设 → local 模式，走确定性离线 mock bridge（无需 LLM 凭据）。用 `bash run_local.sh 8010` 改端口。

| `APP_MODE` | Bridge | CORS | 用途 |
|---|---|---|---|
| `mock` | 强制 mock | `*`（告警） | 离线演示 / CI |
| `local`（默认） | 无 LLM env 时回落 mock | `*`（告警） | 本地开发 |
| `production` | **fail-closed**：无 `APP_LLM_*` 拒绝启动 | 空=同源，或显式 allowlist | 镜像默认 |

## 9. Environment variables

| Variable | Required | Sensitive? | Meaning |
|---|---|---|---|
| `APP_MODE` | prod: yes | no | `mock`/`local`/`production` |
| `APP_LLM_BASE_URL` | prod: yes | no | LLM endpoint；空 → mock bridge |
| `APP_LLM_API_KEY` | prod: yes | **yes** | LLM key |
| `APP_LLM_MODEL` | prod: yes | no | 模型名 |
| `APP_LLM_PROVIDER` / `APP_LLM_API_MODE` | no | no | 传给 agent 构造 |
| `APP_ALLOWED_ORIGINS` | prod: yes | no | 逗号分隔 allowlist；prod 拒绝 `*` |
| `RUNTIME_API_KEY` | prod recommended | **yes** | 入站 KeyAuth；空 → 开放本地模式 |
| `RUNTIME_API_KEY_HEADER` | no | no | 默认 `X-Api-Key` |
| `APP_DATA_DIR` | no | no | draft/session 存储目录 |
| `SERVE_FRONTEND_DIST` | no | no | 设为 `web/dist` 以托管 SPA |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | no | no | OTLP endpoint；空 → console |
| `APP_RUNTIME_ENDPOINTS` | no | no | JSON `{runtime_id: url}` 反代白名单 |

Secrets are never printed; the settings layer redacts key/secret/token in any masked summary.
本仓库不提交任何真实 `.env`，仅保留 `.env.example`。

## 10. Test & build

```bash
python -m pytest tests/ -q                 # backend 单测/集成
python -m ruff check server tests deploy    # lint
bash deploy/e2e_smoke.sh                    # 可复现 HTTP E2E
bash deploy/e2e-web.sh                      # 前端 E2E
cd web && npm install && npm run build       # -> web/dist/
```

## 11. Deployment status (generic checklist)

- 本地质量门：后端单测、Ruff、前端 ESLint、类型检查与生产构建均通过。
- 生产模式 fail-closed：未配置 `APP_LLM_*` 拒绝启动；凭据从挂载的安全位置读取，不注入长流水 AK/SK。
- 浏览器端登录/会话由独立 BFF 保持服务端，前端只拿 HttpOnly 会话。
- 观测：每次请求应有可关联的 Trace/Span 树；临时凭据按最小权限只读。
- 发布前必须完成：构建 → 健康检查 → 业务输出校验 → 发新版本 → 回滚旧版本 → 清理并回查。
- **Ready / HTTP 200 都不是业务验收**；浏览器人工点击路径需要用户接管，不可自动注入密码/MFA/CAPTCHA。
- 任何凭据暴露事件后，相关 key/secret 必须在对应控制台轮换，轮换完成前安全验收保持 open。

## 12. Known limitations

1. 生产模式需要真实 LLM endpoint；否则只能 mock/local。
2. 浏览器验收需要人工接管（密码/MFA/CAPTCHA/同意）。
3. 生产 CORS 空 allowlist = 同源；`*` 被拒。
4. 冷启动：实例可缩到 0，首个云请求会唤醒容器。
5. 若 Runtime 契约未提供 secret-reference 字段，按敏感控制面数据处理环境值。

## 13. Licenses

- 本项目：见仓库。
- 内置 vendored **Hermes agent**（MIT）许可证随镜像分发。
- Prompt 来源声明见服务内 prompts 的 NOTICES 文件。

## 2026-10-16 官网同步结论（只读复核）

- 本仓钉版（veadk-python==1.1.13 / agentkit-sdk-python==0.8.7 / google-adk==2.2.0 / mcp==1.26.0 / 公开 agentkit-cli 0.52.13）为**本仓离线实测钉版**，不代表官网最新版本；官网快速上手可能钉更旧 SDK，以本仓钉版为准。
- 已按现行官网公开页修订：MCP 2026-07-28 兼容口径（含 HTTP 转 MCP）、initialize 握手示例版本、KB 环境变量边界、CLI 钉版口径、IAM 策略名拼写注记；详见 `skills/` 各 Skill 与 `docs/volcengine-official/snapshot_index.md`。
- 实际租户/区域可用范围、定价、配额以控制台与公开文档为准；本仓未进行云端实测，不背书内部灰度口径。

## 2026-10-23 周度复扫结论（只读复核，未升级钉版）

- 本轮从线上重新发现导航并完成正文内链闭包：导航+闭包正文集合 **451**（AgentKit 本体 393 + VeADK 3 + DeliveryAI 55，三者分列不混算）；分类为未变 404、正文修改 34、导航新收录 3、真新增 API 2（PauseSession/ResumeSession）、基线覆盖缺口回填 8。
- 数字 86681 引用 326 条：304 canonical 命中本周集合、22 条旧内部数字路由 SSR shell（受限单列，不判删除/缺失），0 外部产品、0 unresolved；2 个集合外 slug（Developing_and_deploying_agents、user-guide-1）为 hub 入口，非正文页。
- 仅按公开证据修订 5 处边界，未改依赖/UI、未升级钉版：sandbox 配额现行公开注记（模板50/实例100，以配额中心为准、非永久）、identity 在线调试公网/M2M 边界、evaluation 仅华北2北京、sandbox PauseSession/ResumeSession、gateway Identity 鉴权插件；详见 `skills/` 各 Skill 与 `docs/volcengine-official/snapshot_index.md`。
- 旧页本周不可达 ≠ 删除；目录/页面新增 ≠ 后端能力新增；UpdatedTime 不替代正文 hash 比对。

### 可复现门禁命令（引自只读门禁审计矩阵，2026-10-16）

```bash
# G1 后端 pytest（unit/integration 为 mock 离线；3 个 veadk 根测试构造 Agent()，可能触发 AK/SK 查找，不得宣称完全离线）
python -m pytest tests/ -q
# G2 Ruff lint（离线）
python -m ruff check server tests deploy
# G3 后端 HTTP E2E（离线 mock；PY 默认 /tmp/agentkit_verify_venv/bin/python，缺失须 PY=<venv> 覆盖）
bash deploy/e2e_smoke.sh [port]
# G4 前端构建（需 Node LTS；registry 取包）
cd web && npm ci && npm run build
# G5/G6 前端 lint / typecheck（依赖 G4 的 node_modules）
cd web && npm run lint && npm run typecheck
# G7 前端 E2E（依赖 G4 产出 web/dist）
bash deploy/e2e-web.sh [port]
# G8 统一 benchmark 门禁（verify_all.py；secret_scan 仅扫 skills/+benchmark，非全仓）
python benchmark_20260928/iteration2/verification/verify_all.py
# G9 ADK 编排离线真跑（google-adk FunctionNode，无模型）
python skills/adk-workflow/scripts/validate_orchestration.py
# G10 冷启动示例（无云凭据、不建云资源）
bash examples/cold-start-agent/run.sh
# G11 全仓秘密扫描（标准库，可立即跑；只报 file:line:pattern 不打值）
python3 sec-audit/scan_secrets.py
```

离线边界：G1/G3/G7/G8/G10 需先在 venv 装 `deploy/requirements.txt` 与钉版依赖（veadk-python==1.1.13[extensions] / agentkit-sdk-python==0.8.7 / google-adk==2.2.0 / mcp==1.26.0）；本机仅有 Python3.13 与 Node v22，venv 与 web/node_modules 未落地时上述命令不可立即跑。local 后端 ≠ 无凭据。
