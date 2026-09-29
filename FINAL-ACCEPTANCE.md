# [PRODUCT] [DELIVERY] 最终验收报告

## 结论（诚实）

已完成：本地工程门禁、API 级四步流程、真实独立目标 Agent、APMPlus 12-Span Trace、公网单用户登录页，以及登录会话下的真实 Trace 查询。

未完成：登录后的普通用户逐按钮浏览器 E2E。登录凭据输入必须由用户本人接管，不能用 API、Cookie 注入或“HTTP 200”替代页面验收。

## 已验证（真实执行）

- 主 [DELIVERY] Runtime：`<RUNTIME_ID>`，状态 Ready；镜像 `[PRODUCT]-[DELIVERY]:0.21.7`，digest `sha256:bd243899fbc74e0b68b52b96db45fe58f6d42605de8a1c18fc0dd7bc627f5bc8`。
- 独立目标 Agent Runtime：`<RUNTIME_ID>`，状态 Ready；镜像 `[PRODUCT]-[DELIVERY]-target:0.1.6`；真实 Ark 模型 `doubao-1-5-pro-32k-250115`。
- 真实目标 Trace：`<TRACE_ID>`。`GetTraceDetail` 使用秒级 `SuggestTime` 并解析 `Result.Trace.SpanList`，返回 12 个 Span，包括 `POST /invoke`、`[PRODUCT]_invocation`、`invoke_agent`、`call_llm`、`openai.chat`。
- 公网前门登录会话调用 Trace API：HTTP 200，`status=ok`，`span_nums=12`；临时测试账号随后停用，旧密码重登返回 401。
- 主 Runtime 观测查询通过挂载的短期 Runtime IAM 凭据签名；角色只新增系统策略 `APMPlusServerReadOnlyAccess`，未授予 FullAccess。
- 工程门禁：后端 134 项测试通过；Ruff、前端 ESLint、TypeScript typecheck、Vite production build 全绿。
- MCP 历史验证：原生 MCP Service + AllTools Toolset 曾完成 initialize、`tools/list` 和真实 `tools/call`，实际工具名为 `[PRODUCT]-[DELIVERY]_invoke`。

## 未完成与安全门禁

1. **浏览器逐按钮 E2E 未完成。** 公网登录页已真实渲染，但用户多次跳过登录接管；因此不能宣称“普通用户全流程验收通过”。
2. **控制面 AK/SK 与模型 Key 必须人工轮换。** 一次诊断命令意外输出了进程环境变量；指纹审计确认活动 Runtime KeyAuth 与环境里的 [PRODUCT] Key 不同，但主、目标 Runtime 使用的模型 Key 与暴露值一致。控制面 AK/SK 和模型 Key 只能在对应控制台/凭据系统中重新生成。
3. **MCP 最终凭据状态需复核。** 现存 MCP Service/Toolset 是较早资源，虽有成功调用历史，但尚未在凭据事件后重建并完成一次新的 `tools/call` 证据。
4. **生产安全验收仍开放。** 完成控制面 AK/SK、Ark 模型 Key 和其他受影响令牌轮换，并重新发布 Runtime/MCP 后，才能关闭该门禁。

## 判定

- 功能与观测链路：通过。
- 本地工程质量门禁：通过。
- 普通用户浏览器逐按钮验收：未通过（等待用户登录接管）。
- 生产凭据安全验收：未通过（等待人工轮换主凭据并复验）。
