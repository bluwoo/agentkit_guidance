# AgentKit 新 Agent 开发操作协议

> **用途**
>
> ：把本文件作为一个没有历史上下文的新 Agent 的首份操作手册。目标不是 “读完文档”，而是让 Agent 按正确顺序使用现有 Skills，快速完成可运行、可验证、可部署的 AgentKit 工程。
> **总原则**
>
> ：优先使用 AgentKit、veADK 和 Google ADK 原生组件；先证明最小闭环，再按需增加组件；任何失败都必须定位根因、修复并重跑，不得绕过错误或把局部成功写成端到端通过。



***

## 0. 启动后必须先做的事

### 0.1 确认目录

设定：



```
<AGENTKIT_SKILLS_ROOT> = 本文件同级目录下的 skills/
<WORKSPACE>            = 为本次任务单独创建的工程目录
<PROJECT_NAME>         = 用户明确授权的 AgentKit Project
<REGION>               = 用户明确授权的地域
```

先检查以下文件存在：



```
<AGENTKIT_SKILLS_ROOT>/README.md
<AGENTKIT_SKILLS_ROOT>/veadk/SKILL.md
<AGENTKIT_SKILLS_ROOT>/agentkit-sdk/SKILL.md
<AGENTKIT_SKILLS_ROOT>/agentkit-runtime/SKILL.md
<AGENTKIT_SKILLS_ROOT>/references/runner-entrypoint.md
```

不要直接修改 `skills/`。业务代码必须写入独立 `<WORKSPACE>`；只有发现 Skill 本身存在错误并完成事实核验后，才单独修订 Skill 并执行整套回归。

### 0.2 建立执行记录

在 `<WORKSPACE>` 创建 `execution-journal.md`，持续记录：



1. 本轮任务和验收标准；

2. 读取过的 Skill；

3. 采用的版本和实际命令；

4. 每次失败的原始错误类型、根因、修复和复验结果；

5. 哪些结论是静态检查、离线真跑、真实模型调用或云端 E2E；

6. 创建的云资源和最终清理状态。

记录错误摘要，不记录 AK/SK、API Key、Cookie、JWT、临时访问令牌或完整 Authorization Header。

### 0.3 先读总入口，不要一次读完全部 Skills

第一份必须读取：



```
<AGENTKIT_SKILLS_ROOT>/README.md
```

然后根据任务按需读取组件 Skill。禁止为了 “学习完整” 一次性加载 14 个 Skill；这会增加上下文噪声，也容易把不同组件、不同版本的示例错误混用。



***

## 1. Skill 路由：遇到什么任务读什么

### 1.1 所有 AgentKit 应用的底座

按顺序读取：



1. `veadk/SKILL.md`：Agent、Runner、工具和火山能力主体；

2. `agentkit-sdk/SKILL.md`：HTTP 入口、请求契约、SSE、短期会话；

3. `references/runner-entrypoint.md`：共享 Runner 骨架和跨组件硬契约；

4. 只有需要部署时才读 `agentkit-runtime/SKILL.md`。

### 1.2 按需求追加组件



| 需求                                 | 必须追加读取                                  |
| ---------------------------------- | --------------------------------------- |
| 固定拓扑、分支、并行、循环、动态控制流、多 Agent 编排     | `adk-workflow/SKILL.md`                 |
| 跨会话用户偏好或事实召回                       | `agentkit-session-memory/SKILL.md`      |
| 文档检索、RAG、VikingDB 或 ContextSearch  | `agentkit-knowledge-base/SKILL.md`      |
| 代码执行、文件会话、快照恢复                     | `agentkit-sandbox/SKILL.md`             |
| Runtime 动态加载业务 Skill               | `agentkit-skills/SKILL.md`              |
| MCP、HTTP API 工具接入、网关认证             | `agentkit-gateway-mcp/SKILL.md`         |
| AgentCard、Agent 注册发现、Agent 间调用     | `agentkit-a2a-registry/SKILL.md`        |
| 入站身份、授权策略、出站凭据托管                   | `agentkit-identity-permission/SKILL.md` |
| Prompt Injection、敏感内容与模型安全         | `agentkit-guardrails/SKILL.md`          |
| Trace、Span、Runtime 日志和诊断           | `agentkit-observability/SKILL.md`       |
| Dataset、Evaluator、Experiment 和上线门禁 | `agentkit-evaluation/SKILL.md`          |

