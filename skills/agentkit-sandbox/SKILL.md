---
name: agentkit-sandbox
description: AgentKit 沙箱（Sandbox）——为 Agent 提供隔离的代码/命令/浏览器/技能执行环境，5 种预置模板（ArkClaw/Hermes/AIO/Skills/Code）+ 自定义镜像；通过 run_code 工具集成、快照生命周期、三层权限模型、同 session_id 复用实例。当需要给 Agent 接代码执行能力、选沙箱模板、做快照恢复、配置审批权限、或 init→build→create 自定义沙箱时使用本 Skill。
---

# AgentKit 沙箱 (Sandbox) Skill

## 1. 概述

沙箱（Sandbox）为 Agent 提供**隔离的代码/命令/浏览器/技能执行环境**。Agent 通过 `run_code`、`execute_skill` 等工具在沙箱中安全执行代码；**同一 `session_id` 复用同一沙箱实例**（文件系统共享），不同 session 相互隔离。平台提供 5 种预置模板 + 自定义容器镜像，并支持快照备份恢复、TOS 挂载、Web 预览、三层权限模型。沙箱 1.0 定位是 Agent 快速调试/安全隔离运行环境，2.0 演进为个人云上智能助手。

## 2. 前置条件

使用本组件前必须满足：
- [ ] 已开通 AgentKit 服务并配置 `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY`
- [ ] 已安装 agentkit CLI（TypeScript 版）：
  ```bash
  wget -qO- https://agentkit-cli.tos-<region>.volces.com/install.sh | sh
  ```
- [ ] 代码执行集成需 `veadk-python==1.1.13`（离线验证版本，2026-09-18）
- 环境变量：`AGENTKIT_TOOL_ID=<沙箱工具实例ID>`、`VOLCENGINE_ACCESS_KEY`、`VOLCENGINE_SECRET_KEY`
- 沙箱端点：`agentkit.<region>.volces.com`；用户会话 ID 形如 `veAgent_<user_id>_<session_id>`

## 3. 快速上手

### 3.1 控制台/CLI 操作路径
AgentKit 控制台 → 工具（Tool）→ 选择沙箱模板 → 创建 → 配置快照/TOS/权限 → 用 `agentkit sandbox` CLI 或 SDK `run_code` 调用。

### 3.2 代码集成（run_code 工具，最小可运行）
```python
# Runner.run(messages=) 签名与 SSE 流式写法 → ../references/runner-entrypoint.md。
from veadk import Agent, Runner
from veadk.tools.builtin_tools.run_code import run_code
from agentkit.apps import AgentkitSimpleApp

app = AgentkitSimpleApp()

agent = Agent(
    name="code_agent",
    model_name="<model-name>",
    description="A fun coding assistant",
    instruction="你是编程助手，使用 run_code 工具执行代码并返回结果。",
    tools=[run_code],
)
runner = Runner(agent=agent, app_name="sandbox_demo")
# app_name 可省略（默认 None，见官方 memory quickstart）；此处显式给出便于追踪

@app.entrypoint
async def run(payload, headers):
    result = await runner.run(
        messages=payload["prompt"],
        user_id=headers["user_id"],
        session_id=headers["session_id"],
    )
    return result

@app.ping
def ping() -> str:
    return "pong!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
```
环境变量 `AGENTKIT_TOOL_ID` 指向已创建的沙箱工具实例；同 `session_id` 自动复用沙箱。

### 3.3 CLI 快速创建与使用（Code 沙箱最佳实践）
```bash
# 【需云凭据联调】以下 agentkit sandbox 子命令来自内部操作文档，未在本环境实测（本阶段未执行云联调，火山引擎凭据可用性尚未核验）。
# 子命令语义（v2 CLI，内部《Sandbox-cli 指令集优化方案》）：
#   exec  = 打开交互式 WebSocket 终端（attach codex 等）；--command 为 ready 后注入的初始命令
#   shell = 经 HTTP 执行单条命令并返回 JSON（脚本化/自动化用，见 §8 验证）
# 创建工具并开启快照（返回 tool-id，如 <returned-tool-id>）
# 【2026-09-22 实测】CodeEnv create 不强制 --model-api-key（shell 执行无需模型注入）；
#   实测该账号 tool 配额已满（已有 133 个），新建返回 quota 错误，需提工单扩容。
agentkit sandbox create --model-api-key *** --enable-snapshot

# 用指定 session 进入交互式终端并启动 codex（--sid / --session-id / -s）
agentkit sandbox exec --sid "${SID:-demo-session}" --command codex

# 上传/下载文件
agentkit sandbox scp my_skills sandbox:/home/gem/my_skills --sid "${SID:-demo-session}"
agentkit sandbox scp sandbox:/home/gem/.codex/config.toml my_files/ --sid "${SID:-demo-session}"

# 查看沙箱 Web 预览
agentkit sandbox web --sid "${SID:-demo-session}"

# TOS 挂载（默认 /home/gem/workspace）
agentkit sandbox create --model-api-key *** --enable-snapshot --tos-bucket YOUR_BUCKET
```

