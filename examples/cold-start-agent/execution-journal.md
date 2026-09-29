# 冷启动离线示例 · 执行日志（execution-journal）

> 本日志按 `AGENTKIT_AGENT_ONBOARDING.md` §0.2 / §10 要求记录。
> 路径约定：`<PROJECT_ROOT>` = 仓库根 `agentkit_dev_skills`；`<WORKSPACE>` = `examples/cold-start-agent/`。
> 全程离线，未读项目外凭据、未建云资源。

## 0. 环境与钉版

- 工作区：`<PROJECT_ROOT>/<WORKSPACE>`
- Python：`<WORKSPACE>/.venv`（Python 3.12.14）
- 钉版：`veadk-python[extensions]==1.1.13`、`agentkit-sdk-python==0.8.7`、`google-adk==2.2.0`、`mcp==1.26.0`
- **pytest 严格钉版（D4）**：`pytest==9.1.1`、`pytest-asyncio==1.4.0`（与 `pip show` 实测一致）
- 传递依赖（正式拉齐）：greenlet 3.5.6、aiosqlite 0.22.1、sqlalchemy 2.1.1

## 1. 实际阅读的文档 / Skill

权威入口（先读）：`README.md`、`AGENTKIT_AGENT_ONBOARDING.md`、`skills/README.md`
按需读：`skills/veadk/SKILL.md`、`skills/agentkit-sdk/SKILL.md`、`skills/references/runner-entrypoint.md`、
`skills/adk-workflow/SKILL.md`、`skills/adk-workflow/scripts/validate_orchestration.py`、
`skills/agentkit-gateway-mcp/SKILL.md`。审计轮新增只读排查：钉版内 `google/adk` 源码
（`_function_node.py`、`Context`、`DatabaseSessionService`、`runners.py`），用于定位状态持久化写法。

## 2. 分步耗时与轮次（D3，本机实测可复跑）

| 步骤 | 命令 | 实测耗时 | 轮次 |
|---|---|---|---|
| 建 venv + 装钉版四件套 | `pip install -r requirements.txt` | ~40–70s（含下载） | 1 |
| 跑 Skill 自带编排回归 | `python -B skills/adk-workflow/scripts/validate_orchestration.py` | <2s（ALL PASSED） | 1 |
| 首次 Graph 冒烟（失败 1） | 见 §3.1 | 即时 | — |
| D1 状态持久化定位（失败 3/4） | 见 §3.3 | 即时 | 2 |
| 全套 pytest（最终） | `python -m pytest -q` | **~6.6s wall，14 passed** | 多次复跑稳定 |
| 真实 HTTP 端到端 | `python app.py` + curl | 启动 ~8s，4 个请求即时 | 1 |

注：pytest wall time 含 venv 导入 veadk/google-adk 的冷启动；同一环境多次复跑在 5.8–8.1s 区间。

## 3. 失败、根因与修复

### 3.1 Graph 根节点绑定报错（首轮）
- 现象：`Missing value for parameter "text" ... not found in state`
- 根因：钉版 2.2.0 FunctionNode 按参数名从 state 绑参，根单参节点须命名 `node_input`。
- 修复：四节点入参统一为 `node_input`。

### 3.2 端到端打空（绕路）
- 现象：curl 返回陌生前端 HTML、/invoke 405。
- 根因：所用端口被本机其它应用占用（`address already in use`），非代码问题。
- 修复：换空闲端口复测。

### 3.3 审计 D1：持久 STM 未真正贯穿 Graph（本轮核心修复）
- 原缺陷：app.py 先 `create_session` 落 sqlite，但 `run_routing` 内部另建
  `InMemorySessionService` + 自有 Runner，**Graph 执行与持久 STM 完全脱节**，create/get 不代表状态贯通。
- 修复：
  1. `run_routing(..., session_service=runner.short_term_memory.session_service)`，
     Graph 直接复用 **DatabaseSessionService**，不再自建内存会话。
  2. 节点经注入的 `Context` 读写 `session.state`。
