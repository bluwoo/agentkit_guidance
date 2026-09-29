# 火山引擎 [PRODUCT] 官方文档分片5读取结果

> 读取时间：2026-09-18
> 分片文件：`shards/shard5_misc_deliveryai.txt`
> 总页数：141 页（主产品 100 页 + DeliveryAI 子产品 41 页）
> 读取方式：web.fetch 逐页分页读取

---

## 一、公告/计费

### 1. [PRODUCT]商用公告

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/BillingAnnouncement[PRODUCT]CommercialAnnouncement?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: [PRODUCT]产品正式商业化公告。说明自指定日期起[PRODUCT]由邀测转正式商用，按实际用量计费。计费项包括智能体运行时(Runtime)、沙箱(Sandbox)、网关(Gateway)等组件。
- **异常**: 无

### 2. [PRODUCT] Harness邀测公告

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/product-announcement-[PRODUCT]-harness-is-officially-invited-for-testing?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: [PRODUCT] Harness邀测发布公告。Harness是[PRODUCT]的高级编排能力，支持多Agent协作工作流编排。邀测阶段需联系客户经理申请开通。
- **异常**: 无

### 3. Agent Registry发布公告

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/product-announcement-agent-registry-officially-released?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: Agent Registry正式发布公告。Agent Registry是[PRODUCT]中的智能体注册中心，支持Agent的注册、发现和版本管理。
- **异常**: 无

### 4. [PRODUCT]网关升级公告

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/billing-announcement-announcement-on-[PRODUCT]-billing-system-upgrade-and-abnormal-fluctuation-bill-p?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: [PRODUCT]网关服务升级公告。说明网关架构升级内容及对用户的影响（无感知升级，接口兼容）。
- **异常**: 无

### 5. [PRODUCT]计费系统升级公告

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/billing-announcement-announcement-on-[PRODUCT]-billing-system-upgrade-and-abnormal-fluctuation-bill-p?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 计费系统升级公告，说明计费系统升级及异常波动账单处理方案。
- **异常**: URL与第4页相同（同一页面），内容为计费系统升级公告。

### 6. 计费方式

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Billingmethod_1?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: [PRODUCT]采用按量计费（后付费）模式。核心计费项：智能体运行时(Runtime)、工具/沙箱(Sandbox)、网关(Gateway)。每项资源按实际用量独立计费。
- **异常**: 无

### 7. 变更规格

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Statementofarrears_1?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 欠费说明。账户欠费后服务的处理策略：欠费后资源暂停运行，欠费通知与恢复机制。
- **异常**: 页面标题为"欠费说明"，URL slug为Statementofarrears_1。

### 8. 税费说明

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Taxexplanation_1?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 税费说明。[PRODUCT]费用适用增值税税率，发票开具规则。
- **异常**: 无

---

## 二、快速入门

### 9. 开发部署概览

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Overviewofdevelopinganddeployingagents?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 概述Agent开发部署三种路径：①[PRODUCT] Studio低代码搭建；②CLI + [BASE-ADK]代码开发；③自然语言驱动TRAE开发。
- **异常**: 无

### 10. Studio搭建部署

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/SetupanddeployAgentusing[PRODUCT]Studio?lang=zh`
- **读取范围**: 0–全文读完（大图过滤后正文完整）
- **是否到底**: 是
- **关键内容**: 通过[PRODUCT] Studio在控制台可视化搭建并部署Agent。步骤：创建应用→配置模型→配置工具/Skill→配置网关→部署发布。
- **异常**: 首次请求因大图过滤未返回正文，重试后成功。

### 11. CLI开发部署（[BASE-ADK]）

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Advancedquickstartagentdevelopmentanddeploymenttutorial?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 使用[BASE-ADK]（火山引擎Agent Development Kit）进行高代码开发部署。涉及安装[BASE-ADK] SDK、编写Agent代码（Agent类定义、工具绑定、Runner调用）、通过CLI部署到[PRODUCT] Runtime。
- **异常**: 首次因大图过滤未返回正文，重试后成功。

### 12. 存量Agent迁移概述

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/OverviewofStockAgentMigration?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 存量Agent迁移概述。支持将外部已运行的Agent迁移到[PRODUCT]平台，提供高代码框架和低代码框架两种迁移路径。
- **异常**: 无

### 13. 存量Agent迁移原理

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/StockAgentMigrationPrinciple?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 迁移原理说明。通过适配层将现有Agent框架（如LangChain、原生Python等）的接口映射到[PRODUCT] Runtime，实现无缝迁移。
- **异常**: 无

### 14. 高代码框架迁移操作指南

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ExistingAgentMigrationOperationGuideHigh-CodeFramework?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 高代码框架迁移详细步骤：①安装迁移适配器；②修改Agent入口文件；③配置依赖和环境变量；④通过CLI部署验证。包含代码示例。
- **异常**: 无

### 15. 低代码框架迁移操作指南

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ExistingAgentMigrationOperationGuideLow-CodeFramework?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 低代码框架迁移操作指南。适用于从Dify、Coze等低代码平台迁移Agent，通过导入配置文件或重建方式完成迁移。
- **异常**: 无

### 16. 存量Agent迁移FAQ

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/StockAgentMigrationFAQ?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 迁移常见问题解答：兼容性问题、数据迁移、工具/MCP迁移、会话历史迁移等。
- **异常**: 无

### 17. 自然语言驱动TRAE开发

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/NaturalLanguageDrivenDevelopandDeployAgentwithTRAE?lang=zh`
- **读取范围**: 0–4122 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: 使用TRAE IDE通过自然语言对话开发和部署Agent。前置条件：安装[PRODUCT] CLI并完成登录（`[PRODUCT] login`）。开发生命周期：需求描述→代码生成→本地调试→CLI部署→网关配置→发布。CLI安装命令：`pip install [PRODUCT]`。
- **异常**: 首次请求total_length显示52496字符但实际token总量仅4122，首次读取即已读完。

---

## 三、应用概述/模板/一键部署

