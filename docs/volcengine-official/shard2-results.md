# 火山引擎 [PRODUCT] 官方文档 API参考分片2 读取结果

> 抓取时间：2026-09-18
> 基础URL：`https://docs.volcengineapi.com`（实际API域名）
> API版本统一：`Version=2025-10-30`
> 说明：以下每页均通过 web.fetch 分页读取，因页面较短均为单页读完（total_length 已返回），无二次分页。

---

## 1. 删除 Skill（控制台操作页，非API）

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/DeleteSkillCreateTask?lang=zh
- **读取范围**: 0–1147 / 1147（已到底）
- **异常**: 无
- **正文摘要**: 控制台操作指南，非REST API。说明智能工坊创建的Skill任务24小时后自动删除，可手动删除。无请求/响应参数。

---

## 2. CreateSkill - 创建Skill

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/CreateSkill-CreateaSkill?lang=zh
- **读取范围**: 0–695 / 695（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选 — 固定值 CreateSkill
  - `Version` string 必选 — 2025-10-30
  - `Name` string 可选 — Skill名称，最多64字符，小写字母/数字/连字符，不能含XML标签，不能用保留字 [PRODUCT]；不传则从SKILL.md解析
  - `Description` string 可选 — Skill描述，最多1024字符
  - `TosUrl` string 必选 — Skill.md ZIP在TOS中的地址
  - `SkillSpaces` string[] 可选 — 加入的Skill空间ID列表
  - `ProjectName` string 可选 — 所属项目名，默认 default
  - `Tags` object[] 可选 — 标签数组，含 `Key`（必选）、`Value`（必选）
- **返回参数**:
  - `Id` string — Skill ID（如 `<RESOURCE_ID>***`）
  - `Tags` object[] — 标签详情
- **错误码**: 公共错误码（无业务专属错误码表）

---

## 3. UpdateSkill - 更新Skill

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/UpdateSkill-UpdatesSkill?lang=zh
- **读取范围**: 0–574 / 574（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选 — UpdateSkill
  - `Version` string 必选 — 2025-10-30
  - `Id` string 必选 — Skill ID
  - `Name` string 可选 — Skill名称，规则同CreateSkill
  - `Description` string 可选 — 描述
  - `TosUrl` string 必选 — Skill.md ZIP的TOS地址
  - `SkillSpaces` string[] 可选 — 加入的Skill空间
- **返回参数**: 本接口无特有返回参数（Result为空对象 `{}`）
- **错误码**: 公共错误码

---

## 4. PublishSkillToSkillSpace - 发布Skill到Skills空间

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/PublishSkillToSkillSpace-PublishesSkilltoaSkillsspace?lang=zh
- **读取范围**: 0–344 / 344（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选 — PublishSkillToSkillSpace
  - `Version` string 必选 — 2025-10-30
  - `SkillSpaces` string[] 必选 — Skills空间ID，支持多个
  - `Skills` object[] 必选 — Skill信息数组
    - `SkillId` string 必选
    - `Version` string 必选 — Skill版本号
- **返回参数**: 无特有返回参数（Result为 `{}`）
- **错误码**: 公共错误码

---

## 5. RemoveSkillFromSkillSpace - 将Skill从Skills空间移除

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/RemoveSkillFromSkillSpace-RemovesSkillfromaSkillsspace?lang=zh
- **读取范围**: 0–303 / 303（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `SkillId` string 必选 — Skill ID
  - `SkillSpaceId` string 必选 — Skills空间ID
- **返回参数**: 无特有返回参数
- **错误码**: 公共错误码

---

## 6. GetSkill - 查询Skill详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetSkill-QueriesSkilldetails?lang=zh
- **读取范围**: 0–537 / 537（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选 — GetSkill
  - `Version` string 必选 — 2025-10-30
  - `Id` string 必选 — Skill ID
- **返回参数**:
  - `Id` string — Skill ID
  - `Name` string — Skill名称
  - `Status` string — 状态：creating / failed / updating / running
  - `Description` string — 描述
  - `Versions` string[] — 版本号列表
  - `CreateTimeStamp` string — 创建时间（Unix时间戳）
  - `UpdateTimeStamp` string — 更新时间
  - `ProjectName` string — 所属项目
  - `Tags` object[] — 标签（Key/Value）
- **错误码**: 公共错误码

---

## 7. ListSkills - 批量查询Skill详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListSkills-BatchqueriesdetailsofmultipleSkills?lang=zh
- **读取范围**: 0–40 / 40（已到底）
- **异常**: 页面正文为空，仅有导航标题，无任何请求/响应参数文档
- **正文摘要**: 标题"ListSkills - 批量查询Skill详情"，正文缺失（仅有导航面包屑）

---

## 8. GetSkillVersion - 查询Skill版本详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetSkillVersion-QueriesdetailsofaSkillversion?lang=zh
- **读取范围**: 0–649 / 649（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选 — GetSkillVersion
  - `Version` string 必选 — 2025-10-30
  - `Id` string 必选 — Skill ID
  - `SkillVersion` string 可选 — 版本号，不传默认最新
- **返回参数**:
  - `Id` / `Name` / `Status`（creating/running/failed）/ `Description` / `Version`
  - `CreateTimeStamp` / `UpdateTimeStamp`（Unix时间戳）
  - `SkillMd` string — Skill markdown文件详情
  - `TosPath` string — ZIP在TOS中的地址
  - `BucketName` string — TOS桶名
- **错误码**: 公共错误码

---

## 9. ListSkillVersions - 批量查询Skill的版本信息

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListSkillVersions-BatchqueriesSkillversioninformation?lang=zh
- **读取范围**: 0–766 / 766（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `Id` string 必选 — Skill ID
  - `PageNumber` integer 可选 — 当前页码，起始1，默认1
  - `PageSize` integer 可选 — 每页行数，1~100，默认10
- **返回参数**:
  - `TotalCount` integer — 总个数
  - `Items` object[] — 版本详情
    - `Id` / `Name` / `Status` / `Description` / `Version`
    - `CreateTimeStamp` / `UpdateTimeStamp`
    - `Relations` object[] — 关联的Skill和Skills空间详情（SkillStatus, SkillSpaceId, SkillSpaceName, SkillSpaceDescription, SkillSpaceStatus, SkillId, SkillName, Version, SkillDescription）
- **错误码**: 公共错误码

---

## 10. GetSkillInfo - 查询Skill加入某个Skills空间的版本详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetSkillInfo-QueriestheversiondetailsofaSkilladdedtoaSkillsspace?lang=zh
- **读取范围**: 0–509 / 509（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `SkillName` string 必选 — Skill名称
  - `SkillSpaceId` string 必选 — Skill空间ID
- **返回参数**:
  - `BucketName` / `SkillName` / `Description` / `SkillMd` / `TosPath`
- **错误码**: 公共错误码

---

