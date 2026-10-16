---
name: agentkit-evaluation
description: AgentKit 评测工具——评测集/评估器/评测实验三件套 + 会话分析，覆盖效果/性能/成本三维优化。支持线上 trace 实时回流评测集、内置评估器（内容质量/工具调用/轨迹质量）+ LLM-as-Judge + 人工校准、观测评测一体闭环（trace回流→热切换即改即评→A/B→上线门禁）。当需要评估 Agent 效果、沉淀 good/bad case、做 A/B 对比、建立上线质量门禁时使用本 Skill。
---

# AgentKit 评测 (Evaluation) Skill

## 1. 概述

AgentKit 评测工具是企业级 AI Agent **可度量可优化**的核心能力，提供评测数据管理、自动化评估器、综合评测实验统计三件套，帮助在**效果、性能、成本**三方面优化 Agent。核心特色是**观测评测一体**：线上 trace 实时回流评测集（固定规则过滤 + 分析采样，自动采集 good/bad case）→ 组件热切换即改即评 → A/B 对比 → 上线质量门禁，把 harness 迭代从"天"压到"小时"。同时提供会话分析能力，把单条消息、整段会话、执行链路、评估结果串成可下钻诊断的路径。

## 2. 前置条件

使用本组件前必须满足：
- [ ] 已创建 AgentKit Runtime 并**开启观测服务**（在线评测必须开启观测）
- [ ] 已开通 APMPlus + TLS（开启观测服务后自动开通）
- [ ] Agent 已上线并有运行 trace 数据（trace 回流评测集的前提）
- 依赖包：无需额外安装（平台侧能力）
- 环境变量：无（通过控制台配置评测集/评估器/实验）

## 3. 快速上手

### 3.1 控制台操作路径

**评测三件套**：
AgentKit 控制台 → 评测工具 → 以下子模块：
1. **评测集**：管理评测数据集（含应用实验模板，2026-03-06）
2. **评估器**：管理自动化评估器（LLM 评估打标，2026-05-29）
3. **评测实验**：管理评测实验，对比效果变化趋势

**会话分析**：
AgentKit 控制台 → 评测工具 → 会话分析 → 查看消息/会话/链路/评估结果串联 → 满意度分析、情绪诊断

**trace 回流评测集（详见 observability 组件 §3.1）**：
AgentKit 控制台 →「可观测」→「数据回流」→「创建导出任务」：设置过滤条件（可套推荐配置卡片，如 LLM 异常/长度截断/高 Token 样本）→ 选时间范围与按天/按周重复频率 → 导出平台选「智能体评测」并指定目标评测集 → 字段映射（`GenAIInput→input`、`GenAIOutput→output`）→ 预览后提交。（回流数量上限、是否只回流新数据、PII 脱敏默认状态等具体口径以控制台与公开文档为准，本仓未做云端实测）

> **评测对象限制（边界注记）**：现行公开文档未明确评测对象范围；本仓曾记录「评测对象仅支持 A2A 中心注册的 Agent」的口径，未经云端实测复核，实际以控制台为准。

### 3.2 代码集成

评测为平台侧能力，业务代码无需修改。关键是确保 Agent 开启了观测服务，trace 会自动上报：

```python
# 【源码核验-签名匹配】VeADK Runner.run(messages=) 已核验源码（veadk/runner.py），返回 str
from veadk import Agent, Runner
from agentkit.apps import AgentkitSimpleApp
from google.genai import types
from google.adk.agents import RunConfig
from google.adk.agents.run_config import StreamingMode

app = AgentkitSimpleApp()

# 业务代码无需修改
# 只要 Runtime 创建时开启了观测服务，trace 自动上报
# trace 经数据回流配置后进入评测集
agent = Agent(
    name="my_eval_agent",
    instruction="你是一个企业知识助手。"
)
runner = Runner(agent=agent, app_name="eval_app")

# --- 非流式（推荐）：runner.run(messages=) 直接返回字符串 ---
# 验证：python3 -c "from veadk.runner import Runner; import inspect; print(inspect.signature(Runner.run))"
@app.entrypoint
async def run(payload, headers):
    result = await runner.run(
        messages=payload["prompt"],
        user_id=headers["user_id"],
        session_id=headers["session_id"],
    )
    return result


# --- 流式 SSE（如需逐事件推送）：run_async + types.Content ---
# 注意：run_async 继承 ADK 父类，auto_create_session 默认 False，session 不存在会 raise SessionNotFoundError。
# 必须先显式建 session（见下），或改用非流式 runner.run(messages=)（其内部自动建 session）。
# @app.entrypoint
# async def run_stream(payload, headers):
#     content = types.Content(role="user", parts=[types.Part(text=payload["prompt"])])
#     async for event in runner.run_async(
#         user_id=headers["user_id"],
#         session_id=headers["session_id"],
#         new_message=content,
#         run_config=RunConfig(streaming_mode=StreamingMode.SSE),
#     ):
#         yield event.model_dump_json(exclude_none=True, by_alias=True)

app.run(host="0.0.0.0", port=8000)
```

