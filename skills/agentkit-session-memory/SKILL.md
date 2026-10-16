---
name: agentkit-session-memory
description: AgentKit 会话与记忆管理——三层记忆架构（会话层 PostgreSQL/短期上下文 Runner 内存/长期记忆 mem0 或 Viking 记忆库），支持 LongTermMemory(backend="mem0"|"viking_mem") SDK 集成。当需要为 Agent 配置会话存储、长期记忆、跨会话记忆持久化、或配置记忆库写入/读取/治理时使用本 Skill。
---

# AgentKit 会话与记忆管理 (Session & Memory) Skill

## 1. 概述

AgentKit 会话与记忆管理采用**三层记忆架构**：会话层（PostgreSQL）负责会话粒度的"对话工单"、短期上下文（Runner 内存）负责单次 Run 内的"工作记忆"、长期记忆（mem0 / Viking 记忆库）负责跨会话持久化的"日记本"。短期上下文负责"正在做什么"，长期记忆负责"我知道什么"。短期上下文受上下文窗口限制，需通过"记忆归档"策略把关键信息抽取后写入长期记忆，下次会话再检索注入。SDK 通过 `LongTermMemory(backend="mem0"|"viking_mem")` 一行集成，支持显式调用 `save_session_to_long_term_memory` 落库。

## 2. 前置条件

使用本组件前必须满足：
- [ ] 已创建 AgentKit Runtime
- [ ] 如需会话层：已创建会话资源（云数据库 PostgreSQL / MySQL / Serverless PostgreSQL）
- [ ] 如需长期记忆：已创建记忆库（mem0 或 Viking 记忆库）
- [ ] 已在 Runtime"关联组件"中选择会话资源和记忆库
- 依赖包：
  - `veadk-python==1.1.13`（基础包；`LongTermMemory` 从 `veadk.memory.long_term_memory` 导入）
  - **本地/离线调试用 `backend="local"` 时必须装 extras：`uv add 'veadk-python[extensions]==1.1.13'`**；裸 `veadk-python` 构造 `InMemoryLTMBackend` 时会因缺 redisvl/opensearch/vikingdb 等扩展子依赖而 ImportError
  - **⚠️ local 后端的真实离线边界（2026-09-28 钉版 venv 无凭据实测）**：装齐 extras 只解决 ImportError，**不代表无凭据可真构造/真读写**。`LongTermMemory(backend="local")` 构造时仍会初始化 embedding/Ark token 并查找 Volcengine AK/SK（或 VeFaaS IAM 文件 `/var/run/secrets/iam/credential`）；无凭据直接抛 `FileNotFoundError: Get Volcengine access key or secret key ... not exists`。因此 local 后端只能离线做 import/后端工厂枚举/签名探针，**不得声称真读写离线可用**；任何真实记忆读写（含 local 的向量化写入/检索）都需云凭据。
  - `mem0ai==0.1.118`（仅使用 mem0 后端时；viking/local 后端不需要）
- 环境变量：见下方关键环境变量表

## 3. 快速上手

### 3.1 控制台操作路径

**会话资源管理**：
AgentKit 控制台 → 会话资源 → 创建/导入会话资源 → 在 Runtime"关联组件"中选择

**记忆库管理**：
AgentKit 控制台 → 记忆库 → 创建记忆库（选择 mem0 或 Viking 后端）→ 在 Runtime"关联组件"中绑定

### 3.2 代码集成（SDK Memory 示例）

```python
# 【已离线核验-2026-09-22，venv=veadk-python==1.1.13】
# - from veadk.memory.long_term_memory import LongTermMemory：import 通过（test_imports#20）
# - save_session_to_long_term_memory：协程（coroutine），签名 (session_id, user_id='', app_name='')
# 注意：LongTermMemory 的 SDK 默认 backend 是 "opensearch"，生产必须显式指定 backend；
#   真实记忆读写需云凭据联调，未在本环境实测
# Runner.run 签名 / SSE 流式写法 → ../references/runner-entrypoint.md。
from veadk import Agent, Runner
from veadk.memory.long_term_memory import LongTermMemory
from agentkit.apps import AgentkitSimpleApp

app = AgentkitSimpleApp()

# 长期记忆后端：mem0 或 viking（"viking_mem" 已废弃，会自动转发到 "viking"）
# LongTermMemory 字段（Pydantic，已核验）：backend/index/top_k(默认5)/app_name/user_id/backend_config
long_term_memory = LongTermMemory(
    backend="mem0",
    index="simple_app",   # 记忆库索引名
    top_k=5,
)

agent = Agent(
    name="simple_app_agent",
    instruction="你是一个有记忆的助手，记住用户的偏好和关键信息。",
    long_term_memory=long_term_memory
)
runner = Runner(agent=agent)

@app.entrypoint
async def run(payload, headers):
    result = await runner.run(
        messages=payload["prompt"],
        user_id=headers["user_id"],
        session_id=headers["session_id"],
    )
    # 显式落库：将本轮会话关键信息写入长期记忆（流式 run_async 时在事件循环后同样调用一次）
    await runner.save_session_to_long_term_memory(
        session_id=headers["session_id"],
        user_id=headers["user_id"]
    )
    return result

app.run(host="0.0.0.0", port=8000)
```