- 过程中的子失败与根因（钉版 2.2.0 实测）：
  - 3.3a 写 `context.session.state` 无效、重建实例读不到 → 根因：须写 **`context.state`（State 对象）**，
    写 `context.session.state` 不会被回写落库。
  - 3.3b run 后预取的 `session.state.get("turn_count")` 恒为 0 → 根因：Runner 内部持久化的是它
    自己取到的 session 对象；须 **run 结束后重新 `get_session`** 再读轮次。
  - 3.3c `history` 用 `setdefault(...).append(...)` 原地改不被追踪（turn_count 落了、history 没落）
    → 根因：State 对象只追踪**赋值**；改为 `state["history"] = list(...) + [item]`。

## 4. 测试与机器结果

`python -m pytest -q` → **14 passed**（~6.6s）。

| 层级 | 用例 | 断言 |
|---|---|---|
| L1 | STM backend | `isinstance(..., DatabaseSessionService)` |
| L1 | 路由表 | 含 `BUG`/`SUPPORT`/`DEFAULT_ROUTE` |
| L2 | /ping 精确（D5） | `r.json() == {"status":"pong!"}` |
| L2 | /invoke 缺参（D5） | 双缺 / 只缺 session_id / **只缺 user_id** → 400 |
| L2 | Graph 三分支 | BUG/SUPPORT/OTHER 字符串精确相等 |
| L2 | **HTTP 同 user+session 两轮** | turn=1 → turn=2 |
| L2 | **重建实例恢复** | 同 sqlite 重建 STM 后 turn_count==2、history==2、last_branch==SUPPORT |
| L2 | **同 user 新 session** | turn 从 1 开始，看不到旧历史 |
| L2 | **异 user 隔离** | bob 用同 session_id 取不到 alice 会话 → None |
| L2 | 本地 MCP | stdio initialize→list→call：echo 回显、add=42 |

真实 HTTP（curl）：
```
turn1 alice/e2e bug    -> "[BUG] ... | turn=1"
turn2 alice/e2e help  -> "[SUPPORT] ... | turn=2"
alice/e2e-2 general    -> "[OTHER] ... | turn=1"   (新 session 从 1 开始)
缺 user_id             -> 400
```

## 5. 审计项闭环

- **D1**：Graph 复用 DatabaseSessionService；新增 HTTP 两轮 / 重建恢复 / 同 user 新 session / 异 user 隔离四组真跑。
- **D2**：本日志绝对路径已替换为 `<PROJECT_ROOT>` / `<WORKSPACE>` 占位。
- **D3**：§2 给出分步命令与实测耗时、轮次。
- **D4**：`requirements.txt` 严格钉 `pytest==9.1.1`、`pytest-asyncio==1.4.0`。
- **D5**：`/ping` 改精确 JSON 断言；负例补充“只缺 user_id”。

## 6. Skill 缺陷记录（仅记录，不修改正式 Skill）

1. adk-workflow §3.2 示例根节点用 `def classify(text: str)`，钉版 2.2.0 下会报
   “Missing value for parameter text”；可运行脚本用的是 `node_input`。建议统一。
2. veadk/agentkit-sdk 入口示例裸 `Agent(...)` 无 `model_api_key`，离线会触发云凭据查找；
   建议在示例处直接标注离线占位 key 用法。
3. **（新增，D1 相关）** agentkit-sdk §3.2/§10 只演示 `ShortTermMemory(db_url=)` 与
   `create_session`/`get_session`，但未说明“Graph/FunctionNode 必须把同一 `session_service`
   传给 Runner、且节点须经 `context.state`（非 `context.session.state`）赋值式写状态，
   run 后要重新 get_session 读”。否则极易出现“建了库、状态却没落”的假象。建议补状态贯通范式。
4. agentkit-sdk §3.2/§10 SQLite 斜杠表述（相对 3 斜杠 / 绝对 4 斜杠）建议明确二选一与 CWD 影响。

## 7. 云资源 / 凭据清理状态

- 未创建云资源、未读项目外凭据；唯一 `model_api_key` 为常量 `OFFLINE_PLACEHOLDER_KEY`（非真实密钥）。
- 本地产物：`data/sessions.db`、`.venv/`、`__pycache__`、`.pytest_cache`（均 gitignore）。