## 11. ListSkillSpacesBySkill - 查询Skill已加入的Skills空间详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListSkillSpacesBySkill-QueriesdetailsoftheSkillsspacestowhichaSkillhasbeenadded?lang=zh
- **读取范围**: 0–803 / 803（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `SkillId` string 必选
  - `SkillVersion` string 可选 — 不传默认所有版本
  - `PageNumber` integer 可选 — 默认1
  - `PageSize` integer 可选 — 1~100，默认10
  - `Filter` object 可选 — 过滤条件
    - `Status` string[] 可选 — creating / running
    - `Id` string 可选 — 空间ID
    - `Name` string 可选 — 空间名称
- **返回参数**:
  - `Items` object[] — SkillStatus, SkillSpaceId, SkillSpaceName, SkillSpaceDescription, SkillSpaceStatus, SkillId, SkillName, Version, SkillDescription
  - `TotalCount` integer
- **错误码**: 公共错误码

---

## 12. ListSkillsBySkillSpace - 查询Skills空间已添加的Skill版本详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListSkillsBySkillSpace-QueriesversiondetailsofaSkillinaspecificspace?lang=zh
- **读取范围**: 0–689 / 689（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `SkillSpaceId` string 必选 — 空间ID
  - `PageSize` integer 可选 — 1~100，默认10
  - `PageNumber` integer 可选 — 起始1，默认1
  - `Filter` object 可选
    - `Status` string[] 可选 — creating/running/failed
    - `Id` string 可选 — Skill ID
    - `Name` string 可选 — Skill名称
- **返回参数**:
  - `Items` object[] — SkillStatus, SkillSpaceId, SkillSpaceName, SkillSpaceDescription, SkillSpaceStatus, SkillId, SkillName, Version, SkillDescription
  - `TotalCount` integer
- **错误码**: 公共错误码

---

## 13. GetSharingSkill - 查询预置Skill详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetSharingSkill-QueriespresetSkilldetails?lang=zh
- **读取范围**: 0–630 / 630（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选 — GetSharingSkill
  - `Version` string 必选 — 2025-10-30
  - `Id` string 必选 — Skill ID
- **返回参数**: 同GetSkill（Id, Name, Status, Description, Versions, CreateTimeStamp, UpdateTimeStamp, ProjectName, Tags）
- **错误码**:
  - 404 ResourceNotFound — 找不到对应资源
  - 500 InternalError — 内部错误

---

## 14. ListSharingSkills - 批量查询共享Skill详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListSharingSkills-BatchqueriessharedSkilldetails?lang=zh
- **读取范围**: 0–55 / 55（已到底）
- **异常**: 页面正文为空，仅有导航标题
- **正文摘要**: 标题存在，无任何参数文档

---

## 15. GetSharingSkillVersion - 查询预置Skill版本详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetSharingSkillVersion-QueriespresetSkillversiondetails?lang=zh
- **读取范围**: 0–767 / 767（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `Id` string 必选 — Skill ID
  - `SkillVersion` string 可选 — 不传默认最新
- **返回参数**: 同GetSkillVersion（Id, Name, Status, Description, Version, CreateTimeStamp, UpdateTimeStamp, SkillMd, TosPath, BucketName）
- **错误码**:
  - 400 InvalidParameter — 请求参数不合法
  - 404 ResourceNotFound — 找不到资源
  - 500 InternalError — 内部错误

---

## 16. ListSharingSkillVersions - 批量查询预置Skill的版本信息

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListSharingSkillVersions-BatchqueriespresetSkillversioninformation?lang=zh
- **读取范围**: 0–773 / 773（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `Id` string 必选 — Skill ID
  - `PageNumber` integer 可选 — 默认1
  - `PageSize` integer 可选 — 1~100，默认10
- **返回参数**: 同ListSkillVersions（TotalCount, Items含Relations）
- **错误码**: 无业务专属错误码表

---

## 17. ListSkillSpacesBySharingSkill - 查询预置Skill已加入的Skills空间详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListSkillSpacesBySharingSkill-QueriesdetailsoftheSkillsspacestowhichapresetSkillhasbeenadded?lang=zh
- **读取范围**: 0–815 / 815（已到底）
- **异常**: 无
- **请求参数**: 同ListSkillSpacesBySkill（SkillId必选, SkillVersion可选, PageNumber, PageSize, Filter含Status/Id/Name）
- **返回参数**: 同ListSkillSpacesBySkill（Items, TotalCount）
- **错误码**: 公共错误码

---

## 18. DeleteSkill - 删除Skill

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/DeleteSkill-DeletesaSkill?lang=zh
- **读取范围**: 0–255 / 255（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选 — DeleteSkill
  - `Version` string 必选 — 2025-10-30
  - `Id` string 必选 — Skill ID
- **返回参数**: 无特有返回参数（Result为 `{}`）
- **错误码**: 公共错误码

---

## 19. CreateSkillSpace - 创建Skills空间

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/CreateSkillSpace-CreatesaSkillsspace?lang=zh
- **读取范围**: 0–524 / 524（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `Name` string 必选 — 空间名称，最多64字符，小写字母/数字/连字符，不能用 [PRODUCT]
  - `Description` string 可选 — 描述，最多1024字符
  - `Skills` object[] 可选 — 添加的Skill（SkillId必选, Version必选）
  - `ProjectName` string 可选
  - `Tags` object[] 可选（Key必选, Value必选）
- **返回参数**:
  - `Id` string — 空间ID（如 `<RESOURCE_ID>***`）
  - `Tags` object[]
- **错误码**: 公共错误码

---

## 20. UpdateSkillSpace - 更新Skills空间

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/UpdateSkillSpace-UpdatesSkillsspace?lang=zh
- **读取范围**: 0–341 / 341（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `Id` string 必选 — 空间ID
  - `Name` string 可选 — 名称，规则同CreateSkillSpace
  - `Description` string 可选 — 描述，最多1024字符
- **返回参数**: 无特有返回参数
- **错误码**: 公共错误码

---

## 21. GetSkillSpace - 查询Skills空间详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetSkillSpace-QueriesdetailsofaSkillsspace?lang=zh
- **读取范围**: 0–476 / 476（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `Id` string 必选 — 空间ID
- **返回参数**:
  - `Id` / `Name` / `Status`（creating/running）/ `Description`
  - `CreateTimeStamp` / `UpdateTimeStamp`
  - `ProjectName` / `Tags`
- **错误码**: 公共错误码

---

## 22. ListSkillSpaces - 批量查询Skills空间详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListSkillSpaces-BatchqueriesSkillsspacedetails?lang=zh
- **读取范围**: 0–926 / 926（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `PageNumber` integer 可选 — 默认1
  - `PageSize` integer 可选 — 1~100，默认10
  - `Filter` object 可选 — Status string[], Name string, Id string
  - `ProjectName` string 可选
  - `TagFilters` object[] 可选 — Key必选, Values string[]必选
- **返回参数**:
  - `TotalCount` integer
  - `Items` object[] — Id, Name, Status, Description, CreateTimeStamp, UpdateTimeStamp, Relations(SkillSpaceId/SkillId/SkillName/SkillDescription/SkillStatus/Version), ProjectName, Tags
