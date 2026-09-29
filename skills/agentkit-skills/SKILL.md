---
name: agentkit-skills
description: AgentKit Skills（智能工坊 + Skills 中心）——Skill 是 Agent 可调用的能力单元，支持智能工坊构建调试和 Skills 中心版本管理。当需要创建/调试/发布 Skill、管理 SkillSpace、在 Runtime 或 CLI 中挂载 Skill、通过 execute_skill 调用 Skill 时使用本 Skill。
---

# AgentKit Skills（智能工坊与中心）Skill

## 1. 概述

Skill 是 Agent 可调用的**能力单元**（封装好的工具/技能）。AgentKit 提供两条路径：**智能工坊**负责构建 Skill（创建→调试→评估→注册），**Skills 中心**负责管理 Skill 版本（SkillSpace 是 Skill 版本的集合，供运行时/Agent 按版本引用）。Skill 可通过三种方式挂载到 Agent：Hub slug 引用、Space 全量挂载、Space 内指定 Skill 挂载。

## 2. 前置条件

使用本组件前必须满足：
- [ ] 已注册火山引擎账号并开通 AgentKit 服务
- [ ] 已获取 `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY`
- [ ] 已有 Runtime 或 Harness 部署环境
- [ ] 已创建至少一个 SkillSpace（Skills 空间）
- 依赖包：`agentkit-cli`，`veadk-python==1.1.13`
- 环境变量：`VOLCENGINE_REGION=cn-beijing`
- **地域前提（核证 2026-09-22）**：Skills 中心/智能工坊已公测地域为**华北2（北京，cn-beijing）与华东2（上海，cn-shanghai）**；广州开服进行中；BytePlus 侧为亚太（Johor）付费公测。**企业私有 SkillSpace 是 region 级隔离的（北京只能看到北京的企业私有 SkillSpace），公开 Skill 才是 global 的**，跨地域引用私有空间需注意（来源：<internal-lark-doc>

## 3. 快速上手

### 3.1 控制台操作路径

**构建 Skill（智能工坊）：**
1. AgentKit 控制台 → 智能工坊 → 创建 Skill → 编写 Skill 定义（名称、描述、参数 schema）
2. 调试 Skill → 评估 Skill 效果 → 注册到 Skills 中心

**管理 Skill（Skills 中心）：**
1. 创建 Skills 空间（SkillSpace）——Skill 版本的逻辑容器
2. 从智能工坊发布 Skill 到 Space，或把平台预置 SharingSkill 加入 Space
3. 在 Runtime"关联组件"中选择该 Skills 空间

### 3.2 CLI 操作（agentkit-cli 0.52.13 实测）

CLI 0.52.13 的 Skill 相关命令为**只读 + upload/delete**，不支持请求级 `--skills` 挂载，也无独立 `skill-space` 创建命令。

```bash
# 列出所有 Skill
agentkit skill list

# 查看 Skill 详情（含版本）
agentkit skill show <skill-id>

# 查看 Skill 版本历史
agentkit skill versions <skill-id>

# 列出 SkillSpace（只读，CLI 无创建命令）
agentkit skill spaces

# 上传本地 Skill 目录（真实创建 Skill，返回 skill-id）
agentkit skills upload <path-to-skill-dir>

# 删除 Skill
agentkit skill delete <skill-id> -y
```

**SkillSpace 创建与 Skill 绑定**：CLI 0.52.13 不支持，需通过**控制台**（Skills 中心 → 创建空间 → 添加 Skill）或**控制面 OpenAPI**（CreateSkillSpace / PublishSkillToSkillSpace，见 §4 API 清单）完成。

**Skill 挂载到 Runtime**：在 Runtime 创建/编辑页的"关联组件"中选择 Skills 空间（部署期配置），CLI `invoke run` 无 `--skills` 请求级参数。

> 历史/内部版本说明：部分内部操作文档记载了 `agentkit invoke --skills <ref>` 的三种挂载写法（Hub slug / Space 全量 / Space:Skill 指定），该参数依赖内部 CLI 版本，公开 `agentkit-cli 0.52.13` 未暴露。如需请求级 Skill 覆盖，请确认所用 CLI 版本是否支持该参数，或改用 Runtime 关联组件的部署期挂载。

