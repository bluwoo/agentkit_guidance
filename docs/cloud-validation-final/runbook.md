# [PRODUCT] 14组件云验证 Runbook（<PROJECT_NAME> / cn-beijing）

## 环境准备

```bash
# 1. 凭据（仅 source，不打印、不落盘、不修改 profile）
source ~/.bash_profile
test -n "$VOLCENGINE_ACCESS_KEY" && test -n "$VOLCENGINE_SECRET_KEY" && echo "creds OK"

# 2. CLI 版本（系统 CLI，不要用 venv 0.8.7）
~/.[PRODUCT]/[PRODUCT] --version  # 期望 0.52.13

# 3. 隔离 venv
cd /home/user/Documents/[PRODUCT]_dev_skills
.venv-verify/bin/python3 -c "import [BASE-ADK], [PRODUCT], google.adk; print([BASE-ADK].__version__, [PRODUCT].__version__)"
```

## 模型选择（避免 429）

```bash
# 可用模型（200 OK）：
# - doubao-seed-2-0-lite-260428（推荐，最低成本）
# - doubao-seed-2-0-mini-260428
# 已知 429 模型：doubao-seed-1-6-250615, doubao-1-5-pro-32k-250115
```

## Runtime 创建与全功能 Agent 部署

```bash
# 1. CR build CLI bug 绕过：本地 docker build + push
# 使用隔离 DOCKER_CONFIG，token 仅内存传递，不落盘
export DOCKER_CONFIG=$(mktemp -d)
trap 'rm -rf "$DOCKER_CONFIG"' EXIT

# CR 登录：调用项目脚本，临时令牌仅通过进程内 stdin 传给 docker login
# 脚本拒绝在未设置临时 DOCKER_CONFIG 时运行，也不会打印或写入令牌
export DOCKER_CONFIG=$(mktemp -d)
trap 'rm -rf "$DOCKER_CONFIG"' EXIT
.venv-verify/bin/python3 scripts/cr_push.py

# 2. Docker build + push（必须 linux/amd64）
docker build --platform linux/amd64 --pull -t <INTERNAL_HOST>.com/[PRODUCT]/full-agent:<tag> /path/to/agent
docker push <INTERNAL_HOST>.com/[PRODUCT]/full-agent:<tag>

# 3. 创建 Runtime（project <PROJECT_NAME>，回读确认）
~/.[PRODUCT]/[PRODUCT] runtime create --name <name> --project <PROJECT_NAME> --region cn-beijing \
  --artifact-url <image> --model-agent-name doubao-seed-2-0-lite-260428 --auto-release

# 4. 回读确认 Project=<PROJECT_NAME>
~/.[PRODUCT]/[PRODUCT] runtime show <runtime-id> | grep -i project

# 5. 等待 Ready 并测试
~/.[PRODUCT]/[PRODUCT] invoke run --runtime-id <runtime-id> \
  --payload '{"prompt":"你好"}' --headers '{"user_id":"u1","session_id":"s1"}'
```

## 全功能 Agent 代码要点

```python
# 持久短期会话必须显式配置 ShortTermMemory(db_url=...)；
# auto_save_session 只控制保存时机，不能替代持久 backend。
short_term_memory = ShortTermMemory(
    db_url=os.getenv("SESSION_DB_URL", "sqlite+aiosqlite:////data/sessions.db")
)

agent = Agent(
    name="full_feature_agent",
    model_name="doubao-seed-2-0-lite-260428",
    long_term_memory=LongTermMemory(backend="viking", backend_config={}, app_name="full_app"),
    knowledgebase=KnowledgeBase(
        backend="viking",
        name="kb",
        index=os.getenv("DATABASE_VIKING_COLLECTION", ""),
        backend_config={},
    ),
    # content_safety 回调需先设 TOOL_LLM_SHIELD_APP_ID
)
runner = Runner(agent=agent, short_term_memory=short_term_memory, app_name="full_feature_app")
```

## 知识库 RAG 验证

```bash
# 1. 创建 KB（注意：用 --viking-project <PROJECT_NAME>，-p <project> 被忽略）
~/.[PRODUCT]/[PRODUCT] knowledge create --name <kb-name> --viking-project <PROJECT_NAME>

# 2. 上传文档（用 add）
~/.[PRODUCT]/[PRODUCT] knowledge add <kb-id> /path/to/doc.txt

# 3. 绑定 Runtime
~/.[PRODUCT]/[PRODUCT] runtime update <runtime-id> --knowledge-id <kb-id> --auto-release

# 4. 等待索引（~30-60s），查询唯一标记
~/.[PRODUCT]/[PRODUCT] invoke run --runtime-id <runtime-id> \
  --payload '{"prompt":"公司代号是什么？"}' --headers '{"user_id":"u1","session_id":"s1"}'
```

