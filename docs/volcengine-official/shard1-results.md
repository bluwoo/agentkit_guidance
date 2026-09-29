# 火山引擎 [PRODUCT] 官方文档 API 参考分片1 读取结果

读取时间：2026-09-18
读取工具：web.fetch（全量分页，每页 end_offset 均等于 total_length，无二次分页续读需求）
输出文件：本文件

---

## 简介 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Overview?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–338（total_length=338），已到底
- 关键内容：API参考首页。基本概念表：地域、可用区、主账号、子用户（IAM用户）。无接口参数。
- 异常：无

## API列表 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/APIoverview-42?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–1332（total_length=1332），已到底
- 关键内容：[PRODUCT] 全量 API 目录，按模块分组：
  - 智能体运行时 Runtime：CreateRuntime/UpdateRuntime/ReleaseRuntime/DeleteRuntime/GetRuntime/GetRuntimeVersion/ListRuntimes/ListRuntimeVersions/GetRuntimeInstanceLogs/ListRuntimeInstances/UpdateRuntimeRelease/AbortRuntimeRelease/ListRuntimeReleaseRecords/GetRuntimeReleaseStatus/GetRuntimeWebshellEndpoint（共15个）
  - 工具 Tool：CreateTool/UpdateTool/DeleteTool/GetTool/ListTools/InvokeTool/AsyncExecCommand/ViewAsyncCommand/CreateSession/DeleteSession/GetSession/ListSessions/SetSessionTtl/GetSessionLogs（共14个）
  - A2A 中心：CreateA2aSpace/UpdateA2aSpace/ListA2aSpaces/GetA2aSpace/DeleteA2aSpace/CreateA2aAgent/UpdateA2aAgent/ListA2aAgents/GetA2aAgent/DeleteA2aAgent/ListA2aAgentVersions/GetA2aAgentVersion/DeleteA2aAgentVersion/SearchAgentCards
  - 会话管理 SessionStore：AddSessionStore/DeleteSessionStore/GetSessionStore/ListSessionStores
  - 记忆库 Memory、知识库 Knowledge、网关 MCP、网关 Skills、标签 Tag 各模块接口清单
- 异常：无

## API错误码列表 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Commonerrorcodes-1?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–859（total_length=859），已到底
- 关键内容：公共错误码表（Code / HTTP状态码 / Message / 处理措施）。共25条：
  - 400：MissingParameter、MissingRequestInfo、InnerApiNeedAccountInfo、InvalidAuthorization、InvalidCredential
  - 401：MissingAuthenticationToken、MissingSignature、InvalidAccessKey、SignatureDoesNotMatch、InvalidSecretToken
  - 403：LackProjectPolicy、InvalidTimestamp、ServiceShouldCallSelfApi、LackPolicy、AccessDenied
  - 404：ServiceNotFound、InvalidActionOrVersion
  - 405：MethodNotAllowed
  - 429：FlowLimitExceeded
  - 500：UndefinedError、InternalError
  - 502：FailToConnect、InternalServiceError
  - 503：ServiceUnavailableTemp
  - 504：InternalServiceTimeout
- 异常：无

## API发布历史 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/APIreleasehistory-16?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–6023（total_length=6023），已到底
- 关键内容：按日期倒序的接口变更记录。关键节点：
  - 2026-09-14：MCP 模块大量新增 GatewayInstanceId/GatewayMode/EnableSharedInternetAccess 等参数与错误码
  - 2026-09-09：Runtime CreateRuntime/GetRuntime/ListRuntimes 新增 GatewayMode、GatewayInstanceId、RequestModifierConfig、TosMountConfig 结构
  - 2026-07-17：Runtime 新增 RequestModifierConfig.FunctionId/Path、TosMountConfig 全套凭证与挂载点；Tool 新增 EnableSnapshot、CreateSession 新增 Envs/ImageInfo/Metadata；GetRuntimeWebshellEndpoint 新增接口
  - 2026-07-10：ToolType 新增取值 CodeEnv
  - 2026-03-06：CreateRuntime/UpdateRuntime 新增 AgentSpaceId；A2A 全部接口新增
  - 2026-02-28：ListRuntimeReleaseRecords 的 OrderBy.Key 取值 CreateTime 变更为 CreationTime；CreateTool 新增 CpuMilli；ToolType 新增 VibeSkill
  - 2026-02-11：Runtime 新增 LlmshieldAppId/LlmshieldStatus/SessionStoreId/Tags.N.Type；ReleaseRuntime 新增 Description/RollingStep/TargetTrafficWeight；UpdateRuntimeRelease/ListRuntimeReleaseRecords/AbortRuntimeRelease/GetRuntimeReleaseStatus 新增接口；Tool 新增 ModelAgentName/SkillSpaceId
  - 2026-02-05：AsyncExecCommand/ViewAsyncCommand 新增接口
  - 2026-01-28：Runtime/Tool 新增 NetworkConfiguration.VpcConfiguration.EnableSharedInternetAccess、TosMountConfig
  - 2026-01-16：GetRuntimeInstanceLogs/ListRuntimeInstances 新增；CreateMCPService/UpdateMCPService 新增 EcsConfiguration/VkeConfiguration/Identity 鉴权；Skills 全部接口新增
  - 2026-01-08：InvokeTool 新增接口
  - 2025-12-15：Runtime 新增 CpuMilli/MaxConcurrency/MaxInstance/MemoryMb/MinInstance；Tool 新增 ApmplusEnable/Command/Envs/ImageUrl/Port，ToolType 新增 Skill/Private
  - 2025-11-30：Runtime 新增 ArtifactType=public_image、KnowledgeId/MCPToolsetId/MemoryId/ToolId/ModelAgentName/ProjectName/RoleName/Tags、AuthorizerConfiguration.CustomJwtAuthorizer、NetworkConfiguration；Tool 新增 ProjectName/RoleName/Tags/KeyAuth/NetworkConfiguration；SessionStore/Memory/Knowledge/MCP/Tag 各模块接口新增
  - 2025-10-30：首次开放 OpenAPI
