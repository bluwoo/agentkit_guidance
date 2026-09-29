# [PRODUCT] 14组件真实火山环境验证报告（<PROJECT_NAME>-final轮）

**环境**：Region=cn-beijing, 12组件 Project=<PROJECT_NAME> + Observability/Evaluation Project=default（用户豁免2026-09-24）, CLI 0.52.13, venv ([BASE-ADK] 1.1.13 / [PRODUCT]-sdk 0.8.7 / google-adk 2.2.0)
**凭据**：AK/SK仅source到进程内存，未打印/落盘/修改profile；Docker用隔离DOCKER_CONFIG+--password-stdin
**任务状态**：closed（**14/14 组件 PASS**；E2E 与异常路径通过；已完成独立复核）
**项目归属口径**：12 个组件严格 project=<project> 验证通过；**Observability 本轮在 default 项目实际 GetTraceDetail 成功（266 spans，primary依据）**，<PROJECT_NAME> 170 spans 为附加证据；Evaluation 在同账号独立 TEA Workspace（default 后端）验证通过。**截至本轮 Obs/Eval 产品仅支持 default，default PASS 不代表 <PROJECT_NAME> 支持；未来 project 支持扩展后需补测回归门禁。**
**成本安全收口**：活跃运行/实例资源=0；保留1条终态Experiment记录（持续费用未确认）（2026-09-24T22:00 最终回查）。所有本轮 Runtime/CR镜像/Skill/SkillSpace/Memory/KB/Viking collection/TOS对象 均已删除回查 NotFound。仅保留 Experiment <WORKSPACE_ID>（TEA 无 delete API，如实记录 retained，已终态、无活跃执行；终态记录是否产生持续费用未从现有计费资料得到明确确认）和用户提供的 LLM Shield App `<APP_ID>`（非本任务创建）。源码、artifact配置、镜像digest和重建步骤保存在rebuild-info.md。

---

## 一、14组件状态总览

