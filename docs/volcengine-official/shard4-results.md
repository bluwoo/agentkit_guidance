# Shard 4 读取结果：网关/身份/观测/评测操作指南

> 读取时间：2026-09-18
> 来源：shards/shard4_ops_gateway_identity_obs_eval.txt（46条URL）
> 读取方式：web.fetch 逐页读取，分页直到读完
> 说明：部分页面返回"欢迎来到文档中心"通用占位页或空页，已如实记录

---

## 1. 【计费公告】[PRODUCT] 网关能力全面升级及计费规则调整公告

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/billing-announcement-[PRODUCT]-gateway-capability-upgrade-and-billing-rule-adjustment-announcement?lang=zh
- **读取范围**: 0-271（完整）
- **是否到底**: 是
- **关键内容**:
  - 专属网关采用独占资源部署形态，适用于核心生产、高并发、强隔离场景
  - 规格：small_x1 - large_x4 共8种，覆盖 1.5k 至 192k QPS
  - 计费方式：按量计费，由固定实例费 + 数据处理费 + 按场景用量费用组成
  - 上线时间：计划本月内全量上线
- **异常**: 无

---

## 2. 变更专属网关实例规格说明

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/change-exclusive-gateway-instance-specifications?lang=zh
- **读取范围**: 0-235（完整）
- **是否到底**: 是
- **关键内容**:
  - 支持实时升配/降配，修改后新配置持续到下次修改或资源释放
  - 升配：新配置刊例价 ≥ 老配置刊例价；降配：新配置 < 老配置
  - 更配成功后生成"更配"类型订单，新配置实时生效
  - 计费规则：实换实付，支持代金券抵扣
- **异常**: 无

---

## 3. 开启/关闭观测服务

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/EnablingDisablingobservabilityservice?lang=zh
- **读取范围**: 0-1324（完整）
- **是否到底**: 是
- **关键内容**:
  - 开启后提供指标、链路、日志一体化观测服务并绘制观测大盘
  - 开启/关闭后需**重新发布**才生效，同时生成新版本
  - 开启后支持查看运行时、会话和Trace三个维度监控
  - 运行日志自动投递至 apmplus-server 项目下的 apmplus-server-log 日志主题
  - 操作路径：智能体运行时 → 配置信息 → 基本信息 → 查看观测数据旁编辑按钮
- **异常**: 无

---

## 4. 更新IAM角色权限

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/UpdatingIAMrolepermissions?lang=zh
- **读取范围**: 0-172（完整）
- **是否到底**: 是
- **关键内容**:
  - 支持添加或移除IAM角色权限，不支持更换IAM角色
  - 更新后需重新发布才生效
  - 操作路径：智能体运行时 → 配置信息 → 权限与访问控制 → 编辑角色权限
- **异常**: 无

---

## 5. MCP 服务通过私网域名方式接入网关实例

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/mcp-service-access-gateway-instance-via-private-domain?lang=zh
- **读取范围**: 0-41（空页/存根）
- **是否到底**: 是
- **关键内容**: 页面仅有标题和导航链接，无实际正文内容
- **异常**: 页面内容为空，可能尚未发布或已重定向

---

## 6. 创建专属网关实例

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/create-a-gateway-instance?lang=zh
- **读取范围**: 0-1171（返回通用文档中心页面）
- **是否到底**: 是
- **关键内容**: 返回"欢迎来到文档中心"通用导航页，无实际操作内容
- **异常**: 页面未渲染实际内容，可能为动态渲染或权限限制

---

## 7. 管理专属网关实例

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/manage-gateway-instances?lang=zh
- **读取范围**: 0-1171（返回通用文档中心页面）
- **是否到底**: 是
- **关键内容**: 返回"欢迎来到文档中心"通用导航页，无实际操作内容
- **异常**: 同上，页面未渲染实际内容

---

## 8. 变更专属网关实例规格

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/change-gateway-instance-specification?lang=zh
- **读取范围**: 0-3421（完整）
- **是否到底**: 是
- **关键内容**:
  - 仅状态为"运行中"或"变配失败"的实例支持变更规格
  - 支持升配和降配，降配需确保降配后规格高于业务所需
  - **网关规格表**：

| 规格 | QPS(k) | 客户端连接数(w) | MCP服务+工具集总数 |
|---|---|---|---|
| gateway_small_x1 | 1.5 | 2 | 500 |
| gateway_small_x2 | 3 | 4 | 500 |
| gateway_small_x4 | 6 | 8 | 500 |
| gateway_medium_x1 | 12 | 16 | 1,000 |
| gateway_medium_x2 | 24 | 32 | 1,000 |
| gateway_large_x1 | 48 | 64 | 2,000 |
| gateway_large_x2 | 96 | 128 | 2,000 |
| gateway_large_x4 | 192 | 256 | 2,000 |

  - 计费项：实例费（/时）、数据处理费（/GB）、公网流量费（/GB）、工具索引费（/万个/时）
- **异常**: 无

---

## 9. 配置专属网关插件

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/configure_dedicated_gateway_plugin?lang=zh
- **读取范围**: 0-5996（部分，总计10065）
- **是否到底**: 否（分页API报错，剩余内容未能读取）
- **关键内容**:
  - 网关插件是安装在专属网关实例上的扩展能力模块，用于在请求/响应处理链中干预数据
  - **当前仅 MCP 类型专属网关实例支持插件能力**
  - 两种插件类型：
    - **凭据转换**：将请求中的认证凭据按规则转换后发往后端服务。支持 Header/Query → POST Body JSON路径、Header → GET Query、移除原凭据位置、屏蔽内部认证Header
    - **自定义服务扩展**：将自有函数服务接入网关处理链路，可修改请求头/体、响应头/体，或直接返回自定义响应。用于自定义签名鉴权、审计风控拦截
  - 安装后不自动影响线上请求，需配置规则后才生效
  - 规则配置：生效范围（仅MCP服务）、匹配条件（可不配置，最多5个/配置组）、最多10个配置组
- **异常**: 分页偏移量超出范围，剩余约4000字符未读取

---

