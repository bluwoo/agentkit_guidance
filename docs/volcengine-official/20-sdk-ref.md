# 20 SDK 参考

> 入口：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/SDKoverview-9?lang=zh
> 快速开始：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Quickstart?lang=zh
> 各子页：Runtime / Tools / Memory / Knowledge / MCP（均已读）；[PRODUCT]AgentServerApp / Anotation使用指南（未逐页读）

## 总览

[PRODUCT] Python SDK 深度封装 [BASE-ADK]，装饰器式 API。核心抽象：
- `[PRODUCT]SimpleApp()`：应用容器
- `@app.entrypoint`：定义 Agent 入口（接收 `payload: dict, headers: dict`）
- `@app.ping`：健康检查返回 `"pong!"`
- `app.run(host, port)`：启动本地服务（默认 0.0.0.0:8000）

请求契约：
- Header：`user_id`、`session_id`
- Body：`{"prompt": "...", "files": [...]}`（files 可选多模态）
- 响应：同步字符串或 SSE 事件流

## 环境变量约定

| 变量 | 用途 |
|---|---|
| `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY` | 火山引擎 AK/SK |
| `MODEL_AGENT_NAME` / `MODEL_AGENT_API_KEY` | 方舟模型 ID 与 Key |
| `[PRODUCT]_TOOL_ID` | 沙箱工具实例 ID |
| `DATABASE_MEM0_BASE_URL` / `DATABASE_MEM0_API_KEY` | mem0 记忆库 |
| `DATABASE_VIKINGMEM_COLLECTION` / `DATABASE_VIKINGMEM_MEMORY_TYPE` | Viking 记忆库 |
| `DATABASE_VIKING_COLLECTION` | Viking 知识库 |
| `MCP_ENDPOINT` / `MCP_AUTH_KEY` | 网关 MCP |
| `API_KEY` | 方舟 Key（MCP 示例） |

## 各能力集成要点

### Runtime（本地→云）
- `uv add [BASE-ADK]-python [PRODUCT]-sdk-python`
- `[PRODUCT] init` 从模板生成项目
- `[PRODUCT] config / launch / invoke` 部署与调用
- SSE 流式：`RunConfig(streaming_mode=StreamingMode.SSE)`
- 会话：`runner.short_term_memory.session_service.get_session/create_session`

### Tools（沙箱代码执行）
- `from [BASE-ADK].tools.builtin_tools.run_code import run_code`
- `Agent(tools=[run_code])`
- 同 `session_id` 复用沙箱实例

### Memory（长期记忆）
- `from [BASE-ADK].memory.long_term_memory import LongTermMemory`
- `LongTermMemory(backend="mem0"|"viking_mem", index=...)`
- 每轮结束 `await runner.save_session_to_long_term_memory(...)`
- 依赖 `mem0ai==0.1.118`

### Knowledge（RAG）
- `from [BASE-ADK].knowledgebase import KnowledgeBase`
- `KnowledgeBase(backend="viking", index=collection_name)`

### MCP
- 用 Google ADK 的 `MCPToolset` + `StreamableHTTPConnectionParams` 接入网关 MCP
- Header 鉴权：`Authorization: Bearer <MCP_AUTH_KEY>`

## 版本信息
- [BASE-ADK] 示例日志中出现版本 `0.2.13`（2025-10 示例）；最新发布记录见 18-[BASE-ADK]。
- SDK 参考子页"最近更新时间"多为 2026-01-08。
