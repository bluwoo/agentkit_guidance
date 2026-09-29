---
name: adk-workflow
description: 设计、实现和排障 Google ADK 2.x / veADK 1.1.13 多节点编排。用于固定拓扑、条件路由、并行汇合、循环、Dynamic 程序化流程、Supervisor 子 Agent 协作、存量 Sequential/Parallel/Loop 模板，以及评估 CreateAgentToolset、RemoteA2aAgent 和 AgentKit A2A Registry 的集成边界。优先使用 Graph/Dynamic；不得把 LangGraph API、TypeScript-only RoutedAgent 或仅凭继承关系推断的 veADK 能力混入 Python 实现。
---

# ADK 工作流

## 1. 先做版本与边界检查

1. 明确站点身份：`adk.dev` 是 **Google ADK**，不是 veADK，也不是 LangGraph。
2. 使用**双基线**，不得把官网主干能力直接当作 AgentKit 钉版能力：
   - **AgentKit 执行基线（本 Skill 的可运行代码）**：`google-adk==2.2.0`、`veadk-python==1.1.13`、`agentkit-sdk-python==0.8.7`。
   - **Google ADK 官网主干参考基线**：`https://adk.dev/llms-full.txt`；2026-09-28 对应 PyPI 最新版 `google-adk==2.10.0`，只用于识别新增能力和升级差异。
3. GitHub 仓库根目录的 `llms-full.txt` 已变成迁移提示，不再含正文；研读时必须跟到 `https://adk.dev/llms-full.txt`，不能把 526 字节占位文件当全文。
4. 工作流原语从 `google.adk` / `google.adk.workflow` 导入；不要写 `veadk.workflow`。
5. `veadk.Agent` 继承 `LlmAgent` 已核实，但真实模型协议、Graph 节点运行、Runtime 部署必须单独联调；继承关系不等于端到端支持。
6. 不需要访问火山云时，不要求 AK/SK。只有 veADK 模型调用、Runtime、A2A Registry 或远程资源才需要相应凭据与权限。
7. 先以固定版运行和源码为准；若采用主干新增参数，必须先升级到目标版本并重跑本 Skill 全套回归。

## 2. 选型顺序

| 需求 | 首选 | 规则 |
|---|---|---|
| 固定步骤、条件分支、并行汇合、可视拓扑 | **Graph Workflow** | `Workflow(edges=[...])`；优先于已弃用的 Template 类 |
| 复杂 if/for/while/递归、运行时动态路径、暂停恢复 | **Dynamic Workflow** | `@node(rerun_on_resume=True)` + `ctx.run_node()` |
| LLM 主管按能力委派专家 | **Collaborative** | root/coordinator 设 `sub_agents`；`mode` 配在子 Agent 上 |
| 维护旧代码 | **Template** | Sequential/Parallel/Loop 可用，但 2.2.0 发出 DeprecationWarning |
| Python 中按函数做 Agent failover/A-B | 应用层自建路由 | `RoutedAgent` 当前是 TypeScript 实验能力，Python 2.2.0 无导出 |
| 动态创建 Agent | veADK `CreateAgentToolset` | 仅确认导入与签名；运行权限及 Runtime 行为仍需联调 |
| 调用远程 Agent | A2A / `RemoteA2aAgent` | 另读 A2A Skill，不能把 Consuming API 当作 Workflow 原语 |

## 3. Graph：固定拓扑的默认方案

### 3.1 最小规则