## 10. 查看共享网关信息

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/view-shared-gateway-info?lang=zh
- **读取范围**: 0-2399（完整）
- **是否到底**: 是
- **关键内容**:
  - 首次选择共享网关模式创建资源时系统自动下单共享网关
  - **免费额度**：智能体运行时每账号每地域2个免费；MCP服务+MCP工具集合计2个免费
  - 存量资源（2026年8月31日前创建）默认升级为共享网关模式但不立即计费
  - 共享网关模式有QPS限制，仅建议POC/开发测试使用，生产推荐专属网关
  - 可查看网关ID、内部服务数量、计费状态
- **异常**: 无

---

## 11. 创建 MCP 服务

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/CreatingMCPservice?lang=zh
- **读取范围**: 0-5998（部分，总计11375）
- **是否到底**: 否
- **关键内容**:
  - 三种创建方式：部署MCP服务、导入MCP服务、HTTP转MCP
  - 兼容MCP协议版本：2026-07-28、2025-11-25、2025-06-18、2025-03-26
  - 所属网关：专属网关（推荐，生产）或共享模式（POC/测试），创建后不可更换
  - 协议支持：仅 Streamable HTTP
  - 入站认证：API Key（最多1个）或 OAuth JWT（最多5个客户端），互斥；生产环境必须开启
  - 后端配置：JSON配置（command+args）或镜像（镜像+启动命令+环境变量）
  - 部署方式需网络打通（TR/专线/DNS UDP/TCP 53）
  - 共享模式后端类型：函数服务、容器服务、云服务器、固定域名；专属网关：函数服务、云服务器、固定域名
- **异常**: 分页未读完，HTTP转MCP方式的详细参数未获取

---

## 12. 调试 MCP 服务

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/TestingMCPservice?lang=zh
- **读取范围**: 0-2532（完整）
- **是否到底**: 是
- **关键内容**:
  - 三步调试：①选择域名并连接测试 ②选择调试工具 ③输入参数测试工具
  - 公网域名调试对所有用户开放；私网域名调试为邀测
  - 调试操作经过网关并计入计费项用量
- **异常**: 无

---

## 13. 添加 MCP 工具

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/AddingMCPtools?lang=zh
- **读取范围**: 0-10（通用占位页）
- **是否到底**: 是
- **关键内容**: 返回"欢迎来到文档中心，敬请期待更多模块"
- **异常**: 页面未渲染实际内容

---

## 14. 更新入站身份认证信息（MCP服务）

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Updatinginboundidentityauthentication?lang=zh
- **读取范围**: 0-2473（完整）
- **是否到底**: 是
- **关键内容**:
  - 不支持切换认证类型，仅可在原类型基础上变更
  - API Key最多5个；新增Key不影响旧Key；删除Key后对应调用方鉴权失败
  - OAuth JWT：可变更关联的用户池和客户端
  - 修改/删除后未同步更新凭证的调用方可能无法访问
- **异常**: 无

---

## 15. 查看 MCP 服务网络信息

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/view-mcp-service-network-info?lang=zh
- **读取范围**: 0-5（通用占位页）
- **是否到底**: 是
- **关键内容**: 返回"欢迎来到文档中心"
- **异常**: 页面未渲染实际内容

---

## 16. 查看 MCP 服务启动失败日志

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ViewinglogsforMCPservicestartupfailures?lang=zh
- **读取范围**: 0-2271（完整）
- **是否到底**: 是
- **关键内容**:
  - 仅适用于部署类型MCP服务，状态为"不可用"时可查看
  - 操作：悬停状态列"不可用"→ 单击"查看日志"→ 弹出MCP服务日志对话框
  - 日志内容包含 FaaS System 日志，可排查镜像、启动命令、环境变量、网络问题
- **异常**: 无

---

## 17. 删除 MCP 服务

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/DeletingMCPservices?lang=zh
- **读取范围**: 0-5（通用占位页）
- **是否到底**: 是
- **关键内容**: 返回"欢迎来到文档中心"
- **异常**: 页面未渲染实际内容

---

## 18. 创建 MCP 工具集

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/CreatingMCPtoolset?lang=zh
- **读取范围**: 0-2640（完整）
- **是否到底**: 是
- **关键内容**:
  - 三种调用模式：全量返回（≤20工具）、语义检索（多工具通用Agent，收工具索引费）、标签检索（多工具垂直Agent）
  - 兼容MCP协议版本同MCP服务
  - 入站认证：API Key（最多1个）或 OAuth JWT（最多5个客户端）
  - 工具添加：共享模式仅选共享模式+API Key+公网的MCP服务；专属网关仅选当前网关实例下的MCP服务
  - 创建后请求次数同时计入工具集和MCP服务用量
- **异常**: 无

---

## 19. 调试 MCP 工具集

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/TestingMCPtoolset?lang=zh
- **读取范围**: 0-2798（完整）
- **是否到底**: 是
- **关键内容**:
  - 四步调试：①连接测试 ②按模式筛选工具（全量直接选/语义检索输入自然语言/标签检索选标签）③选择工具 ④输入参数测试
  - 语义检索模式需先输入自然语言再检索工具
- **异常**: 无

---

## 20. 在 MCP 工具集添加/移除工具

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/AddingRemovingMCPtools?lang=zh
- **读取范围**: 0-4473（部分，总计6574）
- **是否到底**: 否
- **关键内容**:
  - 添加工具：选择MCP服务 → 选择工具 → 确定
  - 移除工具：单个移除或批量移除
  - **工具集至少保留1个MCP工具，不能全部移除**
  - 移除后依赖该工具的Agent可能调用失败或检索结果变化
- **异常**: 分页未读完，移除确认弹窗等细节未获取

---

## 21. 更新入站身份认证信息（MCP工具集）

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Updatinginboundidentityauthentication-1?lang=zh
- **读取范围**: 0-1171（通用文档中心页面）
- **是否到底**: 是
- **关键内容**: 返回通用文档中心导航页
- **异常**: 页面未渲染实际内容

---

## 22. 查看 MCP 工具集网络信息

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/check-mcp-toolset-network-info?lang=zh
- **读取范围**: 0-2255（完整）
- **是否到底**: 是
- **关键内容**:
  - 仅私网访问的工具集可查看VPC和子网ID
  - 用于将VPC/子网配置到数据库等目标服务的访问白名单
  - 可点击跳转查看IPv4 CIDR等详细信息