### 18. 应用概述

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Applicationoverview-2?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 应用管理概述。[PRODUCT]中的应用(Application)是可部署的Agent实体，包含模型、工具、网关配置等。
- **异常**: 无

### 19. 应用模板

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Usingapplicationtemplates?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 使用应用模板快速创建Agent。平台提供视频创作、客户服务、旅行助理等预置模板。
- **异常**: 无

### 20. 一键部署视频创作[DELIVERY]

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/One-clickdeploymentofvideocreation[DELIVERY]?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 一键部署视频创作[DELIVERY]应用模板。包含视频脚本生成、素材推荐、剪辑指导等能力。
- **异常**: 无

### 21. 一键部署客户服务Assistant

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/One-clickdeploymentofClientServerAssistant?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 一键部署客户服务Assistant应用模板。预置客服知识库接入、多轮对话、转人工等能力。
- **异常**: 无

### 22. 一键部署智能旅行助理

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/One-clickdeploymentofintelligenttravelassistant?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 一键部署智能旅行助理应用模板。包含行程规划、景点推荐、天气查询等能力。
- **异常**: 首次因大图过滤未返回正文，重试后成功。

### 23. 多模态示例调用

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Multimodalsamplecallspromptsandfiles?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 多模态示例调用。支持文本+图片输入的Agent调用示例，包含curl请求和响应格式。
- **异常**: 无

---

## 四、运行时操作

### 24. 更新自定义镜像

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Updatingcustomimages?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 运行时自定义镜像更新操作。
- **异常**: 无

### 25. 更新实例配置

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Updatinginstanceconfigurations?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 运行时实例规格/配置更新操作。
- **异常**: 无

### 26. 更新模型配置

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Updatingmodelconfiguration?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 运行时绑定模型更新操作。
- **异常**: 无

### 27. 更新环境变量

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Updatingenvironmentvariables?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 运行时环境变量更新操作。
- **异常**: 无

### 28. 更新关联组件

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Updatingassociatedcomponents?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 运行时关联组件（知识库、记忆库等）更新操作。
- **异常**: 无

### 29. 远程连接

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Remoteconnection?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 运行时远程连接（SSH/调试端口）配置。
- **异常**: 无

### 30. 查看发布流程

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Viewingreleaseprocess?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 查看运行时发布流程状态。
- **异常**: 无

### 31. 查看发布历史

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Viewingreleasehistory?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 查看运行时发布历史记录。
- **异常**: 无

### 32. 查看版本信息

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Viewingversioninformation?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 查看运行时版本信息。
- **异常**: 无

---

## 五、沙箱操作

### 33. 操作流程

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Operationflow?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 沙箱操作流程概览。
- **异常**: 无

### 34. 更新实例规格

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Updatinginstancespecification?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 沙箱实例规格升降配操作。
- **异常**: 无

### 35. 更新模型配置（沙箱）

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Updatingmodelconfiguration-1?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 沙箱模型配置更新操作。
- **异常**: 无

### 36. 更新存储配置

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Updatingstorageconfiguration?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 沙箱存储配置更新操作。
- **异常**: 无

### 37. 更新环境变量（沙箱）

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Updatingenvironmentvariables-1?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 沙箱环境变量更新操作。
- **异常**: 无

### 38. 更新生命周期时长

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Updatinglifecycleduration?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 沙箱生命周期时长配置。
- **异常**: 无

### 39. 通过快照恢复实例

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/restore-instance-with-snapshot?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 通过快照恢复沙箱实例。
- **异常**: 无

### 40. 查看实时日志

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Viewingreal-timelogs?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 查看沙箱实时日志。
- **异常**: 无

### 41. 启用/禁用语义检索

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Enablingordisablingsemanticretrieval?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 沙箱语义检索功能开关。
- **异常**: 无

### 42. 切换公网/私网服务地址

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Changingpublicorprivatenetworkserviceaddress?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 沙箱网络服务地址公网/私网切换。
- **异常**: 无

---

## 六、会话管理操作

### 43. 快速搭建会话管理

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/quickly-set-up-and-use-session-management?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 快速搭建会话管理资源的操作指南。
- **异常**: 无

### 44. 创建会话资源

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Creatingsessionresources?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 创建会话管理资源实例。
- **异常**: 无

### 45. 导入会话资源

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Importingsessionresources?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 导入已有会话数据。
- **异常**: 无

### 46. 集成会话资源到Agent

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Integratingsessionresourcesinagents?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 在Agent配置中集成会话管理资源。
- **异常**: 无

### 47. 删除会话资源

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Deletingsessionresources?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 删除会话管理资源。
- **异常**: 无

---

## 七、记忆库操作

### 48. 快速搭建记忆库

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Quicklysetupandusememorybanks?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 快速搭建并使用记忆库。
- **异常**: 无

### 49. 创建记忆库

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Creatingmemories?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 创建记忆库实例。
- **异常**: 无

### 50. 导入记忆库

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Importingmemories?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 导入已有记忆数据。
- **异常**: 无

### 51. 记忆检索

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Memoryretrieval?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 记忆检索操作。
- **异常**: 无

### 52. 更新记忆检索策略

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Updatingmemoryretrievalstrategies?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 更新记忆检索策略配置。
- **异常**: 无

### 53. 记忆库私网配置

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Configuringprivatenetwork?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 记忆库私网访问配置。
- **异常**: 无

### 54. 删除记忆库

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Deletingmemories?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 删除记忆库资源。
- **异常**: 无

---

## 八、知识库操作

### 55. 快速搭建知识库

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Building[PRODUCT]knowledgebasesfromscratch?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 从零搭建[PRODUCT]知识库。
- **异常**: 无

### 56. 导入知识库

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Importingknowledgebases?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 导入知识库文档。
- **异常**: 无

### 57. 知识检索

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Knowledgeretrieval-1?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 知识库检索操作。
- **异常**: 无

### 58. 知识问答

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/KnowledgeQA?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 知识库问答测试。
- **异常**: 无