- 顺序：`("START", a, b, c)`；前一节点的返回值经 `Event.output` 传给下一节点的 `node_input`。
- 分支：路由节点返回 `Event(route=..., output=...)`；边字典使用相同 route key；加 `DEFAULT_ROUTE` 兜底。
- 并行：从同一源节点发出多条路径；用 `JoinNode` 等待全部前驱，并向后继输出 `{node_name: output}`。
- 循环：下游 back-edge 回到上游。引擎不自动设置循环次数，必须实现可达的退出分支；生产设计再加业务迭代/预算上限。
- 嵌套：`Workflow` 本身可作为父 Graph 的节点；最终叶节点输出作为嵌套 Workflow 输出。
- 失败：可给节点设置 `RetryConfig` / `timeout`。固定版 Graph 的静态节点状态可由 session events 在 resume 时重建；这不替代外部副作用幂等和故障恢复测试。
- 并发上限：`Workflow(max_concurrency=N)` 可限制整个 Graph 同时运行的节点数；它控制 Graph 级调度，不等同于单个 parallel-worker 的列表扇出上限。
- Schema：可在 `Workflow` / Node / Agent 上使用 `input_schema`、`output_schema`、`state_schema`；边两端同时声明 Schema 时必须匹配。不要把大对象塞进 state，文件或大数据改用 Artifact/数据库。
- `LlmAgent` 节点 mode（2.2.0 源码/构造核验）：未显式设置时，在 Workflow 中按 `single_turn` 语义运行；有非 START 前驱的显式 `chat` 节点会在 Graph 校验时报错，因为它不能消费直接 node input。`single_turn` 是确定性 Graph 的默认选择。
- `task` mode：官网 `llms-full.txt` 仍同时存在“Python 2.0 Graph 暂时禁用 task”与“task/single-turn 可作 Workflow 节点”的冲突描述。2.2.0 可构造 task 节点，但本 Skill 不据此宣布端到端支持；涉及澄清、恢复或 live 时必须单独联调。
- 每个节点执行只应有一个最终 `Event.output`；进度用用户可见 `content/message`，不要连续发多个 output 并依赖覆盖顺序。

### 3.2 完整、无模型验证骨架

```python
from google.adk import Event, Workflow
from google.adk.workflow import DEFAULT_ROUTE, JoinNode, node

@node(name="classify")
def classify(node_input: str):
    route = "BUG" if "bug" in node_input.lower() else "OTHER"
    return Event(route=route, output=node_input)

@node(name="bug")
def handle_bug(node_input: str):
    return f"bug:{node_input}"

@node(name="other")
def handle_other(node_input: str):
    return f"other:{node_input}"

routing = Workflow(
    name="routing",
    edges=[
        ("START", classify),
        (classify, {"BUG": handle_bug, DEFAULT_ROUTE: handle_other}),
    ],
)

@node(name="upper")
def upper(text: str):
    return text.upper()

@node(name="length")
def length(text: str):
    return len(text)

join = JoinNode(name="join")

@node(name="merge")
def merge(results: dict):
    return {"upper": results["upper"], "length": results["length"]}

fanout = Workflow(
    name="fanout",
    edges=[
        ("START", upper, join),
        ("START", length, join),
        (join, merge),
    ],
)
```

运行完整断言示例：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B <本Skill目录>/scripts/validate_orchestration.py
```

该脚本覆盖 Graph 顺序、分支和默认路由、Join、back-edge、Dynamic、Sequential、Parallel、Loop；全部使用 FunctionNode 或自定义 BaseAgent，不调用模型或云资源。

## 4. Dynamic：复杂控制流与恢复

```python
from google.adk import Context, Workflow
from google.adk.workflow import node

@node(name="normalize")
def normalize(text: str):
    return text.strip().lower()

@node(rerun_on_resume=True)
async def orchestrate(ctx: Context, text: str):
    normalized = await ctx.run_node(normalize, node_input=text)
    return normalized

root = Workflow(name="dynamic", edges=[("START", orchestrate)])
```

强制规则：

1. 调用 `ctx.run_node()` 的编排节点必须使用 `rerun_on_resume=True`；恢复时从节点顶部重入，已完成的子激活从 checkpoint 跳过。
2. Python `Context.run_node()` 直接返回输出值；不要套用 TypeScript `.output` 语义。
3. HITL 叶节点通常用 `rerun_on_resume=False` 产生 `RequestInput`，让回复成为节点输出；父编排节点仍设 True。必须真实做暂停→新一轮恢复测试，不能只验证 `RequestInput` 对象可构造。
4. `asyncio.gather` 可并发多个 `ctx.run_node()`；创建顺序必须稳定，才能保持自动 run ID 在恢复时确定。业务侧限制并发并明确部分失败策略。
5. 固定 Python 2.2.0 的 `node()` 支持 `parallel_worker=True`，但**没有** `max_parallel_workers` 参数；可用 `Workflow(max_concurrency=N)` 限制 Graph 总并发，或手写 semaphore/gather 控制列表扇出。官网主干/2.10.0 已新增 `max_parallel_workers`，升级前不得照抄。
6. 自定义 `run_id` 仅用于可重排列表等确需稳定ID的少数场景；必须确定、包含至少一个非数字字符，并在恢复时保持同一逻辑项ID不变。默认顺序ID更安全。
7. Dynamic 自动checkpoint只覆盖节点执行；外部写入、付款、发消息等副作用仍需幂等键、去重记录和补偿策略。
8. checkpoint/resume、HITL、RetryConfig/timeout 本 Skill仍必须有单独故障注入门禁；无模型happy path不能充当恢复验收。

## 5. Collaborative：Supervisor 与子 Agent mode

```python
from veadk import Agent

