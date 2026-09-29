# [PRODUCT] [DELIVERY] — 部署指南 (DEPLOYMENT.md)

本文件说明 [PRODUCT] [DELIVERY] 后端（FastAPI 层 - 1 Runtime shim，真实 [BASE-AGENT] 0.21.3

主循环）+ 前端（React/Vite）的本地运行、容器化与云部署方式。镜像与配置**不硬编码**

**任何密钥**；所有运行时开关都走环境变量。



***

## 1. 本地三种起法

### 1.1 单脚本（mock 桥，本地演示）



```
bash run\_local.sh          # http://127.0.0.1:8000，mock 桥 + web/dist
```

### 1.2 Dev 模式（前后端分离，热更新）

后端跑在 8000，前端 Vite dev server 跑在 5173 并把 `/api` 代理到后端。



```
\# 后端（项目根目录）

/tmp/[PRODUCT]\_verify\_venv/bin/uvicorn server.[DELIVERY].main:app --host 0.0.0.0 --port 8000 --reload

\# 前端（另一个终端）

cd web && npm install && npm run dev   # http://localhost:5173，代理 /api -> 8000
```

此模式下不设 `SERVE_FRONTEND_DIST`，`GET /` 返回后端 JSON 健康信息。

### 1.3 Prod 模式（单进程 / 单容器同时托管 API + 前端）



```
cd web && npm run build    # 产物输出到 web/dist/

SERVE\_FRONTEND\_DIST="\$PWD/web/dist" [DELIVERY]\_DATA\_DIR="\$PWD/[DELIVERY]\_data" \\

/tmp/[PRODUCT]\_verify\_venv/bin/uvicorn server.[DELIVERY].main:app --host 0.0.0.0 --port 8000
```



***

## 2. 模式与环境变量表

`[DELIVERY]_MODE` 决定启动行为：



| 模式             | 桥                   | CORS               | 启动条件                                                    |
| -------------- | ------------------- | ------------------ | ------------------------------------------------------- |
| `mock`         | 强制 Mock[BASE-AGENT]Bridge | `*`（告警）            | 无                                                       |
| `local`（未设时默认） | 无 LLM env 时回退 mock  | `*`（告警）            | 无                                                       |
| `production`   | fail-closed         | 空值表示同源，显式配置时拒绝 `*` | 必须具备 `[DELIVERY]_LLM_BASE_URL/API_KEY/MODEL`；前后端分离时再配置来源白名单 |



| 变量                                            | 必填？     | 敏感？   | 默认                 | 说明                                                      |
| --------------------------------------------- | ------- | ----- | ------------------ | ------------------------------------------------------- |
| `[DELIVERY]_MODE`                                 | 生产必填    | 否     | `local`            | `mock`/`local`/`production`。Dockerfile 默认 `production`。 |
| `[DELIVERY]_LLM_BASE_URL`                         | 生产必填    | 否     | 空                  | LLM endpoint；空走 mock。                                   |
| `[DELIVERY]_LLM_API_KEY`                          | 生产必填    | **是** | 空                  | LLM key。                                                |
| `[DELIVERY]_LLM_MODEL`                            | 生产必填    | 否     | 空                  | 模型名。                                                    |
| `[DELIVERY]_LLM_PROVIDER` / `[DELIVERY]_LLM_API_MODE` | 否       | 否     | 空                  | 透传给 `AIAgent(...)`。                                     |
| `[DELIVERY]_ALLOWED_ORIGINS`                      | 否       | 否     | 空                  | 空表示同源；生产拒绝 `*`。                                         |
| `RUNTIME_API_KEY`                             | 否（生产建议） | **是** | 空                  | 入站 KeyAuth；空 → open 本地模式。                               |
| `RUNTIME_API_KEY_HEADER`                      | 否       | 否     | `X-Api-Key`        | 入站 key 头名。                                              |
| `[DELIVERY]_DATA_DIR`                             | 否       | 否     | `./[DELIVERY]_data`    | 草稿 / 会话持久化目录。                                           |
| `SERVE_FRONTEND_DIST`                         | 否       | 否     | 空                  | 指向 `web/dist` 时单进程托管 SPA。                               |
| `OTEL_EXPORTER_OTLP_ENDPOINT`                 | 否       | 否     | 空                  | OTLP endpoint；空 → console。                              |
| `APMPLUS_ACCESS_KEY` / `APMPLUS_SECRET_KEY`   | 否       | **是** | 空                  | APMPlus；空 → `not_configured`。                           |
| `[DELIVERY]_RUNTIME_ENDPOINTS`                    | 否       | 否     | 空                  | JSON `{runtime_id: url}` 反代白名单（反 SSRF）。                 |
| `[DELIVERY]_VERSION` / `[BASE-AGENT]_VERSION`           | 否       | 否     | `0.1.0` / `0.21.3` | span 版本标签。                                              |
| `OTEL_SERVICE_NAME`                           | 否       | 否     | `[DELIVERY]`           | OTel 服务名。                                               |

