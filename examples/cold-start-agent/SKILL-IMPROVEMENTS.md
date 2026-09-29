# Skill 改进清单

1. `adk-workflow`：Graph 根 FunctionNode 示例统一使用 `node_input`，避免钉版运行时按 state 键绑定失败。（已修正正式 Skill）
2. `agentkit-sdk`：明确本地默认 SQLite 路径必须可写，容器 `/data` 仅通过显式环境变量启用。（已在参考实现和文档中体现）
3. `agentkit-sdk`：补充同一 DatabaseSessionService 必须贯穿 HTTP 请求链，而非仅创建空 session。（示例已验证）
4. 通用排障：本地 E2E 使用空闲端口并验证 readiness 身份，避免命中外部残留服务。（e2e_smoke 已修正）
5. MCP：本地协议验收固定为 initialize → tools/list → tools/call，并验证返回值。

所有建议均不涉及真实云资源或凭据。
