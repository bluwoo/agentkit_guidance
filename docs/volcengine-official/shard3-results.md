# Shard3 文档读取结果 — Runtime/沙箱/Skills/A2A 操作指南

> 读取时间：2026-09-18
> 来源：火山引擎 [PRODUCT] 官方文档
> 共 65 页，逐条记录证据。

---

## 1. 创建智能体运行时（CLI 工具）

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/CreatingruntimesCLItool?lang=zh`
- **读取范围**: offset 0–23996（分页读取完成）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: 已安装 [PRODUCT] CLI；已创建业务项目；已配置火山引擎 AK/SK。
  - **操作步骤**:
    1. 执行 `[PRODUCT] runtime create` 创建运行时。
    2. 配置运行时名称、描述、模型、环境变量、A2A 空间等。
    3. 支持关联组件（知识库、工具等）。
    4. 配置 IAM 权限。
  - **关键配置项**:
    - 镜像：可选预置镜像或自定义镜像。
    - 实例规格：CPU/内存可配置。
    - 模型配置：绑定方舟模型。
    - 环境变量：键值对形式注入。
    - A2A 空间：选择关联的 A2A 智能体空间。
    - 关联组件：知识库、工具等。
  - **注意事项**: 创建后需发布才能生效；运行时删除不可恢复。
- **异常**: 无

---

## 2. 智能体运行时概述

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Agentruntimeoverview?lang=zh`
- **读取范围**: offset 0–4287（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **概述**: 智能体运行时是 [PRODUCT] 中托管智能体应用的运行环境，负责接收请求、调度模型和工具、返回响应。
  - **核心概念**:
    - 运行时（Runtime）：一个完整的智能体应用实例，包含代码、模型配置、工具关联等。
    - 实例（Instance）：运行时的实际运行副本，支持多实例部署。
    - 发布（Release）：将运行时版本发布到指定流量比例，支持灰度发布。
  - **操作入口**: [PRODUCT] 控制台 → 智能体运行时。
  - **注意事项**: 仅运行中状态可查看监控数据；查询时间范围最小1小时、最大15天；仅支持过去30天数据。
- **异常**: 无（此前 read_status 标记为"失败"，本次重试成功）

---

## 3. 更新 A2A 空间

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/UpdatingA2Aspaces?lang=zh`
- **读取范围**: offset 0–283（仅导航页）
- **是否到底**: 是
- **关键内容**: 页面仅包含左侧导航树结构，无正文内容。推测为模板页或内容已迁移。
- **异常**: 正文为空，仅导航结构

---

## 4. 运行时实例概述

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Runtimeinstanceoverview?lang=zh`
- **读取范围**: offset 0–1929（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **概述**: 运行时实例是智能体运行时的实际运行副本，承载具体的请求处理。
  - **操作步骤**:
    1. 登录 [PRODUCT] 控制台。
    2. 左侧导航树选择"智能体运行时"。
    3. 单击目标运行时名称，进入"实例"页签查看实例列表。
  - **关键信息**: 实例状态（运行中/异常/已停止）、实例 ID、创建时间、最近活动时间。
  - **注意事项**: 实例生命周期到期后自动回收；实例回收后数据不保留。
- **异常**: 无

---

## 5. 查看运行时实例日志

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ViewRuntimeInstanceLog?lang=zh`
- **读取范围**: offset 0–1926（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: 运行时处于运行中状态。
  - **操作步骤**:
    1. 登录 [PRODUCT] 控制台。
    2. 左侧导航树选择"智能体运行时"。
    3. 单击目标运行时名称，进入"实例"页签。
    4. 单击目标实例操作列下的"日志"按钮。
  - **关键功能**: 实时查看实例 stdout/stderr 日志；支持日志搜索。
  - **注意事项**: 日志保留时间有限；实例停止后日志不可查。
- **异常**: 无

---

## 6. 发布运行时

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Releasingruntimes?lang=zh`
- **读取范围**: offset 0–2318（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: 运行时已创建且配置完成。
  - **操作步骤**:
    1. 登录 [PRODUCT] 控制台。
    2. 左侧导航树选择"智能体运行时"。
    3. 单击目标运行时名称，进入"发布"页签。
    4. 单击"发布"按钮，配置流量比例。
  - **关键配置项**:
    - 流量占比：1–100，100 为全量发布。
    - 支持灰度发布（流量<100）。
  - **注意事项**: 发布后可在"发布记录"中查看历史；支持取消发布。
- **异常**: 无

---

## 7. 查看运行时不可用日志

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Viewinglogsforagentruntimeunavailability?lang=zh`
- **读取范围**: offset 0–1291（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: 运行时存在不可用/异常事件。
  - **操作步骤**:
    1. 登录 [PRODUCT] 控制台。
    2. 左侧导航树选择"智能体运行时"。
    3. 单击目标运行时名称，进入"不可用日志"页签。
  - **关键信息**: 不可用事件时间、原因描述、影响范围。
  - **注意事项**: 用于排查运行时异常中断问题。
- **异常**: 无

---

## 8. 查看运行时网络信息

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Viewruntimenetworkinformation?lang=zh`
- **读取范围**: offset 0–1926（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: 运行时已创建。
  - **操作步骤**:
    1. 登录 [PRODUCT] 控制台。
    2. 左侧导航树选择"智能体运行时"。
    3. 单击目标运行时名称，在"基本信息"页签查看网络配置。
  - **关键信息**: 服务地址（公网/私网）、VPC ID、子网 ID、安全组。
  - **注意事项**: 私网地址适用于 VPC 内部互访，不收取费用；公网地址适用于互联网访问。
- **异常**: 无

---

## 9. 删除运行时

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Deletingruntimes?lang=zh`
- **读取范围**: offset 0–1295（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **警告**: 删除运行时不可恢复；删除后所有实例、配置和数据将被清除。
  - **前置条件**: 运行时已停止。
  - **操作步骤**:
    1. 登录 [PRODUCT] 控制台。
    2. 左侧导航树选择"智能体运行时"。
    3. 单击目标运行时操作列下的"删除"按钮。
    4. 确认风险后单击"删除"。
  - **注意事项**: 删除前建议确认无业务依赖。
- **异常**: 无

---

## 10. 运行时安全最佳实践

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Runtimesecuritybestpractices?lang=zh`
- **读取范围**: offset 0–2757（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **安全最佳实践列表**:
    1. 最小权限原则：仅授予运行时所需的最小 IAM 权限。
    2. 网络隔离：优先使用私网访问，减少公网暴露面。
    3. 密钥管理：API Key、AK/SK 等敏感信息通过环境变量注入，不要硬编码。
    4. 依赖安全：定期更新镜像和依赖包。
    5. 监控告警：开启监控和日志，及时发现异常。
    6. 版本管理：通过发布管理控制变更，支持灰度和回滚。
- **异常**: 无

---