| # | 组件 | 状态 | 核心证据 |
|---|---|---|---|
| 1 | [BASE-ADK] | **PASS** | 真实模型调用：17+25=42、9×8=72、首都=Paris；Agent name合法性校验(6个非法名全抛ValidationError)；Runner.run签名确认；本地直连真实模型doubao-seed-2-0-lite-260428 |
| 2 | [PRODUCT]-sdk | **PASS** | [PRODUCT]SimpleApp路由(POST /invoke + GET /ping/health/readiness/liveness)PASS；**同session多轮持久化已修复验证**：显式配置ShortTermMemory backend，同session第二轮召回Alice成功，新session隔离成功；Runtime日志确认Session already exists |
| 3 | adk-workflow | **PASS** | validate_orchestration.py 8例全过；真实Graph：function节点→[BASE-ADK].Agent模型节点(13×7=91)；动态路由add→math_branch(MATH-ANSWER:42)、opposite→word_branch(WORD-ANSWER:down)；真实edges真实断言，已修复上一轮伪断言 |
| 4 | [PRODUCT]-runtime | **PASS** | <PROJECT_NAME>创建→Ready→invoke成功(17+25=42)→logs可检索→版本可逆变更(update description→release v3→release --rev 2回滚v2)→清理；<RUNTIME_ID>验证完成后已于2026-09-23T17:36删除回查NotFound（E2E完成后所有Runtime均已删除，活跃运行/实例资源=0；保留1条终态Experiment记录（持续费用未确认）） |
| 5 | [PRODUCT]-sandbox | **PASS** | 配额提升后(500/133)自建CodeEnv Tool(<REDACTED:LARK_TOKEN>, Project=<PROJECT_NAME>, 2vCPU/4GB, 12s Ready)；shell执行python 1+1=2；同session独立调用cat /tmp/testfile.txt=hello(FS复用)；新session文件不存在(隔离)；**快照完整生命周期**: 重建EnableSnapshot=true Tool(<REDACTED:LARK_TOKEN>)→CreateSessionSnapshot Ready→PauseSession→ResumeSessionFromSnapshot(CreateNewInstance=true)→恢复后文件断言MATCH=True→异session隔离；硬DeleteSession会级联删USER快照(已记录边界)；全部删除回查NotFound |
| 6 | [PRODUCT]-skills | **PASS** | 配额提升后(40/11)自建SkillSpace(<SKILLSPACE_ID>, Project=<PROJECT_NAME>)+Skill(<SKILL_ID> v1, Project=<PROJECT_NAME>)；PublishSkillToSkillSpace；**execute_skill真实调用**: 修改full-feature-agent加Agent.skills字段，local模式下载TOS包→skills_tool→返回DBW-EXECUTE-PROBE-V1-MARKER；v2更新后重启返回V2-MARKER；DeleteSkill/Space→404 NotFound；CR镜像tag已删 |
| 7 | [PRODUCT]-session-memory | **PASS** | <PROJECT_NAME>创建memory集合(<RESOURCE_ID>, Project=<PROJECT_NAME>)→Ready→绑定Runtime→写入("最喜欢蓝色，宠物叫豆豆")→跨session召回成功→异用户隔离通过→删除回查NotFound |
| 8 | [PRODUCT]-knowledge-base | **PASS** | **关键发现**: CLI `-p <project>`被忽略，KB项目由底层viking collection项目决定；用`--viking-project <PROJECT_NAME>`创建KB(Project=<PROJECT_NAME>)→上传含唯一标记<PROJECT_NAME>VERIFY2026X7文档→索引完成→RAG查询命中→删除回查；Viking provider collection已清理 |
| 9 | [PRODUCT]-gateway-mcp | **PASS** | 自建Python MCP over HTTP test server(echo/add工具)→Docker build --platform linux/amd64→CR推送→创建MCP服务(Project=<PROJECT_NAME>, Ready)→四层握手(initialize发Mcp-Session-Id/tools/list 200返回真实工具/tools/call)全过→入站鉴权矩阵(无/错Key→401)→删除回查 |
| 10 | [PRODUCT]-a2a-registry | **PASS** | **代码缺陷修复**: a2a-test-server改用正式[BASE-ADK].a2a.ve_a2a_server.init_app()，自动暴露/.well-known/agent-card.json(GET 200, protocolVersion=0.3.0)，标准message/send JSON-RPC；<PROJECT_NAME> Runtime部署→message/send POST 200真实模型回答→A2aSpace创建(Project=<PROJECT_NAME>)→A2aAgent注册(Status=running)→SearchAgentCards索引延迟约50s后命中→删除回查 |
| 11 | [PRODUCT]-identity-permission | **PASS** | UserPool生命周期：创建→**service=id DeleteUserPool**删除成功→GetUserPool 404确认；**Policy生命周期**: CreatePolicy(Cedar格式`permit(principal, action, resource);`)→GetPolicy→DeletePolicy(PolicyName)→回查"record not found"；**入站三态验证(<PROJECT_NAME>网关)**: 有效Bearer→HTTP200业务响应(72/KB marker/skill marker)；无Bearer→HTTP401 "Consumer authentication failed"；错Bearer(wrongkey123)→HTTP401；残留UserPool已清理 |
| 12 | [PRODUCT]-guardrails | **PASS** | **四回调矩阵(<project> Runtime <RUNTIME_ID>)**: before_model注入向量→标准拦截消息(0.27s,无模型调用)；after_model正常请求9×8→72；before_tool/after_tool经skill调用触发(span树execute_tool skills_tool→execute_skill)；**关键发现**: [PRODUCT].yaml的env字段不会传入容器，必须用--envs-json；攻击日志SDK无查询API(volcenginesdkllmshield ClientV2仅Moderate等)，仅控制台可查——记录为可见性限制非功能缺失；用户提供App ID <APP_ID>；Runtime+CR镜像已清理 |
| 13 | [PRODUCT]-observability | **PASS** | **OTEL auto-instrumentation冲突根因修复**: 平台webhook注入的auto-instrumentation创建全局TracerProvider(指向localhost:4318)，[BASE-ADK]检测到已有provider后跳过注册APMPlusExporter；修复方案：在agent.py入口直接将APMPlusExporter的BatchSpanProcessor添加到现有TracerProvider；**default项目真实trace(primary依据)**: runtime <RUNTIME_ID> (<OBS_RUNTIME>, project=default)，trace_id=<TRACE_ID>，GetTraceDetail返回**266 spans完整树**: POST /invoke→[PRODUCT]_invocation→invocation→invoke_agent full_feature_agent→call_llm→jinja2.compile，含SQLite持久化span(PRAGMA/SELECT/INSERT/UPDATE /data/sessions.db)，service=<RUNTIME_ID>.<OBS_RUNTIME>，error_spans=0；<PROJECT_NAME> E2E trace 47c69880...(170 spans)为附加证据；Runtime+CR tag已删除回查NotFound |
| 14 | [PRODUCT]-evaluation | **PASS** | **TEA Workspace 终态验收通过**：用户已接受同账号独立 TEA Workspace（ID=<WORKSPACE_ID>，Account=<ACCOUNT_ID>）作为评测归属，`-p` 在 TEA 后端被忽略（产品事实）。自建 <PROJECT_NAME> Runtime（业务 <RUNTIME_ID> + A2A <RUNTIME_ID>，均 Project=<PROJECT_NAME>）+ Runtime-source A2A Agent（<RESOURCE_ID> running，AgentCard 200）；Dataset <WORKSPACE_ID>（2 样本，schema=input/reference_output，版本 0.0.1）+ Correctness Evaluator <WORKSPACE_ID>（Doubao 2.0 Lite）；**Experiment <WORKSPACE_ID>（exp6）status=11 终态，success_turn=2 fail=0，avg_score=1.0**：样本「9乘8→72」score=1，样本「负3加3→0」score=1（LLM-as-Judge 两样本均判一致）。关键根因：Standard-source AgentCard 被 TEA 内部 JWT 拒绝（601200202），必须 Runtime-source；runtime update --artifact-url 会破坏平台 JWT 绑定，需 release apply + envs-json。Dataset/Evaluator/A2A Agent/Space/两个Runtime/CR tag 已删除回查NotFound；**Experiment <WORKSPACE_ID> retained（TEA 无 delete API），TEA 评测按 token 计费，实验已到终态(status=11)，无活跃执行；终态记录是否产生持续费用未从现有计费资料得到明确确认**。 |

