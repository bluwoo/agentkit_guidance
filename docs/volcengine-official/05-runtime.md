# 05 智能体运行时 (Runtime)

> 入口：用户指南 > 智能体运行时
> 概述页：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Agentruntimeoverview?lang=zh （**读取失败：页面含超大图，正文未返回**，见 99-gaps）
> 已读：创建运行时、文本/多模态调用示例、更新类、API 参考

## 概念

智能体运行时（Runtime）是 [PRODUCT] 托管 Agent 应用的服务实例：把你的 Agent 代码（容器镜像）发布为可调用的在线服务，自动完成扩缩容、负载均衡、健康检查、版本管理、日志与观测。

## 创建运行时（控制台）

来源：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Creatingruntimesconsole?lang=zh
关键配置项：
- **镜像**：来源镜像仓库 CR；支持开启公网访问的跨账号镜像（2026-08-07）。
- **模型配置**：模型选择（如 doubao-seed-1-8）、模型 API Key。
- **实例规格**：最低 0.5 vCPU（2026-08-21）；单实例并发请求数可配。
- **网络**：公网访问 / 私网访问（VPC+子网，可查 VPC/子网 ID 与 IPv4 CIDR）。
- **观测服务**：开启后开通 APMPlus + TLS，绘制观测大盘（在线评测必须开启）。
- **安全围栏服务**：可选开启提示词攻击/模型滥用/敏感数据/算力消耗防护。
- **注册到 A2A 空间**：可选，注册地址随网络访问方式自动选公网/私网。
- **关联组件**：会话资源、记忆库、知识库、MCP 工具集、沙箱工具、模型服务等。
- **IAM 角色**：授予 Runtime 访问火山引擎资源的角色权限。

## 调用方式

来源：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Samplecallsfortextprompts?lang=zh
- **文本指令调用（prompt）**：POST `/invoke`，Header 带 `user_id`、`session_id`，Body `{"prompt": "..."}`。
- **多模态调用（prompt + files）**：Body 可携带 files 字段传入图片/文件。
- 支持 SSE 流式返回（SDK 侧 `StreamingMode.SSE`）。

## 生命周期与更新

来源：目录中"更新运行时"8 个子页（未逐页读）
- 更新自定义镜像 / 实例配置 / 模型配置 / 环境变量 / A2A 空间 / 关联组件 / IAM 角色权限。
- 发布运行时（Release）：版本化发布，可查看发布过程/记录；支持 `AbortRuntimeRelease` 取消。
- 运行时实例：Webshell 浏览器终端（2026-07-17）、Shell 命令、实时日志、不可用日志、网络信息。
- 删除运行时；安全最佳实践。

## 计费形态（2026-09-01 起）
- **专属网关**：适用于生产环境；**共享模式**：适用于 POC 与低流量验证。

## Runtime API 参考（数据/控制面，Version 2025-10-30）

来源：API 参考章节（未逐字段读，仅列接口清单）
- CreateRuntime / UpdateRuntime / ReleaseRuntime / DeleteRuntime / GetRuntime / ListRuntimes
- GetRuntimeVersion / ListRuntimeVersions
- GetRuntimeInstanceLogs / ListRuntimeInstances
- UpdateRuntimeRelease / AbortRuntimeRelease / GetRuntimeReleaseStatus / ListRuntimeReleaseRecords
- GetRuntimeWebshellEndpoint
- 服务域名：`<INTERNAL_HOST>.com`（Region: cn-beijing）；API 签名走火山引擎标准 V4 签名。