## 11. 快速使用沙箱模板

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/quickly-use-sandbox-template?lang=zh`
- **读取范围**: offset 0–2830（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: 已开通 [PRODUCT] 服务。
  - **操作步骤**:
    1. 登录 [PRODUCT] 控制台。
    2. 左侧导航树选择"工具 > 沙箱模板"。
    3. 选择预置模板或创建自定义模板。
    4. 创建沙箱实例，关联模板。
  - **关键配置项**:
    - 实例规格：vCPU 2–16 核，内存 4–128 GiB。
    - vCPU:内存比值要求：整数 vCPU 时 1:2/1:4/1:8；非整数时 1:2/1:4。
    - 网络配置：公网/私网访问。
    - 模型配置：绑定方舟模型。
    - 存储配置：TOS 存储桶用于持久化。
    - 环境变量：键值对注入。
  - **注意事项**: 沙箱模板创建后不产生费用；实例创建后才开始计费。
- **异常**: 无

---

## 12. 创建沙箱模板

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Creatingtools?lang=zh`
- **读取范围**: offset 0–5（重定向到文档中心首页）
- **是否到底**: 是
- **关键内容**: 页面重定向至"文档中心-火山引擎"首页，仅返回"欢迎来到文档中心"。
- **异常**: 页面重定向失败，无正文内容

---

## 13. 更新沙箱模板类型

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Updatingtooltypes?lang=zh`
- **读取范围**: offset 0–5（重定向到文档中心首页）
- **是否到底**: 是
- **关键内容**: 页面重定向至"文档中心-火山引擎"首页。
- **异常**: 页面重定向失败，无正文内容

---

## 14. 代码沙箱工具示例

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Codesandboxtoolexample?lang=zh`
- **读取范围**: offset 0–2483（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **概述**: 代码沙箱（AIO Sandbox）提供云端代码执行环境，支持 Python3 和 Node.js。
  - **代码示例**:
    ```python
    # 通过 [PRODUCT] SDK 调用代码沙箱
    from [PRODUCT] import [PRODUCT]Client

    client = [PRODUCT]Client()
    sandbox = client.sandbox.create(
        instance_type="code",
        vcpu=2,
        memory=4
    )
    result = sandbox.execute_code("print('hello world')")
    print(result.output)
    ```
  - **关键配置**: 支持 Python3、Node.js；实例规格可配置；支持文件上传下载。
  - **注意事项**: 实例生命周期到期后数据清理，下次请求创建新实例。
- **异常**: 无

---

## 15. 浏览器沙箱工具示例

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Browsersandboxtoolexample?lang=zh`
- **读取范围**: offset 0–2294（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **概述**: 浏览器沙箱提供云端浏览器环境，支持网页自动化操作。
  - **代码示例**:
    ```python
    from [PRODUCT] import [PRODUCT]Client

    client = [PRODUCT]Client()
    browser = client.sandbox.create(
        instance_type="browser",
        vcpu=2,
        memory=4
    )
    browser.navigate("https://example.com")
    title = browser.get_title()
    print(title)
    ```
  - **关键配置**: 支持 Chromium 浏览器；支持截图、点击、填表等操作。
  - **注意事项**: 浏览器沙箱实例与代码沙箱相互独立。
- **异常**: 无

---

## 16. 预置 Skills 示例

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/UsageexampleofpresetSkills?lang=zh`
- **读取范围**: offset 0–2702（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **概述**: [PRODUCT] 提供预置 Skills，包括文档处理、搜索、代码执行等能力。
  - **使用方式**: 在智能体运行时中关联预置 Skill，智能体即可调用对应能力。
  - **预置 Skill 列表**:
    - 文档处理：PDF 解析、Word 生成等。
    - 搜索：网页搜索、文档搜索。
    - 代码执行：在沙箱中运行代码。
    - 浏览器：网页自动化操作。
  - **注意事项**: 预置 Skill 由平台维护，无需自行开发。
- **异常**: 无

---

## 17. 自定义 Skills 示例

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/UsageexampleofcustomSkills?lang=zh`
- **读取范围**: offset 0–2389（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **概述**: 支持创建自定义 Skill，将自有工具或 API 封装为 Skill 供智能体调用。
  - **创建步骤**:
    1. 在 Skills 中心创建自定义 Skill。
    2. 定义 Skill 的输入参数、输出格式。
    3. 编写 Skill 执行逻辑（Python/Node.js）。
    4. 调试并发布 Skill。
  - **代码示例**:
    ```python
    # Skill 入口函数
    def handler(params: dict) -> dict:
        name = params.get("name", "world")
        return {"message": f"Hello, {name}!"}
    ```
  - **注意事项**: 自定义 Skill 需通过调试验证后才能发布。
- **异常**: 无

---

## 18. 删除沙箱模板

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Deletingtools?lang=zh`
- **读取范围**: offset 0–1182（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **警告**: 删除沙箱模板不可恢复。
  - **前置条件**: 沙箱模板未被实例引用。
  - **操作步骤**:
    1. 登录 [PRODUCT] 控制台。
    2. 左侧导航树选择"工具 > 沙箱模板"。
    3. 单击目标模板操作列下的"删除"按钮。
    4. 确认风险后单击"删除"。
  - **注意事项**: 存在运行中实例时不允许删除；被流程引用时不允许删除。
- **异常**: 无

---

## 19. 创建沙箱实例

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Creatingtoolinstances?lang=zh`
- **读取范围**: offset 0–2211（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: 已创建沙箱模板。
  - **操作步骤**:
    1. 登录 [PRODUCT] 控制台。
    2. 左侧导航树选择"工具 > 沙箱实例"。
    3. 单击"创建实例"按钮，选择沙箱模板。
    4. 配置实例名称、生命周期等。
  - **关键配置项**:
    - 生命周期：默认 8 小时（28800 秒），范围 3 分钟～24 小时。
    - 关联消息渠道：支持飞书等消息渠道。
  - **注意事项**: 实例生命周期到期后自动回收，数据不保留。
- **异常**: 无

---

## 20. 沙箱实例添加消息渠道

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/add-message-channel-to-arkclaw-sandbox-tool-instance?lang=zh`
- **读取范围**: offset 0–1911（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **概述**: 为沙箱实例添加消息渠道（如飞书机器人），实现与用户的消息交互。
  - **前置条件**: 已创建沙箱实例。
  - **操作步骤**:
    1. 登录 [PRODUCT] 控制台。
    2. 左侧导航树选择"工具 > 沙箱实例"。
    3. 单击目标实例名称，进入"消息渠道"页签。
    4. 单击"添加消息渠道"，选择飞书机器人并配置。
  - **关键配置**: 飞书机器人 Webhook、消息模板。
  - **注意事项**: 消息渠道配置后需验证连通性。
- **异常**: 无

---