### 3.3 观测评测闭环流程

```
线上运行 → trace 自动上报 → 数据回流（规则过滤+分析采样）
    ↓
评测集（good/bad case 沉淀）
    ↓
评估器打分（内置 + LLM-as-Judge + 人工校准）
    ↓
评测实验（组件热切换即改即评 → A/B 对比）
    ↓
上线门禁（黄金评测集准出）
```

## 4. 核心概念与 API

| 概念 | 说明 | 关键参数 |
|---|---|---|
| **评测集（Dataset）** | 管理评测数据集，含应用实验模板 | 数据集名称、来源（手动/线上trace回流）、样本 |
| **评估器（Evaluator）** | 自动化评估器，含 LLM 评估打标 | 评估类型（内容质量/工具调用/轨迹质量）、评估模型 |
| **评测实验（Experiment）** | 管理评测实验，对比效果变化趋势 | 实验名称、评测集、评估器、Agent版本 |
| **会话分析** | 消息/会话/链路/评估结果串联 | 满意度分析、情绪诊断 |
| **trace 回流** | 线上运行 trace 自动采集入评测集 | 固定规则过滤 + 分析采样策略 |
| **LLM-as-Judge** | 用大模型作为评估器自动打分 | 评估 Prompt、打分维度 |
| **人工校准** | 人工标注校准评估器准确性 | 校准样本集 |

### 评估器类型与打分形式

| 评估器 | 评估维度 |
|---|---|
| 内容质量 | 回答准确性（Accuracy）、简洁性（Conciseness）、合规性（Compliance）、完整性、流畅度 |
| 工具调用 | 工具选择正确性、参数正确性、调用链路合理性；高频失败点：失败谎报、未验证修改、事务闭环、越权、输出格式、延迟/Token |
| 轨迹质量 | Agent 决策路径合理性（轨迹/过程白盒化评测，P1 路线，建设中） |

**打分形式**：LLM 评估器按 0.0~1.0 打分（可开放客户自选模型/Prompt）；Code 评估器支持 Python / JavaScript（精确规则类指标）。预置评估器数量以控制台公开列表为准。

### 评估器组合模式
- **内置/预置官方评估器**：开箱即用，复用官方预置评估器资产，数量以控制台公开列表为准
- **自建评估器**：自定义评估逻辑（LLM Prompt 或 Code）
- **LLM-as-Judge**：用大模型自动打分（0.0~1.0）
- **人工校准**：人工标注，校准评估器准确性
- **评测集 Dataset**：列含 `input` / `reference_output` / `actual_output`；容量上限（条数/大小/列数）以控制台公开说明为准，通过「提交新版本」固化版本号。

## 5. 输入输出规范

### 评测集输入
- 评测样本：来自手动录入 或 线上 trace 自动回流（规则过滤 + 分析采样）
- 每个样本包含：输入 prompt、期望输出/上下文、关联 trace/session

### 评测实验输出
- 评估分数：各评估器维度得分
- 效果对比：不同 Agent 版本/配置的效果变化趋势
- bad case 列表：标注失败样本
- 会话分析报告：满意度分析、情绪诊断、下钻路径

## 6. 权限与安全

- **所需 IAM 权限**：AgentKit 评测工具管理权限（创建/管理评测集、评估器、实验）
- **入站认证**：与 Runtime 一致；评测平台通过控制台访问
- **出站凭据**：评测本身不涉及出站凭据；LLM-as-Judge 调用模型服务使用模型 API Key
- **数据安全**：评测集包含线上真实对话数据，需注意 PII 脱敏；数据驻留火山引擎境内
- **安全围栏兼容**：可同时开启安全围栏；评测可用于量化安全围栏拦截效果与误杀率

## 7. 失败处理与排障