- **异常**: 无

---

## 23. 删除 MCP 工具集

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/DeletingMCPtoolsets?lang=zh
- **读取范围**: 0-1241（完整）
- **是否到底**: 是
- **关键内容**:
  - 删除后不可恢复
  - 如有Agent或调用方依赖，删除后直接导致调用失败
  - 操作：MCP工具集列表 → 操作列"删除"
- **异常**: 无

---

## 24. 管理模型网关用量

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/manage_model_gateway_usage?lang=zh
- **读取范围**: 0-4999（部分，总计7635）
- **是否到底**: 否
- **关键内容**:
  - 从Proxy API Key和模型两个维度控制Token用量
  - **Proxy API Key限流**：速率限制（百万TPM）、每日额度（百万Token，0点重置）、每周额度（周一0点重置）、每月额度（1日0点重置）
  - 模型范围：全部模型或自定义范围（可选供应商和具体模型）
  - 支持自动授权新增模型
  - 触发限制返回HTTP 429，被拒请求不产生Token用量
  - 模型速率限制：多Key共享同一Provider下同一模型的每分钟Token上限
- **异常**: 分页未读完，模型速率限制配置的后续步骤未获取

---

## 25. MCP服务API文件规范与示例

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/MCPserviceAPIfilespecificationsandexamples?lang=zh
- **读取范围**: 0-680（完整）
- **是否到底**: 是
- **关键内容**:
  - 用于将存量API快速转换为MCP服务
  - **语法要求**：Swagger/OpenAPI 3，必须包含元数据title和version，建议设置operationId
  - **请求方法**：仅支持GET/POST/PUT/DELETE/PATCH
  - **请求类型**：支持JSON和Form，不支持XML/multipart/binary
  - **参数**：array类型序列化为CSV，不支持file类型参数
  - **响应**：仅解析200/201/default，优先级200>201>default
  - 提供Swagger 2.0和OpenAPI 3.0完整JSON示例
- **异常**: 无

---

## 26. 开通智能体身份和权限管理平台并完成授权

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/activate-the-agent-identity-and-permission-management-platform-and-complete-authorization?lang=zh
- **读取范围**: 0-1227（完整）
- **是否到底**: 是
- **关键内容**:
  - 服务开通是全局一次性操作，所有地域自动生效
  - 前提：已完成企业实名认证
  - 开通两个服务：Agent Identity（按量计费）和密钥管理服务（按量计费）
  - 开通后自动创建服务关联角色 **ServiceRoleForID**
  - 操作：登录平台 → 勾选同意条款 → 单击开通并授权
- **异常**: 无

---

## 27. 入站授权：为你的 Agent 开启快速登录功能

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/inbound-authorization-enable-quick-login-function-for-your-agent?lang=zh
- **读取范围**: 0-7766（部分，总计10043；后续分页因缓存问题无法重新读取）
- **是否到底**: 约77%
- **关键内容**:
  - **步骤一：创建用户池**：用户池名称、用户登录属性（用户名/手机号/邮箱）、注册属性、所属项目
  - **步骤二：创建客户端**：客户端名称、类型（Web应用/SPA/移动应用/M2M）、授权回调URL（必须与代码中Redirect URI完全一致，否则redirect_uri_mismatch）
  - **步骤三：创建用户**：用户名、手机号、临时密码（必须含数字+特殊字符+大小写字母，≥8位）、附加属性
  - **步骤四：集成OIDC**：Agent Identity兼容标准OIDC协议
    - OIDC发现端点（Discovery URL）→ ISSUER_URL/AUTHORITY
    - 客户端ID → CLIENT_ID
    - 客户端密钥 → CLIENT_SECRET
  - 支持使用任意OIDC客户端库（Python authlib, Node.js openid-client）
- **异常**: 首次读取后页面被缓存为"容器服务"，剩余约23%（OIDC集成代码示例和验证步骤）未获取

---

## 28. 入站授权：集成企业 SSO 实现联合登录

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/inbound-authorization-integrate-enterprise-sso-to-implement-federated-login?lang=zh
- **读取范围**: 0-5846（完整）
- **是否到底**: 是
- **关键内容**:
  - 前提：已开通平台，已获取外部IdP的Issuer/Discovery URL、Client ID、Client Secret
  - **步骤一：创建用户池**（同快速登录）
  - **步骤二：创建客户端**（同快速登录）
  - **步骤三：添加外部身份提供商**：
    - 提供商名称（展示在登录页）、类型选OIDC
    - 发行者URL、Client ID、Client Secret
    - 授权作用域至少openid
    - 用户身份联动配置：ID Token映射、授权码安全模式、允许新用户注册、自动创建用户、自动更新用户属性
  - **步骤四：回填回调地址**：复制系统生成的OIDC登录回调地址，填入外部IdP的Redirect URI
  - 验证：登录页出现新按钮 → 跳转企业登录页 → 完成登录 → 跳回Agent获取Token
- **异常**: 无

---

## 29. 出站授权：Agent 代表用户访问第三方资源

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/outbound-authorization-agent-represents-the-user-to-access-thirdparty-resources?lang=zh
- **读取范围**: 0-9144（完整，通过snippet补全）
- **是否到底**: 是
- **关键内容**:
  - 以访问飞书开放平台为例，配置OAuth Client
  - 步骤一~三：创建用户池、客户端、用户（同前）
  - **步骤四：配置OAuth Client**：
    - 路径：身份凭据托管 → 新建OAuth Client
    - 提供商名称、类型（飞书）、Client ID/Secret、权限范围（如contact:user.base:readonly）、回调URL
  - **步骤五：回填回调地址**：将OIDC登录回调地址填入飞书开放平台 → 开发配置 → 安全设置 → 重定向URL
  - **验证机制**：
    - 首次调用：平台检测无有效授权 → 返回重定向URL → 用户登录授权 → 保存Refresh Token
    - 后续调用：平台利用Refresh Token后台静默获取新Access Token，对用户透明
  - 可查看托管凭据但无法直接看到Refresh Token；撤销授权可删除出站凭据配置
- **异常**: 无

---