## 21. 删除沙箱实例

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Deletingtoolinstances?lang=zh`
- **读取范围**: offset 0–5（空页面）
- **是否到底**: 是
- **关键内容**: 页面正文为空，仅返回"欢迎来到文档中心"。
- **异常**: 正文为空页面

---

## 22. 在火山方舟中使用 [PRODUCT] Self-hosted Skills Sandbox

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Using[PRODUCT]Self-hostedSkillsSandboxinVolcanoArk?lang=zh`
- **读取范围**: offset 0–17623（分3次分页读完）
- **是否到底**: 是
- **关键内容**:
  - **概述**: Self-hosted Skills Sandbox 允许在火山方舟（Volcano Ark）中使用 [PRODUCT] 的 Skills 沙箱能力。
  - **前置条件**:
    - 已开通火山方舟服务。
    - 已在 [PRODUCT] 中创建 Skills 沙箱模板。
    - 已配置网络连通性。
  - **操作步骤**:
    1. 在火山方舟控制台创建应用。
    2. 关联 [PRODUCT] Skills 沙箱。
    3. 配置调用参数和环境变量。
    4. 在应用中调用沙箱工具。
  - **关键配置项**:
    - 沙箱端点地址（Endpoint）。
    - 认证方式（API Key）。
    - 超时时间。
  - **注意事项**: 需确保网络连通；沙箱实例生命周期与方舟应用独立。
- **异常**: 无

---

## 23. 快速上手 Skills — 基于智能工坊从 Skill 构建到业务落地

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/quick-start-skills-skill-construction-to-business-implementation-based-on-intelligent-workshop?lang=zh`
- **读取范围**: offset 0–36051（分5次分页读完）
- **是否到底**: 是
- **关键内容**:
  - **概述**: 基于智能工坊（Intelligent Workshop）快速构建 Skill 并落地到业务场景的完整指南。
  - **流程**:
    1. 创建 Skill：在智能工坊中定义 Skill 名称、描述、输入输出。
    2. 调试 Skill：使用测试数据验证 Skill 执行逻辑。
    3. 评估 Skill：评估 Skill 效果和性能。
    4. 注册 Skill：将 Skill 注册到 Skills 中心。
    5. 业务集成：在智能体应用中调用 Skill。
  - **关键配置**:
    - Skill 描述：用于模型自动选择 Skill。
    - 输入参数：JSON Schema 定义。
    - 输出格式：JSON Schema 定义。
  - **注意事项**: 调试和评估是发布前的必要步骤；Skill 描述质量直接影响模型选择准确率。
- **异常**: 无

---

## 24. 创建 Skill

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/CreatingSkills-1?lang=zh`
- **读取范围**: offset 0–1986（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: 已登录 [PRODUCT] 控制台。
  - **操作步骤**:
    1. 左侧导航树选择"Skills 中心 > Skill 管理"。
    2. 单击"创建 Skill"按钮。
    3. 填写 Skill 名称、描述、输入输出定义。
    4. 编写 Skill 执行代码。
  - **关键配置项**:
    - Skill 名称：唯一标识。
    - 描述：用于模型路由。
    - 输入参数：JSON Schema。
    - 输出格式：JSON Schema。
  - **注意事项**: Skill 描述应清晰准确，影响模型自动选择。
- **异常**: 无

---

## 25. 调试 Skill

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/DebuggingSkills?lang=zh`
- **读取范围**: offset 0–1974（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: 已创建 Skill。
  - **操作步骤**:
    1. 进入 Skill 详情页。
    2. 单击"调试"页签。
    3. 输入测试参数，单击"运行"。
    4. 查看执行结果和日志。
  - **关键功能**: 实时调试、日志查看、错误定位。
  - **注意事项**: 调试环境与生产环境隔离；调试不产生计费。
- **异常**: 无

---

## 26. 评估 Skill

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/AssessmentSkills?lang=zh`
- **读取范围**: offset 0–1997（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: 已创建并调试 Skill。
  - **操作步骤**:
    1. 进入 Skill 详情页。
    2. 单击"评估"页签。
    3. 创建评估任务，上传测试数据集。
    4. 查看评估报告（准确率、延迟、成功率）。
  - **关键指标**: 成功率、平均延迟、输出质量评分。
  - **注意事项**: 评估结果作为发布决策依据。
- **异常**: 无

---

## 27. 注册 Skill

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/RegisteredSkills?lang=zh`
- **读取范围**: offset 0–1774（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: Skill 已调试和评估通过。
  - **操作步骤**:
    1. 进入 Skill 详情页。
    2. 单击"发布"按钮。
    3. 选择注册到的 Skills 空间。
    4. 确认发布。
  - **关键配置**: 版本号、可见范围、关联空间。
  - **注意事项**: 注册后其他智能体可通过空间发现并调用该 Skill。
- **异常**: 无

---

## 28. 创建 Skill 空间

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/CreatingSkillsspaces?lang=zh`
- **读取范围**: offset 0–1296（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **概述**: Skill 空间用于组织和管理 Skill，实现团队级共享。
  - **操作步骤**:
    1. 左侧导航树选择"Skills 中心 > 空间管理"。
    2. 单击"创建空间"按钮。
    3. 填写空间名称、描述。
    4. 配置空间成员权限。
  - **关键配置**: 空间名称、描述、成员管理。
  - **注意事项**: 空间是 Skill 的逻辑分组单位。
- **异常**: 无

---

## 29. 添加/移除 Skill

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/AddingRemovingSkills?lang=zh`
- **读取范围**: offset 0–1701（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: 已创建 Skill 空间。
  - **操作步骤**:
    1. 进入 Skill 空间详情页。
    2. 单击"添加 Skill"，选择目标 Skill。
    3. 确认添加。
    4. 如需移除，单击 Skill 操作列下的"移除"。
  - **注意事项**: 同一 Skill 可添加到多个空间；移除后不删除 Skill 本身。
- **异常**: 无

---

## 30. 修改 Skill 版本

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ChangingSkillversions?lang=zh`
- **读取范围**: offset 0–1459（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: 空间中已添加多个版本的 Skill。
  - **操作步骤**:
    1. 进入 Skill 空间详情页。
    2. 单击目标 Skill 操作列下的"修改版本"。
    3. 选择目标版本号。
    4. 确认修改。
  - **注意事项**: 版本切换后，空间内引用该 Skill 的智能体将使用新版本。
- **异常**: 无

---

## 31. 删除 Skill 空间

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/DeletingSkillsspaces?lang=zh`
- **读取范围**: offset 0–1113（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **警告**: 删除空间不可恢复。
  - **前置条件**: 空间中无 Skill 引用。
  - **操作步骤**:
    1. 进入"Skills 中心 > 空间管理"。
    2. 单击目标空间操作列下的"删除"。
    3. 确认风险后删除。
  - **注意事项**: 删除前需先移除空间中的所有 Skill。
- **异常**: 无

---

## 32. 预置 Skill

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/PresetSkills?lang=zh`
- **读取范围**: offset 0–15689（分2次分页读完）
- **是否到底**: 是
- **关键内容**:
  - **概述**: [PRODUCT] 预置 Skill 列表及使用说明。
  - **预置 Skill 分类**:
    - 文档处理类：PDF 解析、Word/Excel 生成、文档摘要。
    - 搜索类：网页搜索、企业知识库搜索。
    - 代码执行类：Python 代码执行、Shell 命令执行。
    - 浏览器类：网页截图、网页内容提取、表单自动填写。
    - 消息类：飞书消息发送、邮件发送。
  - **使用方式**: 在智能体运行时中关联预置 Skill，无需自行开发。
  - **注意事项**: 预置 Skill 由平台维护更新；部分 Skill 可能涉及额外计费。