### 3.3 代码集成（execute_skill）
```python
# Runner.run 签名见 ../references/runner-entrypoint.md §3（2026-09-18 results.json 84/84 通过）。
from veadk import Agent, Runner
from agentkit.apps import AgentkitSimpleApp

app = AgentkitSimpleApp()

# Skills Sandbox 模板自动具备执行 Skill 的能力
# 在 Agent 代码中通过 VeADK 工具调用 Skill
agent = Agent(
    name="support_agent",
    instruction="你是企业内部技术支持助手，遇到问题时调用相关 Skill 处理。",
    model_name="<model-name>",
    # Skill 通过 Runtime 关联组件挂载，无需在代码中手动 import（详见 §10.5：须传 skills=[...] 才触发 load_skills）
)

runner = Runner(agent=agent)

# 非流式（推荐）：runner.run(messages=) 返回字符串；SSE 流式见共享 reference §4。
@app.entrypoint
async def run(payload, headers):
    result = await runner.run(
        messages=payload["prompt"],
        user_id=headers["user_id"],
        session_id=headers["session_id"],
    )
    return result

app.run(host="0.0.0.0", port=8000)
```

### 3.4 批量创建 Skill（2026-09-03起）

支持上传压缩包批量创建 Skill，适合从已有 Skill 仓库批量迁移。

## 4. 核心概念与 API

| 概念 | 说明 | 关键参数 |
|---|---|---|
| SkillSpace（Skills 空间） | Skill 版本的逻辑容器 | 可添加/移除 Skill、修改版本、删除空间 |
| 自定义 Skill | 用户自行构建的 Skill | 查看/变更详情/更新/发布/删除 |
| SharingSkill（预置 Skill） | 平台提供的共享 Skill | 可加入自己的 Skills 空间 |
| Skill 版本 | 每次发布生成新版本 | 按版本引用，稳定可复现 |
| execute_skill | VeADK 中调用 Skill 的工具方法 | 在 Agent 代码中通过工具调用 |

### 三种 Skill 挂载方式（平台概念，非 CLI 命令）

| 来源 | 引用格式 | 配置位置 | 粒度 |
|---|---|---|---|
| Skill Hub | `clawhub/作者/skill-name` | 内部 CLI 版本 `--skills` 参数（公开 0.52.13 不支持） | 单 Skill |
| Skill Space 全量 | `ss-<space-id>` | Runtime 关联组件（部署期） | 空间全部 |
| Space 内指定 Skill | `ss-<space-id>:s-<skill-id>` | 内部 CLI 版本 `--skills` 参数（公开 0.52.13 不支持） | 单 Skill |

> 公开 CLI 0.52.13 仅支持 Runtime 关联组件的部署期挂载（Space 全量）。Hub slug 和 Space:Skill 指定格式依赖内部 CLI 版本的 `--skills` 请求级参数。

### 关键环境变量

| 变量名 | 用途 | 是否必填 |
|---|---|---|
| `VOLCENGINE_ACCESS_KEY` | 火山引擎访问密钥 ID | 是 |
| `VOLCENGINE_SECRET_KEY` | 火山引擎 secret 访问密钥 | 是 |
| `VOLCENGINE_REGION` | 地域（cn-beijing） | 是 |

### Skill API 清单（Version 2025-10-30）

| 分类 | API |
|---|---|
| Skill 管理 | CreateSkill / UpdateSkill / GetSkill / ListSkills / DeleteSkill |
| Skill 版本 | GetSkillVersion / ListSkillVersions |
| Skill 发布到 Space | PublishSkillToSkillSpace / RemoveSkillFromSkillSpace |
| Skill 信息 | GetSkillInfo |
| SkillSpace 管理 | CreateSkillSpace / UpdateSkillSpace / GetSkillSpace / ListSkillSpaces / ListSkillsBySpaceId / DeleteSkillSpace |
| SharingSkill | GetSharingSkill / ListSharingSkills / GetSharingSkillVersion / ListSharingSkillVersions / ListSkillSpacesBySharingSkill / ListSkillSpacesBySkill |
| Skill 与 Space 关联 | ListSkillSpacesBySkill / ListSkillsBySkillSpace |