- 异常：无

## 请求结构 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Requeststructure?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–310（total_length=310），已到底
- 关键内容：以 DeleteRuntime 为例的请求结构说明。POST 方式，URL 形如 `https://[PRODUCT].cn-beijing.volcengineapi.com?Action=DeleteRuntime&Version=2025-10-30`。通信协议 HTTP/HTTPS（推荐 HTTPS）。**[PRODUCT] OpenAPI 仅支持 POST 请求**。请求参数分公共请求参数+接口请求参数。字符编码 UTF-8。
- 异常：无

## 服务地址 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Serviceaddress-1?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–203（total_length=203），已到底
- 关键内容：地域与 Endpoint 映射表：
  - 华北2（北京）cn-beijing：`https://[PRODUCT].cn-beijing.volcengineapi.com`
  - 华东2（上海）cn-shanghai：`https://[PRODUCT].cn-shanghai.volcengineapi.com`
  - **重要**：调用 InvokeTool 时服务地址不同，北京用 `https://<INTERNAL_HOST>.com`，上海用 `https://<INTERNAL_HOST>.com`
- 异常：无

## 公共参数 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Commonparameters?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–521（total_length=521），已到底
- 关键内容：
  - Action&Version 放 query：Action（String，必填）、Version（String，必填，当前 2025-10-30）、X-Expires（Int，可选，默认900秒）
  - Header 签名参数：X-Date（必填，UTC，形如 20201103T104027Z）、Authorization（必填，HMAC-SHA256 Credential={AK}/{ShortDate}/{Region}/{Service}/request, SignedHeaders=..., Signature=...；Service 固定为 [PRODUCT]）
  - Query 签名参数：X-Date、X-Algorithm（固定 HMAC-SHA256）、X-Credential、X-SignedHeaders、X-Signature
- 异常：无

## 签名算法 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Signaturealgorithm?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–112（total_length=112），已到底
- 关键内容：仅说明签名机制用途，正文链接到外部"签名方法"文档，本页无具体算法步骤。
- 异常：正文为跳转指针，无独立算法内容。

## 响应结果 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/APIresponse-6?lang=zh)

- 读取状态：成功读取到底（但正文为空壳）
- 读取范围：offset 0–36（total_length=36），已到底
- 关键内容：仅页面标题与导航，无任何响应结构正文。
- 异常：**空壳页面**（36字节，无实质内容）。实际响应结构需从各接口返回示例中的 ResponseMetadata/Result 结构反推。

## 评测中心概述 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ReviewCenterOverview?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–538（total_length=538），已到底
- 关键内容：评测中心功能介绍。三模块：评估器（定义评分标准）、评测集（用例集合）、评测任务（执行评测并出分）。核心概念：评估器/评测集/评测任务/评测节点/Trace。使用流程4步：准备评估器→准备评测集→创建评测任务→查看评测结果。评分负分制，100分基准，不影响需求流转。
- 异常：无

## CreateRuntime - 创建一个运行时 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/CreateRuntime-Createsaruntime?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–3134（total_length=3134），已到底
- 关键请求参数（字段/类型/必填/说明）：
  - Action=CreateRuntime、Version=2025-10-30
  - Name（String，必选，4-64字符，字母数字-_）
  - ArtifactType（String，必选：image/public_image）
  - ArtifactUrl（String，必选，host/namespace/repo:tag；公共镜像用 <INTERNAL_HOST>.com/template/financial:v1117_1）
  - RoleName（String，必选，绑定IAM角色）
  - AuthorizerConfiguration.KeyAuth.{ApiKeyLocation=Header, ApiKeyName 4-64字符} 或 AuthorizerConfiguration.CustomJwtAuthorizer.{DiscoveryUrl, AllowedClients.N}（二选一必填）
  - Envs.N.Key（String[]，必选，1-63字符）、Envs.N.Value（String[]，可选）
  - AgentSpaceId、ApmplusEnable（boolean，默认true）、ClientToken（≤64 ASCII）、CpuMilli（integer，250~16000，默认2000）、Description（≤1000 Unicode）、KnowledgeId、LlmshieldAppId、MCPToolsetId、MaxConcurrency（10~1000，默认100）、MaxInstance（1~10，默认10）、MemoryId、MemoryMb（512~131072，512梯度，默认4096）、MinInstance（0~MaxInstance，默认0）、ModelAgentName
  - NetworkConfiguration.EnablePrivateNetwork / EnablePublicNetwork（二选一）；VpcId（私网时必填）；SubnetIds.N（私网时必填）；VpcConfiguration.EnableSharedInternetAccess（私网时有效，默认true）
  - ProjectName、RequestModifierConfig.FunctionId（veFaaS）、RequestModifierConfig.Path、SessionStoreId、Tags.N.Key（必选，1-20，1-128字符）、Tags.N.Value（可选，0-256字符）、Tags.N.Type（system/custom）、ToolId
  - TosMountConfig.EnableTos（默认false）；为true时必填 Credentials.AccessKeyId/SecretAccessKey、MountPoints.N.{BucketName,BucketPath,Endpoint,LocalMountPath,ReadOnly}
  - GatewayMode（Shared默认/Exclusive）、GatewayInstanceId（Exclusive时必填）
