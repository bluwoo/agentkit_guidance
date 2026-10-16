---
name: agentkit-knowledge-base
description: AgentKit 知识库（基于 VikingDB 向量库的 RAG 服务）——将企业文档导入向量库后，Agent 可自动进行语义检索并基于检索结果回答用户问题。AgentKit Knowledge 为「Viking 知识库 + ContextSearch（开源兼容 ES/OpenSearch）」双引擎统一检索网关，可用同一接口灵活切换后端。当需要为 Agent 挂载知识库、构建 RAG 问答、管理文档切片、配置 Viking/ContextSearch/OpenSearch 等后端或配置知识库文档级访问控制时使用本 Skill。纯 VikingDB 集群运维、非 RAG 的通用向量检索场景不适用。
---

# AgentKit 知识库 (VikingDB RAG) Skill

## 1. 概述

知识库是 AgentKit 基于 **VikingDB 向量库**实现的一体化 RAG 服务，提供"文档管理—语义检索—智能对话"完整链路，支持结构化与非结构化多模态文档，适用于法律、教育、企业内部文档问答等场景。Agent 通过 `KnowledgeBase(backend="viking")` 关联知识库后，VeADK 自动挂载 `LoadKnowledgebaseTool` 工具，Agent 可在对话中调用该工具检索相关文档切片并组织回答；**是否每轮触发检索由 Agent 根据 instruction 与工具描述决定，不保证每轮必检索**，无需手动编写检索逻辑。

> **后端形态（已离线核验 veadk-python==1.1.13 源码）**：AgentKit Knowledge 是「多知识库接入与检索网关」，打通向量/图/全文引擎，用同一接口灵活切换后端。产品侧双引擎为 **Viking 知识库**（高性价比、精准召回、多模态）与 **ContextSearch**（开源兼容 Elasticsearch/OpenSearch）；VeADK SDK `KnowledgeBase` 的 `backend` 还可选 `opensearch`、`redis`、`milvus`、`tos_vector`、`openviking`、`local`（详见 §4）。（后端枚举依据本仓钉版 `veadk-python==1.1.13` 源码）

## 2. 前置条件

使用本组件前必须满足（按后端路径区分）：
- **Viking 后端路径（生产主路径）**：
  - [ ] 已注册火山引擎账号并开通 AgentKit 与 VikingDB 服务
  - [ ] 已在 VikingDB 控制台创建向量库 Collection 并上传文档
  - [ ] 已获取 `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY`
  - [ ] 已在 AgentKit 知识库控制台完成 VikingDB 知识库导入
- **ContextSearch 后端路径（统一检索网关另一引擎，兼容 ES/OpenSearch）**：
  - [ ] 已开通 ContextSearch 服务并创建 engine（project/engine_id/engine_endpoint/engine_apikey）
  - [ ] 不需要 VikingDB Collection；通过 `backend_config` 传入服务配置（见 §4）
- **通用**：
  - [ ] Python ≥ 3.10
  - 依赖包：`veadk-python==1.1.13`（与本套件其余组件对齐；KnowledgeBase import 与字段签名已离线核验，见 §8）
    - **本地/离线调试用 `backend="local"` 时必须装 extras：`uv add 'veadk-python[extensions]==1.1.13'`**；裸 `veadk-python` 构造 `InMemoryKnowledgeBackend` 时会因缺扩展子依赖而 ImportError。Viking/ContextSearch 生产路径只需基础包 + 对应服务凭据。
- 环境变量（Viking 后端，源码读取自 `veadk.knowledgebase.backends.vikingdb_knowledge_backend`）：
  - `DATABASE_VIKING_COLLECTION=<viking collection 名称>`（即 `KnowledgeBase(index=...)`）
  - `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY`（控制面/后端访问 AK/SK；BytePlus 环境读 `BYTEPLUS_ACCESS_KEY`/`BYTEPLUS_SECRET_KEY`）
  - 可选：`DATABASE_VIKING_PROJECT`（默认 `default`）、`DATABASE_VIKING_RESOURCE_ID`（默认空）、`DATABASE_VIKING_VERSION`（默认 `2`）、`DATABASE_VIKING_REGION` / `REGION`（默认 `cn-beijing`）、`KNOWLEDGEBASE_INDEX`
  - 注意：AK/SK 是部署/后端访问凭证，不是用户身份；**不得提交或写入示例/YAML/.env 明文**。