### 1.3 固定依赖顺序



```
veADK
  → AgentKit SDK
    → Google ADK Workflow（有编排时）
      → 按需挂载 Memory / KB / Sandbox / Skills / MCP / A2A
        → Identity + Guardrails
          → Runtime
            → Observability
              → Evaluation
```

重要约束：



* 先开观测，再做在线评测；

* 会话标识不是身份授权；

* Guardrails 控制台开关不等于高代码流量已被拦截；

* `backend="local"` 不等于完全无凭据或无外部依赖；

* Runtime、MCP Gateway、A2A Registry 是不同组件，不可互相替代；

* Google ADK 编排原语从 `google.adk` / `google.adk.workflow` 导入，不写 `veadk.workflow`。



***

## 2. 环境基线

除非用户明确要求升级并接受兼容性复验，否则使用项目验证基线：



```
Python                  3.12
veadk-python             1.1.13
agentkit-sdk-python      0.8.7
google-adk               2.2.0
mcp                      1.26.0
AgentKit CLI             0.52.13
```

在独立工作区创建环境：



```
cd <WORKSPACE>
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install \
  'veadk-python==1.1.13' \
  'agentkit-sdk-python==0.8.7' \
  'google-adk==2.2.0' \
  'mcp==1.26.0'
```

只有使用相关后端时才增加：



```
python -m pip install 'veadk-python[extensions]==1.1.13'
python -m pip install 'mem0ai==0.1.118'
```

安装后立即记录并核对：



```
python --version
python -m pip show veadk-python agentkit-sdk-python google-adk mcp
agentkit --version
agentkit --help
```

**不要凭 Skill 中的命令名猜 CLI 支持情况。** 每个将执行的 CLI 分支先运行对应 `--help`；若当前 CLI 与 Skill 不一致，保存版本和帮助输出，选择当前版本真实支持的路径。



***

## 3. 开发闭环：按阶段推进

## 阶段 A：定义任务和验收标准

在写代码前明确：



* 输入与输出；

* 是否需要多轮会话；

* 是否需要 Workflow；

* 需要哪些外部组件；

* 哪些动作有副作用；

* 本地验收、真实模型验收和云端验收分别是什么；

* 云资源归属、预算、命名和清理规则。

把每条要求转成可失败的断言。例如：



```
输入缺少 user_id → HTTP 400
相同 user_id + session_id → 上下文连续
不同 user_id → 记忆不能串用
未知 Graph route → DEFAULT_ROUTE
MCP 无凭据或错误凭据 → 401
Runtime 更新后 → 新版本生效且旧版本可回滚
```

## 阶段 B：先做最小无云实现

先证明核心代码结构和确定性逻辑，不加载不需要的云组件。

最低要求：



1. `veadk.Agent` / `Runner` 或纯 Google ADK Workflow 能正确构造；

2. AgentKit SDK 入口监听 `0.0.0.0:8000`；

3. `/ping` 可用；

4. `/invoke` 严格要求 `user_id`、`session_id`；

5. 缺任一标识返回 400，不回落共享默认值，不随机补值；

6. 测试覆盖正常路径、默认路径、错误路径和隔离路径。

推荐代码结构：



```
<WORKSPACE>/
├── app.py                 # AgentKit SDK 服务入口
├── agent.py               # veADK Agent 构造
├── workflow.py            # 仅在需要编排时存在
├── tests/
│   ├── test_contract.py
│   ├── test_workflow.py
│   └── test_isolation.py
├── requirements.txt 或 pyproject.toml
├── .env.example           # 只有变量名和占位符
├── .gitignore
└── execution-journal.md
```

## 阶段 C：Workflow 先用无模型节点证明拓扑

需要编排时，先读 `adk-workflow/SKILL.md`，新设计优先：



* 固定拓扑：Graph Workflow；