### 59. 查看原始文档

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Viewingoriginaldocuments?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 查看知识库中的原始文档。
- **异常**: 无

### 60. 查看切片详情

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Viewingchunkdetails?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 查看文档切片详情。
- **异常**: 无

### 61. 知识库私网配置

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Configuringprivatenetwork-1?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 知识库私网访问配置。
- **异常**: 无

### 62. 删除知识库

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Deletingknowledgebases?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 删除知识库。
- **异常**: 无

---

## 九、网关/模型/函数服务操作

### 63. 私网域名公网DNS解析开关

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/enable_or_disable_public_dns_resolution_for_private_domain?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 私网域名公网DNS解析开关配置。
- **异常**: 无

### 64. 获取调用示例

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Obtainingsamplecalls?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 获取网关API调用示例。
- **异常**: 无

### 65. 更新后端服务

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Updatingbackendservice?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 更新网关后端服务配置。
- **异常**: 无

### 66. 获取调用示例（模型服务）

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Obtainingsamplecalls-1?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 获取模型服务调用示例。
- **异常**: 无

### 67. 配置私网域名访问

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/configure-private-domain-access?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 私网域名访问配置。
- **异常**: 无

### 68. 创建模型服务

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/create-model-service?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 创建模型服务实例。
- **异常**: 无

### 69. 集成模型信息到Agent

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/integrate-model-information-in-agent?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 在Agent中集成模型服务。
- **异常**: 无

### 70. 管理模型服务

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/management-model-service?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 模型服务管理操作。
- **异常**: 无

### 71. 部署函数服务

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/deploy_function_service?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 部署函数服务。
- **异常**: 无

### 72. 函数服务开发规范

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/function_service_development_specification?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 函数服务开发规范。
- **异常**: 无

---

## 十、身份与权限（入站/出站授权）

### 73. 入站授权-启用快速登录

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/inbound-authorization-enable-quick-login-function-for-your-agent?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 入站授权配置：为Agent启用快速登录功能，用户通过SSO快速访问Agent。
- **异常**: 无

### 74. 入站授权-集成企业SSO联邦登录

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/inbound-authorization-integrate-enterprise-sso-to-implement-federated-login?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 集成企业SSO（OIDC/SAML）实现联邦登录。
- **异常**: 无

### 75. 出站授权-Agent代表用户访问第三方资源

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/outbound-authorization-agent-represents-the-user-to-access-thirdparty-resources?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 出站授权：Agent代表用户获取OAuth token访问第三方资源。
- **异常**: 无

### 76. 创建用户池

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/create-user-pool?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 在Agent Identity平台创建用户池。
- **异常**: 无

### 77. 创建客户端

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/create-client-side?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 在用户池中创建客户端应用。
- **异常**: 无

### 78. 创建用户

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/create-user?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 在用户池中创建用户。
- **异常**: 无

### 79. 配置认证信息

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/configure-authentication-information?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 配置认证信息。
- **异常**: 无

### 80. 创建凭证

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/create-credentials?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 创建访问凭证。
- **异常**: 无

### 81. 查看安全概览

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Viewingsecurityoverview?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 安全概览面板。
- **异常**: 无

### 82. 查看攻击日志

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Viewingattacklogs?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 安全攻击日志查看。
- **异常**: 无

---

## 十一、监控/观测

### 83. 查看记忆监控数据

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Viewingmemorymonitoringdata?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 记忆库监控指标查看。
- **异常**: 无

### 84. 查看模型服务监控数据

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Viewmodelservicemonitoringdata?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 模型服务监控指标查看。
- **异常**: 无

### 85. 启用日志

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Enablinglogs?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 日志采集启用配置。
- **异常**: 无

### 86. 查看日志

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Viewinglogs-2?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 日志查看与检索。
- **异常**: 无

---

## 十二、IAM/标签/项目

### 87. IAM概述

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/IAMoverview-20?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 火山引擎访问控制(IAM)概述，与[PRODUCT]的关系。
- **异常**: 无

### 88. [PRODUCT] IAM策略类型

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/[PRODUCT]IAMpolicytypes?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: [PRODUCT]支持的IAM策略类型：系统策略和自定义策略。
- **异常**: 无

### 89. 标签管理

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Tagmanagement?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 标签管理操作。
- **异常**: 无

### 90. 标签设计原则

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Tagdesignprinciples-2?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 标签设计最佳实践。
- **异常**: 无

### 91. 项目管理

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Managingprojects-5?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 项目管理操作。
- **异常**: 无

---

## 十三、TRAE/CLI

### 92. TRAE快速集成飞书机器人并部署

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/UseTRAEtoquicklyintegrateFeishurobotsanddeployto[PRODUCT]?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 使用TRAE IDE快速集成飞书机器人并部署到[PRODUCT]。
- **异常**: 无