## 3. 快速上手

### 3.1 控制台操作路径

1. **VikingDB 控制台** → 创建知识库 Collection（如 `customer_support`）→ 上传文档（如 `qa.md`）
2. **AgentKit 控制台 → 知识库** → 导入 VikingDB 知识库 → 选中目标 Collection → 查看集成代码，复制环境变量
3. **Runtime 关联组件** → 选择已导入的知识库；或在代码中直接用 SDK 关联

### 3.2 代码集成
```python
# 【已离线核验-2026-09-22，venv=veadk-python==1.1.13】
# - from veadk.knowledgebase import KnowledgeBase：import 通过（test_imports#18）
# - Agent(knowledgebase=...)：veadk/agent.py:264 确认为合法字段（挂载 LoadKnowledgebaseTool）
# - VeADK Runner.run(messages=)：已核验源码，返回 str
# 注意：以下为 SDK 骨架，真实检索/建库需云凭据联调，未在本环境实测
import os
from veadk import Agent, Runner
from veadk.knowledgebase import KnowledgeBase
from agentkit.apps import AgentkitSimpleApp
from google.genai import types
from google.adk.agents import RunConfig
from google.adk.agents.run_config import StreamingMode

app = AgentkitSimpleApp()

# 通过环境变量指定 VikingDB Collection 名称
# KnowledgeBase 字段（Pydantic，已核验）：backend/index/top_k(默认10)/app_name/
#   enable_profile(默认False)/query_with_user_profile(默认False，开启需 Viking 记忆库后端)/backend_config
# 注意：index 为必填项；os.getenv 缺失时会传入 None 导致后续检索失败，必须显式检测
_viking_collection = os.getenv("DATABASE_VIKING_COLLECTION")
if not _viking_collection:
    raise RuntimeError(
        "DATABASE_VIKING_COLLECTION 必须设置（Viking 后端必填）；"
        "缺失时 KnowledgeBase(index=None) 会导致检索工具无法定位 Collection"
    )
knowledgebase = KnowledgeBase(
    backend="viking",
    index=_viking_collection,
    top_k=10,
)

agent = Agent(
    instruction="Answer customer's questions according to your knowledgebase.",
    model_name="<model-name>",
    knowledgebase=knowledgebase
)

runner = Runner(agent=agent)

# --- 非流式（推荐）：runner.run(messages=) 直接返回字符串 ---
# 验证：python3 -c "from veadk.runner import Runner; import inspect; print(inspect.signature(Runner.run))"
@app.entrypoint
async def run(payload, headers):
    result = await runner.run(
        messages=payload["prompt"],
        user_id=headers["user_id"],
        session_id=headers["session_id"],
    )
    return result


# --- 流式 SSE（如需逐事件推送）：run_async + types.Content ---
# 注意：run_async 继承 ADK 父类，auto_create_session 默认 False，session 不存在会 raise SessionNotFoundError。
# 必须先显式建 session（见下），或改用非流式 runner.run(messages=)（其内部自动建 session）。
# @app.entrypoint
# async def run_stream(payload, headers):
#     content = types.Content(role="user", parts=[types.Part(text=payload["prompt"])])
#     async for event in runner.run_async(
#         user_id=headers["user_id"],
#         session_id=headers["session_id"],
#         new_message=content,
#         run_config=RunConfig(streaming_mode=StreamingMode.SSE),
#     ):
#         yield event.model_dump_json(exclude_none=True, by_alias=True)

app.run(host="0.0.0.0", port=8000)
```

### 3.3 配置文件（agentkit.yaml）
```yaml
DATABASE_VIKING_COLLECTION: customer_support
```

