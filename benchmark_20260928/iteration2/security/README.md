# iteration2 / security — Default-deny machine guard

Slice B 产物：为 Benchmark 增加**默认拒绝外联与云写**的机器防护。防护在
`harness/c09_sandbox.py` 内自包含实现（不依赖第三方包），本目录提供进程内可复用
guard 与文档。

## 默认拒绝（deny-by-default）矩阵

`LocalSandbox()` 不加任何参数即启用全部拒绝层。每个子进程由 `PYTHONPATH` 注入生成的
`sitecustomize.py`，解释器启动时即打补丁：

| 层 | 默认行为 | 触发异常（子进程内） | 解除方式 |
|---|---|---|---|
| 出站 TCP | 阻断 `socket.socket.connect` / `connect_ex` | `EgressBlocked` | `allow_egress=True` 或 env `AGENTKIT_SANDBOX_UNSAFE=1` |
| 云写 CLI | 拦截 `aws s3*` / `gcloud storage cp` / `tosutil` / `huggingface-cli upload` / `twine upload` / `npm publish` / `docker push` / `git push` 等 | `CloudCLIBlocked` | `allow_cloud_cli=True` 或 master env |
| shell profile / 秘密路径读取 | 拒绝打开 `~/.zshrc`、`~/.bash*`、`~/.profile`、`~/.aws/`、`~/.ssh/`、`~/.netrc`、`~/.config/gcloud/` 等 | `SecretPathBlocked` | `allow_secret_read=True` 或 master env |
| `read-only` 模式写 | 阻断 `open(..., 'w'/'a'/'x'/'+')`、`os.open` 写标志、`os.remove/mkdir/...`、`os.system`、一切 `subprocess` | `WriteBlocked` | 切回 `workspace-write` |

## 显式测试开关

```python
LocalSandbox(allow_egress=True)                      # 逐层解除
LocalSandbox()  # 进程环境 AGENTKIT_SANDBOX_UNSAFE=1  # master 开关，全解除
```

测试范式：默认下子进程尝试外联 → 打印 `EgressBlocked`（负向证明）；开关解除后同一
代码抛的是真实网络错误（`OSError`/`gaierror`），**而不是** `EgressBlocked`（正向证明
阻断确实来自本 guard，而非环境本身无网）。

## 可复用 guard / fixture

- `iteration2/security/guard.py`：进程内 `process_guard()` 上下文管理器（补丁
  `socket.connect`），pytest 直接 `with process_guard():` 断言 `EgressBlocked`。
- 子进程内 guard 见 `harness/c09_sandbox.py` 的 `_SITECUSTOMIZE_TEMPLATE`。

## 诚实边界

- 这是**应用层中介**（在被补丁的 Python 解释器内生效），不是内核级沙箱
  （macOS 无 seccomp/landlock）。用原始 syscall 的绕过不在本防护承诺内；产品级隔离
  仍是云沙箱（`sandbox.live` 需 `AGENTKIT_TOOL_ID`，即 `CloudBoundary`）。
- guard **只匹配路径字符串**，从不打开或读取 shell profile / 秘密文件本身。
- DNS（UDP/53）与原始 ICMP 不在 TCP connect 层拦截范围内；文档照实标注。

## 测试

`tests/test_sandbox_security.py`：正负向用例覆盖上表全部四层 + master env 开关 +
进程内 fixture。运行：

```bash
benchmark_20260928/.venv/bin/python -m pytest tests/test_sandbox_security.py -q
```