- **异常**: 无

---

## 33. 创建自定义 Skill

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/CreatingSkills?lang=zh`
- **读取范围**: offset 0–2011（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: 已登录 [PRODUCT] 控制台。
  - **操作步骤**:
    1. 左侧导航树选择"Skills 中心 > Skill 管理"。
    2. 单击"创建 Skill"。
    3. 选择"自定义 Skill"类型。
    4. 填写名称、描述、输入输出 JSON Schema。
    5. 编写执行代码（Python/Node.js）。
  - **关键配置项**:
    - 名称、描述。
    - 输入参数 Schema。
    - 输出格式 Schema。
    - 执行代码。
  - **注意事项**: 自定义 Skill 需通过调试验证后才能发布。
- **异常**: 无

---

## 34. 在 Skills 空间添加/移除 Skill

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/AddingRemovingSkillsinSkillsSpaces?lang=zh`
- **读取范围**: offset 0–1353（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: 已创建 Skill 空间和 Skill。
  - **操作步骤**:
    1. 进入 Skills 空间详情页。
    2. 单击"添加 Skill"，从 Skill 列表中选择。
    3. 确认添加。
    4. 移除时单击"移除"按钮。
  - **注意事项**: 添加到空间后，空间内的智能体即可发现并调用该 Skill。
- **异常**: 无

---

## 35. 查看 Skill 版本信息

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ViewingversiondetailsofSkills?lang=zh`
- **读取范围**: offset 0–1263（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: 已注册 Skill。
  - **操作步骤**:
    1. 进入 Skill 详情页。
    2. 单击"版本管理"页签。
    3. 查看版本列表（版本号、创建时间、状态）。
    4. 单击"查看"查看具体版本配置。
  - **注意事项**: 版本管理支持回滚到历史版本。
- **异常**: 无

---

## 36. 查看 Skill 变更详情

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ViewingSkillchangedetails?lang=zh`
- **读取范围**: offset 0–1125（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: Skill 已有变更记录。
  - **操作步骤**:
    1. 进入 Skill 详情页。
    2. 单击"变更记录"页签。
    3. 查看变更历史（变更时间、变更人、变更内容摘要）。
  - **注意事项**: 变更记录用于追溯 Skill 的修改历史。
- **异常**: 无

---

## 37. 更新自定义 Skill

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/UpdatingSkills?lang=zh`
- **读取范围**: offset 0–15695（分2次分页读完）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: 已创建自定义 Skill。
  - **操作步骤**:
    1. 进入 Skill 详情页。
    2. 单击"编辑"按钮。
    3. 修改 Skill 配置（描述、参数、代码等）。
    4. 保存并重新调试。
  - **关键配置项**: 描述、输入输出 Schema、执行代码、环境变量。
  - **注意事项**: 更新后需重新发布才能生效；版本号自动递增。
- **异常**: 无

---

## 38. 发布 Skill

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/PublishingSkills?lang=zh`
- **读取范围**: offset 0–1745（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: Skill 已调试和评估通过。
  - **操作步骤**:
    1. 进入 Skill 详情页。
    2. 单击"发布"按钮。
    3. 确认版本号和发布说明。
    4. 单击"确认发布"。
  - **注意事项**: 发布后 Skill 才可被其他智能体调用；发布不可撤销。
- **异常**: 无

---

## 39. 删除 Skill

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/DeletingSkills?lang=zh`
- **读取范围**: offset 0–1169（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **警告**: 删除 Skill 不可恢复。
  - **前置条件**: Skill 未被智能体运行时引用。
  - **操作步骤**:
    1. 进入 Skill 管理列表。
    2. 单击目标 Skill 操作列下的"删除"。
    3. 确认风险后删除。
  - **注意事项**: 删除前需确认无业务依赖。
- **异常**: 无

---

## 40. 创建 A2A 智能体空间

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/CreatingA2Aagentspaces?lang=zh`
- **读取范围**: offset 0–1298（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **概述**: A2A 智能体空间是 A2A 中心中组织智能体注册和发现的逻辑单元。
  - **操作步骤**:
    1. 登录 [PRODUCT] 控制台。
    2. 左侧导航树选择"基础组件 > A2A 中心"。
    3. 单击"创建空间"按钮。
    4. 填写空间名称、描述。
  - **关键配置**: 空间名称、描述。
  - **注意事项**: 未主动创建空间时，智能体默认注册到 Default 空间。
- **异常**: 无

---

## 41. 删除 A2A 智能体空间

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/DeletingA2Aagentspaces?lang=zh`
- **读取范围**: offset 0–1197（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **警告**: 删除智能体空间不可恢复，属于高风险操作。
  - **前置条件**: 已注销空间中的所有智能体。
  - **操作步骤**:
    1. 登录 [PRODUCT] 控制台。
    2. 左侧导航树选择"基础组件 > A2A 中心"。
    3. 在 A2A 智能体空间下拉框，单击目标空间"... > 删除"。
    4. 确认风险后单击"删除"。
  - **注意事项**: 删除后调用方无法继续基于该空间发现或调度智能体。
- **异常**: 无

---

## 42. 注册 A2A 智能体

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/RegisteringA2Aagents?lang=zh`
- **读取范围**: offset 0–1898（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **核心概念**:
    - A2A 智能体：可通过 A2A 协议被其他智能体发现和调用的智能体服务。
    - AgentCard：智能体对外暴露的能力说明文件。
    - JSON 文件：以 JSON 形式维护的智能体描述文件。
    - AgentCard 地址：可访问 AgentCard 的 URL。
  - **前置条件**:
    - （可选）已创建智能体空间。
    - 已根据注册来源准备相应资源（智能体运行时 / JSON 文件 / AgentCard 地址）。
  - **操作步骤**:
    1. 登录 [PRODUCT] 控制台。
    2. 左侧导航树选择"基础组件 > A2A 中心"。
    3. 选择目标空间，单击"注册智能体"。
    4. 根据注册来源配置参数：
       - **智能体运行时**：选择目标运行时，自动匹配服务地址（公网/私网）。
       - **自定义 - JSON 文件**：粘贴符合 A2A 标准的 JSON 信息。
       - **自定义 - AgentCard 地址**：填写 AgentCard URL，单击"解析"。
    5. 单击"立即注册"。
  - **注意事项**:
    - 私网连通不收费；公网适用于互联网访问。
    - 未创建空间时注册至 Default 空间。
- **异常**: 无

---

## 43. 更新 A2A 智能体 JSON 文件

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/UpdatingA2AagentJSONfile?lang=zh`
- **读取范围**: offset 0–3445（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: 已注册来源为"自定义"的 A2A 智能体。
  - **操作步骤**:
    1. 登录 [PRODUCT] 控制台。
    2. 左侧导航树选择"基础组件 > A2A 中心"。
    3. 选择目标空间，单击目标智能体名称。
    4. 单击右上角"编辑"按钮。
    5. 在"AgentCard"区域调整 JSON 配置。
    6. 单击"立即注册"，确认页面单击"确定"。
  - **关键逻辑**:
    - 若更新涉及 version 参数 → 生成新版本，自动设为默认版本。
    - 若不涉及 version 参数 → 覆盖当前版本配置。
  - **注意事项**: JSON 字段规范参见 A2A 协议官网文档。
- **异常**: 无

---

## 44. 更新智能体 AgentCard 地址

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/UpdatingAgentCardaddressesofA2Aagents?lang=zh`
- **读取范围**: offset 0–5（重定向到文档中心首页）
- **是否到底**: 是
- **关键内容**: 页面重定向至"文档中心-火山引擎"首页。
- **异常**: 页面重定向失败，无正文内容