weather = Agent(
    name="weather_checker",
    mode="single_turn",
    instruction="只完成一次天气查询并返回结构化结果。",
)
planner = Agent(
    name="travel_planner",
    instruction="选择合适的专家并合并结果。",
    sub_agents=[weather],
)
```

- 不给 root/coordinator 设置 `mode`；把 `chat` / `task` / `single_turn` 配在子 Agent 上。
- `chat`：完整交互、手动交接；不适合并行委派。
- `task`：可澄清，完成后自动返回；必须是叶子节点。Graph 中的适用性需按当前版本复核。
- `single_turn`：无 HITL，返回后自动交回，可用于独立并行任务。
- coordinator 的委派工具在运行时 LLM flow 注入；构造时 `tools=[]` 不是失败证据。本 Skill未进行真实 LLM 委派验证。
- `enable_supervisor=True` 是 veADK 扩展；不要把它等同于 Google ADK 的全部 Collaborative 语义。

## 6. Template：只用于存量或迁移过渡

- `SequentialAgent`、`ParallelAgent`、`LoopAgent` 在 google-adk 2.2.0 和 2.10.0 均可运行，但构造时都会产生 `DeprecationWarning`；新设计优先 Graph/Dynamic。
- 官网仍保留 Template 教程是为了迁移与兼容，不等于推荐新建项目继续使用。2.10.0 的警告还明确指出：`Workflow` 当前不能在所有场景中直接替代 `LlmAgent` 的 sub-agent；迁移前要验证父子结构，不做机械替换。
- `LoopAgent.max_iterations` 在固定版中的默认值是 `None`，**不是 5**。必须显式设置硬上限，并通过 `EventActions(escalate=True)` 或工具上下文的 `actions.escalate=True` 主动退出。
- Parallel 子 Agent 运行在独立 branch / isolation scope；模型上下文看不到同级分支事件。但这不代表底层 `session.state` 是事务隔离副本：并行分支仍不得写同一个state键。
- 并行分支应：读取显式输入、分别写独占 `output_key`/`state_delta`，结束后统一聚合。不要使用全局“上一输出键”串联分支；不要直接修改共享 state 后就宣布并发安全。
- 一个 Agent 实例只能有一个 parent；需要放入不同拓扑时优先使用 `agent.clone(update={"name": ...})` 或创建新实例，不复用已挂载实例。
- 自定义 `BaseAgent._run_async_impl()` 在2.2.0兼容路径仍会被Template调用，但ADK 2.0迁移指南明确不再推荐把它作为Graph执行驱动或遥测注入点；新控制流用FunctionNode/Dynamic，横切逻辑用before/after callbacks。

## 7. veADK / AgentKit 集成边界

### 已核实

- `veadk.Agent` 是 `LlmAgent` 子类；`sub_agents` 非必填，默认空列表；`mode` 支持 `chat/task/single_turn`；`enable_supervisor` 存在。
- Graph/Dynamic 原语从 Google ADK 导入；`veadk.workflow` 不存在。
- Template 类可接受全新的 `veadk.Agent` 实例作为子节点；仅证明构造成功，不证明模型/Runtime 已跑通。
- `CreateAgentToolset` 存在：

```python
from veadk.tools.builtin_tools.create_agent.toolset import CreateAgentToolset

