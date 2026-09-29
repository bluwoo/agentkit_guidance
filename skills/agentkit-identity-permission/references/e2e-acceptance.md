# identity-permission 深度参考：端到端鉴权验收脚本与严格输出

> 本文件是 `agentkit-identity-permission` SKILL.md §8 的展开：完整 E2E 验收脚本与「最后一行必须同时出现三个 true」的严格输出。
> 本块为云凭据联调脚本，**本环境未实测**；钉版环境与验收结论保留原文。

## 端到端验证脚本（以 0714 教学 Demo 为例）

> 【需云凭据联调】本环境未实测。
> 该脚本钉版环境（已云端验收 2026-07-16，见 doc06）：Python 3.10.19, agentkit-sdk-python 0.6.2, mcp 1.28.1。
> 与本仓库离线导入基线（0.8.7 / Python 3.13.7）不同，二者不要混装。

```bash
(
  set -eu
  read -rp "火山主账号 ID: " EXPECTED_VOLCENGINE_ACCOUNT_ID
  read -rsp "短期 AK: " VOLCENGINE_ACCESS_KEY; echo
  read -rsp "短期 SK: " VOLCENGINE_SECRET_KEY; echo
  read -rsp "STS Session Token（没有则直接回车）: " VOLCENGINE_SESSION_TOKEN; echo
  export EXPECTED_VOLCENGINE_ACCOUNT_ID VOLCENGINE_ACCESS_KEY VOLCENGINE_SECRET_KEY
  export VOLCENGINE_REGION=cn-beijing
  if [ -n "$VOLCENGINE_SESSION_TOKEN" ]; then export VOLCENGINE_SESSION_TOKEN; else unset VOLCENGINE_SESSION_TOKEN; fi
  .venv/bin/python agentkit_gateway_identity_e2e.py
)
```

## 严格验收输出（最后一行必须同时出现三个 true）

```
probe valid_bearer handshake=true tool_visible=true tool_error=false backend_authenticated=true
probe no_auth handshake=false http_statuses=[401]
probe wrong_bearer handshake=false http_statuses=[401]
cleanup_summary mcp_removed=true function_removed=true provider_removed=true
final functional_acceptance=true cleanup_complete=true passed=true
```

## 对应安全验收矩阵（SKILL.md §6）

| # | 操作 | 期望结果 |
|---|---|---|
| 1 | CLI 裸调（无任何凭证） | 401 |
| 2 | 用过期 token 调用 | 401 |
| 3 | 有权限用户登录后调工具 | 200，返回预期业务结果 |
| 4 | 无权限用户调同样工具 | 能聊天，但调工具 403 |