---

## 45. 查看智能体 JSON 文件

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ViewingA2AagentJSONfile?lang=zh`
- **读取范围**: offset 0–2342（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: 已注册 A2A 智能体。
  - **操作步骤**:
    1. 登录 [PRODUCT] 控制台。
    2. 左侧导航树选择"基础组件 > A2A 中心"。
    3. 选择目标空间，单击目标智能体名称。
    4. 单击右上角"JSON 文件"按钮。
    5. 查看、复制 JSON 代码。
  - **JSON 示例片段**:
    ```json
    {
      "capabilities": {"streaming": true},
      "defaultInputModes": ["text"],
      "defaultOutputModes": ["text"],
      "description": "hello world agent...",
      "name": "hello_world_agent",
      "preferredTransport": "JSONRPC",
      "protocolVersion": "0.3.0",
      "provider": {"organization": "[PRODUCT]", "url": ""},
      "security": [{"apiKeyAuth": []}],
      "securitySchemes": {
        "apiKeyAuth": {
          "type": "apiKey",
          "description": "ApiKey client credentials",
          "in": "header",
          "name": "apikey_vy9p****"
        }
      },
      "skills": [{"description": "Chat", "id": "0", "name": "chat", "tags": ["chat"]}]
    }
    ```
  - **注意事项**: 用于排查"智能体可见但不可用"等问题。
- **异常**: 无

---

## 46. 管理智能体版本

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ManagingA2Aagentversions?lang=zh`
- **读取范围**: offset 0–4614（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **创建版本**: 更新 JSON 文件时通过 version 参数指定新版本号，平台自动设为默认版本。仅"自定义"来源支持。
  - **查看版本信息**:
    1. 进入 A2A 中心，选择空间和智能体。
    2. 选择"版本管理"页签。
    3. 查看版本列表（版本号、创建时间、更新时间）。
    4. 单击"查看"查看对应版本的 JSON 配置。
    - 自定义来源：支持查看所有版本。
    - 智能体运行时来源：仅支持查看最新信息。
  - **删除版本**:
    1. 进入"版本管理"页签。
    2. 单击目标版本操作列下的"删除"。
    3. 确认后删除。
  - **注意事项**: 仅支持删除"自定义"来源的版本；删除不可恢复。
- **异常**: 无

---

## 47. 注销 A2A 智能体

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/UnregisteringA2Aagents?lang=zh`
- **读取范围**: offset 0–1226（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **注意事项**:
    - 注销后外部智能体无法调用该空间内的对应智能体，可能导致现有调用失败。
    - 注销不会删除来源（如智能体运行时），只是无法通过 A2A 空间发现与调用。
  - **前置条件**: 已注册 A2A 智能体。
  - **操作步骤**:
    1. 登录 [PRODUCT] 控制台。
    2. 左侧导航树选择"基础组件 > A2A 中心"。
    3. 选择目标空间，单击目标智能体操作列下的"注销"。
    4. 确认页面单击"注销"。
- **异常**: 无

---

## 48. A2A 智能体 JSON 文件示例

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/SampleA2AagentJSONfile?lang=zh`
- **读取范围**: offset 0–934（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **完整 JSON 示例（0.3.0 版本协议）**:
    ```json
    {
      "capabilities": {"streaming": true},
      "defaultInputModes": ["text"],
      "defaultOutputModes": ["text"],
      "description": "hello world agent that can roll a dice of 8 sides and check prime numbers.",
      "name": "hello_world_agent",
      "preferredTransport": "JSONRPC",
      "protocolVersion": "0.3.0",
      "provider": {"organization": "[PRODUCT]", "url": ""},
      "security": [{"apiKeyAuth": []}],
      "securitySchemes": {
        "apiKeyAuth": {
          "type": "apiKey",
          "description": "ApiKey client credentials",
          "in": "header",
          "name": "Authorization"
        }
      },
      "skills": [
        {"description": "Chat", "id": "0", "name": "chat", "tags": ["chat"]}
      ],
      "url": "https://sd6k****.com",
      "version": "1.0.0"
    }
    ```
  - **参数说明**:
    | 参数 | 必填 | 说明 |
    |---|---|---|
    | name | 是 | 智能体名称 |
    | description | 是 | 功能描述 |
    | version | 是 | 语义化版本号，如 1.0.0 |
    | url | 是 | A2A 服务入口地址 |
    | preferredTransport | 是 | 传输协议：JSONRPC/GRPC/HTTP+JSON |
    | protocolVersion | 是 | A2A 协议版本，如 0.3.0 |
    | capabilities | 是 | 可选能力集合，streaming 表示是否支持流式 |
    | skills | 是 | 技能列表，至少 1 个，含 id/name/tags/description |
    | defaultInputModes | 是 | 默认输入媒体类型，如 ["text"] |
    | defaultOutputModes | 是 | 默认输出媒体类型，如 ["text"] |
    | provider | 否 | 服务提供方信息 |
    | security | 否 | 安全要求列表 |
    | securitySchemes | 否 | 鉴权方案定义 |
  - **注意事项**: 不同版本协议的必填字段可能不同，以实际版本为准。
- **异常**: 无（此前 read_status 标记为"失败"，本次重试成功）

---

## 49. 添加 MCP 工具

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/AddingMCPtools?lang=zh`
- **读取范围**: offset 0–10（重定向到文档中心首页）
- **是否到底**: 是
- **关键内容**: 页面重定向至"文档中心-火山引擎"首页，显示"敬请期待更多模块"。
- **异常**: 页面重定向失败，无正文内容

---

## 50. 创建 MCP 工具集

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/CreatingMCPtoolset?lang=zh`
- **读取范围**: offset 0–2640（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **调用模式**:
    | 模式 | 说明 | 适用场景 |
    |---|---|---|
    | 全量返回 | 返回所有工具 | 工具≤20个 |
    | 语义检索 | 基于意图语义匹配 | 工具多、通用 Agent |
    | 标签检索 | 按标签筛选 | 工具多、垂直领域 Agent |
  - **MCP 协议版本兼容**: 2026-07-28、2025-11-25、2025-06-18、2025-03-26。
  - **前置条件**: 已创建 MCP 服务；已了解计费；（可选）已配置 VPC。
  - **操作步骤**:
    1. 登录 [PRODUCT] 控制台。
    2. 左侧导航树选择"网关 > MCP 工具集"。
    3. 单击"创建 MCP 工具集"，配置参数。
  - **关键配置项**:
    - 所属网关：专属网关（推荐，资源独立）/ 共享模式（POC/低流量）。
    - 访问路径：默认 /mcp。
    - 网络访问：公网访问 / 私网访问。
    - 入站身份认证：API Key（最多1个）/ OAuth JWT（最多5个客户端），互斥。
    - 调用模式：全量返回 / 语义检索 / 标签检索。
    - 工具：从 MCP 服务中选择添加。
  - **注意事项**: 所属网关创建后不可更换；请求次数同时计入工具集与 MCP 服务用量。
