# 07 Skills

> 概述：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/SkillsOverview?lang=zh
> 集成：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/IntegratingSkillsintoagent?lang=zh

## 概念

Skill 是 Agent 可调用的**能力单元**（封装好的工具/技能）。[PRODUCT] 提供两条路径：
- **智能工坊（Skill 构建）**：创建 → 调试 → 评估 → 注册 Skill。
- **Skills 中心（Skill 管理）**：Skills 空间 = Skill 版本的集合，供运行时/Agent 按版本引用。

## Skills 中心结构

- **Skills 空间（SkillSpace）**：逻辑容器，可添加/移除 Skill、修改版本、删除空间。
- **自定义 Skill**：查看/变更详情/更新/发布/删除。
- **预置 Skill（SharingSkill）**：平台提供，可加入自己的 Skills 空间。
- 2026-09-03 起：上传压缩包创建 Skill 支持批量创建。

## 在 Agent 中集成 Skill

来源：IntegratingSkillsintoagent
- 在 Runtime 创建/编辑时，于"关联组件"中选择已有 Skills 空间，运行时即可按版本调用其中 Skill。
- 也可在代码中通过 [BASE-ADK] 工具（如 `execute_skill`）调用；Skills Sandbox 模板自动具备执行 Skill 的能力。

## Skill API 清单
CreateSkill/UpdateSkill/PublishSkillToSkillSpace/RemoveSkillFromSkillSpace/GetSkill/ListSkills/GetSkillVersion/ListSkillVersions/GetSkillInfo/ListSkillSpacesBySkill/ListSkillsBySkillSpace/GetSharingSkill/ListSharingSkills/GetSharingSkillVersion/ListSharingSkillVersions/ListSkillSpacesBySharingSkill/DeleteSkill；SkillSpace：Create/Update/Get/List/ListSkillsBySpaceId/Delete。
