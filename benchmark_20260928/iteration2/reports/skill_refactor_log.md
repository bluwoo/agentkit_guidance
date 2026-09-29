# 切片 C（迭代2）Skills 重构日志

范围：skills/ 下除 agentkit-evaluation/**、agentkit-knowledge-base/** 外的 12 个正式 Skill。
备份基准：benchmark_20260928/iteration2/backup_skills/<name>/SKILL.md（未新建备份）。未触碰 harness/tests/security/evaluation/knowledge-base。

## 0. 权威共享产物
- skills/references/runner-entrypoint.md — 非流式骨架/SSE run_async+types.Content+预建session/钉版签名/四契约表（鉴权400、session预建、记忆落库、短期会话持久化），注明各归哪个 Skill
- skills/references/verify_runner_signature.py (chmod +x) — 签名自检，venv 运行 exit=0
- skills/agentkit-observability/references/span-attributes-and-query-api.md — 下沉 span 字段/APMPlus OpenAPI/日志字段三表（原文未删改）
- skills/agentkit-a2a-registry/references/agentcard-schema.md — AgentCard 必填/可选字段全表 + protocolVersion 0.2.6/0.3.0 + 来源 URL
- skills/agentkit-identity-permission/references/e2e-acceptance.md — E2E 验收脚本 + 严格三 true 输出 + 验收矩阵

## 1. 行数（备份 -> 现）
agentkit-runtime 201->172; agentkit-observability 430->256; agentkit-gateway-mcp 287->268;
agentkit-guardrails 314->294; agentkit-sandbox 279->255; agentkit-sdk 298->272;
agentkit-session-memory 298->274; agentkit-skills 283->263; veadk 220->220;
agentkit-a2a-registry 286->272; agentkit-identity-permission 288->265; adk-workflow 279->279(未动).
合计 3359 -> 2980（净 -379）。

## 2. 保留的独有约束（grep 全部命中）
- sdk: 400 JSONResponse 不回落 default / ShortTermMemory(db_url)+DatabaseSessionService assert / SQLite 4 斜杠 / 两包分装
- session-memory: save_session_to_long_term_memory 落库 / viking_mem 废弃->viking / [extensions] extras / mem0ai==0.1.118
- identity: 400/401/403 矩阵 / 两层钉版 0.8.7 vs 0.6.2 / MCP 握手四层断言 / 出入站 Header 不共用
- a2a: _GatewayPathRewrite ASGI / AgentCard protocolVersion 0.2.6/0.3.0 / CLI 0.52.13 漂移警告
- guardrails: content_safety 4 回调 + TOOL_LLM_SHIELD_APP_ID / runtime update --envs-json --auto-release / 2026-09-23 <PROJECT_NAME> 云实测
- gateway-mcp: 四层 MCP 验收 / 协议版本矩阵(…2026-07-28)
- sandbox: 2026-09-24 <PROJECT_NAME> 云实测(ProjectName/CodeEnv/快照级联/DeleteTool 异步) / 同 session FS 复用
- skills: §10.5 <PROJECT_NAME> 云校正(SKILLS/SKILL_SPACE_ID env、须传 skills=[…] 才 load_skills、UpdateRuntime.SkillSpaceId 被静默忽略) / CLI 0.52.13
- observability: 单次 trace duration=span 起止差 vs P50/P95 聚合铁律 / 定价(Trace 0.4 元/GB) / 回流 10 万条/PII

## 3. 跳转完整性
全仓 skills/*/SKILL.md 中 ../references/ 与 references/ 相对链接共 9 条，逐条解析全部命中，无断链。

## 4. 样板残留
inspect.signature(Runner.run) 与注释 SSE run_stream 块：范围内 12 个 SKILL.md 零残留；仅存于 evaluation/knowledge-base(分工外) 与 skills/references/*(权威单一位置，预期)。

## 5. 验证结果
- 签名脚本: benchmark_20260928/.venv/bin/python skills/references/verify_runner_signature.py -> exit=0，三契约断言全 OK
- 相对链接: 9/9 命中
- 样板残留: 范围内零残留
- 独有约束: grep 全保留
- 禁改区: evaluation/knowledge-base/harness/tests/security 未触碰

## 6. 备注
来源 URL 按构造无丢失：a2a 两条 larkoffice 来源随表移入 references/agentcard-schema.md；observability §来源追溯 表仍在 SKILL.md；identity E2E 块本身无来源 URL，§来源追溯 表保留。
