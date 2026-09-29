# 安全匿名化与发布前审计报告

## 结论

- 状态：**PASS**
- 禁用私有项目代号：项目内容、路径、ZIP 内部均 **0 命中**
- 真实账号、资源 ID、Workspace/Experiment/Runtime/A2A/SkillSpace/KB/Memory/Sandbox/Tool ID、Trace、Endpoint、Registry、项目用户身份、Cookie/JWT/AK/SK/API Key/Bearer：**0 高风险命中**
- Vendored Hermes 开源归属信息与公开 npm 包元数据中的邮箱被保留（2,559 处、136 个文件）；它们不属于项目用户或私有身份，保留是为了许可证溯源与 lockfile 完整性。
- 公开名称 AgentKit、veADK、Google ADK、Hermes 已保留。
- 原始审计证据已移至项目外私有备份；项目内只留匿名化副本。

## 验证

- 正式 Skill：14/14
- Markdown 代码块：69 个围栏代码块，0 失败
- benchmark tests：53/53
- evaluation tests：9/9
- cold-start tests：7/7
- 重复 Skill：0
- 断链：0
- 统一秘密扫描：0 findings


## 最终功能回归（发布候选）

- 根测试：**158/158 通过**。
- 冷启动示例：**14/14 通过**，并由独立审计复核 Graph/STM/MCP/HTTP 链路。
- A2A wrapper：保留网关路径改写中间件，验证下游 FastAPI 路由和真实 AgentCard HTTP 响应。
- ShortTermMemory：默认 SQLite 使用本地可写路径；`SESSION_SQLITE_PATH` / `SESSION_DB_URL` 生效；DatabaseSessionService 跨实例持久化断言通过。
- 安全扫描测试夹具：使用运行时构造的合成格式值，生产扫描规则保持有效，3 项安全测试通过。
- HTTP E2E：mock/local 端口隔离、owner bootstrap、认证后的组件接口、`/invoke` 和 `/run_sse` 全部通过。
- 前端：`npm ci`、build、lint、typecheck 全部通过。
- server/deploy Ruff：通过。
- 正式 Skill：14/14；31 个 Markdown 文件、69 个围栏代码块，0 失败。
- 统一 benchmark 回归：53/53 + 9/9 + 7/7 通过。

## 冷启动真实性验收

- 新 Agent 仅以根 README、Onboarding、`skills/README.md` 和 4 个按需 Skill 为知识入口；未读取邻近工程、shell profile 或云凭据。
- 独立示例：`examples/cold-start-agent/`，L1/L2 测试 **14/14**。
- 能力闭环：veADK Agent 构造、AgentKit SDK HTTP 入口、Graph 条件/default 路由、贯穿 HTTP 的持久 ShortTermMemory、缺身份 Header 400、真实 MCP stdio initialize/list/call。
- 持久化经同 session 两轮、同库重建实例恢复、新 session、异 user 隔离验证；HTTP 实测 turn 1→2。
- 首次失败与修复：FunctionNode 参数绑定使用 `node_input`；端口冲突改用空闲端口与 responder 身份检查；状态写入采用 `Context.state` 赋值并在 run 后回读。
- 正式 Skill 改进：`adk-workflow` 修正参数绑定示例；`agentkit-sdk` 增加 `SESSION_DB_URL` / `SESSION_SQLITE_PATH` 可写路径示例并禁止 import 时无条件创建 `/data`。

## npm 锁文件完整性

- 5 个目标 lockfile 均从各自 `package.json` 或确切公开包元数据，通过 `https://registry.npmjs.org/` 重新生成；禁止并未执行摘要反向替换。
- 全项目共 5 个源码 lockfile、2,075 条 integrity：合法 `sha512-` Base64，非法 0、占位符 0。
- web：`npm ci`、build、lint、typecheck 通过。
- Hermes 根 workspace：`npm ci`、web 构建、338 项 web 测试、1,768 项 UI/TUI 测试通过（另有3项上游跳过）。
- Photon sidecar 和 WhatsApp bridge：`npm ci` 成功；sidecar 模块语法检查通过。

## 公开 Git 发布收口

- 已从公开候选中排除：内部 Lark 摘录、历史 Skill 备份、编辑前副本、设计备份、中间失败/误报扫描结果及旧归档。
- 根 `CHANGELOG` 中内部协作文档 URL 已移除；公开官方来源保留。
- 文件名与目录名不存在尖括号占位符或 `CONTACT_EMAIL` 占位符。
- 公开产品/开源术语 AgentKit、veADK、Google ADK、Hermes 均保留。
- 待提交集合：7,249 个文件；以最新 Git index 为准，扫描结果见 `git-index-scan.json`。
- 最终 ZIP 从同一候选清单生成；CRC、逐文件清单与 ZIP 内敏感扫描均需通过。
- ZIP SHA256 单独记录于 `FINAL-PACKAGE.sha256`（不纳入 ZIP，避免自引用导致校验失效）。
- 未执行 Git commit 或 push。

## 发布准备

- 根 README 已整合 Agent onboarding，并引导先读 `skills/README.md`。
- `.gitignore` 已覆盖本地环境、依赖、缓存、日志、Docker 认证、凭据和平台状态；保留 `.env.example`。
- 待提交白名单及逐文件 SHA256：`COMMIT-CANDIDATES.sha256`。
- 未执行 Git commit 或 push。