## 记忆验证

```bash
# 1. 创建 memory（-p <project> 生效）
~/.[PRODUCT]/[PRODUCT] memory create --name <name> -p <project>

# 2. 绑定 Runtime
~/.[PRODUCT]/[PRODUCT] runtime update <runtime-id> --memory-id <mem-id> --auto-release

# 3. 写入 → 等待 15-30s → 新 session 同 user 召回
# 4. 异用户隔离验证
```

## MCP 自建验证

```bash
# 1. 构建 MCP test server 镜像（echo/add 工具）
docker build --platform linux/amd64 -t <registry>/[PRODUCT]/mcp-test-server:<tag> /path/to/mcp-server
docker push <registry>/[PRODUCT]/mcp-test-server:<tag>

# 2. 创建 MCP 服务
~/.[PRODUCT]/[PRODUCT] mcp service create --name <name> --project <PROJECT_NAME> --image-url <image> --backend-type custom-private

# 3. 四层握手 + 鉴权矩阵
# initialize → tools/list → tools/call
# 无/错 key → 401, 有效 key → 200
```

## 清理

```bash
# 逆序删除所有本轮资源
~/.[PRODUCT]/[PRODUCT] runtime delete <runtime-id> -y
~/.[PRODUCT]/[PRODUCT] mcp service delete <mcp-id> -y
~/.[PRODUCT]/[PRODUCT] knowledge delete <kb-id> -y
~/.[PRODUCT]/[PRODUCT] memory delete --memory-id <mem-id> -y
~/.[PRODUCT]/[PRODUCT] eval dataset delete <dataset-name> -y
~/.[PRODUCT]/[PRODUCT] eval evaluator delete <evaluator-name> -y

# A2A 资源（OpenAPI）
# DeleteA2aAgent + DeleteA2aSpace

# CR 镜像删除（精确 tag，不删仓库/命名空间）
.venv-verify/bin/python3 -c "
from volcenginesdkcore import Configuration
from volcenginesdkcr import CRApi, DeleteTagsRequest
import os
config = Configuration(ak=os.getenv('VOLCENGINE_ACCESS_KEY'), sk=os.getenv('VOLCENGINE_SECRET_KEY'), region='cn-beijing')
Configuration.set_default(config)
api = CRApi()
api.delete_tags(DeleteTagsRequest(names=['<tag>'], registry='[PRODUCT]-platform-<ACCOUNT_ID>', namespace='[PRODUCT]', repository='<repo>'))
"

# 回查确认删除
~/.[PRODUCT]/[PRODUCT] runtime list -p <project> | grep <name>  # 应无匹配

# 已核实的额外清理路径：
# - UserPool 使用 service=id 的 DeleteUserPool(UserPoolUid)
# - Viking provider collection 使用 VikingDB 对应删除接口
# - Evaluation Experiment 当前 CLI 无 delete 子命令：保留终态审计记录，标注无活跃执行；
#   终态记录是否产生持续费用以账单/最新计费说明为准，不做无依据承诺
```

## 已知问题与绕过

| 问题 | 绕过/说明 |
|---|---|
| CR build CLI 误报 "instance disappeared" | 本地 docker build + push |
| SDK 多轮不生效 | 显式 `ShortTermMemory(db_url=...)` 并传给 `Runner(short_term_memory=...)`；缺失 user/session header 返回 400 |
| KnowledgeBase 不挂载工具 | 传 backend_config={} + index |
| knowledge -p <project> 无效 | 用 --viking-project <PROJECT_NAME> |
| knowledge upload 命令不存在 | 用 knowledge add |
| content_safety 导入报错 | 先设 TOOL_LLM_SHIELD_APP_ID |
| 模型 429 | 换 doubao-seed-2-0-lite-260428 |
| Runtime 不支持 agent card | API/CLI创建的Runtime均不支持, 需控制台或开白 |
| eval -p 仅coze生效 | TEA后端忽略, workspace为default_space |
| APMPlus OpenAPI 404 | 端点未确认, Runtime日志可替代取证 |

## 安全注意事项

- AK/SK 仅从 ~/.bash_profile source 使用，禁止打印/落盘/修改 profile
- CR token 使用隔离 DOCKER_CONFIG + --password-stdin，完成后 rm -rf
- Runtime API Key 仅内存使用，不写入文件/报告
- 所有命令输出避免 env/dump/debug 泄露
- 不触碰既有生产资源，仅操作本轮创建的 <TEMP_PREFIX>- 前缀资源