- 返回参数：RuntimeId（String）
- 请求/返回示例：齐全（KeyAuth 方式 Envs 含 MODEL_AGENT_API_KEY、OBSERVABILITY_OPENTELEMETRY_*）
- 错误码：400 InvalidDescription.Malformed/InvalidKey.Malformed/InvalidName.Malformed/InvalidParameter.ArtifactType/ArtifactUrl/ConflictingAuthorizerConfiguration/InvalidParams.MaxConcurrency/LimitExceeded.MaximumSubnetIds/MinimumSubnetIds/MissingParameter.ArtifactType/ArtifactUrl/AuthorizerConfiguration/DiscoveryUrl/EnableLog/Key/Name/NetworkConfiguration/RoleName/VpcId/QuotaExceeded.Runtime；403 AccessDenied.Unauthorized；409 InvalidParameter.DuplicateName
- 异常：无

## UpdateRuntime - 修改运行时配置 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/UpdateRuntime-Modifiesruntimeconfiguration?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–1946（total_length=1946），已到底
- 关键请求参数：RuntimeId（必选）；其余同 CreateRuntime 的可选子集（AgentSpaceId/ApmplusEnable/ArtifactType/ArtifactUrl/CpuMilli/Description/Envs.N.Key必选/N.Value可选/KnowledgeId/LlmshieldAppId/LlmshieldStatus(1启用/0未启用)/MCPToolsetId/MaxConcurrency/MaxInstance/MemoryId/MemoryMb/MinInstance/ModelAgentName/ReleaseEnable(true立即发布)/RequestModifierConfig.FunctionId/Path/SessionStoreId/Tags.N.Key必选/N.Type/N.Value/ToolId/TosMountConfig全套）
- 返回参数：RuntimeId（返回示例中 Result.Id 字段）
- 请求示例：仅改 Description
- 错误码：400 InvalidDescription.Malformed/InvalidKey.Malformed/InvalidParams.MaxInstance/MinInstance/InvalidResourceStatus/MissingParameter.DiscoveryUrl/Key/RuntimeId/InvalidParameter.MemoryId/InvalidEnvKey.Malformed/ArtifactUrl/KnowledgeIds/InvalidParams.CpuMilli([1000,1250,1500,2000,4000,8000,16000])；404 Invalid[PRODUCT]Runtime.NotFound
- 异常：无

## ReleaseRuntime - 更新运行时版本 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ReleaseRuntime-Updatesruntimeversion?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–466（total_length=466），已到底
- 关键请求参数：RuntimeId（必选）、Description（可选）、RollingStep（integer，0~100，灰度步长%）、TargetTrafficWeight（integer，0~100，新版本流量占比%）、VersionNumber（integer，0=最新版本）
- 返回参数：RuntimeId
- 错误码：400 MissingParameter.RuntimeId、MissingParameter.VersionNumber
- 异常：无

## DeleteRuntime - 删除运行时 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/DeleteRuntime-Deletesruntime?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–414（total_length=414），已到底
- 关键请求参数：RuntimeId（必选）、ClientToken（可选，≤64 ASCII 幂等）
- 返回参数：RuntimeId
- 错误码：400 MissingParameter.RuntimeId
- 异常：无

## GetRuntime - 获取一个运行时详情 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetRuntime-Retrievesdetailsofaruntime?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–1954（total_length=1954），已到底
- 请求参数：RuntimeId（必选）
- 返回参数（关键字段/类型/说明）：
  - Endpoint（访问域名）、AgentSpaceId、ApmplusEnable、ArtifactType(image/public_image)、ArtifactUrl
  - AuthorizerConfiguration.{CustomJwtAuthorizer.{AllowedClients,DiscoveryUrl}, KeyAuth.{ApiKey,ApiKeyLocation=Header,ApiKeyName}}
  - Command（启动命令）、CpuMilli（milli cpu）、CreatedAt、CurrentVersionNumber、Description
  - Envs[].{Key,Value}、FailedLogFileUrl（部署失败日志下载地址）、KnowledgeId、LlmshieldAppId、MCPToolsetId、MaxConcurrency、MaxInstance、MemoryId、MemoryMb、MinInstance、ModelAgentName、Name
  - NetworkConfigurations[].{Endpoint, NetworkType(public/private), VpcConfiguration.{EnableSharedInternetAccess,SecurityGroupIds,SubnetIds,VpcId}}
  - ProjectName、RequestModifierConfig.{FunctionId,Path}、RoleName、RuntimeId、SessionStoreId
  - Status（Creating/Error/Releasing/Ready/Deleting/Deleted/Updating/UnReleased）、StatusMessage
  - Tags[].{Key,Type,Value}、ToolId、TosMountConfig.{Credentials.{AccessKeyId,SecretAccessKey}, EnableTos, MountPoints[].{BucketName,BucketPath,Endpoint,LocalMountPath,ReadOnly}}
  - UpdatedAt、GatewayMode(Shared/Exclusive)、GatewayInstanceId（Exclusive时返回）