### 3.3 配置文件（agentkit.yaml）

```yaml
# mem0 后端
launch_types:
  cloud:
    runtime_envs:
      DATABASE_MEM0_BASE_URL: "<your mem0 url>"
      DATABASE_MEM0_API_KEY: "<your mem0 api key>"

# Viking 记忆库后端
launch_types:
  cloud:
    runtime_envs:
      DATABASE_VIKINGMEM_COLLECTION: "<your vikingdb collection name>"
      DATABASE_VIKINGMEM_MEMORY_TYPE: "event_v1"  # 默认 event_v1，逗号分隔
```

## 4. 核心概念与 API

### 4.1 三层记忆架构对比

| 层 | 存储载体 | 生命周期 | 类比 | 说明 |
|---|---|---|---|---|
| **会话层（Session）** | PostgreSQL / MySQL / Serverless PostgreSQL | 会话粒度，会话结束可销毁 | "一张对话工单" | 按 app_name/user_id/session_id 存取会话 |
| **短期上下文（Short-term）** | Runner 内存 / Session 表 | 单次 Agent Run 内有效 | "工作记忆" | 受上下文窗口限制 |
| **长期记忆（Long-term）** | mem0 / Viking 记忆库 | 跨会话持久化 | "日记本/知识库" | 语义检索注入 prompt |

### 4.2 记忆库工作原理（四步）

| 步骤 | 说明 |
|---|---|
| **写入** | 每轮对话结束后，Agent（或独立抽取模型）从对话中抽取事实/偏好/画像，结构化写入记忆库 |
| **更新** | 检测到与已有记忆矛盾时合并/更新 |
| **读取** | 新对话到来时按语义检索相关记忆，注入 prompt |
| **治理** | 过期/错误记忆可人工或自动清理 |

### 4.3 记忆库后端对比

| 后端 | 说明 |
|---|---|
| **mem0 记忆库** | 火山引擎托管的兼容开源 Mem0 的记忆服务 |
| **Viking 记忆库** | 火山引擎标准化长期记忆产品，自动抽取事件/用户画像并结构化存储 |

### 4.4 LongTermMemory 后端工厂

`veadk.memory.long_term_memory.LongTermMemory` 继承 Google ADK 的 `BaseMemoryService`，后端工厂 `_get_backend_cls(backend)` 支持：

| backend 值 | 后端类 |
|---|---|
| `"local"` | InMemoryLTMBackend |
| `"opensearch"` | OpensearchLTMBackend |
| `"viking"` | VikingDBLTMBackend |
| `"viking_mem"` | 已废弃，转发到 `"viking"` |
| `"redis"` | RedisLTMBackend |
| `"mem0"` | Mem0LTMBackend |
| `"openviking"` | OpenVikingLTMBackend |
| `"tos_context"` | TosContextBucketLTMBackend |

### 4.5 自动保存策略

`MemoryAutoSavePolicy` 控制哪些事件被写入长期记忆，支持三种预设：
- `default`
- `all`
- `custom`

### 4.6 关键 API 清单

| API | 用途 |
|---|---|
| AddMemoryCollection | 添加记忆集合 |
| CreateMemoryCollection | 创建记忆集合 |
| UpdateMemoryCollection | 更新记忆集合 |
| DeleteMemoryCollection | 删除记忆集合 |
| GetMemoryCollection | 获取记忆集合 |
| GetMemoryConnectionInfo | 获取长期记忆提取策略连接信息 |
| ListMemoryCollections | 列出记忆集合 |
| AddSessionStore | 添加会话存储 |
| DeleteSessionStore | 删除会话存储 |
| GetSessionStore | 获取会话存储 |
| ListSessionStores | 列出会话存储 |
| `runner.save_session_to_long_term_memory(session_id, user_id)` | 显式将会话落库到长期记忆 |