## 30. 出站授权：Agent 代表用户访问火山引擎资源

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/outbound-authorization-agent-represents-the-user-to-access-volcano-engine-resources?lang=zh
- **读取范围**: 已在read_status.json中标记为"已读"
- **是否到底**: 是（此前分片已读）
- **关键内容**: 略（见此前分片结果）
- **异常**: 无

---

## 31. 添加外部身份提供商

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/add-an-external-identity-provider?lang=zh
- **读取范围**: 0-2844（完整）
- **是否到底**: 是
- **关键内容**:
  - 支持OAuth 2.0、OIDC、SAML 2.0三种协议类型
  - **OAuth 2.0配置**：客户端ID/密钥、授权范围（至少openid）、授权端点、令牌端点、用户信息端点、PKCE
  - **OIDC配置**：Issuer URL、客户端ID/密钥、授权范围、PKCE、ID Token映射用户属性
  - **SAML 2.0配置**：SAML元数据XML、签名认证、加密、用户属性映射、用户唯一标识属性(NameID)、自动链接配置
  - **预置飞书（OAuth2.0）**：Client ID/Secret、默认作用域contact:user.base:readonly和contact:contact.base:readonly
  - 所有类型均支持：允许新用户注册、自动创建账号、自动更新用户信息
  - 创建后提供商类型不可修改，需删除重建
- **异常**: 无

---

## 32. 创建权限策略

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/create-permission-policies?lang=zh
- **读取范围**: 0-4142（完整）
- **是否到底**: 是
- **关键内容**:
  - 基于 **Cedar 声明式授权语言**，覆盖 User→Agent→Tool 全链路
  - **核心概念**：
    - Cedar语言：声明式策略语言，定义"谁能对什么执行什么操作"
    - 策略空间(Policy Space)：策略的逻辑容器，按项目/场景隔离
    - 链式鉴权：用户→智能体→工具逐级校验
  - **步骤一**：创建策略空间（名称、描述、所属项目、标签）
  - **步骤二**：创建权限策略
    - 可视化编辑：效果（允许/拒绝）、用户（用户池+用户）、中间层Agent（最多5级）、资源（类型+ID）
    - Cedar代码编辑：直接编写 permit/forbid(principal, action, resource) 语句
    - 示例：`permit(principal == user::"alice", action == Action::"invoke", resource == agent::"trip_agent");`
  - **步骤三**：管理策略（筛选、展开查看Cedar代码、删除）
  - **步骤四**：模拟权限校验——配置完整调用链（用户+1~5级Agent+资源），返回通过/拒绝
- **异常**: 无

---

## 33. 创建权限网关

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/create-permission-gateway?lang=zh
- **读取范围**: 0-4031（部分，总计5439）
- **是否到底**: 否
- **关键内容**:
  - 基于火山引擎API网关(APIG)构建，无侵入式全链路权限管控
  - **工作原理**：流量劫持（专属劫持域名）→ 策略关联（绑定权限空间）→ 自动校验（解析用户/Agent/资源身份）→ 智能放行/拒绝
  - **步骤一：创建权限网关服务**：
    - 服务名称、后端服务类型（自定义HTTP/HTTPS 或 VikingDB）
    - 关联权限空间
    - 后端域名、端口、超时时间
  - **步骤二：配置路由规则**：
    - 自动解析：上传OpenAPI/Swagger或自然语言描述文档，自动生成路由
    - 手动配置：路由名称、请求方法、接口路径（支持路径变量如/api/documents/{docId}）、匹配类型（前缀/精确）
    - 关联资源：资源类型、位置（Header/Body/Path）、字段名（JSONPath如$.data.items[*].id）、是否作为鉴权对象
- **异常**: 分页未读完，发布步骤和后续配置未获取

---

## 34. 开启安全围栏

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/EnablingGuardrails?lang=zh
- **读取范围**: 0-3449（完整）
- **是否到底**: 是
- **关键内容**:
  - 前提：已开启大模型防火墙服务
  - 单个安全围栏服务资产最多绑定100个智能体运行时
  - 两种开启方式：创建运行时时开启 / 为已有运行时开启
  - 支持自动创建（输入名称自动创建绑定）或选择已有
  - **启用后必须发布运行时才生效**
  - 后续需在Agent中集成安全围栏服务，否则防护策略不生效
  - 防护能力：提示词攻击防护、模型滥用防护、敏感数据防护、算力消耗防护
- **异常**: 无

---

## 35. 关闭安全围栏

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/DisablingGuardrails?lang=zh
- **读取范围**: 0-1140（完整）
- **是否到底**: 是
- **关键内容**:
  - 关闭后失去提示词攻击、模型滥用、敏感数据、算力消耗等防护
  - 操作：智能体运行时 → 安全围栏页签 → 单击开关 → 确定
- **异常**: 无

---

## 36. 查看MCP服务监控数据

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ViewingMCPservicemonitoringdata?lang=zh
- **读取范围**: 0-657（完整）
- **是否到底**: 是
- **关键内容**:
  - 对接云监控，仅运行中状态可查看
  - 查询限制：单次最小1小时最大15天，仅支持过去30天数据，采集频率30s
  - **指标列表**：

| 分类 | 指标名称 | 单位 | 说明 |
|---|---|---|---|
| 服务调用 | 请求次数 | Count | 接收的总请求量 |
| 服务调用 | 请求分布（范围/精确） | Count | 范围维度和精确对象维度统计 |
| 服务调用 | 平均延迟 | ms | 处理请求平均耗时 |
| 服务调用 | 出向响应带宽 | bit/s | 每秒流出流量（公网+私网） |
| 服务调用 | 公网出向响应带宽 | bit/s | 公网访问时每秒响应流量 |
| 服务运行 | CPU使用率 | % | 所有实例CPU使用率平均值 |
| 服务运行 | 内存使用率 | % | 所有实例内存使用率平均值 |
| 服务运行 | 实例数量 | Count | 运行中的实例数量 |

  - 服务运行指标仅部署方式（JSON配置或镜像）支持
- **异常**: 无

---

## 37. 查看MCP工具集监控数据

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ViewingMCPtoolsetmonitoringdata?lang=zh
- **读取范围**: 0-1709（完整）
- **是否到底**: 是
- **关键内容**:
  - 查询限制同MCP服务
  - **指标列表**：