### 3.4 调用验证
```bash
agentkit invoke "你们有什么产品？"
# Agent 自动检索知识库并组织回答
```

## 4. 核心概念与 API

| 概念/类/函数 | 说明 | 关键参数 |
|---|---|---|
| `KnowledgeBase` | RAG 知识库对象，挂载到 Agent（`Agent(knowledgebase=...)`，veadk 自动挂载 `LoadKnowledgebaseTool`） | `backend: str`（默认 `local`，生产用 `viking`）；`index: str` — Collection 名称；`top_k: int`（默认 10）；`enable_profile`/`query_with_user_profile`（后者开启需 Viking 记忆库后端）；`backend_config: dict`（service 类后端如 `context_search`/`openviking` 用各自服务配置） |
| VikingDB Collection | 向量库中的文档集合，包含切片与索引 | 由 VikingDB 控制台创建和管理 |
| 文档切片（Chunk） | 文档被拆分后的最小检索单元 | 可在控制台查看切片详情 |
| 细粒度访问控制 | 文档级访问策略（2026-06-19起） | 按文档/用户维度配置可见性；**按 `user_id` 的文档级隔离依赖可信身份映射**，SSO 同角色共用账号场景为已知卡点，需联调验证（见 §10） |

**KnowledgeBase 后端选项（已离线核验 `_get_backend_cls` 工厂，veadk-python==1.1.13）**

| backend 值 | 后端 | 备注 |
|---|---|---|
| `viking` | VikingDBKnowledgeBackend | 生产推荐，走 Viking 后端环境变量 |
| `context_search` | ContextSearchBackend | 火山 Context Search 统一检索网关，兼容 ES/OpenSearch；用 `backend_config` 传 `project/engine_id/engine_endpoint/engine_apikey` 等服务配置 |
| `opensearch` / `redis` / `milvus` / `tos_vector` / `openviking` | 对应向量后端 | SDK 可选；需各自集群/服务配置 |
| `local` | InMemoryKnowledgeBackend | 内存，仅本地调试（程序退出即丢失） |

> **双引擎定位**：AgentKit 产品侧「Viking 知识库 + ContextSearch」为统一检索网关，向量/图/全文同源切换；ContextSearch 面向开源 ES/OpenSearch 生态（以官网公开文档为准）。

### 关键环境变量

| 变量名 | 用途 | 是否必填 |
|---|---|---|
| `DATABASE_VIKING_COLLECTION` | 指定 Agent 关联的 VikingDB Collection 名称 | 是 |
| `VOLCENGINE_ACCESS_KEY` | 火山引擎访问密钥 ID | 是 |
| `VOLCENGINE_SECRET_KEY` | 火山引擎 secret 访问密钥 | 是 |
| `DATABASE_VIKING_PROJECT` | Viking 项目名（默认 `default`） | 否 |
| `DATABASE_VIKING_RESOURCE_ID` | Viking 资源 ID（默认空） | 视部署 |
| `DATABASE_VIKING_VERSION` | Viking 协议版本（默认 `2`） | 否 |
| `DATABASE_VIKING_REGION` / `REGION` | 地域（默认 `cn-beijing`） | 否 |
| `KNOWLEDGEBASE_INDEX` | 知识库索引名（与 `index` 等效别名） | 否 |
| `context_search_*`（经 `backend_config`） | ContextSearch 后端的 project/engine_id/endpoint/apikey | 用 context_search 时必填 |

> **关于 `DATABASE_VIKING_API_KEY`（2026-10-16 边界注记）**：现行官网运行时控制台已文档化该变量（知识库级 API Key 鉴权，与 AK/SK 二选一、同时配置优先 API Key）。但本仓钉版 `veadk-python==1.1.13` 的 Viking 后端源码不读取该变量，仍走 `VOLCENGINE_ACCESS_KEY/SECRET_KEY`。升级到支持该鉴权的新版 SDK 前，本地开发与部署仍须配置 AK/SK；不要把 `DATABASE_VIKING_API_KEY` 列为本地 SDK 必填环境变量。