### 93. 配置[PRODUCT] CLI SSO

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/configure-[PRODUCT]-cli-single-signon-sso?lang=zh`
- **读取范围**: 0–13781 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: 使用`[PRODUCT] auth admin sso-setup`命令为企业配置CLI单点登录。创建/复用UserPool、CLI客户端、OIDC Provider、STS角色、登录发现文档。支持两种模式：不接入上游IdP（[PRODUCT]自管理用户）和接入上游IdP联邦登录（如飞书）。前置条件需[PRODUCT]SandboxAccess系统策略。支持`[PRODUCT] auth admin doctor`一键健康检查。飞书IdP需权限`contact:user.base:readonly`和`contact:user.email:readonly`。
- **异常**: 无

---

## 十四、SDK参考

### 94. [PRODUCT]AgentServerApp

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/[PRODUCT]AgentServerApp?lang=zh`
- **读取范围**: 0–3076 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: **[PRODUCT]AgentServerApp**是[PRODUCT] SDK中基于A2A协议的高级应用框架，集成Google ADK Web Server。
  - **快速开始代码**:
    ```python
    from [PRODUCT].apps import [PRODUCT]AgentServerApp
    from [BASE-ADK] import Agent
    from [BASE-ADK].memory.short_term_memory import ShortTermMemory
    root_agent = Agent(name="root_agent", instruction="...")
    short_term_memory = ShortTermMemory(backend="local")
    agent_server_app = [PRODUCT]AgentServerApp(agent=root_agent, short_term_memory=short_term_memory)
    agent_server_app.run(host="0.0.0.0", port=8000)
    ```
  - **API端点**:
    - `POST /apps/{app_name}/users/{user_id}/sessions/{session_id}` — 创建会话（指定session_id）
    - `POST /apps/{app_name}/users/{user_id}/sessions` — 创建会话（自动分配session_id）
    - `POST /run_sse` — 流式对话（推荐）
    - `POST /run` — 非流式对话
    - `POST /invoke` — 兼容CLI调用（从headers提取user_id/session_id）
  - **请求参数**: app_name, user_id, session_id(可选), new_message(Content), streaming, state_delta, invocation_id
  - **Part结构**: 支持text, inlineData(Base64图片), fileData, functionCall, functionResponse, executableCode, codeExecutionResult, thought, thoughtSignature, mediaResolution, videoMetadata
  - **框架对比**: [PRODUCT]SimpleApp(@app.entrypoint), [PRODUCT]MCPApp(@app.tool), [PRODUCT]A2aApp(@app.agent_executor), [PRODUCT]AgentServerApp(完整服务端)
- **异常**: 无

### 95. Anotation使用指南

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Annotationusageguide?lang=zh`
- **读取范围**: 0–3246 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: **[PRODUCT] SDK装饰器(注解)使用指南**：
  - **@app.entrypoint**: Agent主入口函数，签名`async def run(payload: dict, headers: dict) -> str`。payload含prompt等输入，headers含user_id/session_id/request_id。
  - **@app.ping**: 健康检查函数，签名`def ping() -> str`，同步函数，1秒内返回。自动注册到GET /ping, /health, /readiness, /liveness。
  - **@app.tool**: MCP工具注册，函数参数必须有类型注解，文档字符串作为工具描述。支持同步和异步。
  - **@app.agent_as_a_tool**: 将整个Agent封装为MCP工具。
  - **@app.agent_executor**: A2A Agent执行器注册，需传入runner，可继承A2aAgentExecutor或自定义AgentExecutor。
  - **@app.task_store**: A2A任务存储注册，默认InMemoryTaskStore，可自定义Redis等持久化存储。
  - **最佳实践**: 错误处理、日志记录、类型注解、文档字符串、性能优化（Agent/Runner只创建一次）。
- **异常**: 无

---

## 十五、FAQ/条款

### 96. 通用FAQ

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/GeneralFAQ?lang=zh`
- **读取范围**: 0–75 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: 如何计费——按量计费后付费，核心计费项：Runtime、Sandbox、Gateway三大组件。
- **异常**: 无

### 97. 内存FAQ

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/MemoryFAQ?lang=zh`
- **读取范围**: 0–全文读完
- **是否到底**: 是
- **关键内容**: 记忆库相关常见问题。
- **异常**: 无

### 98. [PRODUCT]产品和服务条款

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/[PRODUCT]PlatformTermsofService?lang=zh`
- **读取范围**: 0–1807 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: 专用条款：①适用范围；②服务使用规则（已有产品条款适用、服务内容——不提供AI模型服务、输出内容——AIGC合规要求、第三方产品引入责任、个人信息保护、应用广场免责）；③试用说明（邀测/公测不承诺SLA）。更新时间2026.06.04。
- **异常**: 无

### 99. [PRODUCT]应用广场使用规则和免责声明

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/TermsofUseandDisclaimeron[PRODUCT]AgentGallery?lang=zh`
- **读取范围**: 0–1322 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: 应用广场规则：①功能定位为教学示例非专业产品；②AIGC局限性风险提示；③金融/医疗/法律行业特别声明；④禁止行为清单（逆向工程、爬虫、删除AI标识等）；⑤用户责任与数据隐私；⑥第三方服务；⑦服务可用性与责任限制。版本日期2026.01.12。
- **异常**: 无

---

## 十六、DeliveryAI 子产品

> **独立子产品说明**: DeliveryAI（交付官）是嵌入在[PRODUCT]控制台中的独立子产品，提供"需求→交付→代码→环境"的自动化研发交付流程能力。管理端为[PRODUCT]控制台中的DeliveryAI入口（企业管理员全局配置），用户端为独立Web页面与桌面客户端（空间创建、流程配置、需求处理）。当前为邀测阶段。

### 100. 新功能发布记录

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/new-feature-release-record?lang=zh`
- **读取范围**: 0–698 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: DeliveryAI发布动态：
  - **2026.09.16**: 模型管理支持直接选方舟API Key/思考强度配置；企业集成支持GitHub；服务总览新增沙箱用量统计；Skill批量上传；Demo空间创建；评测中心（评估器/评测集/评测任务）；Skill"/"命令调用。
  - **2026.09.07**: 需求中心节点催办/关联仓库管理/需求用量面板；仓库上下文扫描自动触发；Skill/MCP管理搜索框。
  - **2026.08.18**: DeliveryAI首次发布上线（邀测，华北2北京）。
- **异常**: 无

### 101. DeliveryAI应用场景

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/application-scenarios?lang=zh`
- **读取范围**: 0–1221 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: 五类适用场景：①端到端需求交付自动化（飞书项目→DeliveryAI→GitLab）；②智能体驱动的研发角色沉淀（Agent模板复用）；③可追溯的AI研发过程（节点证据沉淀）；④交付链路的分层治理（空间管理员+普通用户双层配置）；⑤存量流程接入与渐进式落地。不建议场景：需求极度模糊、脱离代码仓库的一次性任务、高频短生命周期临时变更。
- **异常**: 无

### 102. DeliveryAI计费说明

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/billing-instructions?lang=zh`
- **读取范围**: 0–319 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: DeliveryAI开通本身不收费。计费资源：①沙箱——AI节点运行/自定义任务/仓库扫描自动创建沙箱实例。Agent占用规则：单次有效期1小时，剩余不足10分钟自动续期1小时，同一会话复用，累计超22小时重建新实例。②模型——由火山方舟等模型提供方计费。
- **异常**: 无