### 3.4 自定义沙箱（init → build → create）
```bash
export VOLCENGINE_ACCESS_KEY=...
export VOLCENGINE_SECRET_KEY=...
agentkit sandbox init -o ./Dockerfile --force   # 生成 Dockerfile
agentkit sandbox build                          # 云上 cp 流水线构建镜像
agentkit sandbox create                         # 用镜像创建自定义沙箱工具
```

## 4. 核心概念与 API

### 模板选择指南（5 种预置 + 自定义）

| 模板 | 内置能力 | 适用场景 |
|---|---|---|
| **ArkClaw Sandbox** | OpenClaw + 部分 ArkClaw 自研插件 | 个人/轻办公、自然语言日常事务、个人智能助手 |
| **Hermes Sandbox** | 开源 Hermes Agent | 长期记忆、技能进化、多模型、复杂任务、个人智能助手 |
| **AIO Sandbox** | Browser + Terminal + Code 一体化，按任务自动切换 | 隔离执行代码/脚本，通用执行环境（`run_code` 同时支持代码与 shell） |
| **Skills Sandbox** | 基于 AIO，内置 VeADK Agent，预置常用 Skills | 需同时用 `run_code` + `execute_skill`；复用平台预置 Skill |
| **Code Sandbox** | Codex CLI（也支持 OpenCode/Claude Code；为性能默认关闭 VSCode） | 纯代码开发链路（生成/调试/依赖/脚本/测试） |
| **自定义模板** | 任意容器镜像 | 企业专属依赖环境 |

> WIP：Janus（Agent 控制浏览器）、Dev（VeADK/AgentKit 开发加速）暂未全量上线。
>
> 说明：上表 5 种为**控制台预置模板**（产品概念）。OpenAPI `CreateTool.ToolType` 的取值枚举为 `All-in-one / Skill / Private / CodeEnv / PersonalAssistant / VibeSkill`（见 shard1 CreateTool/UpdateTool），二者不是同一概念，勿混用。

**预置 Skills**：`tos-file-access`（TOS 上传下载）、`code-optimization`（C++/Python/Java/Rust 最多 2 轮性能优化）、`veadk-python`（生成可运行 Agent）、`internal-comms`（企业沟通文案）、`skill-creator`（生成新 Skill）。

**VeADK 内置工具模板**：`web_search`、`image_generate`、`image_edit`、`video_generate`。

### 会话复用模型
- 同一 `--sid/--session-id` 复用文件系统；不同 session 文件系统隔离
- 适合一个需求拆多并行沙箱（如 api/tests/docs），各自独立 FS
- 短生命周期沙箱适合 AI-Native CI/CD（PR Review、代码迁移、依赖升级、不可信代码验证）

### 快照生命周期
- `--enable-snapshot`：实例到期前自动快照，下次访问无感恢复；2026-09-10 起支持手动快照
- 完整闭环：create → snapshot → list snapshots → delete instance → restore from snapshot → delete snapshot
- ⚠️ 写自动化脚本时各步之间需**分钟级间隔**，避免快照未完成又基于快照恢复的竞态

### 权限模型（三层）
| 维度 | 取值 | 说明 |
|---|---|---|
| **Sandbox mode** | `read-only` / `workspace-write` / `danger-full-access` | 文件系统读写权限 |
| **Approval policy** | `untrusted` / `on-request` / `never` | 命令执行是否需审批 |
| **Approvals reviewer** | `user` / `auto_review` | 审批人 |

- 工作空间为远程绝对路径，**首条消息后锁定**

### Sandbox Tool API（Version 2025-10-30）
CreateTool / UpdateTool / DeleteTool / GetTool / ListTools / InvokeTool / AsyncExecCommand / ViewAsyncCommand / CreateSession / DeleteSession / GetSession / ListSessions / SetSessionTtl / GetSessionLogs

### 关键环境变量

| 变量名 | 用途 | 是否必填 |
|---|---|---|
| `AGENTKIT_TOOL_ID` | 沙箱工具实例 ID | 是 |
| `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY` | 火山引擎凭证 | 是 |
| `SANDBOX_CHAT_CODEX` / `SANDBOX_OPENCLAW_TOOL` / `SANDBOX_HERMES_TOOL` | 把沙箱工具注入 VeADK Studio | Studio 体验时 |
| `SANDBOX_CHAT_CODEX_SNAPSHOT` | 指向已开启快照的 codex 沙箱 | 快照演练时 |
| `--tos-bucket`（CLI 参数） | TOS 挂载 bucket | 持久化产物时 |