- 错误码：400 MissingParameter.RuntimeId；404 Invalid[PRODUCT]Runtime.NotFound
- 异常：无

## GetRuntimeVersion - 查询运行时某个版本的详情 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetRuntimeVersion-Queriesdetailsofaspecificruntimeversion?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–1550（total_length=1550），已到底
- 请求参数：RuntimeId（必选）、VersionNumber（integer，可选，默认0=最新）
- 返回参数：与 GetRuntime 类似版本级配置，含 ApmplusEnable/ArtifactType/ArtifactUrl/AuthorizerConfiguration/Command/CpuMilli/CreatedAt/Description/Endpoint/Envs[]/LinkedResources[].{Id,Name,Type(Knowledge/Memory/MCPToolset/BuiltInTool/SessionStore)}/LlmshieldAppId/LlmshieldStatus/MaxConcurrency/MemoryMb/ModelAgentName/Name/ProjectName/RoleName/RuntimeId/Status/Tags[]/TosMountConfig/UpdatedAt/VersionNumber
- 错误码：400 MissingParameter.RuntimeId；404 InvalidResource.NotFound
- 异常：无

## ListRuntimes - 批量查询运行时详情 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListRuntimes-Batchqueriesruntimedetails?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–2509（total_length=2509），已到底
- 请求参数：CreateTimeAfter/CreateTimeBefore/UpdateTimeAfter/UpdateTimeBefore（RFC3339）、Filters.N.Name（精确，取值 Id/Name/Description/Status，N=1~10）、Filters.N.NameContains（模糊，同取值）、Filters.N.Values.N（Status 取值同 GetRuntime.Status）、MaxResults（1~100，默认10）、NextToken、ProjectName、TagFilters.N.Key（1~10）、TagFilters.N.Values.N（1~3）
- 返回参数：[PRODUCT]Runtimes[]（结构同 GetRuntime 单条，含 RequestModifierConfig/TosMountConfig/GatewayMode/GatewayInstanceId）、NextToken
- 错误码：页面"错误码"标题下**无表格内容**（未列举业务错误码）
- 异常：错误码章节为空。

## ListRuntimeVersions - 查询运行时所有版本详情 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListRuntimeVersions-Queriesdetailsofallruntimeversions?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–1559（total_length=1559），已到底
- 请求参数：RuntimeId（必选）、MaxResults（1~100，默认10）、NextToken
- 返回参数：[PRODUCT]RuntimeVersions[]（含 TosMountConfig/ApmplusEnable/ArtifactType/ArtifactUrl/AuthorizerConfiguration/Command/CpuMilli/CreatedAt/Description/Envs[]/MemoryMb/RoleName/RuntimeId/Status/UpdatedAt/VersionNumber）、NextToken
- 错误码：400 MissingParameter.RuntimeId；404 Invalid[PRODUCT]Runtime.NotFound
- 异常：无

## GetRuntimeInstanceLogs - 查询运行时日志 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetRuntimeInstanceLogs-Queriesruntimelogs?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–497（total_length=497），已到底
- 请求参数：RuntimeId（必选）、InstanceName（必选）、Limit（integer，0~1000，默认1000）
- 返回参数：Logs（String，日志文本）
- 错误码：400 MissingParameter.InstanceName、MissingParameter.RuntimeId
- 异常：无

## ListRuntimeInstances - 查询运行时实例信息 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListRuntimeInstances-Queriesruntimeinstanceinformation?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–535（total_length=535），已到底
- 请求参数：RuntimeId（必选）
- 返回参数：InstanceItems[].{AliasName, RuntimeId, CreateTime, InstanceName, InstanceStatus(Starting/Ready/Failed/Terminating/Unknown), RevisionNumber}、RunningInstance（integer，运行中个数）
- 错误码：400 MissingParameter.RuntimeId
- 异常：无

## AbortRuntimeRelease - 取消运行时发布 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/AbortRuntimeRelease-Cancelsruntimerelease?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–362（total_length=362），已到底
- 请求参数：RuntimeId（必选）
- 返回参数：RuntimeId
- 错误码：400 MissingParameter.RuntimeId
- 异常：无

## GetRuntimeReleaseStatus - 查询运行时发布状态 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetRuntimeReleaseStatus-Queriesruntimereleasestatus?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–853（total_length=853），已到底
- 请求参数：RuntimeId（必选）
- 返回参数：CurrentTrafficWeight（0~100，inprogress/failed时返回）、ErrorCode（function_start_failed/function_start_timeout/function_health_check_failed/system_internal_error）、FailedInstanceLogs、NewVersionNumber、OldVersionNumber（pending不返回）、ReleaseRecordId、RuntimeId、StableVersionNumber（初次发布前为-1）、StartTime（pending不返回）、Status（pending/inprogress/done/failed）、StatusMessage、TargetTrafficWeight（1~100，100=全量）
- 错误码：400 InvalidResourceStatus、MissingParameter.RuntimeId
- 异常：无