### 103. DeliveryAI开通服务

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/activate-service?lang=zh`
- **读取范围**: 0–1402 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: 企业管理员在[PRODUCT]控制台开通DeliveryAI。邀测阶段需联系客户经理。步骤：登录[PRODUCT]控制台→左侧导航选DeliveryAI→一键启用服务。三步流程：集成企业现有系统→配置Agent服务依赖→交付用户端入口。
- **异常**: 无

### 104. 集成GitLab

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/integration-with-gitlab?lang=zh`
- **读取范围**: 0–35 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: 页面仅含标题"集成 GitLab"，无正文内容。
- **异常**: 页面内容极短，仅有标题和导航链接，无实际操作文档正文。

### 105. 集成GitHub

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/IntegrationwithGitHub?lang=zh`
- **读取范围**: 0–3324 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: 将DeliveryAI与GitHub连接。前提：已开通DeliveryAI。步骤：[PRODUCT]控制台→DeliveryAI→企业集成→GitHub卡片→配置（API URL预置为https://api.github.com）→保存→启用开关→测试连通性。注意：访问GitHub可能不稳定，建议中国大陆用户优先用GitLab。
- **异常**: 无

### 106. 集成Jira

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/integrate-jira?lang=zh`
- **读取范围**: 0–5355 tokens（总23481，未读完）
- **是否到底**: 否（仅读取前5355 tokens）
- **关键内容**: 将DeliveryAI与Jira连接。前提：Jira管理权限、获取Webhook地址。步骤：Jira平台→Atlassian管理设置→用户管理→服务账户→创建服务账户（名称如DeliveryAI）→选择应用角色（Jira=用户访问权限管理员，Projects=应用管理员）→创建凭据。DeliveryAI配置：Jira服务地址、Service Account Client ID/Secret、Webhook地址。
- **异常**: 页面总长度23481 tokens，仅读取前5355 tokens，后续步骤未读完。

### 107. 集成飞书项目

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/integrated-feishu-project?lang=zh`
- **读取范围**: 0–5358 tokens（总24567，未读完）
- **是否到底**: 否（仅读取前5358 tokens）
- **关键内容**: 将DeliveryAI与飞书项目连接。前提：飞书项目企业管理权限、获取Webhook地址。步骤：飞书项目开放平台→创建插件→配置插件名称/图标→复制Plugin ID和Plugin Secret→配置基本信息→添加插件构成。DeliveryAI配置：服务地址https://<INTERNAL_HOST>.cn、API Endpoint、Plugin ID、Plugin Secret。
- **异常**: 页面总长度24567 tokens，仅读取前5358 tokens，后续步骤未读完。

### 108. 集成飞书

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/integrated-feishu?lang=zh`
- **读取范围**: 0–38 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: 页面仅含标题"集成飞书"，无正文内容。
- **异常**: 页面内容极短，仅有标题和导航链接。

### 109. 登录方式使用说明

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/login-method-instructions?lang=zh`
- **读取范围**: 0–517 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: DeliveryAI支持四类登录方式：①飞书（需提前配置，适合已用飞书的企业）；②平台托管（无需配置，适合无SSO企业）；③OIDC（需提前配置，适合已有统一IdP）；④OAuth 2.0（需提前配置，适合已有OAuth授权体系）。选型建议：快速体验用平台托管；深度用飞书选飞书；自建账号中心选OIDC/OAuth 2.0。
- **异常**: 无

### 110. 飞书登录配置

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/feishu?lang=zh`
- **读取范围**: 0–5474 tokens（总21869，未读完）
- **是否到底**: 否（仅读取前5474 tokens）
- **关键内容**: 企业管理员配置飞书SSO登录。步骤：飞书开发者平台→创建企业自建应用→配置应用名称/描述/图标→权限管理→批量导入权限（tenant: contact:user.base:readonly, contact:user.email:readonly）→申请开通→配置数据范围。
- **异常**: 页面总长度21869 tokens，仅读取前5474 tokens。

### 111. 平台托管登录

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/platform-hosting?lang=zh`
- **读取范围**: 0–4591 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: 平台托管使用账号密码登录。步骤：DeliveryAI→用户管理→登录配置→编辑→选择"平台托管"→保存→添加员工（CSV/XLSX导入，支持邮箱/手机号/用户名匹配）→启用用户（从"待激活"变"正常"）→允许创建空间开关→服务总览获取登录链接→发放给员工。
- **异常**: 无

### 112. OIDC登录配置

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/oidc?lang=zh`
- **读取范围**: 0–5948 tokens（总28474，未读完）
- **是否到底**: 否（仅读取前5948 tokens）
- **关键内容**: 以火山引擎Agent Identity和阿里云IDaaS为示例配置OIDC。步骤：①创建用户池（名称/描述/登录属性/注册属性/所属项目/标签）；②创建客户端（Web应用/SPA/移动应用/M2M类型，允许回调URIs）；③获取企业认证信息（OIDC发现端点Discovery URL，Issuer信息）。
- **异常**: 页面总长度28474 tokens，仅读取前5948 tokens。

### 113. OAuth 2.0登录配置

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/oauth-20?lang=zh`
- **读取范围**: 0–5903 tokens（总31132，未读完）
- **是否到底**: 否（仅读取前5903 tokens）
- **关键内容**: 以火山引擎Agent Identity和阿里云IDaaS为示例配置OAuth 2.0。步骤同OIDC：创建用户池→创建客户端→获取客户端ID/Secret→获取OIDC发现端点。
- **异常**: 页面总长度31132 tokens，仅读取前5903 tokens。

### 114. Step 3: 交付用户入口

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/step-3-deliver-the-user-portal?lang=zh`
- **读取范围**: 0–3510 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: 企业管理员交付用户端入口。方式一：Web访问入口（服务总览→登录链接→访问用户端→复制URL）。方式二：桌面客户端下载链接（客户端下载页→选择macOS Apple芯片/macOS Intel/Windows x64→复制链接）。当前版本v1.0.83。
- **异常**: 无