- **错误码**: 公共错误码

---

## 23. ListSkillsBySpaceId - 通过Skills空间查询已添加Skill的基本信息

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListSkillsBySpaceId-QuerybasicinformationofaddedskillsthroughSkillsspace?lang=zh
- **读取范围**: 0–334 / 334（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `SkillSpaceId` string 必选 — 空间ID
- **返回参数**:
  - `Items` object[] — Name, Description
- **错误码**: 公共错误码

---

## 24. DeleteSkillSpace - 删除Skills空间

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/DeleteSkillSpace-DeletesSkillsspace?lang=zh
- **读取范围**: 0–266 / 266（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `Id` string 必选 — 空间ID
- **返回参数**: 无特有返回参数
- **错误码**: 公共错误码

---

## 25. CreateA2aSpace - 创建A2A智能体空间

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/CreateA2aSpace-CreatesanA2Aagentspace?lang=zh
- **读取范围**: 0–660 / 660（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `Name` string 必选 — 空间名称
  - `IntentEnabled` boolean 可选 — 是否开启语义检索，默认false
  - `Tags` object[] 可选（Key必选, Value必选）
  - `ProjectName` string 可选
- **返回参数**:
  - `Id` string — 空间ID（如 `<RESOURCE_ID>***`）
  - `Tags` object[]
- **错误码**:
  - 400 InvalidParameter — 参数不合法
  - 403 AccessDenied — 无权限
  - 500 InternalError — 内部错误

---

## 26. UpdateA2aSpace - 更新A2A智能体空间

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/UpdateA2aSpace-UpdatesanA2Aagentspace?lang=zh
- **读取范围**: 0–572 / 572（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `Id` string 必选 — 空间ID
  - `Name` string 可选
  - `IntentEnabled` boolean 可选
  - `Tags` object[] 可选（Key必选, Value必选）
- **返回参数**: 无特有返回参数
- **错误码**:
  - 403 AccessDenied
  - 404 ResourceNotFound
  - 500 InternalError

---

## 27. ListA2aSpaces - 批量查询A2A智能体空间

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListA2aSpaces-BatchqueriesA2Aagentspaces?lang=zh
- **读取范围**: 0–794 / 794（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `PageNumber` integer 可选 — 默认1
  - `PageSize` integer 可选 — 1~100，默认10
  - `ProjectName` string 可选
  - `TagFilters` object[] 可选 — Key必选, Values string[]必选
- **返回参数**:
  - `TotalCount` integer
  - `Items` object[] — Id, Name, IntentEnabled, ProjectName, Tags, IsDefault（boolean，是否默认空间）
- **错误码**:
  - 403 AccessDenied
  - 500 InternalError

---

## 28. GetA2aSpace - 查询A2A智能体空间详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetA2aSpace-QueriesdetailsofanA2Aagentspace?lang=zh
- **读取范围**: 0–648 / 648（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `Id` string 必选 — 空间ID
- **返回参数**: 同ListA2aSpaces Items字段（Id, Name, IntentEnabled, ProjectName, Tags, IsDefault）
- **错误码**:
  - 403 AccessDenied
  - 500 InternalError

---

## 29. DeleteA2aSpace - 删除A2A智能体空间

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/DeleteA2aSpace-DeletesanA2Aagentspace?lang=zh
- **读取范围**: 0–419 / 419（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `Id` string 必选 — 空间ID
- **返回参数**: 无特有返回参数
- **错误码**:
  - 403 AccessDenied
  - 500 InternalError

---

## 30. CreateA2aAgent - 创建A2A智能体

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/CreateA2aAgent-CreatesanA2Aagent?lang=zh
- **读取范围**: 0–1646 / 1646（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `Source` string 必选 — 注册来源：Runtime / Standard
  - `A2aSpaceId` string 必选 — 空间ID
  - `AgentCard` string 可选 — Standard时必填，AgentCard JSON文本
  - `RuntimeConfig` object 可选 — Runtime时必填
    - `RuntimeId` string 必选 — 运行时ID
    - `NetworkType` string 必选 — private / public
  - `ProjectName` string 可选
  - `Tags` object[] 可选（Key必选, Value必选）
  - `SetDefaultVersion` boolean 可选 — 是否设为默认版本
  - `StandardConfig` object 可选 — Standard时必填
    - `ImportType` string 必选 — json / url
    - `AgentCardUrl` string 可选 — AgentCard地址（ImportType为url时填写）
  - `EnableProxy` boolean 可选
  - `ProxyConfig` object 可选
    - `NetworkConfiguration` object 必选
      - `NetworkType` string 必选 — private/public
      - `VpcConfiguration` object 可选 — VpcId, SubnetIds[]
    - `InboundAuthorizerConfiguration` object 必选
      - `AuthorizerType` string 必选 — KEY_AUTH/OAUTH/NONE
      - `Authorizer` object 可选
        - `KeyAuth` object 可选 — ApiKeys[]必选, ApiKeyLocation可选(HEADER/URL), ApiKeyLocationKey可选
        - `JWTAuthorizer` object 可选 — DiscoveryUrl可选, AllowedClients[]可选
- **返回参数**:
  - `Id` string — A2A智能体ID（如 `<RESOURCE_ID>***`）
  - `Tags` object[]
- **错误码**:
  - 403 AccessDenied
  - 500 InternalError

---

## 31. UpdateA2aAgent - 更新A2A智能体

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/UpdateA2aAgent-UpdatesanA2Aagent?lang=zh
- **读取范围**: 0–1058 / 1058（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `Id` string 必选 — 智能体ID
  - `Source` string 必选 — Runtime / Standard
  - `A2aSpaceId` string 必选 — 空间ID
  - `AgentCard` string 可选 — Standard+JSON时必填
  - `RuntimeConfig` object 可选 — Runtime时必填（RuntimeId必选, NetworkType必选）
  - `ProjectName` string 可选
  - `Tags` object[] 可选
  - `SetDefaultVersion` boolean 可选
  - `StandardConfig` object 可选 — Standard时必填（ImportType必选: json/url, AgentCardUrl可选）
- **返回参数**: 无特有返回参数
- **错误码**:
  - 403 AccessDenied
  - 500 InternalError

---

## 32. ListA2aAgents - 批量查询A2A智能体

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListA2aAgents-BatchqueriesA2Aagents?lang=zh
- **读取范围**: 0–1089 / 1089（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `PageNumber` integer 可选 — 默认1
  - `PageSize` integer 可选 — 1~100，默认10
  - `Filter` object 可选
    - `Id` / `Name` / `Version` / `Skill` string 可选
    - `Source` string[] 可选 — Runtime/Standard
  - `SpaceId` string 必选 — 空间ID
  - `ProjectName` string 可选
  - `TagFilters` object[] 可选 — Key必选, Values[]必选
- **返回参数**:
  - `TotalCount` integer
  - `Items` object[] — Id, Name, Source, DefaultVersion, Host, Capabilities[], Skills[], CreateTimeStamp, UpdateTimeStamp, Status(running/failed), Reason