### 4.7 关键环境变量

| 变量名 | 用途 | 是否必填 |
|---|---|---|
| `DATABASE_MEM0_BASE_URL` | mem0 记忆库连接 URL | 使用 mem0 后端时必填 |
| `DATABASE_MEM0_API_KEY` | mem0 记忆库 API Key | 使用 mem0 后端时必填 |
| `DATABASE_VIKINGMEM_COLLECTION` | Viking 记忆库 Collection 名称 | 使用 Viking 后端时必填 |
| `DATABASE_VIKINGMEM_MEMORY_TYPE` | Viking 记忆类型（默认 `event_v1`，逗号分隔） | 使用 Viking 后端时必填 |

## 5. 输入输出规范

### 输入
- **会话层**：`app_name`, `user_id`, `session_id` — 三元组定位会话
- **长期记忆写入**：对话结束后的对话内容（自动抽取事实/偏好/画像）
- **长期记忆读取**：新对话 prompt + user_id — 语义检索相关记忆注入

### 输出
- **会话层**：历史会话消息列表
- **长期记忆读取**：检索到的相关记忆片段，自动注入 Agent prompt
- **API 响应**：标准 CRUD 操作成功/失败状态

## 6. 权限与安全

- **所需 IAM 权限**：AgentKit 记忆库/会话资源管理权限
- **入站认证**：与 Runtime 一致
- **出站凭据**：记忆库连接通过 API Key（mem0）或 Collection 配置（Viking）
- **数据安全**：长期记忆存储用户偏好/画像等 PII，需注意数据脱敏与治理；数据驻留火山引擎境内
- **安全围栏兼容**：可与安全围栏联动，对记忆内容中的敏感数据做 PII 识别

## 7. 失败处理与排障

| 错误现象 | 可能原因 | 处理方式 |
|---|---|---|
| 长期记忆未写入 | 未调用 `save_session_to_long_term_memory` / 自动保存策略未触发 | 确认 entrypoint 中显式调用 `runner.save_session_to_long_term_memory` |
| 记忆读取不到 | 记忆抽取延迟（约1分钟）/ 索引未建好 | 等待约 1 分钟抽取完成后再验证 |
| 记忆后端连接失败 | 环境变量未配置 / API Key 错误 | 检查 `DATABASE_MEM0_BASE_URL`/`API_KEY` 或 `DATABASE_VIKINGMEM_COLLECTION` |
| `mem0ai` 依赖缺失 | 未安装指定版本 | `pip install mem0ai==0.1.118` |
| 会话不持久 | 未在 Runtime 关联组件中选择会话资源 | 编辑 Runtime，在关联组件中绑定会话资源 |
| `viking_mem` 后端报错 | 该值已废弃 | 使用 `"viking"` 代替（`"viking_mem"` 会自动转发） |
| 记忆内容矛盾 | 记忆更新策略未合并冲突 | 检查记忆库治理配置，确认矛盾检测与合并逻辑 |

排障路径：观测大盘看记忆库调用量/检索时延 → 下钻 Trace 看记忆读写节点 → TLS 日志。

## 8. 可执行验证办法

1. **首轮存入信息**：用 `session_id=A` 调用 Agent，在对话中告知一个关键信息（如"我的密码是 XYZ"或"我偏好简洁回答"）
2. **显式落库**：确认 `save_session_to_long_term_memory` 被调用
3. **等待抽取**：等待约 1 分钟（长期记忆抽取有延迟）
4. **换 session_id 验证**：用新的 `session_id=B`（同一 `user_id`）调用 Agent，询问之前存入的信息
5. **预期结果**：Agent 能从长期记忆中读出之前存入的信息

```bash
# 【需云凭据联调】<runtime-domain> 为 GetRuntime.Endpoint，未在本环境实测
# 步骤1：首轮存入
curl -X POST https://<runtime-domain>/invoke \
  -H "Content-Type: application/json" \
  -H "user_id: demo-user" \
  -H "session_id: session-A" \
  -d '{"prompt": "记住：我叫张三，偏好简洁回答"}'
# 预期：200

# 等待约 1 分钟...

# 步骤2：换 session_id 读出
curl -X POST https://<runtime-domain>/invoke \
  -H "Content-Type: application/json" \
  -H "user_id: demo-user" \
  -H "session_id: session-B" \
  -d '{"prompt": "我叫什么名字？我偏好什么风格的回答？"}'
# 预期：Agent 回答"你叫张三，偏好简洁回答"（从长期记忆检索）
```