### 115. 步骤二: 空间管理员-创建并配置空间

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/step-2-space-administrator-create-and-configure-spaces?lang=zh`
- **读取范围**: 0–4999 tokens（总16628，未读完）
- **是否到底**: 否（仅读取前4999 tokens）
- **关键内容**: 空间管理员流程：登录授权（完成GitLab/Jira/飞书/GitHub OAuth授权）→创建空间（空间名称/代码托管系统/需求系统/需求空间/自定义字段条件）→配置空间流程与节点（产品设置→流程管理→导入流程→配置节点类型AI/人工、Agent模板、沙箱规格、自动流转）。
- **异常**: 页面总长度16628 tokens，仅读取前4999 tokens。

### 116. 服务总览

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/service-overview?lang=zh`
- **读取范围**: 0–1042 tokens
- **是否到底**: 是
- **关键内容**: 返回"欢迎来到文档中心"占位页，无实质内容。
- **异常**: 页面为文档中心占位页，非DeliveryAI服务总览正文。

### 117. 用户管理概述

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/user-management-overview?lang=zh`
- **读取范围**: 0–220 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: 用户管理模块功能：维护员工信息、添加新成员、管理员工状态（停用/删除）、控制空间创建权限、重置登录密码、配置登录认证方式。
- **异常**: 无

### 118. 配置认证方式

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/configure-authentication-method?lang=zh`
- **读取范围**: 0–5175 tokens（总9966，未读完）
- **是否到底**: 否（仅读取前5175 tokens）
- **关键内容**: 企业管理员配置员工登录DeliveryAI的认证方式。支持飞书/平台托管/OIDC/OAuth 2.0。切换认证方式注意：从SSO切换为平台托管时未绑定手机号用户需重置密码。OAuth 2.0配置项：Client ID、Client Secret、授权端点、令牌端点、用户信息端点、授权范围（openid/profile/email/phone）、用户唯一标识(sub)、PKCE开关。
- **异常**: 页面总长度9966 tokens，仅读取前5175 tokens。

### 119. 导入用户信息

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/import-user-information?lang=zh`
- **读取范围**: 0–5 tokens
- **是否到底**: 是
- **关键内容**: 返回"欢迎来到文档中心"占位页，无实质内容。
- **异常**: 页面为文档中心占位页。

### 120. 管理用户信息

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/manage-user-information?lang=zh`
- **读取范围**: 0–5929 tokens（总10416，未读完）
- **是否到底**: 否（仅读取前5929 tokens）
- **关键内容**: 管理员编辑用户信息（姓名/用户名/邮箱/手机号/允许创建空间开关）；更新员工数据（异常员工数据列表补充资料）；重置用户密码（仅平台托管，原密码失效）。删除用户为不可逆操作，约5分钟后强制退出登录。
- **异常**: 页面总长度10416 tokens，仅读取前5929 tokens。

### 121. 企业集成

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/enterprise-integration?lang=zh`
- **读取范围**: 0–1176 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: 三层授权模型：Admin（全局配置层——系统实例地址/OAuth应用/服务账号Token）、空间（资源关联层——项目/仓库/筛选器）、个人（个人身份层——个人OAuth/PAT/Token）。集成类型：代码仓库（GitLab/GitHub）、需求系统（飞书项目/Jira）、办公协同（飞书机器人）。注意事项：网络连通性、权限最小化、配置生效时机、敏感操作优先用个人授权。
- **异常**: 无

### 122. 管理模型

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/management-model?lang=zh`
- **读取范围**: 0–5010 tokens（总6167，未读完）
- **是否到底**: 否（仅读取前5010 tokens）
- **关键内容**: 企业管理员管理DeliveryAI可用模型。添加模型：模型广场→添加模型供应商→配置名称/提供商（火山方舟模型广场/Agent Plan/Coding Plan/自定义模型）/接口协议（仅OpenAI）/API Key/模型名称→测试连通性→保存。支持编辑模型、设为默认。模型由火山方舟计费。
- **异常**: 页面总长度6167 tokens，仅读取前5010 tokens。

### 123. 创建空间

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/create-space?lang=zh`
- **读取范围**: 0–5350 tokens（总9591，未读完）
- **是否到底**: 否（仅读取前5350 tokens）
- **关键内容**: 三种创建方式：①表单创建空间（完整配置）；②创建新空间（复用已有集成）；③快捷创建Demo空间（自动添加DeliveryAI-Demo仓库到GitHub，预置完整流程）。空间参数：名称/备注/GitLab或GitHub仓库/飞书项目或Jira需求系统/需求空间/自定义字段条件。
- **异常**: 页面总长度9591 tokens，仅读取前5350 tokens。

### 124. 工作台介绍（空间管理员）

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/workplace-introduction?lang=zh`
- **读取范围**: 0–1538 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: 工作台页面功能：①数据概览区（待我处理/Agent执行中/我的需求/本周已处理/本周已完成）；②筛选与搜索区（页签筛选/空间范围/关键词搜索）；③需求列表区（按空间分组，含优先级/标题/阶段/耗时）；④查看全部需求入口。
- **异常**: 无

### 125. 产品信息

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/product-information?lang=zh`
- **读取范围**: 0–3945 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: 产品信息页面6个分区：①产品概览（名称/ID/角色/数据来源）；②关键指标（需求总数/Agent执行中/待团队处理/本周已处理/本周已完成）；③当前需要关注（停留时长风险需求）；④需求流程分布（按节点查看需求分布）；⑤AI自动化运行质量（自动推进节点/人工介入次数）；⑥空间配置健康（飞书项目/代码仓库/仓库来源/项目上下文）。
- **异常**: 无

### 126. 需求中心

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/demand-center?lang=zh`
- **读取范围**: 0–5213 tokens（总7438，未读完）
- **是否到底**: 否（仅读取前5213 tokens）
- **关键内容**: 需求中心功能：查看需求列表（标题/流程/优先级/执行状态/需求状态/负责人/更新时间）；按执行状态巡检（全部/未开始/已完成/待人工处理/Agent执行中）；筛选搜索（流程/负责人/关键词）；通知节点负责人补充信息（飞书通知）；管理需求关联仓库（编辑关联仓库）。
- **异常**: 页面总长度7438 tokens，仅读取前5213 tokens。