| 错误现象 | 可能原因 | 处理方式 |
|---|---|---|
| trace 未回流到评测集 | 未开启观测服务 / 数据回流规则未配置 | 确认 Runtime 开启观测；在观测→数据回流中配置过滤规则 |
| 评测实验无结果 | 评测集为空 / 评估器未绑定 | 确认评测集有样本、实验绑定了评估器 |
| LLM-as-Judge 打分不稳定 | 评估 Prompt 不够明确 / 模型版本问题 | 优化评估 Prompt；用人工校准样本验证打分一致性 |
| 轨迹白盒化评测无数据 | 轨迹评测功能建设中 | 官方计划9月补齐轨迹白盒化评测，当前以结果评估为主 |
| 会话分析无法下钻 | trace 链路不完整 | 检查观测埋点字段是否完整；确认 AI 层与微服务同一条 trace |
| 评测结果与人工判断偏差大 | 评估器未校准 | 用人工标注样本做校准，调整评估器 |

排障路径：评测实验结果 → 下钻具体样本 trace → 观测大盘定位 → TLS 日志。

## 8. 可执行验证办法

1. 确认 Runtime 开启观测服务后运行若干线上请求
2. 在观测→数据回流中确认 trace 已采集
3. 在评测集中确认 good/bad case 已自动回流
4. 创建评测实验，绑定评测集 + 评估器，运行后查看评估分数
5. 在会话分析中确认消息/会话/链路/评估结果可串联下钻

```bash
# 【需云凭据联调】<runtime-domain> 为 GetRuntime.Endpoint，未在本环境实测
# 验证 Runtime 有 trace 上报（观测大盘确认）
# 调用 Runtime 产生 trace
curl -X POST https://<runtime-domain>/invoke \
  -H "Content-Type: application/json" \
  -H "user_id: test-user" \
  -H "session_id: eval-test" \
  -d '{"prompt": "帮我查一下Q3销售数据"}'
# 预期：200 返回；观测大盘可见对应 trace；数据回流后进入评测集
```

## 9. 与其他组件的关系

- **上游依赖**：AgentKit Runtime（必须开启观测服务）、APMPlus + TLS（观测基础设施）
- **下游联动**：
  - **观测（Observability）**：trace 回流是评测的数据源；观测评测一体
  - **A/B 实验**：评测实验支持 A/B 对比不同 Agent 版本效果
  - **上线门禁**：黄金评测集准出，把关 Agent 版本上线质量
- **常见组合**：
  - Runtime + 观测 + 评测 = 完整 Eval-driven 闭环
  - 评测 + 安全围栏 = 安全效果量化（拦截率/误杀率）
  - 会话分析 + 评测 = bad case 沉淀 → 驱动 Prompt/工具迭代

## 10. 已知限制与注意事项

- **在线评测必须先开启观测服务**，否则 trace 无法回流
- 评测对象范围以控制台公开文档为准（本仓未云端实测）。
- **轨迹/过程白盒化评测建设中**（P1），当前以端到端结果评估为主；计划 Q3/Q4 补齐轨迹、工具序列、副作用、循环检测等过程评测。
- 产品发布状态与租户可用范围以官方公告/控制台为准（本仓不引用内部灰度口径）。
- **评测暂按 token 计费**，观测评测套餐包设计中
- **路线图（尚未发布，以官方为准）**：
  - 已上线：评测集 + 评估器 + 评测实验（8 月），trace 回流自动识别 BadCase（8 月起，部分 10 月）
  - 本仓不记录未发布功能路线图；后续能力以官方发布文档为准。
- 复用官方预置评估器资产与官方评测集，降低从零搭建门槛
- 数据回流支持：回流到 agentkit、暴露原始 topic 给 TLS 加工、导出 Kafka/las/tos
- **云端已实测（2026-09-28）**：使用独立 Runtime-source A2A Agent、3 条评测样本、`builtin_template_correctness` 和 Doubao 2.0 Lite，Experiment 到达 `status=11` 且 `end_time` 已设置，`success_turn_cnt=3`、`fail_turn_cnt=0`，3 条 `actual_output` 与 reference 一致，3 条 score 均为 1.0。详见下方《在线实测校正》。
- **项目边界**：TEA 后端忽略 `-p/--project`，评测集/评估器/实验归属账号独立工作区；当前只把 default/TEA 验收视为通过，不外推为任意 AgentKit project 均支持。

## 11. 来源追溯

| 信息点 | 来源 URL | 文档章节 |
|---|---|---|
| 评测工具概述与三件套 | https://docs.volcengine.com/docs/AgentKit/overview-of-evaluation-tools?lang=zh | 概述 |
| 评测工具（AgentKit） | https://docs.volcengine.com/docs/86681/2607692?lang=zh | 评测工具 |
| 数据回流（全栈可观测平台） | https://docs.volcengine.com/docs/86845/2232301?lang=zh | 数据回流 |

