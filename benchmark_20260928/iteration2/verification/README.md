# iteration2 / verification — 统一验证入口

`verify_all.py` 一次执行六项检查，输出机器可读 JSON（stdout + `verify_report.json`），
全部通过退出码 0，否则 1。

## 六项检查

| 检查 | 内容 |
|---|---|
| `skill_structure` | 正式目录 `skills/` 下 14 个 Skill：`SKILL.md` 存在、YAML frontmatter 含 `name`/`description`、name 与目录名一致 |
| `code_blocks` | Markdown 围栏平衡；```python 块 `compile()` 语法校验；```yaml 块 PyYAML 解析（占位符骨架 `<...>` 与 `SKILL-TEMPLATE.md` 跳过编译） |
| `pytest` | 项目 venv 依次跑三个 suite，各自记录 name/passed/failed/duration_s，**全部通过才算 ok**：`benchmark_tests`（`tests/`）、`iteration2_evaluation`（`iteration2/evaluation/tests`，KB 导入较慢可容忍）、`iteration2_cold_start`（`iteration2/cold_start/test_cold_start.py`） |
| `secret_scan` | 只扫仓库文件文本；命中 AWS AKIA / 私钥块 / GitHub / Slack / OpenAI / `aws_secret_access_key` 赋值等模式；**只报告 file:line + 模式名，绝不打印命中值**；从不打开 `~/.aws`、`~/.ssh`、shell profile 等真实秘密 |
| `duplicate_skills` | 正式目录内重复 Skill name / 重复 `SKILL.md` 内容哈希；排除 `backup_skills`、`_backup`、`.venv`、`.git`、缓存与 zip |
| `reference_links` | 正式 Skill 内 Markdown 相对链接逐一解析落盘检查；覆盖共享参考 `../references/runner-entrypoint.md`；外链与锚点跳过；只报 file + 链接目标 |

## 运行

```bash
benchmark_20260928/.venv/bin/python \
  benchmark_20260928/iteration2/verification/verify_all.py
```

结果文件：`iteration2/verification/verify_report.json`。