| 指标名称 | 单位 | 说明 |
|---|---|---|
| 请求次数 | Count | 收到客户端请求总次数 |
| 请求分布（范围/精确） | Count | 范围/精确维度统计 |
| 平均延时 | ms | 处理请求平均耗时 |
| 出向响应带宽 | bit/s | 每秒向客户端响应流量 |
| 公网出向响应带宽 | bit/s | 公网访问时公网流量 |
| 语义检索请求次数 | Count | search_tools请求调用总次数 |
| 语义检索请求任务数 | Count | search_tools总任务数（≥请求次数） |
| 标签检索请求次数 | Count | list_tools_by_tags调用总次数 |
| 语义检索工具索引数 | Count | 内部构建的工具索引数量 |

- **异常**: 无

---

## 38. 查看网关实例监控数据

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Viewgatewayinstancemonitoringdata?lang=zh
- **读取范围**: 0-41（空页/存根）
- **是否到底**: 是
- **关键内容**: 页面仅有标题和导航链接，无实际正文
- **异常**: 页面内容为空

---

## 39. 数据回流

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/data-return?lang=zh
- **读取范围**: 0-959（完整）
- **是否到底**: 是
- **关键内容**:
  - **目的**：将线上Trace数据批量导出至评测集，形成标准化链路样本库，用于链路诊断算法验证、检测规则优化、异常识别效果评估
  - **使用限制**：
    - 导出总上限和单次导出上限均为 **100000条**
    - 仅支持回流新数据，不支持回流历史数据
  - **操作路径**：[PRODUCT]控制台 → 可观测 → 数据回流 → 创建导出任务
  - **配置参数**：
    - 基础信息：任务名称、数据总上限（每任务最多100000条）
    - 数据过滤：Span类型、AI Span类型、服务名称、模型名称、接口名、状态码、操作、耗时（同筛选项内"或"逻辑，跨筛选项"与"逻辑）
    - 时间范围：回流新数据、总时间范围、重复频率（不重复/按天重复/按周重复）
    - 导出配置：导出平台（智能体评测平台）、数据脱敏（默认开启，关闭可导出完整Input/Output）、目标评测集（已有或新增）、导入方式（追加数据）、字段映射（Trace Span字段→评测集字段）
  - **后续操作**：暂停/开启、复制、编辑、删除
- **异常**: 无

---

## 40. 埋点字段与指标说明

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Trackingfieldsandmetricsdescription?lang=zh
- **读取范围**: 0-208（完整导航页）
- **是否到底**: 是
- **关键内容**:
  - **本页为导航/概述页，详细字段定义在两个外部子页面中**
  - **AI应用监控**：在[PRODUCT] SDK内部接入OpenTelemetry埋点，涵盖分布式追踪（Tracing）和指标监控（Metrics）两大核心模块
  - **[BASE-ADK]**：在[BASE-ADK] SDK内部接入OpenTelemetry埋点，涵盖通用类、LLM类和Tool类三大核心模块
  - 两个子页面链接文本为"[PRODUCT]埋点字段与指标说明"和"[BASE-ADK]埋点与字段说明"，但实际URL不在[PRODUCT]文档路径下（尝试猜测URL失败，重定向到新功能发布记录页）
- **异常**: **详细埋点字段定义页面未能获取**——子页面为动态渲染链接，实际URL未在文档站静态HTML中暴露，可能在APMPlus或[BASE-ADK]独立文档站中。此为**关键缺口**。

---

## 41. 日志字段说明

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Logfielddescription-5?lang=zh
- **读取范围**: 0-340（完整）
- **是否到底**: 是
- **关键内容**:
  - [PRODUCT]专用日志存储在 **apmplus-server** 项目下的 **apmplus-server-log** 日志主题中
  - 完整字段表见文件末尾"附录A：日志字段表"
- **异常**: 无

---

## 42. 管理评测集（[PRODUCT]控制台）

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/management-evaluation-set?lang=zh
- **读取范围**: 0-4912（部分，总计17739）
- **是否到底**: 否
- **关键内容**:
  - 评测集包含：输入数据(input)、预期输出(reference_output)、实际输出(actual_output)
  - **限制**：最多5000条测试数据，文件最大200MB，最多50个自定义列
  - **设计原则**：覆盖核心链路、评估范围全面、覆盖极端/异常场景、覆盖异常案例
  - **步骤一**：新建评测集（名称、描述、配置列——默认input和reference_output，支持自定义列含名称/数据类型/Required/描述）
  - **步骤二**：添加数据——手动添加（最多10条/次）或本地导入（csv/xlsx/xls，追加或全量覆盖）
  - **步骤三**：提交评测集版本
  - 需先开通Agent运营分析服务（IAM角色ServiceRoleForUBA）
- **异常**: 分页未读完，版本管理、关联实验等后续内容未获取

---

## 43. 管理实验评估器

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/management-experiment-evaluator?lang=zh
- **读取范围**: 0-4448（部分，总计10871）
- **是否到底**: 否
- **关键内容**:
  - 评估器充当裁判角色，LLM评估器根据Prompt标准打分，得分范围0.0~1.0
  - **创建评估器**：名称、描述、模型选择（含max_tokens/temperature/top_p）、Prompt（System Prompt + 可选User Prompt，User Prompt优先级更高）
  - **预置模板**：Agent任务完成度、简洁性、争议性、正确性、创造性、犯罪性、深度性、细节性、事实准确性、幻觉现象、有害性等
  - 支持调试预览——构造测试数据预览评估结果
- **异常**: 分页未读完，管理和版本功能未获取

---

## 44. 管理评测实验

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/management-evaluation-experiment?lang=zh
- **读取范围**: 0-4693（部分，总计27708）
- **是否到底**: 否
- **关键内容**:
  - 实验 = 评测数据集 + 评测对象 + 若干评估器
  - **前提条件**：评测集必须；Agent/A2A Agent可选（不选则评测评测集本身）；评估器可选（不选仅获取实际输出，适用于人工标注）
  - **新建实验步骤**：
    1. 基础信息：名称、描述、最大并发执行条数（默认5，最多20）
    2. 评测集：选择评测集和版本
    3. 评测对象（可选）：Agent或A2A Agent，字段映射
    4. 评估器（可选）：最多10个，选择评估器和版本，配置字段映射
  - 发起实验后等待执行完成，查看数据明细和指标统计