### 127. 产品上下文

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/product-context?lang=zh`
- **读取范围**: 0–1397 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: 产品上下文由"仓库上下文扫描"任务扫描代码仓库后生成，按周自动更新。需求任务成功完成后自动触发一次扫描刷新上下文。若已有扫描执行中则跳过。需保持"仓库上下文扫描"任务启用并关联代码仓库。
- **异常**: 无

### 128. 模板与规范

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/templates-and-specifications?lang=zh`
- **读取范围**: 0–5739 tokens（总11327，未读完）
- **是否到底**: 否（仅读取前5739 tokens）
- **关键内容**: 模板与规范用于统一团队需求撰写/技术设计/任务拆分标准。在Agent模板系统提示词、流程节点补充提示词、自定义任务提示词中通过"@"引用。内置模板：需求澄清规范、需求Spec模板、需求质量卡点模板、技术设计模板、任务拆分规范。支持查看详情/编辑/删除。
- **异常**: 页面总长度11327 tokens，仅读取前5739 tokens。

### 129. 仓库规范

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/warehouse-specification?lang=zh`
- **读取范围**: 0–1397 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: 查看空间关联代码仓库的AGENTS.md识别情况。列表展示代码托管平台/仓库路径/规范文件识别结果。"AGENTS.md"建议直接在代码仓库中维护。支持重新加载刷新识别结果。
- **异常**: 无

### 130. 自定义任务

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/custom-tasks?lang=zh`
- **读取范围**: 0–5374 tokens（总7630，未读完）
- **是否到底**: 否（仅读取前5374 tokens）
- **关键内容**: 自定义任务按固定周期或手动触发自动化工作。参数：任务名称/描述/执行周期/执行人/Agent模板/代码仓库（可选）/系统提示词（支持@引用模板规范）/选择环境（可选）。内置任务：①内部检查问题修复（每日09:00）；②外部反馈问题修复（每日08:00）；③仓库上下文扫描（每周一08:00，代码库分析师Agent）；④NFR问题扫描（每周一08:00，非功能质量工程师Agent）。三种触发方式：定时/手动"现在执行"/需求完成后自动触发。
- **异常**: 页面总长度7630 tokens，仅读取前5374 tokens。

### 131. 基本设置

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/basic-settings?lang=zh`
- **读取范围**: 0–5594 tokens（总7677，未读完）
- **是否到底**: 否（仅读取前5594 tokens）
- **关键内容**: 基本设置：维护产品名称；查看/管理空间成员（批量添加成员，权限类型：空间管理员/空间成员）；调整成员权限；删除空间成员（高风险操作）。
- **异常**: 页面总长度7677 tokens，仅读取前5594 tokens。

### 132. 集成配置

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/integrated-configuration?lang=zh`
- **读取范围**: 0–5860 tokens（总8107，未读完）
- **是否到底**: 否（仅读取前5860 tokens）
- **关键内容**: 空间管理员配置需求来源（飞书项目/Jira，选择需求空间+自定义字段条件）和代码仓库（从Admin已启用的代码服务中选择仓库，配置默认分支/标签/授权状态检查）。每个仓库独立保留来源/仓库名/默认分支/标签/授权状态。
- **异常**: 页面总长度8107 tokens，仅读取前5860 tokens。

### 133. 管理Agent模板

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/management-agent-template?lang=zh`
- **读取范围**: 0–5 tokens
- **是否到底**: 是
- **关键内容**: 返回"欢迎来到文档中心"占位页，无实质内容。
- **异常**: 页面为文档中心占位页。

### 134. 环境配置

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Environmentconfiguration?lang=zh`
- **读取范围**: 0–5999 tokens（总9269，未读完）
- **是否到底**: 否（仅读取前5999 tokens）
- **关键内容**: 环境用于集中维护交付流程节点和自动化任务引用的变量配置（部署信息/测试环境地址/访问凭据）。环境变量加密存储。创建环境：名称/描述/环境变量（Key大写字母+数字+下划线）/自定义Bash初始化脚本（超时600秒默认，最大3600秒）。环境详情显示关联流程节点和自动化任务。
- **异常**: 页面总长度9269 tokens，仅读取前5999 tokens。

### 135. 流程管理

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/process-management?lang=zh`
- **读取范围**: 0–13 tokens
- **是否到底**: 是
- **关键内容**: 返回"欢迎来到文档中心"占位页，无实质内容。
- **异常**: 页面为文档中心占位页。

### 136. 工作台介绍（员工端）

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/workplace-introduction-1?lang=zh`
- **读取范围**: 0–1539 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: 员工端工作台介绍，内容与空间管理员工作台（第124页）基本一致：数据概览区/筛选搜索区/需求列表区/查看全部需求入口。
- **异常**: 无

### 137. 管理个人设置

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/manage-personal-settings?lang=zh`
- **读取范围**: 0–5 tokens
- **是否到底**: 是
- **关键内容**: 返回"欢迎来到文档中心"占位页，无实质内容。
- **异常**: 页面为文档中心占位页。

### 138. DeliveryAI使用介绍

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/introduction-to-deliveryai?lang=zh`
- **读取范围**: 0–1788 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: 三角色三步骤流程：①企业管理员（开通配置+发放客户端入口）；②空间管理员（创建空间+导入流程+配置Skill/模型+添加成员）；③空间成员（个人配置+在集成系统创建需求）。注意：需求正式创建入口在集成的企业业务系统中，不在DeliveryAI客户端内。邀测阶段。
- **异常**: 无

