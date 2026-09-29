# [PRODUCT] 在线评测报告（default / TEA Workspace）

**执行日期**：2026-09-28
**区域**：cn-beijing
**评测归属**：[PRODUCT] `default` 对应的独立 TEA Workspace
**CLI**：[PRODUCT]-cli 0.52.13
**结论**：PASS（3/3 样本完成真实 Agent 调用并获得 LLM Correctness 评分）

## 1. 验收范围

本次不是离线 reference 或 Mock。完整执行了：

1. 从 `~/.bash_profile` 加载火山 AK/SK，仅检查存在性，不打印、不落盘。
2. 构建并推送 linux/amd64 A2A Provider 镜像。
3. 在 [PRODUCT] `default` project 创建独立 Runtime。
4. 验证 Runtime 为 Ready、AgentCard 可访问、A2A 0.3.0 JSON-RPC 可真实调用模型。
5. 创建独立 A2A Space，将 Runtime 以 `Source=Runtime` 注册为评测对象。
6. 等待新 Agent 出现在 TEA `eval target list --cache-refresh`。
7. 创建 3 条样本的 Dataset 并提交版本 0.0.1。
8. 从 `builtin_template_correctness` 创建 Correctness Evaluator，Judge 模型为 Doubao 2.0 Lite，版本 0.0.1。
9. 执行 dry-run，核对 Dataset / Evaluator / Target 版本和四个字段映射。
10. 提交 Experiment，轮询到终态，逐样本检查真实输出、分数、trace 与 token 用量。
11. 逆序删除 Dataset、Evaluator、A2A Agent、A2A Space、Runtime 和 CR tag，并刷新列表/NotFound 回查。

## 2. 实验结果

| 样本 | 输入 | 期望输出 | 实际输出 | Correctness |
|---|---|---:|---:|---:|
| 1 | 计算负5加12，只回答数字 | 7 | 7 | 1.0 |
| 2 | 计算100减37，只回答数字 | 63 | 63 | 1.0 |
| 3 | 计算12乘8，只回答数字 | 96 | 96 | 1.0 |

- 成功轮次：**3**
- 失败轮次：**0**
- 平均 Correctness：**1.0**
- 平均 Agent 响应时间：**1916.33 ms**
- Judge 输入 Token：**1237**
- Judge 输出 Token：**734**
- 实验状态：`status=11`，`end_time` 已设置，属于终态
- Dataset、Evaluator、Target 和 Runtime 的 project/workspace 归属均通过回读确认

逐样本的 `actual_output` 来自：

`payload.target_output.eval_target_record.eval_target_output_data.output_fields.actual_output.text`

逐样本评分来自：

`payload.evaluator_output.evaluator_records[*].evaluator_output_data.evaluator_result.score`

## 3. 本轮发现并修正的问题

### 3.1 Runtime-source A2A 重复路径

- Runtime 基础 POST 路径返回 404。
- 平台生成的 Runtime-source 调用路径为 `/runtime/<id>/runtime/<id>`，真实请求返回 200。
- 容器中的 `_GatewayPathRewrite` 正确把 POST 路径重写为 `/`，最终模型返回正确结果。

### 3.2 不能只根据 `status=11` 宣告成功

成功门禁已收紧为同时满足：

- `end_time` 非空；
- `success_turn_cnt == 样本数`；
- `fail_turn_cnt == 0`；
- 每个样本存在真实 `actual_output`；
- 每个样本存在 evaluator score；
- actual 与 reference 逐条核对。

### 3.3 CLI JSON 嵌套路径变化

首次轮询器按扁平字段寻找 `actual_output`，实验虽已成功但校验器拒绝通过。读取真实响应后，修正为上述嵌套路径，并重新做逐样本断言。

### 3.4 删除命令不支持 `--json`

`eval evaluator delete` 与 `eval dataset delete` 不接受 `--json`。首次带该参数时命令解析失败，空输出文件不能作为删除成功证据。修正后使用正确命令，并通过 `list --json --cache-refresh` 确认两类资源均为 0 条匹配。

## 4. 资源清理

| 资源 | 收口结果 |
|---|---|
| Dataset | 已删除，刷新列表 0 匹配 |
| Evaluator | 已删除，刷新列表 0 匹配 |
| A2A Agent | 已删除，服务端列表 0 匹配 |
| A2A Space | 已删除，服务端列表 0 匹配 |
| Runtime | 已删除，回查 `Invalid[PRODUCT]Runtime.NotFound` |
| CR image tag | 已删除，`tag_count=0` |
| Experiment | 平台当前无 delete 子命令；保留终态审计记录，无活跃执行 |

终态 Experiment 是否产生持续的记录级费用，现有资料无法确认；本报告不做无依据承诺。

## 5. 安全与回归

- AK/SK 仅在命令进程内加载，未打印、未写入报告。
- CR 临时凭据只通过隔离 `DOCKER_CONFIG` 和 stdin 使用，任务结束后删除。
- 评测证据目录敏感信息扫描：0 命中。
- 更新后的 `[PRODUCT]-evaluation` Skill 结构校验通过。
- 全套 Python 代码块：20/20 编译通过。

## 6. 正式 Skill 回写

已把以下真实结论写入：

`skills/[PRODUCT]-evaluation/SKILL.md`

包括 Runtime-source 评测对象、重复路径、版本固化和 dry-run、终态门禁、JSON 结果路径、资源删除注意事项、TEA/default project 边界及本次真实指标。