- **异常**: 分页未读完，结果分析和实验对比等大量内容未获取

---

## 45. 为IAM用户授权[PRODUCT]权限

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Granting[PRODUCT]permissionstoIAMusers?lang=zh
- **读取范围**: 0-4435（部分，总计12911）
- **是否到底**: 否
- **关键内容**:
  - 支持直接为IAM用户授权或将IAM用户加入用户组继承权限
  - **系统策略**：
    - [PRODUCT]DeveloperAccess（推荐）：全功能开发权限，大于只读小于完全管理
    - [PRODUCT]ReadOnlyAccess：只读权限
    - [PRODUCT]FullAccess：完全管理权限
    - [PRODUCT]TosAccess：TOS服务权限
    - [PRODUCT]ToolAccess：工具服务权限
  - 支持限制到项目资源
  - 操作路径：访问控制控制台 → 用户/用户组 → 添加权限 → 选择策略 → 提交
- **异常**: 分页未读完，服务依赖权限说明和策略详情未获取

---

## 46. 网关FAQ

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GatewayFAQ?lang=zh
- **读取范围**: 0-165（完整）
- **是否到底**: 是
- **关键内容**:
  - 如何访问MCP服务？→ 在MCP服务详情查看调用示例
  - 403 Forbidden RBAC: access denied？→ 使用携带认证API Key的请求
  - 是否支持SSE协议？→ 暂不支持，建议使用Streamable HTTP
  - 是否支持STDIO类型MCP远程访问？→ 支持，创建时选择STDIO类型自动转换为remote MCP
- **异常**: 无

---

## 47. 观测FAQ

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ObservabilityFAQ?lang=zh
- **读取范围**: 0-122（完整）
- **是否到底**: 是
- **关键内容**:
  - Trace数据是否可导出本地？→ 可在Trace界面选中后本地下载
  - 数据观测是否有免费额度？→ 暂无，公测期间可申请APMPlus代金券
  - 是否必须开启数据观测才能评测？→ 是，Trace信息是评测必须数据
- **异常**: 无

---

## 48. 管理评测集（DeliveryAI评测中心）

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/management_evaluation_set?lang=zh
- **读取范围**: 0-4599（完整）
- **是否到底**: 是
- **关键内容**:
  - 这是 **DeliveryAI** 评测中心的评测集管理，与第42页（[PRODUCT]控制台评测集）是不同产品
  - 两类评测集：系统内置（预置示例）和自定义
  - **创建方式一：从Trace汇集**——选择需求，从历史执行记录筛选用例形成评测集
  - **创建方式二：上传评测集**——本地JSONL/CSV文件导入
  - 查看用例明细：用例名称、所属节点、输入和输出
  - 前提：当前账号在DeliveryAI空间中为空间管理员
- **异常**: 无

---

## 49. 管理评测任务（DeliveryAI评测中心）

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Managementevaluationtasks?lang=zh
- **读取范围**: 0-2583（完整）
- **是否到底**: 是
- **关键内容**:
  - **DeliveryAI** 评测中心功能
  - 评测任务 = 选定评估器 + 评测数据执行一次质量评估
  - **报告内容**：总分（100分基准，负分制）、通过率、节点得分、低分用例
  - **新建任务参数**：名称、流程（可选）、需求来源（生产Trace选择需求 或 使用评测集）、评测节点、评估器
  - 支持按"内置数据集/自定义数据集/需求"筛选
- **异常**: 无

---

## 50. 管理 MCP（DeliveryAI Agent配置）

- **URL**: https://<INTERNAL_HOST>.com/docs/[PRODUCT]/manage-mcp?lang=zh
- **读取范围**: 0-4923（部分，总计5966）
- **是否到底**: 否
- **关键内容**:
  - **DeliveryAI** 产品设置中的MCP管理，面向空间管理员
  - **MCP列表字段**：MCP名称、类型（系统内置/自定义）、URL、状态、传输方式、接入时间、描述、Header配置摘要
  - **创建MCP Server参数**：
    - 名称（必填）、URL（必填）
    - Bearer令牌环境变量（推荐，不明文填写Token）
    - 固定Header（名称+值）
    - 来自环境变量的Header（Header名+环境变量名）
    - 描述
  - 支持编辑和删除自定义MCP Server
- **异常**: 分页未读完，删除确认等细节未获取

---

## 统计表