creator = CreateAgentToolset(
    skill_source_ids=None,
    resource_sources=None,
    capabilities=None,
    resource_store=None,
    skill_cache_dir=None,
    leaf_factory=None,
    knowledge_factory=None,
)
```

固定版构造签名已 inspect；资源权限、动态创建结果、模型调用与 Runtime 行为未端到端验证。

### 尚需联调

- `veadk.Agent` 作为 Graph 节点的真实模型调用和 schema 传递。
- coordinator 的运行时委派工具、并行 single_turn、task mode 恢复。
- CreateAgentToolset 的资源来源、授权和动态 Agent 生命周期。
- AgentKit Runtime 发布、A2A Registry 发现、RemoteA2aAgent 调用、流式事件拓扑。

## 8. 权限、安全、状态与迁移门禁

- `user_id` / `session_id` 是会话和路由标识，不是可信授权依据；认证授权由 Runtime/Identity 层完成。
- 不在日志、state、提示词、AgentCard 或示例中写 AK/SK、API Key、token。
- 给循环设置模型调用预算、迭代上限、工具副作用幂等键和取消策略。
- Graph/Dynamic 的 `output` 适合节点间值传递；只有需要跨节点/恢复/模板插值的数据才写 state。`app:` / `user:` / `temp:` / 无前缀分别对应应用、用户、单次invocation和session作用域；大对象用Artifact/数据库。
- 并行节点写不同键；同键并发写必须做冲突策略或外部事务。
- 不要直接 `context.session.events.append(...)` 或调用内部 `enqueue_event`；节点必须 `yield`/`return` Event，让Runner统一持久化、路由和流式输出。
- 不要用宽泛 `except Exception` 吃掉应由 `RetryConfig` 处理的异常；绝不吞掉 `BaseException` / `NodeInterruptedError`，否则会破坏自动重试与HITL暂停。只有确实完成补偿并输出业务结果时才在节点内终止异常。
- ADK 1.x自定义Session存储升级到2.x时，刚性表结构和严格JSON消费者必须至少兼容 Event 的 `node_info` 与 `output` 字段；固定2.2.0实际Event还包含`isolationScope`等可选字段，存储JSON blob比僵硬列映射更易前向兼容。
- A2A远程调用的数据、身份、超时和重试边界由A2A/Gateway Skill负责，本Skill只负责本地编排。

### Live Graph专门规则

- `run_live()`下整个Workflow共用一个事件循环和一条`LiveRequestQueue`；不要为每个Agent新建run loop或queue。
- 每个会说话的Agent节点必须显式使用`mode="task"`或`mode="chat"`；未设mode的Workflow节点会落到`single_turn`，在live连接外运行，音频队列不会送达。
- 一条LiveRequestQueue不能同时喂两个live节点，所以live路径不要fan-out并发。
- `ParallelAgent`与`LoopAgent`在live模式会抛`NotImplementedError`；`SequentialAgent`虽仍可运行但已弃用，新代码用Graph Workflow。
- `transfer_to_agent`会为目标Agent打开新的Live API session；源Agent的session-resumption handle不会跨Agent转移。

## 9. 失败处理

| 现象 | 优先检查 |
|---|---|
| route 未命中 | 路由节点是否返回 `Event(route=...)`；边字典 key 是否一致；是否有 `DEFAULT_ROUTE` |
| Join 下游缺值 | 所有前驱是否实际完成且产生 output；失败节点是否设置 retry/timeout |
| Graph 循环不收敛 | 退出分支是否可达；增加业务上限与预算；必要时改 Dynamic |
| Dynamic恢复后重复副作用 | 父节点是否`rerun_on_resume=True`；run_id是否稳定；外部写操作是否有幂等键；是否吞掉`NodeInterruptedError` |
| Parallel发生输入串扰 | 是否使用共享“上一输出键”；是否直接改共享state；改为显式输入和独占输出键 |
| 并发过高 | 2.2.0使用`Workflow(max_concurrency=N)`或应用层semaphore；不要使用该版本不存在的`max_parallel_workers` |
| Graph拒绝Agent节点 | 有前驱输入的Agent是否显式`mode="chat"`；改成`single_turn`，task/HITL单独联调 |
| 自定义Session升级失败 | 数据库/ORM/JSON Schema是否接受Event的`node_info`、`output`及新增可选字段 |
| Retry不生效 | 节点或工具是否用宽泛`except Exception`吞掉异常；让异常上抛给`RetryConfig` |
| Live节点无声音 | 是否未显式设置`task/chat`；是否误在live路径fan-out；是否使用ParallelAgent/LoopAgent |
| Loop无限运行 | 不要依赖默认值；显式设`max_iterations`并产生escalate |
| veADK import失败 | 使用固定版本；编排原语从`google.adk`导入；不要写`veadk.workflow` |
| Agent被多个父节点复用 | 用`clone(update={"name": ...})`或创建新实例 |
| Template出现弃用警告 | 对新项目迁移到Graph/Dynamic；不要屏蔽警告冒充无问题 |

## 10. 验证门禁

按层级报告结果，不得混用：

1. **文档证据**：记录确切URL、读取日期与文档基线；GitHub占位文件必须跟到`https://adk.dev/llms-full.txt`。
2. **导入/签名**：至少检查AgentKit钉版2.2.0；如引用官网主干新增能力，再在独立环境检查当前最新版，不能修改AgentKit固定venv。
3. **离线运行**：执行`scripts/validate_orchestration.py`，要求退出码0，并精确断言Graph顺序、三路由、Join、循环、Dynamic、并发上限/版本差异和Template兼容行为。
4. **迁移门禁**：检查Event存储/消费者是否支持`node_info`和`output`；扫描直接append session events、内部enqueue_event、宽泛异常吞噬与旧式Graph自定义Agent驱动。
5. **恢复测试**：另做暂停→新一轮恢复、故障重试、并行部分失败与副作用幂等测试；仅构造RequestInput不算通过。
6. **模型集成**：配置真实模型后验证Agent节点的schema、single_turn/task边界、Supervisor委派；本次无模型回归不替代该层。
7. **Live集成**：若使用`run_live()`，验证单queue连续事件、每个发声节点mode、转移、断线恢复和禁止并发live路径。
8. **AgentKit云端**：Runtime、A2A、身份、观测和安全围栏逐层联调；Google ADK升级必须先验证veADK/AgentKit兼容矩阵。