- **错误码**:
  - 403 AccessDenied
  - 500 InternalError

---

## 33. GetA2aAgent - 查询A2A智能体详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetA2aAgent-QueriesdetailsofanA2Aagent?lang=zh
- **读取范围**: 0–1197 / 1197（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `Id` string 可选 — 智能体ID
  - `Name` string 可选 — 名称
  - `SpaceId` string 必选 — 空间ID
  - `RuntimeId` string 可选 — 运行时ID
- **返回参数**:
  - `Id` / `Source` / `A2aSpaceId` / `AgentCard`
  - `RuntimeConfig` — RuntimeId, NetworkType
  - `ProjectName` / `Tags` / `DefaultVersion` / `Status`(running/failed)
  - `StandardConfig` — ImportType, AgentCardUrl
  - `Name` / `OriginalAgentCard` / `Reason`
- **错误码**:
  - 400 InvalidParameter
  - 403 AccessDenied
  - 404 ResourceNotFound
  - 500 InternalError

---

## 34. DeleteA2aAgent - 删除A2A智能体

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/DeleteA2aAgent-DeletesanA2Aagent?lang=zh
- **读取范围**: 0–418 / 418（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `Id` string 必选 — 智能体ID
- **返回参数**: 无特有返回参数
- **错误码**:
  - 403 AccessDenied
  - 500 InternalError

---

## 35. ListA2aAgentVersions - 批量查询A2A智能体版本

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListA2aAgentVersions-BatchqueriesA2Aagentversions?lang=zh
- **读取范围**: 0–637 / 637（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `Id` string 必选 — 智能体ID
  - `PageNumber` integer 可选 — 默认1
  - `PageSize` integer 可选 — 1~100，默认10
- **返回参数**:
  - `TotalCount` integer
  - `Items` object[] — Version, CreateTimeStamp, UpdateTimeStamp, Status(running/failed), ErrorMessage
- **错误码**:
  - 404 ResourceNotFound
  - 500 InternalError

---

## 36. GetA2aAgentVersion - 查询A2A智能体版本详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetA2aAgentVersion-QueriesversiondetailsofanA2Aagent?lang=zh
- **读取范围**: 0–529 / 529（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `Id` string 必选 — 智能体ID
  - `AgentVersion` string 必选 — 版本号
- **返回参数**:
  - `AgentCard` string — AgentCard JSON文本
  - `Status` string — running/failed
  - `ErrorMessage` string
- **错误码**:
  - 404 ResourceNotFound
  - 500 InternalError

---

## 37. DeleteA2aAgentVersion - 删除A2A智能体版本

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/DeleteA2aAgentVersion-DeletesanA2Aagentversion?lang=zh
- **读取范围**: 0–452 / 452（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `Id` string 必选 — 智能体ID
  - `AgentVersion` string 必选 — 版本号
- **返回参数**: 无特有返回参数
- **错误码**:
  - 404 ResourceNotFound
  - 500 InternalError

---

## 38. SearchAgentCards - 通过语义检索查询智能体 ⭐

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/SearchAgentCards-Queriesagentsviaintentrecognition?lang=zh
- **读取范围**: 0–507 / 507（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选 — SearchAgentCards
  - `Version` string 必选 — 2025-10-30
  - `SpaceId` string 必选 — A2A智能体空间ID（如 `<RESOURCE_ID>***`）
  - `Prompt` string 必选 — 搜索目标智能体的提示词（如 "write a book"）
  - `TopK` integer 必选 — 返回匹配度最高的前K个结果（如 10）
- **返回参数**:
  - `TotalCount` integer — 返回智能体总数（如 6）
  - `AgentCards` string — A2A智能体的JSON文本（文档示例中为 `"--"`，实际应为AgentCard JSON字符串数组）
- **错误码**:
  - 500 InternalError — 内部错误
- **关键说明**: 此接口为A2A发现的核心——需先在CreateA2aSpace/UpdateA2aSpace中开启 `IntentEnabled=true`（语义检索），才能调用此接口按自然语言意图检索空间内匹配的智能体。

---

## 39. AddSessionStore - 导入会话资源

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/AddSessionStore-Importssessionresources?lang=zh
- **读取范围**: 0–982 / 982（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `DatabaseConfiguration.AccountName` string 必选 — 数据库账号
  - `DatabaseConfiguration.Database` string 必选 — 数据库名
  - `DatabaseConfiguration.EndpointConfiguration.EndpointId` string 必选 — 连接点ID
  - `DatabaseConfiguration.InstanceId` string 必选 — 实例ID
  - `Description` string 可选 — 描述，0~200字符
  - `Name` string 可选 — 名称，字母数字-_，2~48字符
  - `ProjectName` string 可选
  - `ProviderType` string 可选 — RDS_MYSQL / RDS_PG
- **返回参数**:
  - `Description` / `Name` / `ProviderType`
  - `SessionStoreId` string — 会话资源ID
  - `Status` string — Creating/CreateFailed/Ready/Deleting/DeleteFailed/Deleted/Error
- **错误码**:
  - 400 InvalidDescription.Malformed / InvalidName.Malformed / InvalidProjectName.Malformed
  - 400 MissingParameter.AccountName / Database / DatabaseConfiguration / EndpointId / InstanceId

---

## 40. DeleteSessionStore - 删除会话资源

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/DeleteSessionStore-Deletessessionresources?lang=zh
- **读取范围**: 0–466 / 466（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `SessionStoreId` string 必选
- **返回参数**:
  - `ProviderType` / `SessionStoreId` / `Status`
- **错误码**: 400 MissingParameter.SessionStoreId

---

## 41. GetSessionStore - 查询会话资源详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetSessionStore-Queriessessionresourcedetails?lang=zh
- **读取范围**: 0–990 / 990（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `SessionStoreId` string 必选
- **返回参数**:
  - `AssociatedAgents` object[] — Id(运行时ID), Name, UpdateTime
  - `CreateTime` / `UpdateTime`（RFC3339）
  - `DatabaseConfiguration` — AccountName, Database, EndpointConfiguration(EndpointId/PrivateEndpoint/PublicEndpoint), InstanceId
  - `Description` / `Managed`(boolean) / `Name` / `ProjectName` / `ProviderType` / `SessionStoreId` / `Status` / `Trn` / `VpcId`
- **错误码**: 400 MissingParameter.SessionStoreId

---

## 42. ListSessionStores - 批量查询会话资源详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListSessionStores-Batchqueriessessionresourcedetails?lang=zh
- **读取范围**: 0–1372 / 1372（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `CreateTimeAfter` / `CreateTimeBefore` string 可选 — RFC3339
  - `Filters.N.Name` string[] 可选 — 精确过滤字段：session_store_id/name/status/provider_type
  - `Filters.N.NameContains` string[] 可选 — 模糊过滤：name/description/provider_type
  - `Filters.N.Values.N` string[] 可选 — 过滤值
  - `MaxResults` integer 可选 — 1~100，默认10
  - `NextToken` string 可选 — 分页凭证
  - `PageNumber` / `PageSize` integer 可选
  - `ProjectName` string 可选