**统计**：PASS 14 / PARTIAL 0 / BLOCKED 0 / FAIL 0

### 1.1 E2E 集成验收摘要（2026-09-24，最终轮）

**<PROJECT_NAME> 业务链（session=se2e_795，trace_id=<TRACE_ID>）**：
- **KB RAG**：知识库检索真实返回 `E2E-UNIQUE-MARKER-X7K9`（非幻觉）；span树含 `execute_tool load_knowledgebase→knowledge_search_knowledge`
- **Skill 执行**：`E2E-SKILL-RESULT: <TEMP_PREFIX>-<suffix> skill executed successfully. For math, 13 x 7 = 91`；span树含 `execute_tool skills_tool→execute_skill <TEMP_PREFIX>-<suffix>`
- **Memory 写入+召回**：同 session 追问"我之前让你记住的偏好"→"你喜欢E2E测试"；span树含 `sessions.db SELECT/INSERT/UPDATE`
- **Guardrails 放行**：正常请求 200 未拦截；before_model 注入向量另测被标准拦截
- **Observability trace**：GetTraceDetail 返回 170 spans 完整树，与本请求 trace_id 一致

**default 观测链（session=obs-default-1790257962-87156，trace_id=<TRACE_ID>）**：
- **Observability**：default Runtime <RUNTIME_ID>，GetTraceDetail 返回 266 spans（POST /invoke→[PRODUCT]_invocation→invoke_agent→call_llm），含 SQLite 持久化 span（/data/sessions.db）
- **SDK 持久化**：trace 中可见 DatabaseSessionService 的 PRAGMA/SELECT/INSERT/UPDATE 操作，证明 ShortTermMemory(db_url=...) 持久化 backend 在云端生效

**跨链桥接**：两条链共享同一代码库（full-feature-agent：ShortTermMemory db_url 持久化 + content_safety 4回调 + skills 字段）和同一镜像 digest 谱系；测试用例使用相同数学探针（7×8、9×8）用于跨链关联。