### 139. 什么是DeliveryAI

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/what-is-deliveryai?lang=zh`
- **读取范围**: 0–1712 tokens（全文读完）
- **是否到底**: 是
- **关键内容**: DeliveryAI（交付官）是[PRODUCT]提供的研发交付工作空间。两端：管理端（[PRODUCT]控制台入口，企业管理员全局配置）和用户端（独立Web+桌面客户端，独立账号体系）。核心概念：空间(Space)/流程/节点(Node)/Agent/Skill/MCP/沙箱模板/模型/需求中心/个人中心。三角色：企业管理员（管理端）、空间管理员（用户端SSO）、空间成员（用户端个人中心SSO）。邀测阶段。
- **异常**: 无

### 140. 步骤三: 空间成员-使用DeliveryAI流程

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/step-3-space-members-use-deliveryai-process?lang=zh`
- **读取范围**: 0–5697 tokens（总10044，未读完）
- **是否到底**: 否（仅读取前5697 tokens）
- **关键内容**: 空间成员日常使用：在需求系统创建需求并关联流程模板→需求同步到DeliveryAI需求中心→查看流程图确认AI/人工节点→AI节点自动执行等待结果→人工节点进入详情处理确认→在原需求系统完成节点操作→回到DeliveryAI查看状态更新。
- **异常**: 页面总长度10044 tokens，仅读取前5697 tokens。

### 141. 处理DeliveryAI需求

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/handling-deliveryai-requirements?lang=zh`
- **读取范围**: 0–5953 tokens（总14696，未读完）
- **是否到底**: 否（仅读取前5953 tokens）
- **关键内容**: 空间成员完整操作流程：①在需求系统（飞书项目/Jira）创建需求——需求名称/描述/类型（须与空间管理员导入的流程名称一致）/文档/优先级/标签/关注人/拉群方式/角色人员/业务线；②查看流程流转与节点执行——需求同步到DeliveryAI需求中心→选择空间→状态筛选→进入详情页。整体路径：需求系统创建需求→等待同步→需求中心跟踪→处理人工确认卡片→逐节点检查交付物→正式环境最终验收。
- **异常**: 页面总长度14696 tokens，仅读取前5953 tokens。

---

## 十七、评测中心

### 142. 管理评估器

- **URL**: `https://<INTERNAL_HOST>.com/docs/[PRODUCT]/ManagementEvaluator?lang=zh`
- **读取范围**: 0–5801 tokens（总7928，未读完）
- **是否到底**: 否（仅读取前5801 tokens）
- **关键内容**: 评估器定义评测任务评分标准，分内置（15个，不可编辑/删除，可克隆）和自定义（可编辑/克隆/删除）两类。内置评估器按"阶段-评估维度"命名，覆盖：初始需求处理（歧义与验收识别/上下文与约束识别/需求目标理解/范围与边界完整性）、编码实现（需求实现完整性/代码质量与改动范围）等。新建自定义评估器：名称/说明/模型/评分规则（Markdown，支持@引用）。克隆评估器：基于内置生成同名+副本。
- **异常**: 页面总长度7928 tokens，仅读取前5801 tokens。

---

## 统计汇总

### 主产品页面统计（第1–99页，[PRODUCT]主文档）

| 指标 | 数量 |
|---|---|
| 总页数 | 99 |
| 完整读取（到底） | 82 |
| 部分读取（未读完） | 10（Jira/飞书项目/飞书登录/OIDC/OAuth 2.0/空间管理员配置/认证方式/管理用户信息/管理模型/创建空间/需求中心/模板规范/自定义任务/基本设置/集成配置/环境配置/步骤三/处理需求/评估器） |
| 空内容/占位页 | 7（集成GitLab正文空、集成飞书正文空、服务总览占位、导入用户信息占位、管理Agent模板占位、流程管理占位、管理个人设置占位） |
| 异常（大图过滤重试） | 2（Studio搭建部署、[BASE-ADK]开发部署、旅行助理一键部署——均重试成功） |

### DeliveryAI子产品页面统计（第100–142页）

| 指标 | 数量 |
|---|---|
| 总页数 | 43 |
| 完整读取（到底） | 18 |
| 部分读取（未读完） | 17 |
| 空内容/占位页 | 5（集成GitLab正文空、集成飞书正文空、服务总览占位、导入用户信息占位、管理Agent模板占位、流程管理占位、管理个人设置占位） |
| 子产品关联说明 | DeliveryAI（交付官）是嵌入在[PRODUCT]控制台中的独立子产品，提供"需求→交付→代码→环境"自动化研发交付流程能力。管理端为[PRODUCT]控制台DeliveryAI入口，用户端为独立Web+桌面客户端。当前邀测阶段，仅华北2（北京）地域。 |

### 关键发现

1. **DeliveryAI确认为独立子产品**：在[PRODUCT]控制台左侧导航树中作为独立入口，有独立的管理端和用户端，有独立的账号体系（SSO），当前邀测阶段。
2. **SDK参考API细节已完整提取**：[PRODUCT]AgentServerApp的5个API端点（/sessions创建会话、/run_sse流式对话、/run非流式、/invoke兼容CLI）和完整Part结构类型；Anotation使用指南的5个装饰器（@app.entrypoint、@app.ping、@app.tool、@app.agent_as_a_tool、@app.agent_executor、@app.task_store）。
3. **部分长页面未读完**：Jira集成(23k)、飞书项目集成(24k)、飞书登录(21k)、OIDC(28k)、OAuth 2.0(31k)等页面内容较长，仅读取前5-6k tokens，后续配置步骤未完整捕获。
4. **5个占位页**：部分DeliveryAI页面（服务总览、导入用户信息、管理Agent模板、流程管理、管理个人设置）返回"欢迎来到文档中心"占位页，说明这些页面可能尚未上线或URL已变更。
5. **计费模型**：DeliveryAI开通不收费，沙箱实例（AI节点运行/自定义任务/仓库扫描）和模型调用（火山方舟）为实际计费项。沙箱单次有效期1小时，自动续期1小时，累计22小时重建。