* 动态 if/for/while/ 恢复：Dynamic Workflow；

* LLM 主管委派：Collaborative；

* Sequential/Parallel/Loop 仅用于存量兼容。

先运行 Skill 自带回归：



```
PYTHONDONTWRITEBYTECODE=1 python -B \
  <AGENTKIT_SKILLS_ROOT>/adk-workflow/scripts/validate_orchestration.py
```

自己的 Workflow 至少验证：



* 每个 route；

* `DEFAULT_ROUTE`；

* Join 输入完整；

* 循环退出条件；

* 并发上限；

* 外部副作用幂等；

* Dynamic 恢复不重复副作用。

不要把 LangGraph API、TypeScript-only 能力或 Google ADK 新版本参数直接混入固定基线。

## 阶段 D：加入真实模型

只有阶段 B/C 全部通过后，才引入真实模型。

验收必须检查业务语义，而不只是 HTTP 200：



* 回答确实由模型产生，不是测试代码硬编码；

* 工具调用或 Workflow 节点确实发生；

* 相同输入具有可接受结果；

* 超时、限流、认证错误被正确区分；

* 未调用模型时不得写 “模型验证通过”。

真实凭据只从用户授权的安全位置加载。不得把值写入代码、文档、日志、命令历史、`.env.example` 或交付包。

## 阶段 E：逐个接入平台组件

每次只新增一个组件，使用对应 Skill 的最小真实验收：



| 组件             | 最小真实验收                                               |
| -------------- | ---------------------------------------------------- |
| Session Memory | 写入 → 新 Session 同用户召回 → 异用户隔离                         |
| Knowledge Base | 建库 / 索引 → 唯一测试标记检索命中 → 删除                            |
| Sandbox        | 真执行 → 同 Session 文件复用 → 异 Session 隔离 → 快照恢复           |
| Skills         | 创建空间 / 版本 → Agent 实际调用并返回版本 marker                   |
| MCP            | initialize → tools/list → tools/call；无 / 错凭据负例       |
| A2A            | 标准 AgentCard → Registry 发现 → JSON-RPC `message/send` |
| Identity       | 无凭据 / 错凭据 / 有效凭据 + Allow/Deny 四象限                    |
| Guardrails     | 正常请求放行 + 受控攻击样本被真实围栏拦截 + 回调 / 日志证据                   |

组件未完成数据面调用时，只能写 “控制面创建成功” 或 “部分通过”，不能写端到端通过。

## 阶段 F：部署 Runtime

部署前读取 `agentkit-runtime/SKILL.md`，并核对当前 CLI 帮助。

必须检查：



1. 镜像为目标 Runtime 架构；

2. 容器监听 8000；

3. 健康检查成功；

4. Runtime 回读为目标 `<PROJECT_NAME>` 和 `<REGION>`；

5. 状态 Ready；

6. `/invoke` 得到正确业务输出；

7. 错误路径按预期失败；

8. Runtime 日志能关联请求；

9. 发布新版本并验证；

10. 回滚旧版本并验证；

11. 清理本轮资源并回查 NotFound / 列表消失。

**Ready 不是业务验收。HTTP 200 也不是业务验收。** 必须检查响应内容、状态变化和服务端证据。

## 阶段 G：安全、观测与评测闭环

上线前：



1. Identity：验证认证和授权，不把 `user_id` 当可信身份；

2. Guardrails：验证四回调或产品要求的高代码接入方式；

3. Observability：产生本轮 Trace，检查完整 Span 树和错误关联；

4. Evaluation：使用本轮独立 Dataset、Evaluator 和 Target；

5. 评测终态同时检查：结束时间、成功 / 失败样本、每条实际输出、每条分数、Trace；

6. 阈值不满足时停止发布，不通过降低门槛换 PASS。



***

## 4. 四级证据口径

所有结论必须标注证据等级：



| 等级        | 含义                  | 允许的表述      |
| --------- | ------------------- | ---------- |
| L1 静态     | import、签名、schema、编译 | “静态检查通过”   |
| L2 离线真跑   | 本地真实函数、节点、协议、测试     | “离线行为通过”   |
| L3 真实依赖   | 真实模型、MCP 或云组件数据面    | “真实依赖调用通过” |
| L4 云端 E2E | 创建→调用→观测 / 评测→清理    | “端到端通过”    |