> 约定：
>
> **留空即降级**
>
> 。生产模式下缺失必填项会
>
> **拒绝启动**
>
> （fail-closed），而不是悄悄降级。



***

## 3. 容器构建与运行

> 构建上下文必须是
>
> **仓库根目录**
>
> （需要复制
>
> `server/`
>
> 、
>
> `vendor/[BASE-AGENT]-agent/`
>
> 、
>
> `web/dist/`
>
> ）。



```
docker build -f deploy/Dockerfile -t [PRODUCT]-[DELIVERY]:0.21.7 .

\# 生产运行（fail-closed：必须给 LLM 与 CORS 白名单）

docker run --rm -p 8000:8000 \\

&#x20; -e [DELIVERY]\_LLM\_BASE\_URL=https://llm/v1 -e [DELIVERY]\_LLM\_API\_KEY=sk-... -e [DELIVERY]\_LLM\_MODEL=gpt-x \\

&#x20; -e [DELIVERY]\_ALLOWED\_ORIGINS=https://app.example.com \\

&#x20; -v [DELIVERY]\_data:/app/[DELIVERY]\_data \\

&#x20; [PRODUCT]-[DELIVERY]:0.21.7

\# 本地 mock 运行（compose 已把 [DELIVERY]\_MODE 覆盖为 mock）

docker compose -f deploy/docker-compose.yml up --build
```

文件清单：



* `deploy/Dockerfile` — 基于 `python:3.12-slim`；装 `deploy/requirements.txt`（**真实** [BASE-AGENT] 核心依赖 + shim 栈，非 MockBridge）；构建期跑 `deploy/[BASE-AGENT]_import_check.py` 做离线 import 校验；`ENV [DELIVERY]_MODE=production`；`EXPOSE 8000`；`HEALTHCHECK /health`；`CMD uvicorn`。

* `deploy/requirements.txt` — 精确 pin 的直接依赖（见文件头说明）。pydantic 统一到 `2.13.4`（[BASE-AGENT] 要求；2.12.5 的 pydantic-core 在 OpenAI Responses API 非主线程会 segfault）。

* `deploy/[BASE-AGENT]_import_check.py` — 离线 import 校验（构建期与本地都可跑）。

* `deploy/docker-compose.yml` — 本地单服务编排（默认 mock）。

* `.dockerignore`（仓库根，生效）+ `deploy/.dockerignore`（镜像副本）— 额外排除 `vendor/[BASE-AGENT]-agent/.git`（\~990MB）与 `**/node_modules`，**保留** `vendor/[BASE-AGENT]-agent/LICENSE`。



***

## 4. 云部署（cn-beijing /default project）

控制面 AK/SK 在环境变量 `VOLCENGINE_ACCESS_KEY` / `VOLCENGINE_SECRET_KEY`（只读 ListRuntimes 已验证 200）。