- **返回参数**:
  - `PageNumber` / `PageSize`
  - `SessionStores` object[] — AssociatedAgentsCount, CreateTime, DatabaseConfiguration, Description, Managed, Name, ProjectName, ProviderType, SessionStoreId, Status, UpdateTime, VpcId
  - `TotalCount` integer
- **错误码**: 400 InvalidProjectName.Malformed

---

## 43. AddMemoryCollection - 导入记忆库

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/AddMemoryCollection-Importsmemories?lang=zh
- **读取范围**: 0–1068 / 1068（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `ClientToken` string 可选 — 幂等性，ASCII≤64字符
  - `Collections.N.ProviderCollectionId` string[] 必选 — 记忆库ID（Mem0填MemoryProjectId, Viking填ResourceId）
  - `Collections.N.Description` string[] 可选 — ≤200字符
  - `Collections.N.Name` string[] 可选 — 名称
  - `Collections.N.ProjectName` string[] 可选
  - `Collections.N.ProviderType` string[] 可选 — MEM0 / VIKINGDB_MEMORY
- **返回参数**:
  - `Collections` object[] — MemoryId, Message, ProviderCollectionId, ProviderType, Status(Creating/CreateFailed/Ready/Deleting/DeleteFailed/Deleted/Error)
- **错误码**:
  - 400 InvalidClientToken/Description/Name/ProjectName/ProviderCollectionId/Region.Malformed
  - 400 LimitExceeded.MaximumCollections
  - 400 MissingParameter.Collections / ProviderCollectionId

---

## 44. CreateMemoryCollection - 创建记忆库

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/CreateMemoryCollection-Createsmemories?lang=zh
- **读取范围**: 0–1841 / 1841（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `ClientToken` string 可选
  - `Description` string 可选 — ≤200字符
  - `LongTermConfiguration.Strategies.N.Name` string[] 必选 — 策略名，1~48字符，字母数字下划线
  - `LongTermConfiguration.Strategies.N.Type` string[] 必选 — Summary/Semantic/UserPreference
  - `LongTermConfiguration.Strategies.N.CustomExtractionInstructions` string[] 可选 — 自定义Prompt，≤8000字符
  - `Name` string 必选 — 记忆库名，1~48字符，字母数字下划线
  - `ProjectName` string 可选
  - `ProviderType` string 可选 — MEM0(默认) / VIKINGDB_MEMORY
  - `Tags.N.Key` string[] 必选 — 标签键，1~128字符，不能volc:/sys:开头
  - `Tags.N.Value` string[] 可选 — 标签值，0~256字符
  - `Tags.N.Type` string[] 可选 — system/custom
  - `VpcConfig.VpcId` string 必选 — VPC ID（不可变更）
  - `VpcConfig.SubnetIds.N` string[] 可选 — 子网列表，MEM0最多1个
- **返回参数**:
  - `MemoryId` / `ProviderCollectionId` / `ProviderType` / `Status`
- **错误码**:
  - 400 InvalidDescription/Name/ProjectName.Malformed
  - 400 LimitExceeded.MaximumTags / MinimumSubnetIds
  - 400 MissingParameter.Key/LongTermConfiguration/Name/VpcId/StrategyName/Strategies
  - 400 InvalidParameter.UnsupportedStrategyType / StrategyName / MemoryCollectionName / InvalidSubnets / RedundantSubnet
  - 400 QuotaExceeded.VikingMemories
  - 500 InternalError

---

## 45. UpdateMemoryCollection - 修改记忆库信息

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/UpdateMemory-Modifiesmemoryinformation?lang=zh
- **读取范围**: 0–1211 / 1211（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选 — UpdateMemoryCollection
  - `Version` string 必选 — 2025-10-30
  - `Description` string 可选
  - `LongTermConfiguration.Strategies.N.Name/Type/CustomExtractionInstructions` 同Create
  - `MemoryId` string 必选
  - `VpcConfig.VpcId` string 必选（不可变更）
  - `VpcConfig.SubnetIds.N` string[] 可选
- **返回参数**:
  - `LongTermConfiguration` — Strategies(CustomExtractionInstructions, Name, Type)
  - `MemoryId` / `ProviderCollectionId` / `ProviderType`
- **错误码**:
  - 400 InvalidDescription.Malformed / LimitExceeded.MinimumSubnetIds
  - 400 MissingParameter.MemoryId / VpcId
  - 400 InvalidParameter.InvalidSubnets / Mem0VpcConfig / UpdateVpcNotAllowed
  - 400 OperationDenied.TooManyVpcUpdates
  - 404 InvalidResource.NotFound

---

## 46. DeleteMemoryCollection - 删除记忆库

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/DeleteMemoryCollection-Deletesmemory?lang=zh
- **读取范围**: 0–479 / 479（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `MemoryId` string 必选
- **返回参数**:
  - `MemoryId` / `ProviderCollectionId` / `ProviderType` / `Status`
- **错误码**: 400 MissingParameter.MemoryId

---

## 47. GetMemoryCollection - 查询记忆库详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetMemoryCollection-Queriesmemorydetails?lang=zh
- **读取范围**: 0–1014 / 1014（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `MemoryId` string 必选
- **返回参数**:
  - `AssociatedRuntimes` object[] — Id, Name
  - `CreateTime` / `Description` / `LastUpdateTime`
  - `LongTermConfiguration` — Strategies(CustomExtractionInstructions, Name, Type)
  - `Managed` boolean / `MemoryId` / `Name` / `ProjectName` / `ProviderCollectionId` / `ProviderType` / `Region` / `Status`
  - `Tags` object[] — Type, Key, Value
  - `Trn` / `VpcConfig`(SubnetIds[], VpcId)
- **错误码**:
  - 400 MissingParameter.MemoryId
  - 404 InvalidResource.NotFound

---

## 48. GetMemoryConnectionInfo - 查询记忆库长期记忆提取策略详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetMemoryConnectionInfo-QueriesmemoryLTMretrievalstrategydetails?lang=zh
- **读取范围**: 0–816 / 816（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `MemoryId` string 必选
- **返回参数**:
  - `ConnectionInfos` object[] — AddrType(PUBLIC/PRIVATE), AuthKey, AuthType(BEARER_TOKEN/APIKEY/AK_SK), BaseUrl, ExpireAt, Status(AVAILABLE/CREATING/UNAVAILABLE), VpcId
  - `Managed` / `MemoryId` / `Message` / `ProviderCollectionId` / `ProviderType` / `Status`
- **错误码**: 400 MissingParameter.MemoryId

---

## 49. ListMemoryCollections - 批量查询记忆库详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListMemoryCollections-Batchqueriesmemorydetails?lang=zh
- **读取范围**: 0–1728 / 1728（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `CreateTimeAfter` / `CreateTimeBefore` / `UpdateTimeAfter` / `UpdateTimeBefore` string 可选 — RFC3339
  - `Filters.N.Name` / `Filters.N.NameContains` / `Filters.N.Values.N` string[] 可选
    - 精确字段：collection_id/name/description/status/provider_type
  - `MaxResults` integer 可选 — 1~100
  - `NextToken` string 可选
  - `ProjectName` string 可选
  - `TagFilters.N.Key` / `TagFilters.N.Values.N` string[] 可选
