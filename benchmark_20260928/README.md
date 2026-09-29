# AgentKit 冷启动 Benchmark

## 目的

验证一个没有 AgentKit 历史上下文的独立代理，能否仅依靠项目现有的 14 个正式 Skill，完成全组件最小 Harness 开发、测试和边界识别。

## 目录

- `harness/`：14 个组件模块与总装流水线。
- `tests/`：离线行为与契约测试。
- `journal/execution_journal.md`：执行代理的阅读顺序、决策、首次失败、返工、猜测和耗时。
- `journal/components_coverage.md`：逐组件的真实运行、真实构造、契约桩及云边界说明。
- `audit/audit_report.md`：独立审计、十维评分、不足清单和修正后复验。

## 环境

推荐 Python 3.12。核心钉版：

- `veadk-python==1.1.13`
- `veadk-python[extensions]==1.1.13`
- `agentkit-sdk-python==0.8.7`
- `google-adk==2.2.0`
- `mcp==1.26.0`
- `pytest`

Benchmark 源码包不包含本机 `.venv`；请在独立虚拟环境中安装以上依赖。

## 运行

从本目录执行：

```bash
python -m pytest tests -q
```

修正后独立复验结果：40 passed，0 failed；固定版 Google ADK 产生 4 个 `BaseAgentConfig` 弃用警告。

## 结果解释

40 项通过代表本地真跑、真实对象构造和契约桩共同通过，不代表 14 个云组件全部完成真实云端 E2E。逐组件真实度和未验证云边界以 `journal/components_coverage.md` 为准。