- **异常**: 无

---

## 51. 调试 MCP 工具集

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/TestingMCPtoolset?lang=zh`
- **读取范围**: offset 0–2798（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: 已创建 MCP 工具集；（可选）私网调试需 VPN/专线连通。
  - **操作步骤**:
    1. 登录 [PRODUCT] 控制台。
    2. 左侧导航树选择"网关 > MCP"，单击"MCP 工具集"页签。
    3. 单击目标工具集名称，选择"调试"页签。
    4. Step 1：选择域名并连接测试。
    5. Step 2：（可选）标签检索选标签 / 语义检索输入自然语言检索。
    6. Step 3：选择调试工具。
    7. Step 4：输入参数，单击"测试工具"。
  - **注意事项**:
    - 公网域名调试对所有用户开放；私网调试为邀测。
    - 调试操作计入计费项用量。
- **异常**: 无

---

## 52. 在 MCP 工具集添加/移除工具

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/AddingRemovingMCPtools?lang=zh`
- **读取范围**: offset 0–6574（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: 已创建 MCP 工具集；目标 MCP 服务可用。
  - **添加工具步骤**:
    1. 进入工具集详情页，单击"MCP 工具"页签。
    2. 单击"添加工具"。
    3. 选择目标 MCP 服务，再选择工具，单击"确定"。
  - **移除工具步骤**:
    - 单个移除：单击目标工具"操作"列下的"移除"。
    - 批量移除：勾选多个工具，单击"批量移除"。
  - **注意事项**:
    - 工具集中至少保留 1 个工具，不能全部移除。
    - 移除后依赖该工具的 Agent 可能出现能力缺失。
- **异常**: 无

---

## 53. 更新工具调用模式

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Updatingtoolcallingmode?lang=zh`
- **读取范围**: offset 0–2379（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: 已创建 MCP 工具集。
  - **操作步骤**:
    1. 进入工具集详情页，选择"基本信息"页签。
    2. 单击"调用模式"区域的"编辑"按钮。
    3. 选择目标调用模式（全量返回/语义检索/标签检索），单击"✓"。
  - **注意事项**: 更新后工具集返回的工具信息将发生变化。
- **异常**: 无

---

## 54. 查看 MCP 工具集网络信息

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/check-mcp-toolset-network-info?lang=zh`
- **读取范围**: offset 0–2255（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: 已创建 MCP 工具集，配置为私网访问。
  - **操作步骤**:
    1. 进入工具集详情页，选择"基本信息"页签。
    2. 查看私有网络/子网 ID 信息。
    3. 单击目标 VPC/子网跳转详情页查看 IPv4 CIDR。
  - **用途**: 将 VPC/子网配置到目标服务访问白名单中。
- **异常**: 无

---

## 55. 删除 MCP 工具集

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/DeletingMCPtoolsets?lang=zh`
- **读取范围**: offset 0–1241（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **警告**: 删除后无法恢复；仍有 Agent 依赖时将导致调用失败。
  - **前置条件**: 已创建 MCP 工具集。
  - **操作步骤**:
    1. 左侧导航树选择"网关 > MCP"，单击"MCP 工具集"页签。
    2. 单击目标工具集操作列的"删除"按钮。
  - **建议**: 暂时不使用时优先调整调用配置或移除工具。
- **异常**: 无

---

## 56. 查看智能体运行时监控数据

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Viewingagentruntimemonitoringdata?lang=zh`
- **读取范围**: offset 0–572（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **查询限制**: 单次最小1小时、最大15天；仅过去30天；采集频率30s。
  - **操作步骤**:
    1. 登录 [PRODUCT] 控制台。
    2. 左侧导航树选择"智能体运行时"。
    3. 单击目标运行时名称，选择"监控"页签。
  - **监控指标**:
    | 类别 | 指标 | 单位 |
    |---|---|---|
    | 运行时 | 请求次数 | Count |
    | 运行时 | 请求分布（范围/精确） | Count |
    | 运行时 | 平均延迟 | ms |
    | 运行时 | 出向响应带宽 | bit/s |
    | 实例资源 | CPU 使用率 | % |
    | 实例资源 | 内存使用率 | % |
    | 实例资源 | 实例数量 | Count |
- **异常**: 无

---

## 57. 查看工具监控数据

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Viewingtoolmonitoringdata?lang=zh`
- **读取范围**: offset 0–526（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **查询限制**: 同运行时监控（1小时~15天，30天内，30s采集）。
  - **操作步骤**:
    1. 左侧导航树选择"工具"。
    2. 单击目标工具名称，选择"监控"页签。
  - **监控指标**: 请求次数、请求分布、平均延迟、出向响应带宽、CPU、内存、实例数量。
- **异常**: 无

---

## 58. 查看 MCP 工具集监控数据

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ViewingMCPtoolsetmonitoringdata?lang=zh`
- **读取范围**: offset 0–1709（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **查询限制**: 同前（1小时~15天，30天内，30s采集）。
  - **操作步骤**:
    1. 左侧导航树选择"网关 > MCP 工具集"。
    2. 单击目标工具集名称，选择"监控"页签。
  - **监控指标**: 请求次数、请求分布、平均延时、出向响应带宽、公网出向响应带宽、语义检索请求次数、语义检索请求任务数、标签检索请求次数、语义检索工具索引数。
- **异常**: 无

---

## 59. 通过 [PRODUCT] CLI 在沙箱中运行 Codex

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/RunningCodexinasandboxvia[PRODUCT]CLI?lang=zh`
- **读取范围**: offset 0–1050（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **前置条件**: Python ≥3.10；已配置方舟 Deepseek v4 模型 API Key；已获取火山引擎 AK/SK。
  - **安装步骤**:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    uv init --no-workspace
    uv venv --python 3.12
    uv pip install [PRODUCT]-sdk-python==0.6.4
    uv add [BASE-ADK]-python
    source .venv/bin/activate
    ```
  - **环境变量**:
    ```bash
    export VOLCENGINE_ACCESS_KEY=<your_access_key>
    export VOLCENGINE_SECRET_KEY=<your_secret_key>
    export MODEL_API_KEY=<your_ark_api_key>
    export [PRODUCT]_SANDBOX_TTL=28800  # 默认8小时，范围3分钟~24小时
    ```
  - **创建沙箱**:
    ```bash
    [PRODUCT] sandbox create --model-name deepseek-v4-flash-260425 --tos-bucket [PRODUCT]-platform-{{accountid}}
    ```
  - **执行任务**:
    ```bash
    # 交互式
    [PRODUCT] sandbox exec --session-id "test-0610-12" --command "codex 'hello'"
    # 非交互式
    [PRODUCT] sandbox exec --session-id "test-0610-12" --command 'codex exec --skip-git-repo-check "/goal ..."'
    ```
  - **查看产物**: `[PRODUCT] sandbox web --session-id "test-0610-12"`
  - **注意事项**: 相同 session-id 可复用实例；未配置 TOS 时文件不持久化。