## 5. 输入输出规范

### 输入
- SDK 侧：Agent 调用 `run_code` 工具，输入代码字符串（Python/JavaScript 等多语言）
- CLI 侧：`--command <cmd>` / `--sid <session>` / `--tool-id <id>`
- 多 Agent 直连：`sandbox_a2a_invoke.py --tool-id ... --session-id ... --prompt '...'`

### 输出
- `run_code`：执行 stdout/stderr 与退出码
- CLI：命令输出 + 实例实时日志
- 会话管理：`ListSessions` / `GetSessionLogs` / `SetSessionTtl`

## 6. 权限与安全

- **所需 IAM 权限**：创建/管理沙箱工具（Tool）的权限；AK/SK 或 IAM Role（TOS 挂载 2026-08-13 起推荐用 Role 代替 AKSK）
- **入站认证**：AK/SK（demo）；2026-09-01 起入站认证新增 **OAuth JWT**，生产推荐 userpool/OAuth 替代 AK/SK
- **出站凭据**：沙箱内执行不可信代码时用 `danger-full-access` 需谨慎；审批策略 `untrusted` 最严
- **数据安全**：session 间文件系统隔离；TOS 只挂产物/工作空间（默认 `/home/gem/workspace`），不要全量挂载整个沙箱目录
- **MCP 对外能力**：2026-09-01 起沙箱模板可配置 MCP 服务对外，第三方 Agent 经 MCP 接入

## 7. 失败处理与排障

| 错误现象 | 可能原因 | 处理方式 |
|---|---|---|
| `run_code` 无返回 | `AGENTKIT_TOOL_ID` 未配 / 工具未创建 | 确认环境变量指向已创建的沙箱工具 |
| 命令执行被拒 | Approval policy 为 `on-request`/`untrusted` | 调整审批策略或由 reviewer 批准 |
| 文件系统不共享 | 不同 session_id | 同一任务复用相同 `--sid` |
| 快照恢复失败 | 快照未完成就触发恢复 | 快照与恢复之间留分钟级间隔 |
| TOS 挂载失败 | bucket 不存在 / 权限不足 | 确认 bucket 与 Role 授权 |
| Web 预览打不开 | 端口未暴露 | 让 codex 自验可访问并明确端口 |
| 实例到期丢失 | 未开快照 | `--enable-snapshot` 后实例到期自动快照恢复 |

排障路径：`agentkit sandbox list --tool-id ...` 看实例 → `GetSessionLogs` 看日志 → 实时日志。

## 8. 可执行验证办法

1. 创建并执行（`shell` 为单条命令 HTTP 子命令，同 session_id 复用文件系统）：
```bash
agentkit sandbox create --model-api-key *** --enable-snapshot
# shell：执行单条命令并返回结果（非交互式）
agentkit sandbox shell --tool-id "t-xxx" --session-id demo \
  --command 'echo hello > /tmp/demo.txt'
agentkit sandbox shell --tool-id "t-xxx" --session-id demo \
  --command 'cat /tmp/demo.txt'   # 应输出 hello（证明同 session 文件系统复用）
```
2. SDK 侧：Agent 收到"算 1+1"后调用 run_code，返回 `2`
3. 快照闭环：create → snapshot → list → delete instance → restore → delete snapshot 全链路跑通
4. Web 预览：`agentkit sandbox web --sid <sid>` 能打开产物页面

## 9. 与其他组件的关系

- **上游依赖**：Agent/Runner（调用方）、模型 API Key、TOS（可选挂载）
- **下游联动**：Skills（Skills 沙箱执行）、知识库、MCP 网关（沙箱对外 MCP）、VeADK Studio（以"智能体"呈现）
- **常见组合**：
  - AIO 沙箱 + `run_code` = 通用代码执行 Agent
  - Skills 沙箱 + `SkillToolset`/`VeSkillRegistry` = 技能执行 Agent
  - Code 沙箱 + Codex CLI = AI 编码助手
  - 沙箱 + 快照 + TOS = 可恢复、产物持久的开发环境

## 10. 已知限制与注意事项

