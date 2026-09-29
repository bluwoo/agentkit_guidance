---
name: agentkit-runtime
description: AgentKit 智能体运行时（Runtime）——将 Agent 代码（容器镜像）发布为可调用在线服务，自动完成扩缩容、负载均衡、健康检查、版本管理、日志与观测。当需要部署、调用、更新或管理 Agent 在线服务时使用本 Skill。
---

# AgentKit 智能体运行时 (Runtime) Skill

## 1. 概述

Runtime 是 AgentKit 托管 Agent 应用的服务实例。它把 Agent 代码（容器镜像）发布为可调用的在线服务，自动完成扩缩容、负载均衡、健康检查、版本管理、日志与观测。Runtime 是 Agent 从本地开发到云端生产的核心交付载体，支持专属网关（生产）和共享模式（POC）两种计费形态。

## 2. 前置条件

使用本组件前必须满足：
- [ ] 已注册火山引擎账号并开通 AgentKit 服务
- [ ] 已获取 `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY`
- [ ] 已有容器镜像（来自镜像仓库 CR，支持跨账号公网镜像）
- [ ] 已选择模型（如 <model-name>）并获取模型 API Key
- 依赖包：`veadk-python==1.1.13`、`agentkit-sdk-python==0.8.7`（与离线验证环境一致，2026-09-18）
- Region：`cn-beijing`。注意区分域名——**控制面 OpenAPI** 用 `agentkit.<region>.volcengineapi.com`；**InvokeTool/AsyncExecCommand** 工具执行接口用 `agentkit.<region>.volces.com`；已部署 Runtime 的调用域名由 `GetRuntime.Endpoint` 返回。

## 3. 快速上手

### 3.1 控制台操作路径
AgentKit 控制台 → 智能体运行时 → 创建运行时 → 配置镜像/模型/实例规格/网络/观测/关联组件 → 发布

### 3.2 代码集成（本地开发模板）

> Runner 入口的**权威通用骨架**（`runner.run(messages=)` 非流式 / `run_async` SSE 流式 / `inspect.signature` 验证命令 / session 预建契约）统一见 [`../references/runner-entrypoint.md`](../references/runner-entrypoint.md)；签名自检脚本 `python3 skills/references/verify_runner_signature.py`。本节只保留 Runtime 本地开发最小入口。

```python
# Runner.run(messages=) 自动建 session、返回 str（签名见共享 reference §3）。
# 如需 SSE 流式（run_async + types.Content + 先 create_session），勿在此复制，见 ../references/runner-entrypoint.md §4。
from veadk import Agent, Runner
from agentkit.apps import AgentkitSimpleApp

app = AgentkitSimpleApp()
agent = Agent(name="my_agent", instruction="你是一个助手")
runner = Runner(agent=agent, app_name="my_app")

@app.entrypoint
async def run(payload, headers):
    result = await runner.run(
        messages=payload["prompt"],
        user_id=headers["user_id"],
        session_id=headers["session_id"],
    )
    return result  # 返回字符串

app.run(host="0.0.0.0", port=8000)
```

### 3.3 部署命令
```bash
# 【需云凭据联调】CLI 命令未在本环境实际执行（本阶段未执行云联调，火山引擎凭据可用性尚未核验）
uv add veadk-python agentkit-sdk-python
agentkit init          # 从模板生成项目
agentkit config        # 配置项目
agentkit launch        # 部署到 Runtime
agentkit invoke "你好" # 调用已部署的 Runtime
```

## 4. 核心概念与 API

| 概念 | 说明 | 关键参数 |
|---|---|---|
| Runtime | 托管 Agent 的服务实例 | 镜像、模型配置、实例规格、网络 |
| Runtime Version | 版本化发布 | Release 过程可追踪、可取消 |
| Runtime Instance | 运行中的实例 | Webshell、实时日志、网络信息 |
| 关联组件 | Runtime 绑定的平台资源 | 会话资源、记忆库、知识库、MCP工具集、沙箱、模型服务 |

### 创建运行时关键配置项
- **镜像**：来源 CR 镜像仓库；支持公网跨账号镜像（2026-08-07起）
- **模型配置**：模型选择 + 模型 API Key
- **实例规格**：最低 0.5 vCPU（2026-08-21起）；单实例并发请求数可配
- **网络**：公网访问 / 私网访问（VPC+子网）
- **观测服务**：开启后自动开通 APMPlus + TLS（在线评测必须开启）
- **安全围栏**：可选开启提示词攻击/模型滥用/敏感数据/算力消耗防护
- **注册到 A2A 空间**：可选，注册地址随网络方式自动选公网/私网
- **IAM 角色**：授予 Runtime 访问火山引擎资源的权限

### 调用方式
- **文本指令**：POST `/invoke`，Header 带 `user_id`、`session_id`，Body `{"prompt": "..."}`
- **多模态**：Body 携带 `files` 字段传入图片/文件
- **流式**：SSE 返回（SDK 侧 `StreamingMode.SSE`）