## ListRuntimeReleaseRecords - 批量查询运行时发布记录详情 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListRuntimeReleaseRecords-Batchqueriesruntimereleaserecorddetails?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–911（total_length=911），已到底
- 请求参数：RuntimeId（必选）、Filters.N.Name（精确，取值 Id/Status/SourceVersionNumber/TargetVersionNumber，N=1~10）、Filters.N.NameContains、Filters.N.Values.N、OrderBy.Key（必选，CreationTime/FinishTime）、OrderBy.Ascend（默认false降序）、PageNumber（默认1）、PageSize（1~100，默认10）
- 返回参数：Items[].{CreationTime, Description, Id, LastUpdateTime, NewVersionNumber, OldVersionNumber, RuntimeId, Status(rolling/finished/rollbacking/rollbacked/failed)}、Total
- 错误码：400 MissingParameter.Key、MissingParameter.RuntimeId
- 异常：无

## GetRuntimeWebshellEndpoint - 获取运行时实例 Webshell 连接地址 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetRuntimeWebshellEndpoint-GettheRuntimeinstanceWebshellconnectionaddress?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–599（total_length=599），已到底
- 请求参数：RuntimeId（必选）、InstanceName（必选，需 Ready 状态，通过 ListRuntimeInstances 获取）
- 返回参数：Endpoint（String，Webshell 终端连接地址，含 faasInstanceName 与 Authorization 参数）
- 错误码：400 MissingParameter.InstanceName、MissingParameter.RuntimeId；404 Invalid[PRODUCT]Runtime.NotFound
- 异常：页面含 API Explorer 调试入口链接。

## CreateTool - 创建沙箱工具 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/CreateTool-Createssandboxtool?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–2699（total_length=2699），已到底
- 关键请求参数：
  - Name（必选，4-64字符，字母数字-_,）、ToolType（必选：All-in-one/Skill/Private/CodeEnv）
  - AuthorizerConfiguration.KeyAuth.{ApiKey(可空，空则随机), ApiKeyLocation=Header, ApiKeyName(4-64)}
  - ApmplusEnable（默认true）、Description（≤200 Unicode）、Command（自定义工具时需，默认 ./run.sh）、Port（自定义工具时需，默认8000）、ImageUrl（自定义工具必填）
  - CpuMilli（All-in-one/Skill 默认2000）、MemoryMb（512~131072）
  - NetworkConfiguration.EnablePrivateNetwork/EnablePublicNetwork（二选一）；VpcId/SecurityGroupIds.N/SubnetIds.N（私网时必填，SubnetIds N=1~5）；VpcConfiguration.EnableSharedInternetAccess（私网时有效，默认true）
  - Envs.N.Key（必选，N=1~30）/Envs.N.Value（可选）
  - EnableSnapshot（默认false）、ProjectName、RoleName、ModelAgentName、SkillSpaceId、UseCodingPlan（boolean）
  - Tags.N.Key（必选，1~20）/Tags.N.Value/Tags.N.Type(system/custom)
  - TosMountConfig 全套（同 CreateRuntime）
- 返回参数：ToolId
- 错误码：400 InvalidDescription.Malformed/InvalidKey.Malformed/InvalidModelAgentName.Malformed/InvalidName.Malformed/LimitExceeded.MaximumSubnetIds/MinimumSubnetIds/MissingParameter.AuthorizerConfiguration/DiscoveryUrl/EnableLog/Key/Value/Name/NetworkConfiguration/ToolType/VpcId/NetworkType/ApiKeyName/Command/Port/ImageUrl/InvalidParameter.VpcConfiguration/ToolType/NetworkConfiguration/InvalidApiKeyLocation.Malformed/InvalidParameter.Port/InvalidEnvKey.Malformed；409 InvalidParameter.DuplicateName；500 InternalError
- 异常：无

## UpdateTool - 修改工具的描述信息 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/UpdateTool-Modifiestooldescription?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–1297（total_length=1297），已到底
- 请求参数：ToolId（必选）、Description（≤1000）、ApmplusEnable、Command、CpuMilli、Envs.N.Key（必选）/Envs.N.Value、EnableSnapshot、ImageUrl、Port、ModelAgentName、ToolType（All-in-one/Skill/PersonalAssistant/VibeSkill/Private）、MemoryMb、TosMountConfig 全套
- 返回参数：ToolId
- 错误码：400 InvalidDescription.Malformed/InvalidKey.Malformed/InvalidModelAgentName.Malformed/MissingParameter.Key/ToolId/InvalidResourceStatus/InvalidParameter.Port/ToolType/MissingParameter.ImageUrl；404 InvalidResource.NotFound
- 异常：无

## DeleteTool - 删除沙箱工具 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/DeleteTool-Deletestool?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–368（total_length=368），已到底
- 说明：删除工具同时自动回收关联 Session，不可恢复。
- 请求参数：ToolId（可选，文档标注可选但示例传入）、ClientToken（可选，≤64 ASCII 幂等）
- 返回参数：ToolId
- 错误码：页面仅提示"访问公共错误码"，**未列举业务错误码表**
- 异常：业务错误码未列举（指向公共错误码）。