- 沙箱与 Runtime 是两类组件：Runtime 是高代码托管服务；Sandbox 是开箱即用执行环境/智能助手
- Code 沙箱为性能默认关闭部分 AIO 能力（如 VSCode）；ArkClaw 插件未全量，能力/时延有差异
- 同名 session 复用文件系统，跨任务务必换 sid；并行子任务各自独立 sid
- 快照自动化需分钟级间隔避免竞态
- AK/SK 仅适合 demo，生产用 OAuth JWT / userpool
- 2026-08-07 前后陆续上线 ArkClaw/Hermes 控制台入口、OAuth 鉴权、MCP 对外能力，以官方最新文档为准
- Studio 对终端用户只暴露"智能体"概念，不露出"沙箱"

## 11. 来源追溯

| 信息点 | 来源 URL | 文档章节 |
|---|---|---|
| 沙箱概念与模板 | https://docs.volcengine.com/docs/AgentKit/Tooloverview?lang=zh | 工具总览 |
| 沙箱类型 | https://docs.volcengine.com/docs/AgentKit/Tooltypes?lang=zh | 工具类型 |
| run_code 集成代码 | https://docs.volcengine.com/docs/AgentKit/Tools-2?lang=zh | Tools（代码执行） |
| 模板选型/CLI/权限模型 | <internal-lark-doc> | doc02 沙箱全景 |
| 快照生命周期闭环 | <internal-lark-doc> | doc03 沙箱场景 |
| 自定义沙箱 init/build/create | <internal-lark-doc> | doc02 自定义沙箱 |
| 示例接口仓库 | <internal-samples-repo> | agentkit-samples |
| 沙箱 SDK | https://github.com/volcengine/agentkit-sdk-python | agentkit-sdk-python |
| `exec`（交互式 WS 终端）与 `shell`（单命令 HTTP）子命令语义 | <internal-lark-doc> ；<internal-lark-doc> | Sandbox-cli 指令集优化方案 / sandbox-cli-v2 使用指南（企业内部，2026-09-22 核证） |


---

## 措辞与契约修正记录（2026-09-18）

- §3.3 注释「（无云凭据）」改为「（本阶段未执行云联调，火山引擎凭据可用性尚未核验）」。

---

## 云联调实测修正（2026-09-24，project=<project-name> / cn-beijing，系统CLI 0.52.13 + venv SDK agentkit-sdk 0.8.7）

本次在 <project-name> 项目真实创建 CodeEnv 沙箱 Tool 并完成创建→调用→隔离→清理全闭环，实测结论如下，修正/补充上文：

1. **项目归属（重要）**：系统 CLI `agentkit sandbox create` **没有 `-p/--project` 参数**，且 `agentkit tools` 子命令在 0.52.13 不存在。CLI 创建的 Tool 默认落在 `default` 项目。要落到指定项目（如 `<project-name>`），必须走 OpenAPI `CreateTool` 并显式传 `ProjectName=<project-name>`（venv SDK：`AgentkitToolsClient.create_tool(CreateToolRequest(Name=..., ToolType="CodeEnv", ProjectName="<project-name>", CpuMilli=2000, MemoryMb=4096, ...))`）。创建后用 `GetTool(ToolId)` 回读 `ProjectName` 验证归属，不是 <project-name> 立即删除。
2. **CodeEnv 最低规格**：`ToolType=CodeEnv` 时无需 `ImageUrl/Command/Port`（后端自动用 `agentkit-sandbox:codexenv-x.y.z`，`Command=/opt/gem/run.sh`，`Port=8080`）。CPU 2 → `CpuMilli=2000, MemoryMb=4096`。`--enable-snapshot` 不传即 `EnableSnapshot=false`。CodeEnv 创建不强制 `--model-api-key`（shell 执行无需模型注入）。
3. **shell 调用**：`agentkit sandbox shell --tool-id t-xxx --sid <user_sid> --command '...'` 返回 JSON `{success, data:{output, exit_code}}`；同 `--sid` 复用同一实例文件系统，不同 `--sid` 隔离（实测新 sid 看不到旧 sid 的 `/tmp` 文件）。首次调用需数秒建实例。
4. **快照边界**：即使 Tool 创建时 `EnableSnapshot=false`，`CreateSessionSnapshot(ToolId,SessionId)` 仍可成功并返回 `SnapshotId/Status=Ready`；但该手动快照**绑定源 session**——`ResumeSessionFromSnapshot` 要求源 session 不存在（否则 `DuplicateUserSessionId`），而删除源 session 后快照随之 `InvalidSnapshot.NotFound`（级联）。要验证「删实例→从快照恢复」闭环，必须用创建时 `--enable-snapshot=true` 的 Tool。
5. **删除**：`DeleteTool` 是异步的，先进入 `Deleting` 状态，数秒后 `GetTool` 返回 `InvalidResource.NotFound`；先删 session 再删 tool。

实测 Tool（已清理）：`<cleaned-tool-id>` / `<cleaned-sandbox-name>` / ProjectName=<project-name>。