### 知识库 API 清单（Version 2025-10-30）

| API | 说明 |
|---|---|
| `AddKnowledgeBase` | 新增知识库 |
| `UpdateKnowledgeBase` | 更新知识库配置 |
| `DeleteKnowledgeBase` | 删除知识库 |
| `GetKnowledgeBase` | 获取知识库详情 |
| `GetKnowledgeConnectionInfo` | 获取知识库连接信息 |
| `ListKnowledgeBases` | 列出当前账号下所有知识库 |

## 5. 输入输出规范

### 输入（Agent 对话触发检索）
- `prompt`: `string` — 用户自然语言问题，Agent 自动向量化并检索
- 隐式输入：文档切片（由 VikingDB 向量索引管理）

### 输出
- Agent 回答：`string` — 基于检索到的文档切片组织的自然语言回答
- 控制台可查看：检索命中的原始文档、切片详情
- 错误：标准 HTTP 状态码 + 错误信息

## 6. 权限与安全

- **所需 IAM 权限**：VikingDB 读写权限 + AgentKit 知识库管理权限
- **入站认证**：通过 Runtime 网关（API Key / SSO）
- **出站凭据**：Runtime 通过 IAM 角色访问 VikingDB
- **细粒度访问控制**：2026-06-19 起支持对知识库文档的细粒度访问控制，可按文档级别控制不同用户/Agent 的可见范围
- **数据安全**：文档与切片存储在 VikingDB 向量库中；支持配置私网访问
- **安全围栏兼容**：可与 Runtime 安全围栏联动，对检索内容做敏感数据检测

## 7. 失败处理与排障

| 错误现象 | 可能原因 | 处理方式 |
|---|---|---|
| 检索结果为空 | Collection 名称错误 / 文档未成功导入 | 检查 `DATABASE_VIKING_COLLECTION` 值与 VikingDB 控制台 Collection 名是否一致；确认文档已完成索引 |
| Agent 未使用知识库回答 | KnowledgeBase 对象未正确传入 Agent | 确认 `Agent(knowledgebase=knowledgebase)` 参数已传入；确认 `backend="viking"` |
| 导入 VikingDB 知识库失败 | VikingDB 与 AgentKit 不在同一 Region / 权限不足 | 确认两个服务 Region 一致；检查 IAM 权限 |
| 检索精度低 | 文档切片过大/过小 / Embedding 模型不匹配 | 在 VikingDB 控制台调整切片策略；检查 Embedding 模型配置 |
| 私网访问不通 | 未配置私网网络 | 在知识库控制台配置私网访问（VPC+子网） |

排障路径：Agent 响应中检查是否引用了知识库内容 → 查看 VikingDB 控制台切片详情 → 确认索引状态 → 检查 Runtime 关联组件配置

## 8. 可执行验证办法

1. 在 VikingDB 控制台确认目标 Collection 存在且文档索引完成
2. 在 AgentKit 知识库控制台确认该 Collection 已导入并状态正常
3. 部署 Runtime 并关联知识库后，执行：
```bash
agentkit invoke "你们的退款政策是什么？"
```
4. 确认返回内容基于知识库文档（非模型幻觉）
5. 在控制台查看"查看原始文档"和"查看切片详情"，确认检索命中正确

## 9. 与其他组件的关系

- **上游依赖**：VikingDB 向量库（文档存储与向量索引）、Runtime（Agent 运行环境）
- **下游联动**：Agent 对话（自动检索）、观测（检索 trace）、评测（知识库问答准确率）
- **常见组合**：
  - Runtime + 知识库 = RAG 问答 Agent
  - Runtime + 知识库 + MCP 工具集 = 企业知识+操作双能力 Agent
  - Runtime + 知识库 + 安全围栏 = 合规知识问答（敏感数据检测）

## 10. 已知限制与注意事项