## 5. 输入输出规范

### 输入
- Skill 调用时的参数：由 Skill 自身的 JSON schema 定义
- 部署期配置：Runtime 创建/编辑时关联 Skills 空间（CLI 0.52.13 无请求级 `--skills` 参数）
- 内部 CLI 版本的 `--skills` 参数：逗号分隔的 Skill 引用列表（Hub slug / Space ID / Space:Skill 组合），公开 0.52.13 不支持

### 输出
- Skill 执行结果：按 Skill 定义返回
- 内部 CLI 版本 `--skills` 请求级覆盖返回 `overwrite: true`（公开 0.52.13 无此返回）
- 注意：`description`、`structured tool calls`、`tool context`、知识库、记忆属于创建/部署期配置

## 6. 权限与安全

- **所需 IAM 权限**：AgentKit Skill 管理权限（创建/发布/删除）
- **入站认证**：通过 Runtime 网关（API Key / SSO）
- **出站凭据**：Skill 内部如需访问外部服务，凭据由网关/Identity 托管
- **Skill Hub 边界**：Skill Hub 只分发 Skill 内容（代码/定义），**不自动提供 Skill 声明的 MCP**——Skill 依赖的 MCP 工具需另行配置
- **生产建议**：通过 Runtime 关联组件挂载 Skills 空间时，优先使用包含最小必要 Skill 的空间，避免全量挂载带来的指令冲突和外部依赖不确定性；内部 CLI 版本可用 `ss-<space-id>:s-<skill-id>` 指定方式

## 7. 失败处理与排障

| 错误现象 | 可能原因 | 处理方式 |
|---|---|---|
| Skill 未生效 | Runtime 未关联 Skills 空间，或 Agent 代码未传 `skills` 字段 | 控制台 → Runtime 编辑 → 关联组件 → 选择 Skills 空间 → 重新发布；**代码层面**：Agent 构造必须传 `skills=[os.getenv("SKILL_SPACE_ID")]`，否则 `skills=[]` 不触发 `load_skills()` |
| Skill 调用了 MCP 但报错 | Skill Hub 未分发 MCP 依赖 | 手动配置 Skill 所需的 MCP 工具集，关联到 Runtime |
| 多 Skill 挂载冲突 | 指令冲突或外部依赖重复 | 缩小 Space 范围；拆分不同场景用不同 Skill 组合 |
| 批量创建失败 | 压缩包格式不规范 | 检查压缩包结构是否符合 Skill 规范（2026-09-03起支持） |
| `agentkit invoke --skills` 报 unknown option | 公开 CLI 0.52.13 不支持该参数 | 改用 Runtime 关联组件部署期挂载，或确认是否使用内部 CLI 版本 |

排障路径：确认 Runtime 已关联 Skills 空间 → 检查 Skill 调试页面 → 确认 MCP 依赖已配置 → 查看 Agent 日志

## 8. 可执行验证办法

1. **上传 Skill（CLI）**：
```bash
agentkit skills upload <path-to-skill-dir>
# 记录返回的 skill-id
```
2. **查看 Skill 详情与版本**：
```bash
agentkit skill show <skill-id>
agentkit skill versions <skill-id>
```
3. **列出 SkillSpace（只读）**：
```bash
agentkit skill spaces
```
4. **Runtime 关联 Skills 空间（控制台）**：Runtime 编辑 → 关联组件 → 选择 Skills 空间 → 重新发布
5. **调用 Runtime 验证 Skill 生效**：通过 Runtime `/invoke` 发送触发 Skill 的 prompt，确认 Agent 调用了预期 Skill
6. **清理**：
```bash
agentkit skill delete <skill-id> -y
```

