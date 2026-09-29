# cold-start-agent（离线冷启动示例）

一个从零冷启动、**完全离线可复跑**的 AgentKit 示例工程。不依赖火山云凭据，演示一套最小但完整的链路：

- **veADK Agent**（`agent.py`）——离线占位 `model_api_key` 构造，不触发云凭据查找。
- **AgentKit SDK 服务入口**（`app.py`）——`AgentkitSimpleApp` + `@entrypoint` + `@ping` + `app.run`。
- **Google ADK Graph 条件路由 + default route**（`workflow.py`）——`classify` → `BUG` / `SUPPORT` / `DEFAULT_ROUTE→other`。
- **显式持久化 ShortTermMemory**——`ShortTermMemory(db_url="sqlite+aiosqlite:///<绝对路径>")` 传入 `Runner`，底层为 `DatabaseSessionService`；**Graph 执行复用同一个 session_service**，节点经 `context.state` 写状态，跨请求/重建实例可召回同一 user+session 的轮次与历史。
- **缺 `user_id` / `session_id` 返回 400**——entrypoint 内手动判空（含只缺其一），不回落默认值、不随机补值。
- **真实本地 MCP 协议**（`mcp_server.py` + `mcp_client.py`）——stdio 下 initialize → tools/list → tools/call。

## 目录结构

```
cold-start-agent/
├── agent.py            # veADK Agent（离线占位 key）
├── workflow.py         # Google ADK Graph 三分支 + DEFAULT_ROUTE + 离线运行器
├── mcp_server.py       # 本地 stdio FastMCP server（add / echo）
├── mcp_client.py       # 本地 MCP 客户端（initialize/list/call）
├── app.py              # AgentKit SDK 入口（400 契约 + 持久化 STM）
├── tests/              # L1 静态 + L2 离线真跑
├── requirements.txt
├── pytest.ini
├── run.sh              # 本地启动脚本
├── .env.example
└── execution-journal.md # 执行日志（读过的文档/失败根因/证据等级/Skill 缺陷记录）
```

## 快速复跑

```bash
# 1. 建环境（Python 3.12）
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. 跑测试（L1 + L2，离线）
pytest -q                      # 预期：14 passed（含 HTTP 两轮状态/重建恢复/隔离/MCP）

# 3. 本地起服务（默认 0.0.0.0:8000，本地 sqlite，无云凭据）
./run.sh
# 另开终端（同一 user+session 两轮，状态累计 turn=1 -> turn=2）：
curl http://127.0.0.1:8000/ping
curl -X POST http://127.0.0.1:8000/invoke -H 'Content-Type: application/json' \
  -H 'user_id: alice' -H 'session_id: s1' -d '{"prompt":"I found a bug in login"}'
curl -X POST http://127.0.0.1:8000/invoke -H 'Content-Type: application/json' \
  -H 'user_id: alice' -H 'session_id: s1' -d '{"prompt":"I need help"}'
```

> 本离线阶段不调用真实模型：入口用无模型 FunctionNode 的 Graph 做确定性路由。
> 真实模型联调、A2A、Runtime 部署属后续 L3/L4 门禁，不在本示例范围。
