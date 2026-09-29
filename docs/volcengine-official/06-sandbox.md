# 06 沙箱 (Sandbox / 沙箱模板)

> 概述：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Tooloverview?lang=zh
> 类型：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Tooltypes?lang=zh

## 概念

沙箱模板（Sandbox Template）为 Agent 提供**隔离的代码/命令/浏览器/技能执行环境**。Agent 通过 `run_code`、`execute_skill` 等工具在沙箱中安全执行代码，同一 `session_id` 复用同一沙箱实例。

## 模板类型（5 种预置 + 自定义 + [BASE-ADK] 内置）

| 模板 | 内置能力 | 场景 |
|---|---|---|
| ArkClaw Sandbox | ArkClaw | 个人/轻办公，自然语言日常事务 |
| [BASE-AGENT] Sandbox | [BASE-AGENT] Agent | 长期记忆、技能进化、多模型、复杂任务 |
| AIO Sandbox | Browser+Terminal+Code 一体化，按任务自动切换 | 混合型多步复杂任务 |
| Skills Sandbox | 预置常用 Skills，自动选取执行 | 需同时用 `run_code` + `execute_skill`；复用平台预置 Skill |
| Code Sandbox | Codex CLI | 纯代码开发链路（生成/调试/依赖/脚本/测试） |
| 自定义模板 | 任意容器镜像 | 自定义环境 |

**预置 Skills**：`tos-file-access`（上传/下载 TOS）、`code-optimization`（最多 2 轮性能优化，C++/Python/Java/Rust）、`[BASE-ADK]-python`（生成可运行 Agent）、`internal-comms`（企业沟通文案）、`skill-creator`（生成新 Skill 描述/JSON Schema/Mock）。

**[BASE-ADK] 内置工具模板**：`web_search`、`image_generate`、`image_edit`、`video_generate`。

## 沙箱流程与实例

- 创建沙箱模板（可选开启快照：实例到期前自动快照，可恢复）；2026-09-10 起支持手动快照。
- 2026-09-01 起：沙箱模板可配置 **MCP 服务对外能力**（第三方 Agent 经 MCP 协议接入）；入站认证新增 **OAuth JWT**。
- ArkClaw Sandbox 实例支持配置**消息渠道**，用自然语言与实例背后 Agent 对话。
- 实例生命周期：TLL 配置、快照备份恢复、实时日志、删除。

## 代码执行工具集成（SDK Tools）

来源：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Tools-2?lang=zh
```python
from [BASE-ADK] import Agent, Runner
from [BASE-ADK].tools.builtin_tools.run_code import run_code
from [PRODUCT].apps import [PRODUCT]SimpleApp
app = [PRODUCT]SimpleApp()
agent = Agent(tools=[run_code])
runner = Runner(agent=agent)
@app.entrypoint
async def run(payload, headers):
    return await runner.run(messages=payload["prompt"],
                            user_id=headers["user_id"],
                            session_id=headers["session_id"])
```
环境变量：`[PRODUCT]_TOOL_ID=<沙箱工具实例ID>`、`VOLCENGINE_ACCESS_KEY`、`VOLCENGINE_SECRET_KEY`。
- 沙箱端点：`<INTERNAL_HOST>.com`；用户会话 ID 形如 `veAgent_<user_id>_<session_id>`。
- 支持 Python/JavaScript 等多语言代码执行。

## Sandbox Tool API（Version 2025-10-30）
CreateTool / UpdateTool / DeleteTool / GetTool / ListTools / InvokeTool / AsyncExecCommand / ViewAsyncCommand / CreateSession / DeleteSession / GetSession / ListSessions / SetSessionTtl / GetSessionLogs。