## GetTool - 查询工具详情 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetTool-Queriestooldetails?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–1633（total_length=1633），已到底
- 请求参数：ToolId（必选）
- 返回参数：CpuMilli/MemoryMb/ApmplusEnable/AssociatedRuntimes[].{Id,Name}/AuthorizerConfiguration.{CustomJwtAuthorizer.{AllowedClients,DiscoveryUrl}, KeyAuth.{ApiKey,ApiKeyLocation,ApiKeyName}}/Command/CreatedAt/Description/EnableSnapshot/Envs[].{Key,Value}/ImageUrl/ModelAgentName/Name/NetworkConfigurations[].{Endpoint,NetworkType,VpcConfiguration.{EnableSharedInternetAccess,SecurityGroupIds,SubnetIds,VpcId}}/Port/ProjectName/RoleName/SkillSpaceId/Status(Creating/Error/Ready/Deleting/Updating)/Tags[].{Key,Type,Value}/ToolId/ToolType(All-in-one/Skill/VibeSkill/Private/CodeEnv)/TosMountConfig/UpdatedAt
- 错误码：400 MissingParameter.ToolId；404 InvalidResource.NotFound
- 异常：无

## ListTools - 批量查询工具详情 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListTools-Batchqueriestooldetails?lang=zh)

- 读取状态：成功读取到底（但正文为空壳）
- 读取范围：offset 0–46（total_length=46），已到底
- 关键内容：仅页面标题与导航，**无任何请求/返回参数、示例或错误码正文**。
- 异常：**空壳页面**（46字节，文档尚未填充正文）。从 API发布历史 可交叉推断：ListTools 支持 ProjectName/TagFilters.N.Key/TagFilters.N.Values.N 请求参数，返回 Tools/Tags/NetworkConfigurations/ProjectName/RoleName/ModelAgentName/EnableSnapshot/ApmplusEnable/Command/Envs/ImageUrl/Port，错误码含 LimitExceeded.MaximumFilters、InvalidTagFilterKey.Malformed。但本页未给出正式字段表。

## InvokeTool - 在工具中执行命令 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/InvokeTool-Executescommandinatool?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–1176（total_length=1176），已到底
- **重要**：调用本接口服务地址不同，使用 `https://[PRODUCT].<region>.volces.com`（非 volcengineapi.com）
- 请求参数（表格形式）：
  - Action=InvokeTool、ToolId（必选）
  - OperationType（必选，取值 RunCode，调用沙箱 /v1/jupyter/execute）
  - OperationPayload（必选，JSON 字符串：code/python代码、timeout/超时秒、kernel_name 默认python3，可选 python3.11/3.12）
  - SessionId（可选，传参但空值=新建会话）
  - UserSessionId（可选，传值则按会话路由/不存在则新建；二者都不传则默认新建 UserSessionId）
  - Ttl（Integer，60~86400秒，默认1800）
- 返回参数：ToolId、UserSessionId、SessionId、Endpoint、InternalEndpoint、Result（String，含 success/message/data.outputs 等 Jupyter 执行结果）
- 请求示例：POST `https://<INTERNAL_HOST>.com?Action=InvokeTool&Version=2025-10-30`，OperationPayload 为 JSON 字符串
- 错误码：页面仅提示"访问公共错误码"，未列举业务错误码表
- 异常：业务错误码未列举。

## AsyncExecCommand - 在工具中异步执行一条Shell命令 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/AsyncExecCommand-AsynchronouslyexecutesaShellcommandinatool?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–1029（total_length=1029），已到底
- **重要**：服务地址同为 `https://[PRODUCT].<region>.volces.com`
- 说明：异步调用，仅返回任务创建状态，用 TaskId 调 ViewAsyncCommand 查结果。
- 请求参数（表格）：ToolId（必选）、Command（必选，Shell命令）、UserSessionId（可选）、SessionId（可选）、TaskId（可选，自定义任务ID）、ExecDir（可选，默认沙箱工作目录）、Ttl（Integer，60~86400，默认1800）
- 返回参数：ToolId、UserSessionId、SessionId、TaskId、Status（初始 Running）、Command、ExecDir
- 错误码：400 MissingParameter.ToolId、MissingParameter.Command
- 异常：无

## ViewAsyncCommand - 查询异步命令执行结果 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ViewAsyncCommand-Queriestheexecutionresultofanasynchronouscommand?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–844（total_length=844），已到底
- **重要**：服务地址同为 `https://[PRODUCT].<region>.volces.com`
- 说明：建议轮询，间隔1~3秒，直到 Status=Succeeded/Failed。
- 请求参数（表格）：ToolId（必选）、TaskId（必选）、UserSessionId（可选）、SessionId（可选）、Ttl（Integer，60~86400，默认1800）
- 返回参数：ToolId、UserSessionId、SessionId、TaskId、Status（Running/Succeeded/Failed/Unknown）、Output（stdout+stderr 组合）、Command、ExitCode（Running时无意义，0=成功）
- 错误码：400 MissingParameter.ToolId、MissingParameter.TaskId
- 异常：无