禁止：



* L1 冒充 L2；

* Mock 冒充真实 SDK 或云端；

* 控制面创建成功冒充数据面成功；

* 链路可达冒充业务正确；

* 历史资源或他人资源冒充本轮生命周期；

* 只看一个状态码、状态字段或 import 就宣布通过。



***

## 5. 失败处理协议

遇到失败时严格执行：



```
复现
→ 保存脱敏错误和版本信息
→ 判断是代码、配置、权限、配额、版本还是平台问题
→ 查对应 Skill 和当前 CLI/API 真实契约
→ 修复根因
→ 重跑最小失败用例
→ 重跑受影响的整条链路
→ 更新测试、文档与执行记录
```

规则：



* 同一错误两次没有新信息就更换诊断通道，不盲目重试；

* 不通过删除断言、跳过测试、换 Mock、复用旧资源或改变用户目标绕过；

* 平台阻塞必须提供已执行证据、最小外部依赖和可复跑步骤；

* 修复公共代码或 Skill 后，必须重跑全部受影响组件。



***

## 6. 安全和通用化硬规则



* 所有项目、账号、资源、Endpoint、Registry、App、Workspace、Trace、用户信息均通过变量或占位符传入；

* 示例使用 `<PROJECT_NAME>`、`<REGION>`、`<RUNTIME_ID>`、`<ENDPOINT>`、`<APP_ID>` 等占位符；

* 不在项目文件中固化任何真实项目名、账号、资源 ID、客户名或临时测试标识；

* 不读取未获授权的 shell profile、浏览器 Cookie、个人密钥目录；

* 不在交付文件中保留访问令牌或鉴权 Header；

* `.env` 不提交，项目只保留 `.env.example`；

* 日志和报告记录凭据类别与是否存在，不记录值；

* 云资源使用唯一任务前缀，写入资源账本，逆序清理并回查。

资源账本最少字段：



```
{
  "resource_type": "<TYPE>",
  "resource_name": "<TASK_PREFIX>-<NAME>",
  "resource_id": "<REDACTED_OR_RUNTIME_ONLY>",
  "project": "<PROJECT_NAME>",
  "region": "<REGION>",
  "created": true,
  "cleanup_status": "pending"
}
```

如果报告需要长期留存，项目内只保存匿名化账本；真实 ID 只保存在用户批准的受限审计系统中。



***

## 7. 完成定义（Definition of Done）

只有全部满足才能宣布完成：



* [ ] 任务输入、输出和失败语义明确；

* [ ] 只读取了任务需要的 Skills，且实际遵循其契约；

* [ ] 版本和 CLI/API 帮助已核对；

* [ ] 代码不是伪实现或硬编码结果；

* [ ] 单元测试、错误测试、隔离测试全部通过；

* [ ] 真实模型 / 组件 / 云端结论与实际证据等级一致；

* [ ] Runtime 项目和地域回读正确；

* [ ] 业务响应、日志、Trace 和评测相互对应；

* [ ] 更新与回滚通过；

* [ ] 所有本轮资源已清理或有明确经批准的保留说明；

* [ ] 代码和产物无凭据、Cookie、JWT、真实资源标识和私有项目硬编码；

* [ ] 使用与生成路径不同的方法回读和验证交付物；

* [ ] `execution-journal.md` 如实区分已验证、部分验证和未验证。



***

## 8. 正式 Skill 套件回归

如果修改了 `skills/`，必须执行项目统一验证：



```bash
cd <AGENTKIT_PROJECT_ROOT>
python3.13 -m venv .venv-verify
source .venv-verify/bin/activate
python -m pip install \
  'veadk-python[extensions]==1.1.13' \
  'agentkit-sdk-python==0.8.7' \
  'google-adk==2.2.0' \
  'mcp==1.26.0' \
  'pytest==9.1.1' 'pytest-asyncio==1.4.0' pyyaml
python benchmark_20260928/iteration2/verification/verify_all.py
```

