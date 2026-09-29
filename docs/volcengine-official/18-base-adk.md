# 18 [BASE-ADK] 参考

> 概述：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/[BASE-ADK]overview?lang=zh
> 发布记录：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/[BASE-ADK]releasenotes?lang=zh

## 概念

**[BASE-ADK]（Volcengine Agent Development Kit）** 火山引擎智能体开发套件，为 Agent 应用提供开发、部署、观测、评测全流程云原生方案。与火山引擎产品体系深度融合。[PRODUCT] Python SDK 是 [BASE-ADK] 的轻量封装。

- 兼容 Google ADK 2.0（2026-06-22）。
- 多语言支持：Python 为主；也支持 LangChain 集成（2026-01-07）。

## 发布记录要点

| 日期 | 要点 |
|---|---|
| 2026-06-22 | 多 Runtime 切换（ADK/Codex/自定义）；飞书 Channel；MCP 隧道（云上 Agent↔本地 MCP）；会话级 Agent Harness 组装/热更新；OAuth 部署 Harness；[BASE-ADK] 前端应用（SSO 登录/远程 Agent 连接/工作台）；标准 A2UI 协议；兼容 Google ADK 2.0 |
| 2026-01-30 | Supabase 内置 MCP；`[BASE-ADK] web` 支持 OAuth 登录 |
| 2026-01-21 | 双向语音工具包；A2A 模式 RocketMQ 消息通信模块 |
| 2026-01-07 | Nacos 运行时动态配置；A2AHub 开箱即用注册中心；Skills；Langchain 社区支持 |

## 关键内置能力（SDK 侧已见）
- `[BASE-ADK].Agent` / `[BASE-ADK].Runner`
- `[BASE-ADK].tools.builtin_tools.run_code`、`web_search` 等
- `[BASE-ADK].memory.long_term_memory.LongTermMemory`（mem0 / viking_mem）
- `[BASE-ADK].knowledgebase.KnowledgeBase`（viking）
- `[BASE-ADK].config.getenv`
- `[BASE-ADK].prompts.agent_default_prompt`