- 知识库集成通过 `KnowledgeBase(backend=...)` 完成；生产主路径为 Viking 后端，**ContextSearch（兼容 ES/OpenSearch）为统一检索网关的另一引擎**，SDK 还可选 opensearch/redis/milvus 等（见 §4）
- 文档级访问策略的配置界面与 API 参数以控制台为准；按用户身份的文档级隔离依赖可信 `user_id` 映射，同角色共用账号场景可能因缺 `user_id` 回退而需联调验证（本仓未云端实测）。
- 索引更新与检索性能指标以官方公开文档/控制台为准；本仓不背书未经实测的具体数值，且非 SLA 承诺。
- 支持配置私网访问以满足数据不出 VPC 的合规要求
- description、知识库等属于创建/部署期配置，不能在 `agentkit invoke` 请求级覆盖中修改
- **云端未实测**：本节所有检索/建库/索引行为均需云凭据联调验证，本环境无真实 VikingDB/ContextSearch 资源

## 11. 来源追溯

| 信息点 | 来源 URL | 文档章节 |
|---|---|---|
| 知识库概念与 VikingDB 定位 | https://docs.volcengine.com/docs/AgentKit/Knowledgebaseoverview?lang=zh | 知识库概述 |
| SDK 集成代码与环境变量 | https://docs.volcengine.com/docs/AgentKit/Integratingknowledgebaseinagent?lang=zh | 在 Agent 中集成知识库 |
| KnowledgeBase SDK 用法 | https://docs.volcengine.com/docs/AgentKit/Knowledge?lang=zh | 知识库 SDK 参考 |
| 细粒度访问控制 | https://docs.volcengine.com/docs/AgentKit/Knowledgebaseoverview?lang=zh | 知识库概述（2026-06-19 更新说明） |
| 知识库 API 清单 | https://docs.volcengine.com/docs/AgentKit/Knowledgebaseoverview?lang=zh | API 参考 |
| KnowledgeBase 类字段/后端工厂（离线源码核验） | veadk-python==1.1.13 `veadk/knowledgebase/knowledgebase.py`、`backends/vikingdb_knowledge_backend.py` | 本地 venv import + inspect，2026-09-22 |

---

## iteration2 / Slice A 实测回写（2026-09-28，钉版 venv）

钉版 venv：`benchmark_20260928/.venv/bin/python`（python 3.12.14，veadk-python==1.1.13）。

### 实测结论：`KnowledgeBase(backend="local")` 不能纯离线检索
- 真 SDK 可导入：`veadk.knowledgebase.KnowledgeBase`；构造器签名里
  `backend: Literal['local','opensearch','viking','redis','milvus','tos_vector','context_search','openviking']`，
  故 `local` 是受支持后端。
- **但默认 `KnowledgeBase(backend="local")` 在构造期即失败**：无凭证时
  `embedding_config.api_key` 回退到 `get_ark_token()`，报
  `FileNotFoundError: ... access key or secret key ... VeFaaS IAM file not exists`。
  即"local"只是**存储在内存**，embedding 仍走 Ark 云端点 `https://ark.<region>.volces.com/api/v3/`
  （模型 `<embedding-model-name>`）。
- `add_from_text` / `search` 实际触发 embedding HTTP 调用；用死本地端点复现为
  `APIConnectionError: Connection error.`。**离线/无密钥无法真实召回**。

### 契约（写死）
- `backend="local"` ≠ 离线可用：它是"内存存储 + 云 embedding"。要离线跑通 search 必须先有可用
  embedding 服务（密钥或本地模型），否则视为阻塞项，不得在离线冒烟里假装召回成功。
- 证据：`benchmark_20260928/iteration2/evaluation/evidence/kb_local_probe.txt`
- 可复现探针：`benchmark_20260928/iteration2/evaluation/scripts/probe_kb_local.py`
- 契约测试：`benchmark_20260928/iteration2/evaluation/tests/test_kb_local_contract.py`（4 passed）
- 云端边界：viking/opensearch/redis/milvus/tos_vector/context_search/openviking 均需各自服务与凭证；
  本切片不发起任何真实云调用、不读密钥。