## 9. 与其他组件的关系

- **上游依赖**：AgentKit Runtime（关联组件中绑定会话资源和记忆库）
- **下游联动**：
  - **观测（Observability）**：记忆库调用量、检索时延是观测大盘的可观测对象
  - **评测（Evaluation）**：记忆质量可纳入评测维度
- **常见组合**：
  - Runtime + 会话资源 + 长期记忆 = 有记忆的多轮 Agent
  - 三层记忆 + 观测 = 记忆读写可监控
  - mem0 后端 + 简单 Agent = 快速集成长期记忆

## 10. 已知限制与注意事项

- **`viking_mem` 已废弃**：依据本仓钉版 `veadk-python==1.1.13` 源码，`viking_mem` 后端实现转发到 `"viking"`，建议直接使用 `"viking"`；生产推荐后端为 `viking`（VikingDB 记忆库）与 `mem0` 两个。
- **长期记忆抽取有延迟**：首轮写入后约需等待 1 分钟抽取完成才能读出（官方集成文档口径），属异步抽取，需重试
- **短期上下文受上下文窗口限制**：不能无限累积，必须通过记忆归档策略写入长期记忆
- **会话后端支持**：后端枚举依据 `veadk-python==1.1.13` 源码（`local`/`sqlite`/`mysql`/`postgresql`/`viking`/`mem0` 等），按 `app_name + user_id + session_id` 三元组隔离。
- **云端创建边界（公开文档可证）**：创建会话资源当前仅支持 **Serverless PostgreSQL**；RDS PostgreSQL/MySQL 需先在对应产品控制台建实例再导入（出处：https://docs.volcengine.com/docs/agentkit/Creating_session_resources?lang=zh）。
- **依赖版本固定**：`mem0ai==0.1.118`
- **会话概述文档（Sessionsoverview）正文为空壳**（仅52字节），操作细节以控制台和子页面为准
- 长期记忆写入需显式调用 `save_session_to_long_term_memory`（协程），或配置 `MemoryAutoSavePolicy`（default/all/custom）自动保存
- Viking 记忆类型 `DATABASE_VIKINGMEM_MEMORY_TYPE` 默认 `event_v1`，支持逗号分隔多类型
- **仍待确认（勿写成平台限制）**：网传「`AddSession` 单次 100 条消息上限」在本次 SDK 源码中未找到依据，是否仍有效以 SDK 报错/控制台为准；`ShortTermMemory` 各后端的并发与容量上限以官方文档为准。
- **云端未实测**：记忆读写、抽取延迟、跨会话读出均需云凭据联调验证，本环境无真实记忆库资源。

## 11. 来源追溯

| 信息点 | 来源 URL | 文档章节 |
|---|---|---|
| 三层记忆架构 | https://docs.volcengine.com/docs/AgentKit/threelayer-memory-architecture-of-ai-dialogue-system-session-division-of-labor-and-coordination-of-s?lang=zh | 三层记忆架构 |
| 记忆工作原理（写入/更新/读取/治理） | https://docs.volcengine.com/docs/AgentKit/Howmemoryworks?lang=zh | How memory works |
| 记忆概述（mem0/Viking后端） | https://docs.volcengine.com/docs/AgentKit/Memoryoverview?lang=zh | 记忆概述 |
| 集成记忆（SDK 代码示例） | https://docs.volcengine.com/docs/AgentKit/Integratingmemoriesinagent?lang=zh | 集成记忆 |
| SDK Memory API | https://docs.volcengine.com/docs/AgentKit/Memory?lang=zh | Memory API |
| 会话概述（空壳文档） | https://docs.volcengine.com/docs/AgentKit/Sessionsoverview?lang=zh | 会话概述 |
| LongTermMemory 源码/后端工厂/自动保存策略 | https://volcengine.github.io/agentkit-sdk-python/content/6.memory/1.memory_quickstart.html | doc03 SDK 核验报告 第2节 |
| LongTermMemory/save_session 签名（离线源码核验） | veadk-python==1.1.13 `veadk/memory/long_term_memory.py`、`Runner.save_session_to_long_term_memory` | 本地 venv import + inspect，2026-09-22 |
