# 09 会话与记忆管理

> 三层架构：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/threelayer-memory-architecture-of-ai-dialogue-system-session-division-of-labor-and-coordination-of-s?lang=zh
> 记忆原理：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Howmemoryworks?lang=zh
> 记忆概述：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Memoryoverview?lang=zh
> 会话概述：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Sessionsoverview?lang=zh （**正文为空壳，仅 52 字节**，见 gaps）
> 集成记忆：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Integratingmemoriesinagent?lang=zh
> SDK Memory：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Memory?lang=zh

## 三层记忆架构

来源：三层记忆架构文档
| 层 | 存储载体 | 生命周期 | 类比 |
|---|---|---|---|
| **会话层（Session）** | PostgreSQL / Serverless PostgreSQL | 会话粒度，会话结束可销毁 | "一张对话工单" |
| **短期上下文（Short-term）** | Runner 内存 / Session 表 | 单次 Agent Run 内有效 | "工作记忆" |
| **长期记忆（Long-term）** | mem0 / Viking 记忆库 | 跨会话持久化 | "日记本/知识库" |

- 短期上下文受上下文窗口限制，需"记忆归档"策略：把关键信息抽取后写入长期记忆，下次会话再检索注入。
- 短期上下文负责"正在做什么"，长期记忆负责"我知道什么"。

## 会话管理（短期）

- 后端支持：云数据库 PostgreSQL 版、MySQL 版、**Serverless PostgreSQL**（2026-07-31 起）。
- 操作：创建会话资源 / 导入会话资源 / 在 Agent 中集成 / 删除。
- 集成：Runtime"关联组件"中选择会话资源；代码侧 [BASE-ADK] `Runner.short_term_memory.session_service` 按 `app_name/user_id/session_id` 存取会话。

## 记忆库（长期）工作原理

来源：Howmemoryworks
1. **写入**：每轮对话结束后，Agent（或独立抽取模型）从对话中抽取事实/偏好/画像，结构化写入记忆库。
2. **更新**：检测到与已有记忆矛盾时合并/更新。
3. **读取**：新对话到来时按语义检索相关记忆，注入 prompt。
4. **治理**：过期/错误记忆可人工或自动清理。

## 记忆库后端

来源：Memoryoverview + 相关云产品
- **mem0 记忆库**：火山引擎托管的兼容开源 Mem0 的记忆服务。
- **Viking 记忆库**：火山引擎标准化长期记忆产品，自动抽取事件/用户画像并结构化存储。

## 在 Agent 中集成（SDK Memory 示例）

来源：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Memory?lang=zh
```python
from [BASE-ADK] import Agent, Runner
from [BASE-ADK].memory.long_term_memory import LongTermMemory
from [PRODUCT].apps import [PRODUCT]SimpleApp
app = [PRODUCT]SimpleApp()
long_term_memory = LongTermMemory(backend="mem0", index="simple_app")  # or "viking_mem"
agent = Agent(name="simple_app_agent", instruction="...", long_term_memory=long_term_memory)
runner = Runner(agent=agent)
@app.entrypoint
async def run(payload, headers):
    resp = await runner.run(messages=payload["prompt"],
                            user_id=headers["user_id"], session_id=headers["session_id"])
    await runner.save_session_to_long_term_memory(session_id=headers["session_id"],
                                                  user_id=headers["user_id"])  # 显式落库
    return resp
```
[PRODUCT].yaml 环境变量：
- mem0：`DATABASE_MEM0_BASE_URL`、`DATABASE_MEM0_API_KEY`
- viking_mem：`DATABASE_VIKINGMEM_COLLECTION`、`DATABASE_VIKINGMEM_MEMORY_TYPE`（默认 `event_v1`，逗号分隔）
- 依赖：`mem0ai==0.1.118`
- 验证：首轮存密码，换 `session_id` 新一轮调用，等待约 1 分钟抽取后即可读出。

## 记忆库 API
AddMemoryCollection / CreateMemoryCollection / UpdateMemoryCollection / DeleteMemoryCollection / GetMemoryCollection / GetMemoryConnectionInfo（长期记忆提取策略）/ ListMemoryCollections；AddSessionStore/DeleteSessionStore/GetSessionStore/ListSessionStores。