也可显式设置 `PY=<兼容的钉版Python>` 运行其他脚本；不要依赖 `/tmp` 或 `benchmark_20260928/.venv` 中预先存在的环境。

该验证检查 Skill 结构、代码块、测试、秘密模式、重复 Skill 和相对链接。它验证的是 Skill 套件，不替代业务项目自己的测试和云端 E2E。

同时确认正式 Skill 数量仍为 14；备份、缓存和实验 Skill 不得混入正式扫描目录。



***

## 9. 新 Agent 首条启动指令

将下面整段作为新 Agent 的第一条任务指令，并补齐尖括号参数：



```
你是负责 AgentKit 工程交付的资深 FDE。你没有历史上下文；本目录中的
AGENTKIT_AGENT_ONBOARDING.md 和 skills/ 是你的唯一工程指南。

先完整阅读 AGENTKIT_AGENT_ONBOARDING.md，再阅读 skills/README.md。
随后只按当前任务需要读取对应 SKILL.md 和其引用文件，不要一次性通读全部组件。

任务：<TASK_DESCRIPTION>
工作目录：<WORKSPACE>
目标 Project：<PROJECT_NAME>
目标 Region：<REGION>
允许使用的凭据来源：<AUTHORIZED_CREDENTIAL_SOURCE_OR_NONE>
允许创建的云资源：<AUTHORIZED_RESOURCES_OR_NONE>
预算与清理要求：<BUDGET_AND_CLEANUP_RULES>

执行要求：
1. 先把需求改写成可失败的验收断言，创建 execution-journal.md。
2. 使用 AgentKit、veADK、Google ADK 原生组件；已有组件能够完成时不得重造。
3. 使用独立虚拟环境，先核对版本、import、签名和CLI --help。
4. 先完成无云最小实现和确定性测试，再逐个加入真实模型与平台组件。
5. 缺 user_id/session_id 必须返回400；会话标识不得作为授权依据。
6. 每加入一个组件，完成其正例、负例、隔离和清理验收。
7. 云端必须执行创建、归属回读、真实调用、日志/Trace、更新、回滚和清理。
8. 所有结论标注L1静态、L2离线真跑、L3真实依赖或L4云端E2E。
9. 遇到错误先定位并修根因；不得跳过测试、降低门禁、换Mock或复用历史资源冒充成功。
10. 不打印或落盘任何凭据；代码、报告和压缩包不得含真实账号、项目、资源ID或Endpoint硬编码。
11. 完成前运行本任务全部测试；若修改skills/，再运行统一verify_all.py。
12. 只有全部验收通过后才宣布完成；否则明确列出阻塞、已验证边界和最小后续动作。

最终交付：
- 可运行源码和依赖锁定；
- 启动、测试、部署、回滚与清理命令；
- 测试和端到端证据；
- execution-journal.md；
- 资源账本和清理回查；
- 已验证/未验证边界及风险。
```



***

## 10. 建议的新 Agent 入门考题

如果目的是检验它是否真的掌握本套 Skills，先给以下任务，不要直接让它开发全组件生产系统：



```
创建一个最小 AgentKit 工程：
1. 使用 Google ADK Graph 实现分类→两个分支→默认路由；
2. 使用真实节点运行，覆盖所有路由的精确断言；
3. 用 veADK Agent + AgentKit SDK 包装服务入口；
4. 显式配置持久化 ShortTermMemory；
5. 缺 user_id/session_id 返回400，不回落默认值；
6. 本地无云阶段不得调用真实模型或读取秘密；
7. 交付源码、测试、执行记录，并标注L1/L2证据；
8. 通过后再授权真实模型和Runtime，完成L3/L4验收。
```

通过标准不是 “写出了代码”，而是新 Agent 能够：



* 正确选择和读取 Skills；

* 不混淆 ADK、veADK 与 AgentKit；

* 避免版本漂移；

* 写出真实可运行节点和负向测试；

* 区分本地、模型、云端证据；

* 遇错修复并复验；

* 保持凭据与项目标识不进入交付物。