> SkillSpace 创建、Skill 发布到 Space、Space 绑定 Runtime 需通过控制台或控制面 OpenAPI（CreateSkillSpace / PublishSkillToSkillSpace）完成，CLI 0.52.13 不支持这些操作。

## 9. 与其他组件的关系

- **上游依赖**：智能工坊（Skill 构建）、Skills 中心（版本管理）、Runtime（执行环境）
- **下游联动**：Agent 对话（自动选择并调用 Skill）、观测（Skill 调用 trace）
- **常见组合**：
  - Runtime 关联 Skills 空间 + 知识库 = 企业 SOP + 知识问答 Agent
  - Skill Space 全量挂载 + Agent 自选 = 灵活的能力扩展
  - Space 指定 Skill + 生产 Runtime = 稳定可控的最小能力集
  - Skills Sandbox 模板 = 自动具备 Skill 执行能力

## 10. 已知限制与注意事项

- **Skill Hub 不分发 MCP**：通过 Hub 安装的 Skill 只获得 Skill 定义和代码，其声明依赖的 MCP 工具需自行在 Runtime 关联组件中配置
- 多 Skill 同空间挂载时，注意指令与外部依赖可能冲突
- Runtime 关联组件的部署期挂载在重新发布后生效
- `description`、`structured tool calls`、`tool context`、知识库、记忆属于创建/部署期配置
- 批量创建 Skill 功能自 2026-09-03 起上线
- **CLI 限制（0.52.13 实测）**：无 `--skills` 请求级挂载参数；无 `skill-space` 独立创建命令；SkillSpace 创建/绑定需控制台或 OpenAPI
- **地域**：已公测华北2（北京）/华东2（上海）；企业私有 SkillSpace 按 region 隔离，公开 Skill 为 global；详见 §2 地域前提
- **Quota（单账号单地域，核证 2026-09-22）**：Skill 400、SkillSpace 40、单 SkillSpace 下绑定 Skill 50（BytePlus 同）（来源：企业内部售前速查指南）
- Skills Sandbox 模板自动具备执行 Skill 的能力，无需额外配置

## 10.5 实测校正（2026-09-24 <project-name>/<region> 端到端验证）

> 备份见 `_backup/cloud-validation/SKILL.md.bak-20260924`。以下为控制面 OpenAPI 实测，与前文措辞有出入时以本节为准。

- **命名规则**：SkillSpace `Name` 只允许小写字母/数字/下划线（`<space-naming-example>`）；Skill `Name` 只允许小写字母/数字/连字符（`<skill-naming-example>`）。
- **CreateSkill**：`{Name, ProjectName, TosUrl, Description?}`，TosUrl 指向已上传 ZIP（含 SKILL.md），返回 `{Id, Version:"v1"}`。`ProjectName` 显式传 <project-name> 才会落 <project-name>（CLI `skills upload -p` 映射 TOS 项目，会落 default）。
- **PublishSkillToSkillSpace 真实请求体**：不是单 `SkillId/SkillSpaceId`，而是 `{"SkillSpaces":["ss-..."], "Skills":[{"SkillId":"s-...","Version":"v1"}]}`（`SkillSpaces` 为 `[]string`，`Skills` 为对象数组）。
- **SkillSpace 绑定 Runtime 的真相**：
  - CLI `runtime update` 0.52.13 **无** `--skill-id/--skill-space-id`（只有 knowledge/memory/tool/mcp-toolset）。
  - OpenAPI `UpdateRuntime` 的 `SkillSpaceId` 字段会被**静默忽略**（实测 v1 与 v2 diff 无任何字段变化），不是真实绑定。
  - veADK 侧实际消费方式是环境变量：harness 镜像读 `SKILLS=space:<skillspace-id>`；sandbox 宿主读 `SKILL_SPACE_ID=<id>` + `AGENTKIT_TOOL_ID=<skill-type-tool-id>`。
  - **~~关键限制（已修复 2026-09-24）~~**：共享 `full-feature-agent` 静态镜像原启动日志固定 `skills=[] tools=[]`，不读 env 自动加载 skills。**根因是 agent.py 构造 Agent 时未传 `skills` 字段**，导致 `Agent.skills=[]` → 不触发 `load_skills()` → 无 `SkillsToolset` 注册。
  - **修复方式（execute_skill 真实接入）**：在 agent.py 的 Agent 构造中添加 `skills` 字段，从环境变量 `SKILL_SPACE_ID` 读取：