- **返回参数**:
  - `Memories` object[] — AssociatedRuntimes, CreateTime, Description, LastUpdateTime, Managed, MemoryId, Name, NetworkConfiguration(EnablePrivateNetwork/EnablePublicNetwork/VpcConfiguration), ProjectName, ProviderCollectionId, ProviderType, Region, Status, StrategiesCount, Tags
  - `NextToken` string
- **错误码**:
  - 400 InvalidProjectName.Malformed
  - 400 LimitExceeded.MaximumFilters / MaximumMaxResults / MaximumPageSize

---

## 50. AddKnowledgeBase - 导入知识库

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/AddKnowledgeBase-Importsknowledgebases?lang=zh
- **读取范围**: 0–1070 / 1070（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `ClientToken` string 可选
  - `KnowledgeBases.N.Name` string[] 必选 — Viking填CollectionName
  - `KnowledgeBases.N.ProviderKnowledgeId` string[] 必选 — Viking填ResourceId
  - `KnowledgeBases.N.ProviderType` string[] 必选 — VIKINGDB_KNOWLEDGE
  - `KnowledgeBases.N.Description` string[] 可选
  - `ProjectName` string 可选
- **返回参数**:
  - `KnowledgeBases` object[] — KnowledgeId, Message, ProviderKnowledgeId, ProviderType, Status(Importing/ImportFailed/Ready/Deleting/DeleteFailed/Deleted/Error)
- **错误码**:
  - 400 InvalidDescription/Name.Malformed
  - 400 LimitExceeded.MaximumKnowledgeBases / MinimumKnowledgeBases
  - 400 MissingParameter.KnowledgeBases / Name / ProviderKnowledgeId
  - 400 InvalidParameter.UnsupportedProviderType

---

## 51. UpdateKnowledgeBase - 更新知识库

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/UpdateKnowledgeBase-Updatesknowledgebase?lang=zh
- **读取范围**: 0–675 / 675（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `Description` string 可选
  - `KnowledgeId` string 必选
  - `VpcConfig.VpcId` string 必选（不可变更）
  - `VpcConfig.SubnetIds.N` string[] 可选
- **返回参数**:
  - `KnowledgeId` / `ProviderKnowledgeId` / `ProviderType`
- **错误码**:
  - 400 InvalidDescription.Malformed / LimitExceeded.MinimumSubnetIds
  - 400 MissingParameter.KnowledgeId / VpcId

---

## 52. DeleteKnowledgeBase - 删除知识库

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/DeleteKnowledgeBase-Deletesknowledgebase?lang=zh
- **读取范围**: 0–434 / 434（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `KnowledgeId` string 必选
- **返回参数**:
  - `KnowledgeId` / `ProviderKnowledgeId` / `ProviderType`
- **说明**: 删除仅解除导入，不删除对应知识库资源
- **错误码**: 400 MissingParameter.KnowledgeId

---

## 53. GetKnowledgeBase - 查询知识库信息

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetKnowledgeBase-Queriesknowledgebaseinformation?lang=zh
- **读取范围**: 0–777 / 777（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `KnowledgeId` string 必选
- **返回参数**:
  - `AssociatedRuntimes` object[] — Id, Name
  - `CreateTime` / `Description` / `KnowledgeId` / `LastUpdateTime` / `Name` / `ProjectName` / `ProviderKnowledgeId` / `ProviderType` / `Region` / `Status` / `Trn` / `VpcConfig`(SubnetIds[], VpcId)
- **错误码**: 400 MissingParameter.KnowledgeId

---

## 54. GetKnowledgeConnectionInfo - 查询知识库详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetKnowledgeConnectionInfo-Queriesknowledgedetails?lang=zh
- **读取范围**: 0–49 / 49（已到底）
- **异常**: 页面正文为空，仅有导航标题，无任何参数文档
- **正文摘要**: 标题存在，正文缺失

---

## 55. ListKnowledgeBases - 批量查询知识库详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListKnowledgeBases-Batchqueriesknowledgebasedetails?lang=zh
- **读取范围**: 0–1373 / 1373（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `CreateTimeAfter` / `CreateTimeBefore` / `UpdateTimeAfter` / `UpdateTimeBefore` string 可选
  - `Filters.N.Name` / `Filters.N.NameContains` / `Filters.N.Values.N` string[] 可选
    - 精确字段：knowledge_id/name/status/provider_type
  - `MaxResults` integer 可选 — 1~100
  - `NextToken` string 可选
  - `ProjectName` string 可选
- **返回参数**:
  - `KnowledgeBases` object[] — AssociatedRuntimes, NetworkConfiguration(EnablePrivateNetwork/EnablePublicNetwork/VpcConfiguration), ProjectName, Region, CreateTime, Description, KnowledgeId, LastUpdateTime, Name, ProviderKnowledgeId, ProviderType, Status
  - `NextToken` string
- **错误码**: 400 LimitExceeded.MaximumMaxResults / MaximumPageSize

---

## 56. CreateMCPService - 创建MCP服务

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/CreateMCPService-CreatesMCPservice?lang=zh
- **读取范围**: 0–4408 / 4408（已到底，单页读完）
- **异常**: 无
- **请求参数（核心）**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `BackendType` string 必选 — Function/Domain/ECS/VKE/CustomPublic/CustomPrivate
  - `BackendConfiguration` object 必选
    - `FunctionConfiguration` — FunctionId, FunctionName
    - `CustomConfiguration` — Domain, Port, ProtocolType(HTTP/HTTPS), TlsSettings.TlsMode(DISABLE/SIMPLE)
    - `EcsConfiguration.Instances.N` — InstanceId, Ip, Port
    - `VkeConfiguration` — ClusterId, Namespace, Port, ServiceName
    - `CustomMcpConfiguration` — EnableApmplus, PrivatePackage(Command/Envs.N.Key/Envs.N.Value/ImageUrl), PublicPackage(McpType:Stdio/Remote, PackageManagerType:NPX/UVX, RawConfig)
  - `Name` string 必选 — 4~64字符，字母数字-_
  - `Path` string 必选 — 访问路径
  - `ProtocolType` string 必选 — HTTP(HTTP转MCP) / MCP(直接访问)
  - `ProtocolConfiguration.HttpApiConfiguration` — Type(Swagger), Configuration(Base64编码的Swagger JSON)
  - `InboundAuthorizerConfiguration` — AuthorizerType(ApiKey/CustomJWT), Authorizer(KeyAuth: <REDACTED>; CustomJwtAuthorizer: DiscoveryUrl/AllowedClients.N)
  - `OutboundAuthorizerConfiguration` — AuthorizerType(ApiKey/Identity), Authorizer(KeyAuth同上; IdentityAuthorizer: ProviderType(ApiKey/Oauth2M2m), CredentialProviderName)
  - `NetworkConfiguration` — EnablePrivateNetwork/EnablePublicNetwork(必传其一), VpcConfiguration(VpcId, SubnetIds.N)
  - `ClientToken` string 可选
  - `ProjectName` / `RoleName` / `Tags.N.Key/Value/Type`
  - `GatewayMode` string 可选 — Shared(默认)/Exclusive
  - `GatewayInstanceId` string 可选 — Exclusive时必传
  - `BackendAccessType` string 可选 — Public/Private（Exclusive+Domain时）