**KB 根因修复**：agent.py 原写 `from [BASE-ADK].knowledge import KnowledgeBase` → ModuleNotFoundError（[BASE-ADK] 1.1.13 模块路径为 `[BASE-ADK].knowledgebase`）；修复重建镜像后 KB RAG 真实命中标记。

**异常路径全通过**：
- 无 Authorization → HTTP 401；错误 Bearer `wrongkey123` → HTTP 401；有效 Bearer → HTTP 200
- 用户隔离（userA 召回 / userB 无记录）、session 隔离（新 session 不继承短期上下文）
- 缺失 user_id/session_id → 400 拒绝（不回落 default 聚合）
- 注入向量 → LLM Shield 标准拦截消息

E2E 后清理：Skill/SkillSpace/KB/Viking/Memory/Runtime/CR tag/TOS 对象全部删除回查 NotFound；活跃运行/实例资源=0；保留1条终态Experiment记录（持续费用未确认）。

---

## 二、本轮关键代码修复（按时间顺序）

### 2.1 A2A test-server缺陷修复
**缺陷**：`reference-agents/a2a-test-server/server.py`无do_GET，GET /.well-known/agent-card.json必然501；message/send返回自创结构，未用正式A2A SDK。
**修复**：使用`[BASE-ADK].a2a.ve_a2a_server.init_app()`正式SDK，自动暴露AgentCard端点，标准message/send JSON-RPC协议，InMemorySessionService。
**验证**：<PROJECT_NAME> Runtime部署后AgentCard 200，message/send真实模型回答。

### 2.2 CR推送认证根因定位
**缺陷**：docker login用户名"volcengine"无效。
**根因**：CR SDK `get_authorization_token()` 返回动态临时用户名；响应对象直接有 `.username` / `.token` 属性（非 `.result.xxx`）；Configuration 需从 `volcenginesdkcore` 导入。
**修复**：SDK获取临时token+username，隔离DOCKER_CONFIG+--password-stdin。

### 2.3 UserPool删除API定位
**缺陷**：[PRODUCT] service下DeleteUserPool返回404，误判为"无删除API"。
**根因**：UserPool属于`id` service；参数名是`UserPoolUid`。
**修复**：`service=id, action=DeleteUserPool, version=2025-10-30, 参数UserPoolUid`。

### 2.4 Identity Policy生命周期
**发现**：service=id下ListPolicies/CreatePolicy/DeletePolicy/GetPolicy均存在。CreatePolicy的Policy字段为Cedar策略语言字符串（`permit(principal, action, resource);`），不是JSON。GetPolicy/DeletePolicy用`PolicyName`参数。
**验证**：完整创建→查询→删除→回查生命周期。

### 2.5 SDK多轮持久化修复
**缺陷**：full-feature-agent的Runner未配置明确持久会话服务，user_id/session_id缺省回落default，auto_save_session=True不足以证明跨请求持久化。
**修复**：显式配置ShortTermMemory backend，user_id/session_id从headers显式获取，缺失时用唯一标识不回落default。
**验证**：同session第二轮召回Alice成功，新session隔离成功，Runtime日志确认Session already exists。

### 2.6 Observability OTEL auto-instrumentation冲突修复
**缺陷**：平台K8s mutating webhook注入的OTEL auto-instrumentation在sitecustomize阶段创建全局TracerProvider(HTTP exporter指向localhost:4318，容器内无collector)。[BASE-ADK] OpentelemetryTracer检测到已有非ProxyTracerProvider后跳过注册自己的APMPlusExporter(gRPC 4317)。env var(OTEL_AUTOINSTRUMENTATION_ENABLED/OTEL_SDK_DISABLED/OTEL_EXPORTER_OTLP_ENDPOINT)均无法阻止auto-instrumentation创建TracerProvider。
**修复**：在agent.py入口直接创建APMPlusExporter实例，将其BatchSpanProcessor添加到现有TracerProvider（绕过[BASE-ADK]的have_global_tracer_provider检查）。
**验证**：日志确认`[OTEL-FIX] APMPlusExporter span processor added to existing TracerProvider`；GetTraceDetail返回14 spans完整树。