| 序号 | 页面标题 | URL关键词 | 读取状态 | 是否完整 | 备注 |
|---|---|---|---|---|---|
| 1 | 计费公告-网关能力升级 | billing-announcement-... | 已读 | 是 | |
| 2 | 变更专属网关实例规格说明 | change-exclusive-gateway-instance-specifications | 已读 | 是 | |
| 3 | 开启/关闭观测服务 | EnablingDisablingobservabilityservice | 已读 | 是 | |
| 4 | 更新IAM角色权限 | UpdatingIAMrolepermissions | 已读 | 是 | |
| 5 | MCP服务通过私网域名接入 | mcp-service-access-gateway-instance-via-private-domain | 已读 | 是(空页) | 无正文内容 |
| 6 | 创建专属网关实例 | create-a-gateway-instance | 已读 | 否(占位页) | 返回通用文档中心页 |
| 7 | 管理专属网关实例 | manage-gateway-instances | 已读 | 否(占位页) | 返回通用文档中心页 |
| 8 | 变更专属网关实例规格 | change-gateway-instance-specification | 已读 | 是 | 含规格表 |
| 9 | 配置专属网关插件 | configure_dedicated_gateway_plugin | 已读 | 部分 | 约60%，分页API报错 |
| 10 | 查看共享网关信息 | view-shared-gateway-info | 已读 | 是 | |
| 11 | 创建MCP服务 | CreatingMCPservice | 已读 | 部分 | 约53%，含三种创建方式参数表 |
| 12 | 调试MCP服务 | TestingMCPservice | 已读 | 是 | |
| 13 | 添加MCP工具 | AddingMCPtools | 已读 | 否(占位页) | 返回通用文档中心页 |
| 14 | 更新入站身份认证(MCP服务) | Updatinginboundidentityauthentication | 已读 | 是 | |
| 15 | 查看MCP服务网络信息 | view-mcp-service-network-info | 已读 | 否(占位页) | 返回通用文档中心页 |
| 16 | 查看MCP服务启动失败日志 | ViewinglogsforMCPservicestartupfailures | 已读 | 是 | |
| 17 | 删除MCP服务 | DeletingMCPservices | 已读 | 否(占位页) | 返回通用文档中心页 |
| 18 | 创建MCP工具集 | CreatingMCPtoolset | 已读 | 是 | |
| 19 | 调试MCP工具集 | TestingMCPtoolset | 已读 | 是 | |
| 20 | 在MCP工具集添加/移除工具 | AddingRemovingMCPtools | 已读 | 部分 | 约68% |
| 21 | 更新入站身份认证(MCP工具集) | Updatinginboundidentityauthentication-1 | 已读 | 否(占位页) | 返回通用文档中心页 |
| 22 | 查看MCP工具集网络信息 | check-mcp-toolset-network-info | 已读 | 是 | |
| 23 | 删除MCP工具集 | DeletingMCPtoolsets | 已读 | 是 | |
| 24 | 管理模型网关用量 | manage_model_gateway_usage | 已读 | 部分 | 约65% |
| 25 | MCP服务API文件规范与示例 | MCPserviceAPIfilespecificationsandexamples | 已读 | 是 | |
| 26 | 开通身份权限平台并授权 | activate-the-agent-identity... | 已读 | 是 | |
| 27 | 入站快速登录(额外发现页) | inbound-authorization-enable-quick-login... | 已读 | 部分 | 约77%，缓存问题 |
| 28 | 入站企业SSO联合登录(额外发现页) | inbound-authorization-integrate-enterprise-sso... | 已读 | 是 | |
| 29 | 出站第三方资源(额外发现页) | outbound-authorization...thirdparty... | 已读 | 是 | |
| 30 | 出站火山引擎资源(额外发现页) | outbound-authorization...volcano... | 已读 | 是(此前已读) | read_status中已标记 |
| 31 | 添加外部身份提供商 | add-an-external-identity-provider | 已读 | 是 | |
| 32 | 创建权限策略 | create-permission-policies | 已读 | 是 | |
| 33 | 创建权限网关 | create-permission-gateway | 已读 | 部分 | 约74% |
| 34 | 开启安全围栏 | EnablingGuardrails | 已读 | 是 | |
| 35 | 关闭安全围栏 | DisablingGuardrails | 已读 | 是 | |
| 36 | 查看MCP服务监控数据 | ViewingMCPservicemonitoringdata | 已读 | 是 | 含指标表 |
| 37 | 查看MCP工具集监控数据 | ViewingMCPtoolsetmonitoringdata | 已读 | 是 | 含指标表 |
| 38 | 查看网关实例监控数据 | Viewgatewayinstancemonitoringdata | 已读 | 是(空页) | 无正文内容 |
| 39 | 数据回流 | data-return | 已读 | 是 | |
| 40 | 埋点字段与指标说明 | Trackingfieldsandmetricsdescription | 已读 | 是(导航页) | **详细字段在外部子页面，未能获取** |
| 41 | 日志字段说明 | Logfielddescription-5 | 已读 | 是 | 含完整字段表 |
| 42 | 管理评测集([PRODUCT]) | management-evaluation-set | 已读 | 部分 | 约28% |
| 43 | 管理实验评估器 | management-experiment-evaluator | 已读 | 部分 | 约41% |
| 44 | 管理评测实验 | management-evaluation-experiment | 已读 | 部分 | 约17% |
| 45 | 为IAM用户授权[PRODUCT]权限 | Granting[PRODUCT]permissionstoIAMusers | 已读 | 部分 | 约34% |
| 46 | 网关FAQ | GatewayFAQ | 已读 | 是 | |
| 47 | 观测FAQ | ObservabilityFAQ | 已读 | 是 | |
| 48 | 管理评测集(DeliveryAI) | management_evaluation_set | 已读 | 是 | |
| 49 | 管理评测任务(DeliveryAI) | Managementevaluationtasks | 已读 | 是 | |
| 50 | 管理MCP(DeliveryAI) | manage-mcp | 已读 | 部分 | 约83% |

**汇总统计**：
- 总计读取页面：50页（46个shard4 URL + 4个额外发现的身份快速入门页面）
- 完整读取：32页（64%）
- 部分读取：11页（22%）——分页API限制或页面过长
- 占位/空页：7页（14%）——返回"欢迎来到文档中心"或无正文

---

## 附录A：日志字段表（日志字段说明页完整提取）

> 来源：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Logfielddescription-5?lang=zh
> [PRODUCT]专用日志存储在 **apmplus-server** 项目下的 **apmplus-server-log** 日志主题中

| 字段名称 | 示例值 | 类型 | 说明 |
|---|---|---|---|
| `attribute` | `{"exception.message":"helloworld","exception.type":"*errors.fundamental","foo":"bar","span_id":"698e4273e1a06c01"}` | JSON对象 | 日志对应的其他属性。包含异常信息、span_id等 |
| `file_line` | `uptracezap_demo.go:10` | String | 日志对应的文件行数 |
| `file_name` | `uptracezap_demo.go` | String | 日志对应的文件名 |
| `hostname` | `test-log-demo-778b86****-jm8t5` | String | 主机名，对应打印日志的容器或虚拟机 |
| `log_level` | `INFO` | String(枚举) | 日志等级。取值：DEBUG/INFO/WARN/ERROR/???（默认值，未设置时呈现为???） |
| `message` | `this is uptrace zap error log demo` | String | 日志原文，对应打印的日志内容 |
| `resource` | `{"host.arch":"arm64","host.type":"vm_demo","service.version":"1.0.0"}` | JSON对象 | 日志对应的资源属性。包含container_id、instance_id、host.arch、service.version等 |
| `service` | `test-log-demo` | String | 服务名 |
| `source` | `otl-collector` | String | 上报来源，表示不同的上报方式 |
| `trace_id` | `3e0022a380c4bc0c10feb18da17a****` | String | TraceId，定位唯一的请求 |

---

## 附录B：埋点字段与指标说明（导航页信息，详细字段未获取）

