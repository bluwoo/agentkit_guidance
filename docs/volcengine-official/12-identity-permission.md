# 12 身份与权限

> 概述：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Identityandpermission?lang=zh
> 出站授权（火山引擎资源）：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/outbound-authorization-agent-represents-the-user-to-access-volcano-engine-resources?lang=zh

## 概念

一站式身份及权限管理平台，解决 **User → Agent → Tool** 全链路的身份认证、权限控制与凭据管理。

## 入站授权（用户访问 Agent）
- **快速登录**：为 Agent 开启内置登录能力。
- **企业 SSO 联合登录**：对接企业 IdP（OIDC/SAML），组织架构直接导入，批量用户导入（2026-06-19）。

## 出站授权（Agent 访问后端资源）
来源：outbound-authorization-agent-represents-the-user-to-access-volcano-engine-resources
- **Agent 代表用户访问火山引擎资源**：基于 IAM 角色 + 级联委托链的身份传递（2026-06-19 新增级联委托链身份传递）。
- **Agent 代表用户访问第三方资源**：OAuth 令牌托管。
- 云凭据托管：平台托管 AK/SK/OAuth 凭据，运行时按需取用，不在代码中硬编码。

## 组件
- **用户池**（UserPool）：创建用户池。
- **客户端**（Client）：OAuth 客户端。
- **用户**：创建/管理。
- **外部身份提供商**（IdP）：添加 OIDC/SAML。
- **身份验证信息**：配置认证。
- **权限策略**（Policy）：细粒度策略（Agent、MCP 服务、Skill、知识库文档级）。
- **权限网关**：策略执行点。
- **凭据**（Credential）：托管 AK/SK/OAuth。