- **异常**: 无

---

## 60. UpdateRuntimeRelease - 更新运行时发布（API）

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Updateruntimerelease-Updatesruntimerelease?lang=zh`
- **读取范围**: offset 0–446（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **API Action**: `UpdateRuntimeRelease`，Version: `2025-10-30`。
  - **请求参数**:
    | 参数 | 必选 | 说明 |
    |---|---|---|
    | RuntimeId | 是 | 运行时 ID |
    | TargetTrafficWeight | 是 | 目标发布流量百分比，1-100，100为全量，<100为灰度 |
  - **请求示例**:
    ```json
    POST https://[PRODUCT].cn-beijing.volcengineapi.com?Action=UpdateRuntimeRelease&Version=2025-10-30
    {
      "RuntimeId": "<RESOURCE_ID>****",
      "TargetTrafficWeight": 100
    }
    ```
  - **返回参数**: `RuntimeId`。
  - **错误码**: 400 MissingParameter.RuntimeId / MissingParameter.TargetTrafficWeight。
- **异常**: 无

---

## 61. Runtime FAQ

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/RuntimeFAQ?lang=zh`
- **读取范围**: offset 0–5（重定向到文档中心首页）
- **是否到底**: 是
- **关键内容**: 页面重定向至"文档中心-火山引擎"首页。
- **异常**: 页面重定向失败，无正文内容

---

## 62. 工具 FAQ

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ToolFAQ?lang=zh`
- **读取范围**: offset 0–114（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **Q: 沙箱工具支持哪些编程语言？** A: 仅支持 Python3 和 Node.js。
  - **Q: 实例生命周期到期后数据还会保留吗？** A: 不会。实例及所有数据都会被清理，下次请求创建新实例。
  - **Q: 沙箱工具支持哪些工具？** A: 提供 AIO Sandbox 和 Skills Sandbox 预置工具及自定义工具。
- **异常**: 无

---

## 63. 操作二：创建沙箱模板和添加模型（DeliveryAI）

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/operation-2-create-sandbox-templates-and-add-models?lang=zh`
- **读取范围**: offset 0–7853（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **创建沙箱模板（DeliveryAI 场景）**:
    - 前置条件: 已开通 DeliveryAI 并具备企业管理员权限；已准备 VPC 和子网。
    - 操作路径: [PRODUCT] 控制台 → DeliveryAI → 沙箱模板 → 创建沙箱模板。
    - 关键参数:
      - 名称、描述（≤200字符）。
      - 实例规格: vCPU 2~16 核，内存 4~128 GiB；比值要求 1:2/1:4/1:8（整数 vCPU）或 1:2/1:4（非整数）。
      - 网络配置: 公网访问（默认）/ 私网访问。
      - 共享公网访问: 仅私网访问时可开启。
      - 工作空间: 控制哪些空间可使用该模板。
  - **添加模型**:
    - 操作路径: DeliveryAI → 模型广场 → 添加模型供应商。
    - 关键参数:
      - 供应商名称。
      - 模型来源: 火山方舟模型广场 / Agent Plan / Coding Plan / 自定义模型。
      - 接口协议: OpenAI 接口协议。
      - API Key。
      - 模型名称、模型 ID。
      - 基础能力: 输入模态（文本/图片/视频）、上下文窗口（Token）。
      - 思考配置: 用户可选思考强度、默认思考强度。
    - 测试联通性后保存。
    - 可设置默认模型（用于未单独指定模型的系统内置 Agent 模板）。
  - **注意事项**: 沙箱模板创建后不产生费用；实例创建后才计费。
- **异常**: 无

---

## 64. 管理沙箱模板（DeliveryAI）

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/manage-sandbox-templates?lang=zh`
- **读取范围**: offset 0–5023（完整读取）
- **是否到底**: 是
- **关键内容**:
  - **创建沙箱模板**:
    - 路径: DeliveryAI → 沙箱模板 → 创建沙箱模板。
    - 参数: 名称、实例规格、网络访问（私网/公网）、共享公网访问、工作空间（不限制/限制）。
  - **编辑沙箱模板**:
    - 路径: 沙箱模板列表 → 目标模板操作列"编辑"。
    - 可修改: 名称、描述、资源规格、网络配置、工作空间范围。
    - 后续新创建的实例按新参数执行。
  - **删除沙箱模板**:
    - 路径: 沙箱模板列表 → 目标模板操作列"删除"。
    - 注意: 存在运行中任务时不允许删除；被流程引用时不允许删除。
  - **注意事项**: 创建模板不收费；删除后不影响已运行中的实例。
- **异常**: 无

---

## 65. 调试沙箱实例

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/debugging-sandbox-instances?lang=zh`
- **读取范围**: offset 0–32（仅导航页）
- **是否到底**: 是
- **关键内容**: 页面标题为"新功能发布记录"，正文仅为导航链接列表，无调试沙箱实例的正文内容。
- **异常**: 正文为空，页面标题与 URL 不匹配（重定向到新功能发布记录页）

---

## 统计汇总表