---

## iteration2 / Slice A 实测回写（2026-09-28，钉版 venv）

钉版 venv：`benchmark_20260928/.venv/bin/python`（python 3.12.14，google-adk==2.2.0，veadk-python==1.1.13）。

### 官方 eval SDK 探测结论
- **官方 eval SDK 确实安装且可导入**：`google.adk.evaluation`（AgentEvaluator/EvalSet/EvalMetrics/
  PrebuiltMetrics/CustomMetricEvaluator）与 `veadk.evaluation`（EvalSetRecorder/BaseEvaluator/
  adk_evaluator/deepeval_evaluator）。
- **但它们不可离线执行**：PrebuiltMetrics 全为 LLM/Vertex 后台（response_match、rubric、
  hallucinations、tool_trajectory、user_simulator、multi_turn_*）；BaseEvaluator.generate_outputs
  要跑 agent；AgentEvaluator 依赖 google-cloud-aiplatform/鉴权。证据：
  `benchmark_20260928/iteration2/evaluation/evidence/eval_sdk_probe.txt`。

### 本切片交付的本地可执行 reference（非官方 SDK）
纯标准库、确定性、离线，覆盖 Dataset + 确定性 Evaluator(exact_match/token_overlap) + Experiment 汇总。
- 代码：`benchmark_20260928/iteration2/evaluation/reference/reference_eval.py`
- 入口：`benchmark_20260928/iteration2/evaluation/scripts/run_local_eval.py`（产出 evidence/local_eval_report.json）
- 测试：`benchmark_20260928/iteration2/evaluation/tests/test_local_eval_reference.py`（5 passed）

### 云端边界（本地 reference 绝不调用）
google.adk AgentEvaluator / LLM-as-Judge / deepeval / EvalSetRecorder 上报 / TEA / default project。
本地报告里 `is_official_sdk=false`，与官方云评测明确区分。

---

## 在线实测校正（2026-09-28，CLI 0.52.13）

本节为真实端到端评测，不是离线 reference：

1. **评测对象必须是 Runtime-source A2A Agent**。先用正式 `veadk.a2a.ve_a2a_server.init_app()` 部署 Runtime，再通过 `CreateA2aAgent` 注册：`Source=Runtime`、`A2aSpaceId`、`RuntimeConfig.RuntimeId/NetworkType=Public`、`SetDefaultVersion=true`。等待 `eval target list --cache-refresh` 可见后再提交实验。
2. **Runtime-source POST 路径可能重复**：平台目标实际可调用路径为 `/runtime/<id>/runtime/<id>`；容器必须使用 A2A Skill 中 `_GatewayPathRewrite` 将所有 POST 路径重写为 `/`。基础 `/runtime/<id>` 在本次验证中返回 404，而重复路径返回 200 和真实模型结果。
3. **提交前必须固化版本并 dry-run**：Dataset 创建样本后提交 `0.0.1`；模板 Evaluator 创建后自动得到 `0.0.1`；使用四个字段映射：`target.input <- dataset.input`、`evaluator.input <- dataset.input`、`evaluator.reference_output <- dataset.reference_output`、`evaluator.output <- target.actual_output`。
4. **成功不能只看 `status=11`**：同时要求 `end_time` 非空、`expt_stats.success_turn_cnt == 样本数`、`fail_turn_cnt == 0`；逐样本真实输出位于 `payload.target_output.eval_target_record.eval_target_output_data.output_fields.actual_output.text`，评分位于 `payload.evaluator_output.evaluator_records[*].evaluator_output_data.evaluator_result.score`。
5. **本次实测结果**：3 条数学样本输出 `96 / 63 / 7`，与 reference 全部一致；Correctness 分数均为 `1.0`；平均 Agent 响应 `1916.33 ms`；Judge 合计输入 `1237` tokens、输出 `734` tokens。
6. **清理注意**：`eval evaluator delete` 与 `eval dataset delete` 不支持 `--json`；错误追加该参数会在命令解析阶段失败，空重定向文件不是删除成功证据。必须用 `list --json --cache-refresh` 回查名称消失。A2A 与 Runtime/CR tag 同样以 List/NotFound 回查为准。
7. **Experiment 当前没有 delete 子命令**：实验到达终态后保留审计记录，不代表仍有活跃执行；终态记录是否产生持续费用仍需以账单/最新计费说明确认。
