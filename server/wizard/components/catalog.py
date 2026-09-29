"""Static catalog of the 14 AgentKit component skills.

These are *metadata cards* distilled from ``skills/agentkit-*``, ``veadk`` and
``adk-workflow`` ``SKILL.md`` frontmatter + prerequisites. We deliberately do
NOT embed the whole SKILL.md — only name / kind / purpose / prerequisites /
permissions / a config-schema summary the frontend can render as a form.

The catalog is the single source for ``GET /api/wizard/components`` and the
Step-3 recommendation engine.
"""
from __future__ import annotations

from typing import Any

from server.wizard.schemas import NodeKind


# A component card is a plain dict; the API validates/shapes it.
def _card(
    component_id: str,
    name: str,
    kind: NodeKind,
    purpose: str,
    prerequisites: list[str],
    permissions: list[str],
    config_schema: dict[str, Any],
    skill_ref: str,
) -> dict[str, Any]:
    return {
        "component_id": component_id,
        "name": name,
        "kind": kind.value,
        "purpose": purpose,
        "prerequisites": prerequisites,
        "permissions": permissions,
        "config_schema": config_schema,
        "skill_ref": skill_ref,
    }


COMPONENTS: list[dict[str, Any]] = [
    _card(
        "runtime:agentkit", "agentkit-runtime", NodeKind.runtime,
        "把 Agent 代码（容器镜像）发布为可调用在线服务，自动扩缩容/负载均衡/健康检查/版本管理/日志观测。",
        ["火山引擎账号 + AgentKit 已开通", "VOLCENGINE_ACCESS_KEY/SECRET_KEY", "已有容器镜像（CR）", "已选模型与模型 API Key", "region cn-beijing"],
        ["Runtime 创建/发布权限", "CR 拉取权限", "模型调用权限"],
        {"image": "string (镜像:tag)", "cpu_milli": "int", "memory_mb": "int",
         "port": "int (默认8000)", "command": "string", "auth": "KeyAuth|CustomJwt",
         "gateway_mode": "shared|dedicated"},
        "skills/agentkit-runtime/SKILL.md",
    ),
    _card(
        "function:agentkit-sdk", "agentkit-sdk", NodeKind.function,
        "Python SDK/CLI：AgentkitSimpleApp + @entrypoint 把 VeADK Agent 包装成可部署服务；CLI 完成 init/launch/invoke 闭环。",
        ["已安装 agentkit-sdk-python", "VeADK Agent 主体已写"],
        ["本地开发机", "Runtime 部署权限"],
        {"entrypoint": "callable", "request_headers": ["user_id", "session_id"],
         "stream": "bool (SSE)", "cli": "agentkit launch|invoke"},
        "skills/agentkit-sdk/SKILL.md",
    ),
    _card(
        "agent:veadk", "veadk", NodeKind.agent,
        "火山引擎智能体开发套件：veadk.Agent 继承 Google ADK LlmAgent，Runner 管理会话事件流，内置工具/记忆/知识库/Skills/追踪。",
        ["已安装 veadk-python", "模型 endpoint 可用"],
        ["模型 API Key"],
        {"model": "string", "tools": "list", "memory": "bool", "knowledge_base": "ref",
         "factory": "create_agentkit_app"},
        "skills/veadk/SKILL.md",
    ),
    _card(
        "agent:adk-workflow", "adk-workflow", NodeKind.agent,
        "Google ADK 原生多 Agent 编排：Sequential/Parallel/Loop/Supervisor/CreateAgentToolset 动态委派/A2A 远程发现。",
        ["已选 veadk 主体", "已确定多 Agent 协作拓扑"],
        ["A2A Registry 权限（远程发现时）"],
        {"pattern": "sequential|parallel|loop|supervisor|dynamic",
         "sub_agents": "list", "a2a_discovery": "bool"},
        "skills/adk-workflow/SKILL.md",
    ),
    _card(
        "knowledge_base:vikingdb", "agentkit-knowledge-base", NodeKind.knowledge_base,
        "基于 VikingDB 向量库的 RAG：导入企业文档后自动语义检索并基于检索结果回答。",
        ["已有待导入文档", "已开通 VikingDB"],
        ["知识库读写权限", "切片管理权限"],
        {"documents": "list", "embedding_model": "string", "chunk_size": "int",
         "retrieval_top_k": "int", "acl": "bool"},
        "skills/agentkit-knowledge-base/SKILL.md",
    ),
    _card(
        "a2a:registry", "agentkit-a2a-registry", NodeKind.a2a,
        "基于 Google A2A 协议的智能体注册与发现中心：注册/语义检索发现/Provider-Consumer 跨 Agent 协作。",
        ["存在需互调的多个 Agent", "已创建智能体空间"],
        ["A2A 空间管理权限"],
        {"space": "string", "agents": "list", "discovery": "semantic",
         "provider_consumer": "bool"},
        "skills/agentkit-a2a-registry/SKILL.md",
    ),
    _card(
        "skill:agentkit-skills", "agentkit-skills", NodeKind.skill,
        "智能工坊 + Skills 中心：Skill 是 Agent 可调用的能力单元，支持构建调试、版本管理、execute_skill 调用。",
        ["已确定可复用能力单元"],
        ["SkillSpace 管理权限"],
        {"skill_name": "string", "version": "string", "mount": "runtime|cli",
         "trigger": "description-driven"},
        "skills/agentkit-skills/SKILL.md",
    ),
    _card(
        "gateway:mcp", "agentkit-gateway-mcp", NodeKind.gateway,
        "Agent 访问后端工具的统一入口：认证/路由/协议转换/治理；MCP 四种接入方式 + 工具集语义检索 + 凭据托管。",
        ["已有 HTTP API 或 MCP Server 待接入"],
        ["网关配置权限", "下游凭据托管权限"],
        {"mcp_mode": "vefaas|rest_to_mcp|existing_server|private_domain",
         "toolset": "string", "credential": "managed", "auth": "oauth|apikey"},
        "skills/agentkit-gateway-mcp/SKILL.md",
    ),
    _card(
        "identity:permission", "agentkit-identity-permission", NodeKind.identity,
        "User→Agent→Tool 全链路身份认证/权限/凭据：入站登录（SSO OIDC/SAML）、出站授权（IAM 委托/OAuth/AK-SK 托管）、Cedar 策略网关。",
        ["生产上线前必须配置"],
        ["UserPool 管理", "Cedar 策略", "IAM 角色委托"],
        {"inbound_auth": "quick|oidc|saml", "outbound_auth": "iam|oauth|aksk",
         "cedar_policy": "string"},
        "skills/agentkit-identity-permission/SKILL.md",
    ),
    _card(
        "guardrails:firewall", "agentkit-guardrails", NodeKind.guardrails,
        "基于大模型应用防火墙的实时防护，覆盖 OWASP LLM Top10：提示词攻击/模型滥用/PII 脱敏/算力防护。",
        ["Runtime 创建时勾选开启即可，无需改代码"],
        ["防火墙策略查看/配置"],
        {"enabled": "bool", "policies": ["prompt_injection", "abuse", "pii_redact", "compute"],
         "attack_log": "bool"},
        "skills/agentkit-guardrails/SKILL.md",
    ),
    _card(
        "function:evaluation", "agentkit-evaluation", NodeKind.function,
        "评测三件套（评测集/评估器/评测实验）+ 会话分析；线上 trace 回流 + 内置评估器 + LLM-as-Judge + 上线门禁。",
        ["已有验收用例（Step2）", "已开启观测"],
        ["评测集/实验管理权限"],
        {"dataset": "string", "judges": ["quality", "tool_call", "trajectory"],
         "auto_reflow": "bool", "baseline_locked": "bool"},
        "skills/agentkit-evaluation/SKILL.md",
    ),
    _card(
        "observability:apmplus", "agentkit-observability", NodeKind.observability,
        "APMPlus（指标/链路）+ TLS（日志），无侵入接入，AI 层与微服务同一条 trace，Follow gen.ai 语义。",
        ["Runtime 已开启观测（需重新发布生效）"],
        ["APMPlus 查询权限（AK/SK 签名）"],
        {"business_carrier": "agentkit_runtime", "trace_content": "bool",
         "objects": ["runtime", "sandbox", "memory", "mcp", "gateway", "model"]},
        "skills/agentkit-observability/SKILL.md",
    ),
    _card(
        "sandbox:code", "agentkit-sandbox", NodeKind.sandbox,
        "隔离的代码/命令/浏览器/技能执行环境，5 种预置模板 + 自定义镜像；run_code 集成、快照、三层权限。",
        ["需要执行不可信/代码逻辑"],
        ["沙箱模板选择", "审批权限级别"],
        {"template": "arkclaw|hermes|aio|skills|code", "image": "string",
         "snapshot": "bool", "permission_level": "string", "session_reuse": "bool"},
        "skills/agentkit-sandbox/SKILL.md",
    ),
    _card(
        "memory:session", "agentkit-session-memory", NodeKind.memory,
        "三层记忆：会话层 PostgreSQL / 短期 Runner 内存 / 长期 mem0 或 Viking 记忆库。",
        ["需要跨会话记忆"],
        ["记忆库读写/治理权限"],
        {"session_store": "postgres", "long_term_backend": "mem0|viking_mem",
         "namespace": "string"},
        "skills/agentkit-session-memory/SKILL.md",
    ),
]


def list_components() -> list[dict[str, Any]]:
    return list(COMPONENTS)


def get_component(component_id: str) -> dict[str, Any] | None:
    for c in COMPONENTS:
        if c["component_id"] == component_id:
            return c
    return None


# Sanity: the design fixes the count at 14.
assert len(COMPONENTS) == 14, f"catalog must hold exactly 14 components, got {len(COMPONENTS)}"


__all__ = ["COMPONENTS", "get_component", "list_components"]