- **返回参数**:
  - `MCPServiceId` string
- **错误码**: 大量400 MissingParameter.* / Invalid*.Malformed / LimitExceeded.* 错误码（详见原文表格）

---

## 57. ListMCPServices - 批量查询MCP服务详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListMCPServices-BatchqueriesMCPservicedetails?lang=zh
- **读取范围**: 0–1835 / 1835（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `Filters.N.Name` / `Filters.N.NameContains` / `Filters.N.Values.N` string[] 可选 — name/status
  - `MaxResults` integer 可选 — 1~100，默认10
  - `NextToken` string 可选
  - `ProjectName` string 可选
  - `TagFilters.N.Key` / `TagFilters.N.Values.N` string[] 可选
  - `GatewayInstanceId` string 可选
- **返回参数**:
  - `MCPServices` object[] — IsAllTools, CreatedAt, MCPServiceId, Name, NetworkConfigurations(Endpoint/NetworkType/VpcConfiguration/EnableSharedInternetAccess), Path, ProjectName, ProtocolConfiguration(ProtocolConvertConfiguration/ProtocolType), Status(Ready/Creating/Updating/Deleting/Error), Tags, UpdatedAt, CanDelete, GatewayMode, InboundAuthorizerConfiguration
  - `NextToken` string
- **错误码**: 400 LimitExceeded.MaximumMaxResults

---

## 58. GetMCPService - 查询MCP服务详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetMCPService-QueriesMCPservicedetails?lang=zh
- **读取范围**: 0–2373 / 2373（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `MCPServiceId` string 必选
- **返回参数**:
  - `MCPService` object — AssociatedMCPToolsets(MCPToolsetId/Name), RoleName, BackendConfiguration(全量配置), BackendType, CreatedAt, FailedLogFileUrl(Error时), InboundAuthorizerConfiguration, MCPServiceId, Name, NetworkConfigurations, OutboundAuthorizerConfiguration, Path, ProjectName, ProtocolConfiguration, Status, Tags, UpdatedAt, GatewayInstanceName, BackendAccessType, GatewayMode
- **错误码**:
  - 400 MissingParameter.MCPServiceId
  - 404 InvalidResource.NotFound

---

## 59. UpdateMCPService - 修改MCP服务配置

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/UpdateMCPService-ModifiesMCPserviceconfiguration?lang=zh
- **读取范围**: 0–3002 / 3002（已到底）
- **异常**: 无
- **说明**: 不支持转换入站认证类型
- **请求参数**: 同CreateMCPService，但 `MCPServiceId` 必选
- **返回参数**:
  - `MCPServiceId` string
- **错误码**: 大量400 Invalid*.Malformed / MissingParameter.* / LimitExceeded.* 错误码

---

## 60. UpdateMCPTools - 修改MCP服务关联的API信息

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/UpdateMCPTools-ModifiesAPIinformationassociatedwithanMCPservice?lang=zh
- **读取范围**: 0–471 / 471（已到底）
- **异常**: 无
- **说明**: 仅当ProtocolType为"HTTP转MCP"时支持修改
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `MCPServiceId` string 必选
  - `MCPToolsetId` string 必选
  - `Tools` string 必选（文档示例为空，具体结构未展开）
- **返回参数**:
  - `MCPServiceId` string
- **错误码**:
  - 400 MissingParameter.MCPServiceId / MCPToolsetId / Tools

---

## 61. DeleteMCPService - 删除MCP服务

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/DeleteMCPService-DeletesMCPservice?lang=zh
- **读取范围**: 0–510 / 510（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `MCPServiceId` string 必选
- **返回参数**:
  - `MCPServiceId` string
- **错误码**:
  - 400 MissingParameter.MCPServiceId
  - 404 InvalidResource.NotFound
  - 412 OperationDenied.ResourceLocked

---

## 62. CreateMCPToolset - 创建MCP工具集

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/CreateMCPToolset-CreatesMCPtoolset?lang=zh
- **读取范围**: 0–2572 / 2572（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `Name` string 必选 — 4~64字符
  - `Path` string 必选
  - `Mode` string 必选 — AllTools(全量)/SemanticSearch(语义检索)/TagSearch(标签检索)
  - `MCPServiceIds.N` string[] 必选 — 1~100个
  - `MCPServices.N.MCPServiceId` string[] 必选
  - `MCPServices.N.IsAllTools` boolean[] 必选
  - `MCPServices.N.MCPTools.N.Name` string[] 必选 — 工具名
  - `MCPServices.N.MCPTools.N.Description` string[] 可选
  - `MCPServices.N.MCPTools.N.Tags.N` string[] 可选
  - `AuthorizerConfiguration` — AuthorizerType(ApiKey/CustomJWT), Authorizer(同MCP服务)
  - `NetworkConfiguration` — EnablePrivateNetwork/EnablePublicNetwork(必传其一), VpcConfiguration(VpcId/SecurityGroupIds.N/SubnetIds.N)
  - `ClientToken` / `ProjectName` / `Tags.N.Key/Value/Type`
  - `GatewayMode` / `GatewayInstanceId` 可选
- **返回参数**:
  - `MCPToolsetId` string
- **错误码**: 大量400 Invalid*.Malformed / MissingParameter.* / LimitExceeded.* 及404 InvalidMCPService.NotFound / 500 InternalError

---

## 63. ListMCPToolsets - 批量查询MCP工具集详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListMCPToolsets-BatchqueriesMCPtoolsetdetails?lang=zh
- **读取范围**: 0–2165 / 2165（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `Filters.N.Name` / `Filters.N.NameContains` / `Filters.N.Values.N` string[] 可选 — name/status
  - `MaxResults` integer 可选 — 1~100
  - `NextToken` string 可选
  - `ProjectName` / `TagFilters` / `GatewayInstanceId` 可选
- **返回参数**:
  - `MCPToolsets` object[] — AuthorizerConfiguration, CreatedAt, MCPServices(含IsAllTools/MCPServiceId/Name/NetworkConfigurations/Path/ProjectName/ProtocolConfiguration/Status/UpdatedAt), MCPToolsetId, Mode(AllTools/SemanticSearch/TagSearch), Name, NetworkConfigurations, Path, ProjectName, Status, Tags, UpdatedAt, GatewayInstanceId, GatewayMode
  - `NextToken` string
- **错误码**: 400 LimitExceeded.MaximumMaxResults

---