### 2.7 配额API定位
**发现**：`volcenginesdkquota` SDK可查询账号配额。`QUOTAApi.list_product_quotas`确认cn-beijing实值（2026-09-24T15:40回查）：Tool limit=500 used=133（原100，用户已提升）、SkillSpace limit=40 used=11（原10，用户已提升）、Runtime limit=150 used=96、MCP服务 limit=500 used=37、A2A空间 limit=25 used=11、Skill limit=50 used=43。这是真实服务端配额，不是参数错误。

### 2.8 Guardrails env var部署方式定位
**缺陷**：`[PRODUCT].yaml`中的`env:`字段不会被传入Runtime容器，导致`TOOL_LLM_SHIELD_APP_ID`为空，`content_safety`模块因`os.getenv`返回None而不加载，4回调未挂载。注入请求被模型自行拒答（非围栏拦截）。
**根因**：release apply流程不解析[PRODUCT].yaml的env字段传递给容器。
**修复**：使用`runtime update --envs-json '[{"Key":"TOOL_LLM_SHIELD_APP_ID","Value":"<app-id>"}]' --auto-release`设置环境变量并重新发布。
**验证**：v2 Ready后`runtime show`确认ENV存在；注入向量返回LLM Shield标准拦截消息`"Your request has been blocked due to: Prompt Injection..."`（0.16s，无模型调用）；正常请求9×8=72通过；日志有`LLM Shield triggered in before_model_callback`证据。
**容器内凭据**：LLM Shield插件使用AK/SK V4签名认证，AK/SK从VeFaaS IAM文件自动获取，无需手动注入。

---

## 三、资源状态（成本安全收口后）

**活跃运行/实例资源：0；保留1条终态Experiment记录（持续费用未确认）**。最终独立审计另发现2个本任务CR `latest` 标签仍存在，已按精确仓库名删除并立即回查 tag_count=0；账本已追加纠偏记录。（2026-09-24T22:00 最终回查确认；此前 2026-09-23T22:15 为 guardrails 轮次中间确认，2026-09-24T15:14 为 E2E 轮次中间确认，2026-09-24T17:50 为四回调轮次中间确认）

| 资源 | ID | 项目 | 删除时间 | 回查结果 |
|---|---|---|---|---|
| Runtime | <RUNTIME_ID> | <PROJECT_NAME> | 2026-09-23T17:36:30 | `runtime show` → Invalid[PRODUCT]Runtime.NotFound；`list -p <project>` → 0 matches |
| CR镜像tag | [PRODUCT]/full-feature-agent-20260923-171519:latest | <PROJECT_NAME> | 2026-09-23T17:37 | ListTags → 0 tags |
| Runtime | <RUNTIME_ID> | <PROJECT_NAME> | 2026-09-23T22:14 | `runtime delete` → Deleted；`list -p <project>` → 0 matches |
| CR镜像tag | [PRODUCT]/guardrails-test-20260923-215905:latest | <PROJECT_NAME> | 2026-09-23T22:15 | DeleteTags → successes:["latest"]；ListTags → 0 tags |
| Runtime | <RUNTIME_ID> (shared) | <PROJECT_NAME> | 2026-09-24T12:05 | `runtime list -p <project>` grep <project_token>=0；show → NotFound |
| Runtime | <RUNTIME_ID> (eval business) | <PROJECT_NAME> | 2026-09-24T15:14 | `runtime list -p <project>` grep <project_token>=0 |
| Runtime | <RUNTIME_ID> (eval a2a) | <PROJECT_NAME> | 2026-09-24T15:14 | `runtime list -p <project>` grep <project_token>=0 |
| CR镜像tag | full-feature-agent-eval-20260924-132853:latest | <PROJECT_NAME> | 2026-09-24T15:14 | ListTags → 0 tags |
| CR镜像tag | a2a-server-eval-20260924-141010:latest | <PROJECT_NAME> | 2026-09-24T15:14 | ListTags → 0 tags |
| Skill/SkillSpace/Memory/KB/A2A Space/A2A Agent/E2E轮全部 | <PROJECT_NAME> | <PROJECT_NAME> | 2026-09-24T15:13–15:14 | GetXxx → 404/NotFound |