## CreateSession - 创建工具会话实例 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/CreateSession-Createstoolsessioninstance?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–1313（total_length=1313），已到底
- 请求参数：ToolId（必选）、Envs.N.Key（必选，1~63字符）/Envs.N.Value（可选，≤8192字符）、Ttl（integer，60~86400秒，默认1800）、TtlUnit（minute/second默认）、TosMountPoints.N.{BucketName,BucketPath,LocalMountPath}、ImageInfo.Command（必选）/ImageInfo.Image（必选，完整URL）/ImageInfo.Port（必选，整数）、UserSessionId（可选，0~200字符，字母数字-_）、Metadata.N.Key（必选，1~10，≤128字符，不可重复）/Metadata.N.Type（可选，String/Int）/Metadata.N.Value（可选，1~10，≤256字符）
- 返回参数：Endpoint（公网）、InternalEndpoint（私网）、SessionId、UserSessionId
- 错误码：400 InvalidKey.Malformed/InvalidUserSessionId.Malformed/MissingParameter.Command/Image/Key/Port/ToolId/InvalidParameter.DuplicateUserSessionId/Ttl/InvalidResourceStatus/ErrCreateSessionFail/QuotaExceeded.ToolSessions；404 InvalidResource.NotFound
- 异常：无

## DeleteSession - 删除工具会话实例 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/DeleteSession-Deletessessioninstancesofatool?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–429（total_length=429），已到底
- 请求参数：SessionId（必选）、ToolId（可选）
- 返回参数：SessionId
- 错误码：400 MissingParameter.SessionId、MissingParameter.ToolId；404 InvalidResource.NotFound
- 异常：无

## GetSession - 查询工具会话详情 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetSession-Queriestoolsessiondetails?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–1078（total_length=1078），已到底
- 请求参数：SessionId（必选）、ToolId（必选）
- 返回参数：Metadata[].{Key,Type,Value}、CreatedAt、Endpoint、ExpireAt、InternalEndpoint、Name、SessionId、SessionMeta.{VncUrl,WebshellUrl}、Status(Starting/Ready/Failed/Terminating)、ToolType(All-in-one/Skill/PersonalAssistant/VibeSkill/Private)、TosMountPoints[].{BucketName,BucketPath,LocalMountPath}、UserSessionId
- 错误码：400 MissingParameter.SessionId、MissingParameter.ToolId；404 InvalidResource.NotFound
- 异常：无

## ListSessions - 批量查询工具会话详情 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ListSessions-Batchqueriestoolsessiondetails?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–1562（total_length=1562），已到底
- 请求参数：ToolId（必选）、CreateTimeAfter/CreateTimeBefore/ExpireTimeAfter/ExpireTimeBefore（RFC3339）、Filters.N.Name（精确，取值 Id/UserSessionId/Status，N=1~10）、Filters.N.NameContains（模糊，同取值）、Filters.N.Values.N（Status: Starting/Ready/Failed/Terminating）、MaxResults（1~100，默认100）、NextToken、Metadata.N.Key（必选，1~10，≤128字符）/Metadata.N.Value（可选，1~10，≤256字符）
- 返回参数：NextToken、SessionInfos[].{CreatedAt,Endpoint,ExpireAt,InternalEndpoint,Metadata[].{Key,Type,Value},SessionId,SessionMeta.{VncUrl,WebshellUrl},Status,ToolType,TosMountPoints[].{BucketName,BucketPath,LocalMountPath},UserSessionId}
- 错误码：400 LimitExceeded.MaximumFilters、MissingParameter.Key、MissingParameter.ToolId；404 InvalidResource.NotFound
- 异常：无

## SetSessionTtl - 配置会话实例存活时长 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/SetSessionTtl-ConfiguresTTLforsessioninstance?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–602（total_length=602），已到底
- 请求参数：SessionId（必选）、ToolId（必选）、Ttl（integer，必选，60~86400秒，默认1800）、TtlUnit（minute/second默认）
- 返回参数：ExpireAt、SessionId、ToolId
- 错误码：400 MissingParameter.SessionId、MissingParameter.ToolId、MissingParameter.Ttl、InvalidParameter.Ttl；404 InvalidResource.NotFound
- 异常：无

## GetSessionLogs - 查看工具会话日志 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetSessionLogs-Viewstoolsessionlogs?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–531（total_length=531），已到底
- 请求参数：ToolId（必选）、SessionId（必选）、Limit（integer，可选，返回最新N行，不传=全部）
- 返回参数：Logs（String，实例日志）
- 错误码：400 MissingParameter.SessionId、MissingParameter.ToolId
- 异常：无

## DeleteSessionStore - 删除会话资源 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/DeleteSessionStore-Deletessessionresources?lang=zh)

- 读取状态：成功读取到底
- 读取范围：offset 0–466（total_length=466），已到底
- 请求参数：SessionStoreId（必选）
- 返回参数：ProviderType（RDS_MYSQL/RDS_PG）、SessionStoreId、Status（Creating/CreateFailed/Ready/Deleting/DeleteFailed/Deleted/Error）
- 错误码：400 MissingParameter.SessionStoreId
- 异常：无

## GetSessionStore - 查询会话资源详情 (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GetSessionStore-Queriessessionresourcedetails?lang=zh)