## 64. GetMCPToolset - 查询MCP工具集详情

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetMCPToolset-QueriesMCPtoolsetdetails?lang=zh
- **读取范围**: 0–1671 / 1671（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `MCPToolsetId` string 必选
- **返回参数**:
  - `MCPToolset` object — AssociatedRuntimes(Id/Name), AuthorizerConfiguration, CreatedAt, MCPServices, MCPToolsetId, Mode, Name, NetworkConfigurations, Path, ProjectName, Status, Tags, UpdatedAt, GatewayInstanceName, GatewayInstanceId, GatewayMode
- **错误码**:
  - 400 MissingParameter.MCPToolsetId
  - 404 InvalidResource.NotFound

---

## 65. UpdateMCPToolset - 修改MCP工具集配置

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/UpdateMCPToolset-ModifiesMCPtoolsetconfiguration?lang=zh
- **读取范围**: 0–1338 / 1338（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `MCPToolsetId` string 必选
  - `MCPServiceIds.N` string[] 可选
  - `MCPServices.N` 结构同Create（IsAllTools/MCPServiceId/MCPTools.N.Name/Description/Tags.N）
  - `AuthorizerConfiguration` 可选
  - `Mode` string 可选 — AllTools/SemanticSearch/TagSearch
  - `ClientToken` 可选
- **返回参数**:
  - `MCPToolsetId` string
- **错误码**:
  - 400 Invalid*.Malformed / MissingParameter.* / LimitExceeded.*
  - 404 InvalidMCPService.NotFound

---

## 66. DeleteMCPToolset - 删除MCP工具集

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/DeleteMCPToolset-DeletesMCPtoolset?lang=zh
- **读取范围**: 0–455 / 455（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `MCPToolsetId` string 必选
- **返回参数**:
  - `MCPToolsetId` string
- **错误码**:
  - 400 MissingParameter.MCPToolsetId
  - 404 InvalidResource.NotFound

---

## 67. ListMCPToolsetTools - 查询MCP工具集中的工具

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListMCPToolsetTools-QueriestoolsinanMCPtoolset?lang=zh
- **读取范围**: 0–1397 / 1397（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `MCPToolsetId` string 必选
- **返回参数**:
  - `MCPToolsetId` string
  - `MCPService` object[] — IsAllTool(boolean), MCPServiceId, MCPTools(Description/Name/Tags[])
- **错误码**: 400 MissingParameter.MCPToolsetId

---

## 68. TagResources - 添加用户标签

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/TagResources-Addsusertags?lang=zh
- **读取范围**: 0–741 / 741（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `ResourceIds.N` string[] 必选 — 1~50个资源ID
  - `ResourceType` string 必选 — runtime/tool/memory/mcpservice/mcptoolset
  - `Tags.N.Key` string[] 必选 — 标签键，1~128字符，不能volc:/sys:开头
  - `Tags.N.Value` string[] 可选 — 标签值，0~256字符
  - `Tags.N.Type` string[] 可选 — system/custom
- **返回参数**: 无特有返回参数
- **错误码**:
  - 400 MissingParameter.Key/ResourceIds/ResourceType/Tags/Value
  - 404 InvalidResource.NotFound
  - 500 InternalError

---

## 69. UntagResources - 删除用户标签

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/UntagResources-Deletesusertags?lang=zh
- **读取范围**: 0–526 / 526（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `ResourceIds.N` string[] 必选 — 1~50个
  - `ResourceType` string 必选 — runtime/tool/memory/mcpservice/mcptoolset
  - `TagKeys.N` string[] 可选 — 要删除的标签键，1~20个
- **返回参数**: 无特有返回参数
- **错误码**:
  - 400 MissingParameter.ResourceIds / ResourceType

---

## 70. ListTagsForResources - 查询已绑定标签的资源

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListTagsForResources-Queriesresourceswithtags?lang=zh
- **读取范围**: 0–838 / 838（已到底）
- **异常**: 无
- **请求参数**:
  - `Action` string 必选
  - `Version` string 必选 — 2025-10-30
  - `ResourceIds.N` string[] 必选 — 1~50个
  - `ResourceType` string 必选 — runtime/tool/memory/mcpservice/mcptoolset
  - `MaxResults` integer 可选 — 最大100，默认10
  - `NextToken` string 可选
  - `TagFilters.N.Key` string[] 可选 — 1~10个
  - `TagFilters.N.Values.N` string[] 可选 — 每键最多3个值
- **返回参数**:
  - `NextToken` string
  - `TagResources` object[] — ResourceId, ResourceType, TagKey, TagValue
- **错误码**:
  - 400 MissingParameter.ResourceIds / ResourceType

---

## 统计表

| 分类 | 页码范围 | 接口数 | 备注 |
|---|---|---|---|
| Skill 基础CRUD | 1–24 | 24 | 含DeleteSkillCreateTask控制台页(1)、ListSkills(7)和ListSharingSkills(14)正文为空 |
| A2A 空间+智能体 | 25–38 | 14 | 含SearchAgentCards语义检索核心接口(38) |
| 会话资源 SessionStore | 39–42 | 4 | RDS_MYSQL/RDS_PG |
| 记忆库 Memory | 43–49 | 7 | MEM0/VIKINGDB_MEMORY |
| 知识库 Knowledge | 50–55 | 6 | VIKINGDB_KNOWLEDGE；GetKnowledgeConnectionInfo(54)正文为空 |
| MCP 服务 | 56–61 | 6 | 含CreateMCPService最长页(4408字符) |
| MCP 工具集 | 62–67 | 6 | 含ListMCPToolsetTools(67) |
| 标签 Tag | 68–70 | 3 | TagResources/UntagResources/ListTagsForResources |
| **合计** | **1–70** | **70** | **全部已抓取，无遗漏** |

### 空页面（正文缺失）统计
| 页码 | 接口 | total_length |
|---|---|---|
| 7 | ListSkills - 批量查询Skill详情 | 40 |
| 14 | ListSharingSkills - 批量查询共享Skill详情 | 55 |
| 54 | GetKnowledgeConnectionInfo - 查询知识库详情 | 49 |

### 关键发现
1. **统一API版本**：所有接口 `Version=2025-10-30`，Endpoint 为 `https://[PRODUCT].cn-beijing.volcengineapi.com`
2. **SearchAgentCards**（第38页）为A2A语义检索核心：入参 `SpaceId` + `Prompt` + `TopK`，返回 `TotalCount` + `AgentCards`(JSON文本)；前置条件是空间需开启 `IntentEnabled=true`
3. **分页模式**：Skill相关接口用 `PageNumber`/`PageSize`；SessionStore/Memory/Knowledge/MCP相关用 `MaxResults`/`NextToken` 游标分页
4. **标签资源类型枚举**：`runtime`(智能体运行时) / `tool`(工具集) / `memory`(记忆库) / `mcpservice`(MCP服务) / `mcptoolset`(MCP工具集)
5. **VPC配置**：记忆库、知识库、MCP服务/工具集均支持VPC私网接入，`VpcId`创建后不可变更
