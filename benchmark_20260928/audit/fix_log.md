# Skill 修正记录（基准验收后回归）

- 修正时间：2026-09-28
- 修正依据：`audit/audit_report.md` 不足清单（B1/H1/H2/H3/M3 + 基准产物 M1/M2）
- 备份位置：`skills/_backup_pre_benchmark_fix_20260928/`（14 个 Skill + 模板，修正前原样）
- 回归结果：`benchmark_20260928/.venv/bin/python -m pytest tests/ -v` → **40 passed, 0 failed**（原 34 + 新增 6 个 skills 行为测试）

## 正式 Skill 修正（5 项）

| 编号 | 不足 | 涉及 Skill | 修正内容 |
|---|---|---|---|
| B1 | 阻塞：离线 local 后端漏写 `[extensions]` extras | `agentkit-session-memory` §2、`agentkit-knowledge-base` §2、`veadk` §2 | 三个 Skill 的依赖段均新增：本地/离线用 `backend="local"` 时必须 `uv add 'veadk-python[extensions]==1.1.13'`，裸装会 ImportError；session-memory 还补了基础包 `veadk-python==1.1.13`（原只写了 mem0ai） |
| H1 | 高：a2a CLI 与公开 0.52.13 漂移未收口 | `agentkit-a2a-registry` §3.2 顶部 | 新增「CLI 版本前提」警示框：§3.2/§3.3 命令来自内部文档未在公开 CLI 实测；照抄前先 `agentkit --version`/`--help`；不支持时改走 §3.4 控制台一键注册或 §3.5 SDK 代码方式 |
| H2 | 高：无跨 Skill 导航 | `skills/` 根目录 | 新增 `README.md`：依赖分层图、推荐阅读顺序、离线可跑 vs 必须云凭据对照表、统一环境基线、跨组件关键约束集中清单 |
| H3 | 高：identity 两套钉版环境易装错 | `agentkit-identity-permission` §2、§3.3 | §2 明确标注 0.8.7 为「默认/推荐」、0.6.2 为「仅历史教学复现，不要用于新项目」；§3.3 私有 import 补注「仅诊断/联调，生产应走控制台+网关出站注入」 |
| M3 | 中：sdk 示例写死 `/data/sessions.db` | `agentkit-sdk` §3.2 | 默认路径改为 `sqlite+aiosqlite:///./.sessions.db`（相对路径，本地无需 root）；注释保留生产容器 4 斜杠绝对路径写法；`os.makedirs` 改为从 URL 动态提取目录 |

## 基准产物修正（2 项，非 Skill）

| 编号 | 不足 | 修正 |
|---|---|---|
| M1 | c05_skills 零行为测试 | 新增 `tests/test_skills.py`（6 用例）：`skills_field_from_env` 设/未设/去空白、Registry publish/list/execute、missing KeyError、unknown space 空列表 |
| M2 | c12 覆盖矩阵措辞高估 | `components_coverage.md` c12 改为「真实构造 + 本地词法桩检索」；c05 测试列补 `test_skills.py`；测试总数 34→40 |

## 未修正项（如实标注）

- **M4（SSE 样板重复）**：~10 个 Skill 重复同一段注释掉的 SSE 代码块。收敛需逐文件大改且风险较高，本次未动；建议后续统一改为「流式写法见 veadk SKILL §5」。
- **L1-L4（低）**：journal 小错、c09 read-only 空 pass、inspect.signature 命令重复、CloudBoundary 非强制——均为低优先级，不影响新手主路径，本次未修正。
- **evaluation Skill 代码可复制性低（评分 2/5）**：需引入真实 eval SDK 或重写示例，超出本次「必要修正」范围，留待后续。

## 验证

- 修正后全量测试：40 passed, 4 warnings (DeprecationWarning BaseAgentConfig, 无害), 4.87s
- 修正前后 Skill 文件 diff 可通过与 `_backup_pre_benchmark_fix_20260928/` 对比复核
- 未触碰 `agentkit_wizard/` 下任何用户文件；未创建云资源；未读取任何密钥文件