```
\# 只读预检（不打印任何密钥）

python deploy/cloud\_deploy.py --check

\# 干看将要发送的 CreateRuntime payload（不调 API）

python deploy/cloud\_deploy.py --print-payload \\

&#x20; \--image <INTERNAL_HOST>.com/[PRODUCT]/[PRODUCT]-[DELIVERY]:0.21.7 --name [PRODUCT]-[DELIVERY]

\# 真部署（需 docker daemon 起 + 镜像已推 CR）

python deploy/cloud\_deploy.py --apply \\

&#x20; \--image <INTERNAL_HOST>.com/[PRODUCT]/[PRODUCT]-[DELIVERY]:0.21.7 --name [PRODUCT]-[DELIVERY]
```

`CreateRuntime`（Version 2025-10-30）字段严格按官方：



| 字段                                                                 | 值 / 说明                                                                  |
| ------------------------------------------------------------------ | ----------------------------------------------------------------------- |
| `Name` / `ArtifactType`=`image` / `ArtifactUrl`                    | 名称 / 镜像地址                                                               |
| `RoleName`                                                         | `[PRODUCT]_Runtime_Default_ServiceRole_v0wx3ea`                          |
| `AuthorizerConfiguration.KeyAuth`                                  | `{ApiKeyLocation: Header, ApiKeyName: X-Api-Key}`（只放 header 名，不放 token） |
| `Envs[]`                                                           | `[DELIVERY]_MODE=production` 等；敏感值另行注入                                      |
| `NetworkConfiguration`                                             | `{EnablePublicNetwork: true}`（或私网 + VpcId/SubnetIds）                    |
| `ClientToken`                                                      | uuid 前 64 位 ASCII，幂等；409/DuplicateName 视为已存在                            |
| `CpuMilli` / `MemoryMb` / `MaxInstance` / `ApmplusEnable` / `Tags` | 资源与观测开关                                                                 |
| `Port`                                                             | **不存在该字段**（旧脚本的 `Port: 8000` 已移除）                                       |

创建后轮询 `GetRuntime.Status`（Creating/UnReleased→Releasing→Ready；Error/Deleting 失败），必要时 `ReleaseRuntime(RuntimeId, VersionNumber=0)`。成功后把 `runtime_id`/`endpoint` 写到 `deploy/runtime_out.json`（不写密钥）。静态字段样例见 `deploy/deploy_payload.contract.json`。

> **当前云状态**
>
> ：Runtime 已部署并发布至版本 6；原生 MCP Service 与 Toolset 均为 Ready。平台工具集会为工具名增加服务前缀，
>
> `tools/list`
>
>  返回
>
> `[PRODUCT]-[DELIVERY]_invoke`
>
> ，实际
>
> `tools/call`
>
>  已返回
>
> `platform-mcp-ok`
>
> 。详见
>
> `FINAL-ACCEPTANCE.md`
>
> 。

健康探针：`GET /health`、`GET /ping`（无需鉴权）；`GET /readiness` 返回 `bridge: real|mock`、`mode`。



***

## 5. 已知限制（诚实说明）



1. [PRODUCT] MCP Toolset 会为工具名增加服务前缀；当前实际工具名为 `[PRODUCT]-[DELIVERY]_invoke`。

2. Runtime `MinInstance=0`，首请求可能有冷启动。

3. Ark key 通过 Runtime Envs 注入；当前控制面契约未核验到 secret-reference 字段。

4. 生产 CORS 允许空值表示同源，拒绝 `*`；原生 MCP Host 使用显式白名单。
## 正式 Owner 初始化入口（本轮）
公网前门 https://<RUNTIME_ENDPOINT_HOST>/ 打开后，若显示"需初始化"，访问 /api/auth/setup-page：一次性页面，owner 未绑定前可用；bootstrap token 服务端持有，用户只在页面输入新密码（≥12 位）。owner 绑定后该页返回 409，不可重复初始化，无公开注册。初始化成功即下发 HttpOnly cookie，可正常登录。