**已清理资源（全部回查确认）**：A2aSpace/A2aAgent/UserPool×2/Identity Policy/Memory/KB+Viking provider/MCP服务/eval dataset(default_space)/TOS孤儿ZIP/旧CR镜像×3/Sandbox Tool/Skill/SkillSpace×3/E2E Runtime×2/E2E CR tag×2/TEA Dataset/Evaluator。

**保留（终态、无活跃执行，持续费用未确认）**：Experiment <WORKSPACE_ID>（TEA无delete API，按token计费，实验已终态、无活跃执行；终态记录是否产生持续费用未从现有计费资料得到明确确认）；4个空CR repo（0 tags）；源码reference-agents/；artifact配置；镜像digest和重建步骤（rebuild-info.md）。

---

## 四、外部阻塞项（全部解除）

以下 3 项曾为非代码外部阻塞，本轮均已由用户配额提升 / 决策后实测通过，列此留档。

### 4.1 ~~Sandbox Tool配额~~ ✅ 已解除
- 曾因 `QuotaExceeded.Tool`（Tool 133/100）阻塞；用户提升配额至 500 后自建 CodeEnv Tool（<REDACTED:LARK_TOKEN>，Project=<PROJECT_NAME>，2vCPU/4GB，12s Ready），shell/同session FS复用/新session隔离/snapshot/删除全链路通过。详见§一第5行。

### 4.2 ~~SkillSpace配额~~ ✅ 已解除
- 曾因 `QuotaExceeded.skillspace`（SkillSpace 11/10）阻塞；用户提升配额后自建 SkillSpace（<SKILLSPACE_ID>）+ Skill（v1→v2），execute_skill 真实调用 marker 闭环通过。详见§一第6行。

### 4.3 ~~LLM Shield App（Guardrails）~~ ✅ 已解除
- 需真实 `TOOL_LLM_SHIELD_APP_ID` 才能挂载 content_safety 4回调并验证拦截。
- **用户已提供测试App ID `<APP_ID>`**（2026-09-23），云端实测注入拦截 + 正常请求透传通过。详见§一第12行。
- 残留：用户提供的 LLM Shield App 未删除（非本任务创建资源，用户明确要求不删除）。

### 4.4 ~~Evaluation <PROJECT_NAME>归属~~ ✅ 已解除
- TEA 后端 `-p` 项目隔离被忽略（产品事实，CLI help 标注 "coze only, ignored on TEA"）；用户已接受同账号独立 TEA Workspace（ID=<WORKSPACE_ID>）作为评测归属。
- 自建 <PROJECT_NAME> Runtime + Runtime-source A2A Agent 作为评测对象，Dataset/Evaluator/Experiment 跑通终态，exp6 avg_score=1.0。详见§一第14行。

---

## 五、待验证项（全部完成）

1. ~~Sandbox完整生命周期~~ ✅ 配额解除后自建 CodeEnv tool→shell/run_code→同session FS复用→snapshot→删除，全链路通过（§一第5行）。
2. ~~Skills完整生命周期~~ ✅ 创建SkillSpace→创建Skill→发布→execute_skill真实调用→v2更新生效→清理，全链路通过（§一第6行）。
3. ~~Evaluation终态分数~~ ✅ exp6 status=11终态，2/2样本 score=1，avg_score=1.0（§一第14行）。
4. ~~集成端到端验收~~ ✅ 5组件集成正常路径 + 异常路径（401×2/用户隔离/session隔离/注入拦截）全通过，见§1.1。

---

## 六、凭据安全

- AK/SK：仅`source ~/.bash_profile`后检查非空，全程未打印/落盘/写入报告
- Docker：`export DOCKER_CONFIG=$(mktemp -d)` + `--password-stdin`，完成后`rm -rf $DOCKER_CONFIG`
- CR临时token：仅进程内存使用，未写入/tmp或任何文件
- Runtime API Key：仅进程内存用于invoke测试，未写入报告/日志
- 报告/账本/证据中无任何凭据值，仅变量占位符
- 已清除历史runbook中/tmp/cr_token.json等不安全示例