### Runtime API 清单（Version 2025-10-30）
CreateRuntime / UpdateRuntime / ReleaseRuntime / DeleteRuntime / GetRuntime / ListRuntimes / GetRuntimeVersion / ListRuntimeVersions / GetRuntimeInstanceLogs / ListRuntimeInstances / UpdateRuntimeRelease / AbortRuntimeRelease / GetRuntimeReleaseStatus / ListRuntimeReleaseRecords / GetRuntimeWebshellEndpoint

## 5. 输入输出规范

### 输入（调用 Runtime）
- Header: `user_id` (string) — 用户标识
- Header: `session_id` (string) — 会话标识，同 session 复用沙箱/会话状态
- Body: `prompt` (string) — 文本指令
- Body: `files` (array, optional) — 多模态文件

### 输出
- 同步：字符串响应
- 流式：SSE 事件流
- 错误：标准 HTTP 状态码 + 错误信息

## 6. 权限与安全

- **所需 IAM 权限**：AgentKit Runtime 管理权限（创建/更新/删除/发布）
- **入站认证**：API Key（共享/专属网关）或 SSO（开启快速登录后）
- **出站凭据**：通过 IAM 角色授权访问火山引擎资源；第三方资源用 OAuth 令牌托管
- **安全围栏**：可在 Runtime 创建时勾选开启，自动集成无需改代码
- **观测**：必须开启观测服务才能使用在线评测和 trace 诊断

## 7. 失败处理与排障

| 错误现象 | 可能原因 | 处理方式 |
|---|---|---|
| 发布失败 | 镜像拉取失败 / 健康检查不通过 | 检查镜像仓库权限、容器启动命令、端口配置 |
| 调用 404 | Runtime 未发布或已删除 | 确认 Release 状态，检查服务域名 |
| 调用 500 | Agent 代码异常 / 模型调用失败 | 查看 Runtime 实例日志 + TLS 日志 |
| 调用超时 | 实例规格不足 / 冷启动 | 提升实例规格、配置预热 |
| 观测无数据 | 未开启观测服务 | 编辑 Runtime 开启观测服务 |

排障路径：观测大盘定位异常 → 下钻 Trace → 查看 TLS 日志 → 结合安全围栏攻击日志

## 8. 可执行验证办法

1. 部署后执行 `agentkit invoke "测试消息"`，返回 200 且有响应内容
2. 在观测大盘确认 Runtime 有 QPS、时延指标
3. 检查 `/invoke` 接口响应包含预期的 Agent 输出
4. 验证版本发布：更新镜像后 Release，确认新版本生效且旧版本可回滚

```bash
# 【需云凭据联调】<runtime-domain> 为 GetRuntime.Endpoint，未在本环境实测
# 验证调用
curl -X POST https://<runtime-domain>/invoke \
  -H "Content-Type: application/json" \
  -H "user_id: test-user" \
  -H "session_id: test-session" \
  -d '{"prompt": "你好"}'
```

## 9. 与其他组件的关系

- **上游依赖**：镜像仓库（CR）、模型服务（方舟）、IAM
- **下游联动**：观测（APMPlus/TLS）、评测（trace回流）、安全围栏、A2A注册
- **常见组合**：
  - Runtime + 观测 + 评测 = Eval-driven 闭环
  - Runtime + MCP工具集 + 知识库 = RAG Agent
  - Runtime + 沙箱 + Skills = 代码执行 Agent
  - Runtime + 身份权限 + 网关 = 生产级安全 Agent

## 10. 已知限制与注意事项

- Runtime 网关与 MCP 网关是两套独立实例，分别下单计费
- 专属网关适用于生产，共享模式适用于 POC/低流量
- 计费口径在 2026-09-01 有变更，以官方计费文档为准
- 最低实例规格 0.5 vCPU（2026-08-21起）

## 11. 来源追溯

| 信息点 | 来源 URL | 文档章节 |
|---|---|---|
| Runtime 概念与创建配置 | https://docs.volcengine.com/docs/AgentKit/Creatingruntimesconsole?lang=zh | 创建运行时（控制台） |
| 调用方式 | https://docs.volcengine.com/docs/AgentKit/Samplecallsfortextprompts?lang=zh | 文本/多模态调用示例 |
| API 清单 | https://docs.volcengine.com/docs/AgentKit/Agentruntimeoverview?lang=zh | API 参考 |
| SDK 集成 | https://docs.volcengine.com/docs/AgentKit/Quickstart?lang=zh | SDK 快速开始 |
| 计费形态 | https://docs.volcengine.com/docs/AgentKit/gateway_mode_and_mcp_request_counting_rules?lang=zh | 计费计数规则 |


---

## 措辞与契约修正记录（2026-09-18）

- §3.3 部署命令注释「（无云凭据）」改为「（本阶段未执行云联调，火山引擎凭据可用性尚未核验）」。