```python
_skill_space_id = os.getenv("SKILL_SPACE_ID", "").strip()
if _skill_space_id:
    agent_kwargs["skills"] = [_skill_space_id]
```

    - Agent 初始化时自动检测 `if self.skills: self.load_skills()`，无 `AGENTKIT_TOOL_ID` 时 `skills_mode="local"`。
    - local 模式：启动时调 `ListSkillsBySpaceId` 拉取 space 内已发布 skill 列表，注册 `SkillsToolset`；调用时模型触发 `skills_tool`，再从 TOS 下载 SKILL.md 包并执行。
    - 容器内 AK/SK 由 VeFaaS IAM sidecar 自动注入，无需手动配置。
  - **部署方式**：`runtime update --artifact-url <新镜像> --envs-json '[{"Key":"SKILL_SPACE_ID","Value":"ss-..."}]' --auto-release`。
  - **版本更新生效条件**：`UpdateSkill` + `PublishSkillToSkillSpace` 后，需 Runtime 重新部署（env 变更触发新 deploy）才能重新 `ListSkillsBySpaceId` 获取最新 published 版本；`enable_dynamic_load_skills=False`（默认）时不热刷新。
- **版本更新**：`UpdateSkill {Id, ProjectName, TosUrl(新包)}` 返回新版本号（v1→v2），再 `PublishSkillToSkillSpace` 带新 Version 发布到 space。
- **清理**：DeleteSkill / DeleteSkillSpace / DeleteTool 后 Get 均 404 `ResourceNotFound.*`。
- **execute_skill 端到端验证（2026-09-24 <project-name>）**：修复 agent.py 后，Runtime invoke 返回 skill 定义的 marker 字符串（v1→v2 版本更新闭环验证通过）。日志全链路：`[SKILLS] skills configured` → `Determined skills_mode: local` → `ListSkillsBySpaceId` → `Successfully loaded skill` → 模型调用 `skills_tool` → TOS 下载 package.zip → `Invoke skill successfully` → 返回 SKILL.md 内容。

## 11. 来源追溯

| 信息点 | 来源 URL | 文档章节 |
|---|---|---|
| Skill 概念与两条路径 | https://docs.volcengine.com/docs/AgentKit/SkillsOverview?lang=zh | Skills 概述 |
| Skills 中心结构（SkillSpace/自定义/SharingSkill） | https://docs.volcengine.com/docs/AgentKit/SkillsOverview?lang=zh | Skills 概述 |
| 在 Agent 中集成 Skill（Runtime 关联 + execute_skill） | https://docs.volcengine.com/docs/AgentKit/IntegratingSkillsintoagent?lang=zh | 在 Agent 中集成 Skills |
| 三种挂载方式与实测样例 | <internal-lark-doc> | AgentKit & VeADK：从 Demo 到 Production（三种 Skill 挂载方式） |
| Skill Hub 不分发 MCP | <internal-lark-doc> | AgentKit & VeADK：从 Demo 到 Production（依赖边界） |
| 批量创建（2026-09-03起） | https://docs.volcengine.com/docs/AgentKit/SkillsOverview?lang=zh | Skills 概述（更新说明） |
| Skill API 清单 | https://docs.volcengine.com/docs/AgentKit/SkillsOverview?lang=zh | API 参考 |
| 已公测地域（北京/上海）与私有空间 region 隔离（核证 2026-09-22） | <internal-lark-doc> | AgentKit Skills One Page |
| 私有 SkillSpace region 级隔离、公开 Skill global（核证 2026-09-22） | <internal-lark-doc>/threads/7626666171135232967 | 企业版内测跟进群（0409） |
| Skill/SkillSpace/绑定数 Quota（核证 2026-09-22） | <internal-lark-doc> | AgentKit 售前速查指南 |