| 序号 | 页面标题 | URL 末段 | 读取状态 | 是否到底 | 异常 |
|---|---|---|---|---|---|
| 1 | 创建智能体运行时（CLI） | CreatingruntimesCLItool | 成功 | 是 | 无 |
| 2 | 智能体运行时概述 | Agentruntimeoverview | 成功（重试） | 是 | 此前标记失败，本次成功 |
| 3 | 更新 A2A 空间 | UpdatingA2Aspaces | 成功 | 是 | 正文仅导航，无内容 |
| 4 | 运行时实例概述 | Runtimeinstanceoverview | 成功 | 是 | 无 |
| 5 | 查看运行时实例日志 | ViewRuntimeInstanceLog | 成功 | 是 | 无 |
| 6 | 发布运行时 | Releasingruntimes | 成功 | 是 | 无 |
| 7 | 查看运行时不可用日志 | Viewinglogsforagentruntimeunavailability | 成功 | 是 | 无 |
| 8 | 查看运行时网络信息 | Viewruntimenetworkinformation | 成功 | 是 | 无 |
| 9 | 删除运行时 | Deletingruntimes | 成功 | 是 | 无 |
| 10 | 运行时安全最佳实践 | Runtimesecuritybestpractices | 成功 | 是 | 无 |
| 11 | 快速使用沙箱模板 | quickly-use-sandbox-template | 成功 | 是 | 无 |
| 12 | 创建沙箱模板 | Creatingtools | 重定向 | 是 | 重定向到文档中心首页 |
| 13 | 更新沙箱模板类型 | Updatingtooltypes | 重定向 | 是 | 重定向到文档中心首页 |
| 14 | 代码沙箱工具示例 | Codesandboxtoolexample | 成功 | 是 | 无 |
| 15 | 浏览器沙箱工具示例 | Browsersandboxtoolexample | 成功 | 是 | 无 |
| 16 | 预置 Skills 示例 | UsageexampleofpresetSkills | 成功 | 是 | 无 |
| 17 | 自定义 Skills 示例 | UsageexampleofcustomSkills | 成功 | 是 | 无 |
| 18 | 删除沙箱模板 | Deletingtools | 成功 | 是 | 无 |
| 19 | 创建沙箱实例 | Creatingtoolinstances | 成功 | 是 | 无 |
| 20 | 沙箱实例添加消息渠道 | add-message-channel-to-arkclaw-sandbox-tool-instance | 成功 | 是 | 无 |
| 21 | 删除沙箱实例 | Deletingtoolinstances | 成功 | 是 | 正文为空 |
| 22 | Self-hosted Skills Sandbox | Using[PRODUCT]Self-hostedSkillsSandboxinVolcanoArk | 成功 | 是 | 无 |
| 23 | 快速上手 Skills | quick-start-skills-skill-construction-to-business-implementation-based-on-intelligent-workshop | 成功 | 是 | 无（长文，分5页读完） |
| 24 | 创建 Skill | CreatingSkills-1 | 成功 | 是 | 无 |
| 25 | 调试 Skill | DebuggingSkills | 成功 | 是 | 无 |
| 26 | 评估 Skill | AssessmentSkills | 成功 | 是 | 无 |
| 27 | 注册 Skill | RegisteredSkills | 成功 | 是 | 无 |
| 28 | 创建 Skill 空间 | CreatingSkillsspaces | 成功 | 是 | 无 |
| 29 | 添加/移除 Skill | AddingRemovingSkills | 成功 | 是 | 无 |
| 30 | 修改 Skill 版本 | ChangingSkillversions | 成功 | 是 | 无 |
| 31 | 删除 Skill 空间 | DeletingSkillsspaces | 成功 | 是 | 无 |
| 32 | 预置 Skill | PresetSkills | 成功 | 是 | 无 |
| 33 | 创建自定义 Skill | CreatingSkills | 成功 | 是 | 无 |
| 34 | 在 Skills 空间添加/移除 Skill | AddingRemovingSkillsinSkillsSpaces | 成功 | 是 | 无 |
| 35 | 查看 Skill 版本信息 | ViewingversiondetailsofSkills | 成功 | 是 | 无 |
| 36 | 查看 Skill 变更详情 | ViewingSkillchangedetails | 成功 | 是 | 无 |
| 37 | 更新自定义 Skill | UpdatingSkills | 成功 | 是 | 无 |
| 38 | 发布 Skill | PublishingSkills | 成功 | 是 | 无 |
| 39 | 删除 Skill | DeletingSkills | 成功 | 是 | 无 |
| 40 | 创建 A2A 智能体空间 | CreatingA2Aagentspaces | 成功 | 是 | 无 |
| 41 | 删除 A2A 智能体空间 | DeletingA2Aagentspaces | 成功 | 是 | 无 |
| 42 | 注册 A2A 智能体 | RegisteringA2Aagents | 成功 | 是 | 无 |
| 43 | 更新 A2A 智能体 JSON 文件 | UpdatingA2AagentJSONfile | 成功 | 是 | 无 |
| 44 | 更新 AgentCard 地址 | UpdatingAgentCardaddressesofA2Aagents | 重定向 | 是 | 重定向到文档中心首页 |
| 45 | 查看智能体 JSON 文件 | ViewingA2AagentJSONfile | 成功 | 是 | 无 |
| 46 | 管理智能体版本 | ManagingA2Aagentversions | 成功 | 是 | 无 |
| 47 | 注销 A2A 智能体 | UnregisteringA2Aagents | 成功 | 是 | 无 |
| 48 | A2A 智能体 JSON 文件示例 | SampleA2AagentJSONfile | 成功（重试） | 是 | 此前标记失败，本次成功 |
| 49 | 添加 MCP 工具 | AddingMCPtools | 重定向 | 是 | 重定向到文档中心首页 |
| 50 | 创建 MCP 工具集 | CreatingMCPtoolset | 成功 | 是 | 无 |
| 51 | 调试 MCP 工具集 | TestingMCPtoolset | 成功 | 是 | 无 |
| 52 | 在 MCP 工具集添加/移除工具 | AddingRemovingMCPtools | 成功 | 是 | 无 |
| 53 | 更新工具调用模式 | Updatingtoolcallingmode | 成功 | 是 | 无 |
| 54 | 查看 MCP 工具集网络信息 | check-mcp-toolset-network-info | 成功 | 是 | 无 |
| 55 | 删除 MCP 工具集 | DeletingMCPtoolsets | 成功 | 是 | 无 |
| 56 | 查看运行时监控数据 | Viewingagentruntimemonitoringdata | 成功 | 是 | 无 |
| 57 | 查看工具监控数据 | Viewingtoolmonitoringdata | 成功 | 是 | 无 |
| 58 | 查看 MCP 工具集监控数据 | ViewingMCPtoolsetmonitoringdata | 成功 | 是 | 无 |
| 59 | CLI 沙箱运行 Codex | RunningCodexinasandboxvia[PRODUCT]CLI | 成功 | 是 | 无 |
| 60 | UpdateRuntimeRelease API | Updateruntimerelease-Updatesruntimerelease | 成功 | 是 | 无 |
| 61 | Runtime FAQ | RuntimeFAQ | 重定向 | 是 | 重定向到文档中心首页 |
| 62 | 工具 FAQ | ToolFAQ | 成功 | 是 | 无 |
| 63 | 创建沙箱模板和添加模型 | operation-2-create-sandbox-templates-and-add-models | 成功 | 是 | 无 |
| 64 | 管理沙箱模板 | manage-sandbox-templates | 成功 | 是 | 无 |
| 65 | 调试沙箱实例 | debugging-sandbox-instances | 成功 | 是 | 标题不匹配，正文为空 |

### 统计汇总

| 指标 | 数量 |
|---|---|
| 总页面数 | 65 |
| 成功读取（含重试） | 58 |
| 重定向/空页面 | 7 |
| 其中：此前失败本次重试成功 | 2（Agentruntimeoverview、SampleA2AagentJSONfile） |
| 分页读取完成 | 65 |
| 未读完 | 0 |

### 异常页面明细

| 序号 | URL 末段 | 异常类型 | 说明 |
|---|---|---|---|
| 3 | UpdatingA2Aspaces | 正文为空 | 仅导航树，无正文内容 |
| 12 | Creatingtools | 重定向 | 重定向到文档中心首页 |
| 13 | Updatingtooltypes | 重定向 | 重定向到文档中心首页 |
| 21 | Deletingtoolinstances | 正文为空 | 仅"欢迎来到文档中心" |
| 44 | UpdatingAgentCardaddressesofA2Aagents | 重定向 | 重定向到文档中心首页 |
| 49 | AddingMCPtools | 重定向 | 重定向到文档中心首页 |
| 61 | RuntimeFAQ | 重定向 | 重定向到文档中心首页 |
| 65 | debugging-sandbox-instances | 标题不匹配 | 重定向到"新功能发布记录"页 |