## 11. 2026-09-28全文审计结果

- 官方机器文档规模：约3.39 MB、74,854行；GitHub`llms-full.txt`仅为迁移提示。
- AgentKit钉版：2.2.0；官网/PyPI对照版：2.10.0，独立venv完成导入与签名检查。
- 2.2.0与2.10.0共同事实：`Workflow(max_concurrency=...)`存在；Template三类构造均发弃用警告；`BaseAgent`继承`BaseNode`；Event含workflow输出/节点元数据。
- 版本差异：2.2.0的`node()`无`max_parallel_workers`；2.10.0已提供该参数。Skill示例继续以2.2.0可执行语法为准。
- 2.2.0运行Dynamic无模型用例时会打印`cancelling ... leftover tasks`，同一用例在2.10.0已无该警告。2.2.0清理源码会把已完成dynamic task也纳入日志计数后统一`gather`；当前测试未发现未完成协程或结果缺失，因此记录为旧版日志噪声，不将其隐藏为成功证据，也不误报成任务泄漏。
- 文档冲突：主干全文对Python Graph中的task mode同时保留“禁用”与“可作为节点”两种描述；Skill不选边猜测，按2.2.0构造/源码规则和真实集成测试报告。
- 当前无模型回归只证明编排与兼容路径；恢复、真实模型、live、AgentKit云端继续作为独立门禁。

## 12. 来源

- https://raw.githubusercontent.com/google/adk-python/main/llms-full.txt — 仓库迁移提示（正文已迁出）
- https://adk.dev/llms-full.txt — ADK机器可读完整文档，2026-09-28审计基线
- https://adk.dev/workflows/ — 工作流模式总览
- https://adk.dev/graphs/ — Graph 入门
- https://adk.dev/graphs/routes/ — 路由、Join、嵌套与循环
- https://adk.dev/graphs/data-handling/ — 节点数据传递
- https://adk.dev/graphs/dynamic/ — Dynamic、并行、HITL、checkpoint 与 run_id
- https://adk.dev/workflows/collaboration/ — Collaborative 与 mode
- https://adk.dev/workflows/patterns/ — 多 Agent 模式
- https://adk.dev/agents/workflow-agents/sequential-agents/ — Sequential 模板
- https://adk.dev/agents/workflow-agents/parallel-agents/ — Parallel 模板
- https://adk.dev/agents/workflow-agents/loop-agents/ — Loop 模板
- https://adk.dev/agents/routing/ — TypeScript 实验性 RoutedAgent
- 本地固定版源码/签名：`google-adk==2.2.0`、`veadk-python==1.1.13`；验证脚本见 `scripts/validate_orchestration.py`