- 读取状态：**失败（外部阻塞）**
- 读取范围：offset 0–5（total_length=5），已到底但仅为拦截页
- 关键内容：两次读取均返回 `<title>文档中心-火山引擎</title>` + "欢迎来到文档中心"，正文仅5字节，无任何 API 内容。
- 异常：**URL 被重定向到文档中心落地页（SPA 拦截），web.fetch 无法取到正文**。已重试1次仍失败。可能原因：该路径在新版文档站点中已迁移/改名，需浏览器渲染或新 URL。替代交叉引用：从 API列表页 与 API发布历史页 可知 GetSessionStore 返回 Status/ProviderType 字段，但本页正式字段表**未获取**。

---

## 附：read_status 中3个历史失败页的重试结果

### Agentruntimeoverview（运行时概述） (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Agentruntimeoverview?lang=zh)

- 读取状态：**本次成功读取**（此前标记"失败"）
- 读取范围：offset 0–2351（total_length=2351），已到底
- 关键内容：智能体运行时概述。Runtime 定义（安全隔离、框架/模型无关的托管运行时，自动扩缩容，内置 IAM Role）。核心能力：Serverless 全托管、自动弹性伸缩、框架/模型无关（适配 [BASE-ADK]/LangGraph/ADK）、完备访问控制、全链路可观测、与 Gateway MCP 生态打通。与自建 K8s/VM 对比表。与10个组件的关系（Gateway/A2A空间/知识库/记忆库/安全围栏/可观测/火山方舟/IAM角色/外部业务后端/沙箱模板）。4种构建方式选型（控制台/[PRODUCT] CLI/[BASE-ADK]/存量迁移/TRAE）。使用流程4步。常见理解误区9条。
- 异常：本次读取正常，无异常。read_status 应更新为"已读"。

### A2AAgentJSONfileexample（A2A Agent JSON 文件示例） (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/A2AAgentJSONfileexample?lang=zh)

- 读取状态：**仍失败（外部阻塞）**
- 读取范围：offset 0–32（total_length=32），已到底但仅为导航
- 关键内容：返回页面标题为"新功能发布记录"，正文仅32字节，含"【计费公告】[PRODUCT]商用公告"导航链接，无 JSON 示例正文。
- 异常：**该 URL 已重定向到"新功能发布记录"产品动态页**，原 A2A Agent JSON 示例内容已不在此路径。web.fetch 两次均得到相同重定向结果，交叉引用其他页面也未找到该示例内容。判定为外部阻塞：原文档已下线/迁移，无法通过当前 URL 获取。

### MCPServiceAPIfile-specificationandexamples（MCP Service API 文件规范与示例） (https://<INTERNAL_HOST>.com/docs/[PRODUCT]/MCPServiceAPIfile-specificationandexamples?lang=zh)

- 读取状态：**仍失败（外部阻塞）**
- 读取范围：offset 0–32（total_length=32），已到底但仅为导航
- 关键内容：与 A2AAgentJSONfileexample 相同，返回"新功能发布记录"页32字节导航，无 MCP Service API 文件规范正文。
- 异常：**该 URL 已重定向到"新功能发布记录"产品动态页**，原 MCP Service API 文件规范内容已不在此路径。web.fetch 两次均得到相同重定向结果。判定为外部阻塞：原文档已下线/迁移，无法通过当前 URL 获取。

---

## 统计表

| 统计项 | 数量 | 说明 |
|---|---|---|
| 分片1 待读 URL 总数 | 41 | [SHARD-1]_api_runtime_tool.txt 全部行 |
| 跳过（已读） | 1 | SkillsOverview（read_status 标记"已读"） |
| 本次实际抓取 | 40 | 分片1中非已读页面 |
| 成功读取到底（含空壳） | 39 | 含2个空壳页：APIresponse-6（36字节）、ListTools（46字节） |
| ├─ 其中正文完整可读 | 37 | 含请求参数表/返回参数表/示例/错误码齐全 |
| ├─ 其中空壳页（已到底但无正文） | 2 | APIresponse-6、ListTools |
| 部分读取（未读完分页） | 0 | 所有页面 end_offset 均等于 total_length |
| 失败（外部阻塞/重定向） | 1 | GetSessionStore（5字节落地页，重试1次仍失败） |
| 附：历史失败页重试 | 3 | Agentruntimeoverview / A2AAgentJSONfileexample / MCPServiceAPIfile |
| ├─ 重试成功 | 1 | Agentruntimeoverview（2351字节完整正文） |
| └─ 重试仍失败 | 2 | A2AAgentJSONfileexample、MCPServiceAPIfile（均重定向到"新功能发布记录"页） |

**合计**：本次共抓取 43 个页面（40分片 + 3历史重试）；成功读取到底 40 个（含2空壳），失败 3 个（GetSessionStore + 2个历史重定向页），跳过 1 个（已读），部分读取 0 个。

**关键异常汇总**：
1. GetSessionStore：URL 重定向到文档中心落地页，正文未获取，建议确认新路径。
2. A2AAgentJSONfileexample / MCPServiceAPIfile-specificationandexamples：URL 均重定向到"新功能发布记录"产品动态页，原内容疑似已迁移/下线。
3. APIresponse-6、ListTools：页面存在但正文为空壳，需后续从其他页面交叉补全（ListTools 已从 API发布历史 交叉推断部分字段）。
4. ListRuntimes、DeleteTool、InvokeTool：错误码章节为空或仅指向公共错误码，未列举业务错误码表。