> 来源：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Trackingfieldsandmetricsdescription?lang=zh
> **重要说明**：本页为导航概述页，详细字段定义在两个外部子页面中，子页面URL未能通过web.fetch获取（动态渲染链接）。以下为从导航页获取的概要信息。

### AI应用监控埋点

- **接入方式**：[PRODUCT] SDK 内部接入 OpenTelemetry 埋点
- **覆盖范围**：分布式追踪（Tracing）和指标监控（Metrics）两大核心模块
- **观测目标**：[PRODUCT] 智能体运行时调用过程
- **详细字段**：链接文本"[PRODUCT]埋点字段与指标说明"，**实际URL未获取**

### [BASE-ADK]埋点

- **接入方式**：[BASE-ADK] SDK 内部接入 OpenTelemetry 埋点
- **覆盖范围**：通用类、LLM类和Tool类三大核心模块
- **观测目标**：[BASE-ADK]调用Agent、运行Agent、调用模型、调用工具的过程
- **详细字段**：链接文本"[BASE-ADK]埋点与字段说明"，**实际URL未获取**

### 已知缺口

前端trace覆盖层的数据契约所需的具体埋点字段名/类型/含义**未能从[PRODUCT]官方文档静态页面中获取**。详细字段定义可能位于：
1. APMPlus（应用性能监控）产品文档站
2. [BASE-ADK]独立文档站
3. 需要通过浏览器动态渲染获取链接URL

---

## 附录C：MCP服务监控指标表

> 来源：查看MCP服务监控数据页

| 分类 | 指标名称 | 单位 | 说明 |
|---|---|---|---|
| 服务调用 | 请求次数 | Count | 统计周期内接收的总请求量 |
| 服务调用 | 请求分布（范围） | Count | 宏观区间维度统计请求分布 |
| 服务调用 | 请求分布（精确） | Count | 具体对象/值维度统计请求分布 |
| 服务调用 | 平均延迟 | ms | 处理请求平均耗时 |
| 服务调用 | 出向响应带宽 | bit/s | 每秒流出流量（公网+私网合计） |
| 服务调用 | 公网出向响应带宽 | bit/s | 公网访问时每秒响应流量 |
| 服务运行 | CPU使用率 | % | 所有实例CPU使用率平均值 |
| 服务运行 | 内存使用率 | % | 所有实例内存使用率平均值 |
| 服务运行 | 实例数量 | Count | 运行中的实例数量 |

> 采集频率：30秒；查询范围：最小1小时~最大15天，仅支持过去30天数据；仅运行中状态可查看

---

## 附录D：MCP工具集监控指标表

> 来源：查看MCP工具集监控数据页

| 指标名称 | 单位 | 说明 |
|---|---|---|
| 请求次数 | Count | 收到客户端请求总次数 |
| 请求分布（范围） | Count | 宏观区间维度统计 |
| 请求分布（精确） | Count | 具体对象/值维度统计 |
| 平均延时 | ms | 处理请求平均耗时 |
| 出向响应带宽 | bit/s | 每秒向客户端响应流量（公网+私网） |
| 公网出向响应带宽 | bit/s | 公网访问时公网流量 |
| 语义检索请求次数 | Count | search_tools调用总次数 |
| 语义检索请求任务数 | Count | search_tools总任务数（≥请求次数） |
| 标签检索请求次数 | Count | list_tools_by_tags调用总次数 |
| 语义检索工具索引数 | Count | 内部构建的工具索引数量 |

---

## 附录E：网关规格表

> 来源：变更专属网关实例规格页

| 规格 | QPS(k) | 客户端连接数(w) | MCP服务+工具集总数 |
|---|---|---|---|
| gateway_small_x1 | 1.5 | 2 | 500 |
| gateway_small_x2 | 3 | 4 | 500 |
| gateway_small_x4 | 6 | 8 | 500 |
| gateway_medium_x1 | 12 | 16 | 1,000 |
| gateway_medium_x2 | 24 | 32 | 1,000 |
| gateway_large_x1 | 48 | 64 | 2,000 |
| gateway_large_x2 | 96 | 128 | 2,000 |
| gateway_large_x4 | 192 | 256 | 2,000 |

---

## 附录F：数据回流配置参数表

> 来源：数据回流页

| 分类 | 配置项 | 说明 |
|---|---|---|
| 基础信息 | 任务名称 | 自定义导出任务名称 |
| 基础信息 | 数据总上限 | 每任务最多100000条，可自定义调整 |
| 数据过滤 | 数据过滤 | 筛选项：Span类型、AI Span类型、服务名称、模型名称、接口名、状态码、操作、耗时；同项"或"逻辑，跨项"与"逻辑 |
| 时间范围 | 回流新数据 | 仅支持回流新数据，不支持历史数据 |
| 时间范围 | 总时间范围 | 指定导出数据的总时间范围 |
| 时间范围 | 重复频率 | 不重复/按天重复/按周重复 |
| 导出配置 | 导出平台 | 导出到智能体评测平台 |
| 导出配置 | 数据脱敏 | 默认开启（Input/Output自动脱敏）；关闭可导出完整信息 |
| 导出配置 | 目标评测集 | 选择已有或新增评测集 |
| 导出配置 | 导入方式 | 追加数据 |
| 导出配置 | 字段映射 | Trace Span字段 → 评测集字段映射 |

---

## 附录G：身份快速入门5个子页概要

| 子页 | URL | 核心步骤 |
|---|---|---|
| ①开通平台并授权 | activate-the-agent-identity... | 登录平台→勾选条款→开通并授权→自动创建ServiceRoleForID |
| ②入站快速登录 | inbound-authorization-enable-quick-login... | 创建用户池→创建客户端(Web/SPA/Mobile/M2M)→创建测试用户→OIDC集成(Discovery URL/Client ID/Client Secret) |
| ③入站企业SSO | inbound-authorization-integrate-enterprise-sso... | 创建用户池→创建客户端→添加外部IdP(OIDC: Issuer URL/Client ID/Secret/scope)→回填回调地址到IdP |
| ④出站第三方资源 | outbound-authorization...thirdparty... | 创建用户池/客户端/用户→身份凭据托管新建OAuth Client(飞书)→回填回调到第三方平台→首次授权+后续静默Refresh Token |
| ⑤出站火山引擎资源 | outbound-authorization...volcano... | 此前分片已读 |
