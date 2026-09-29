# 11 网关 (Gateway / MCP)

> 概述：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/Gatewayoverview?lang=zh
> 计费计数：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/gateway_mode_and_mcp_request_counting_rules?lang=zh
> REST→MCP：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/connect-existing-rest-api-or-openapi-to-mcp-tool?lang=zh
> 已有 MCP Server：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/connect-existing-mcp-server-to-[PRODUCT]-gateway?lang=zh
> 协议兼容：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/MCPprotocolversioncompatibilityinstructions?lang=zh
> Agent 集成：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/IntegratingMCPinagents?lang=zh

## 概念

网关是 Agent 访问后端工具的统一入口，承担**认证、路由、协议转换、访问治理**。支持两种形态：
- **共享网关**：POC/低流量，免费额度内零成本。
- **专属网关**：生产环境，隔离性高，支持插件（凭据转换、自定义服务扩展）。

> Runtime 网关与 MCP 网关是两套独立实例，分别下单计费。

## 核心组件

### MCP 服务（MCPService）
- 把后端工具能力包装为 MCP 服务。接入方式：
  1. **部署 MCP 服务**（函数服务 veFaaS 模式，计 CPU/内存）。
  2. **REST API / OpenAPI 转 MCP**：上传 OpenAPI 规范，网关自动转换为 MCP 工具。
  3. **接入已有 MCP Server**：填写后端 MCP Server 地址与认证，网关代理。
  4. 私网域名方式接入。
- 操作：创建/调试/获取调用示例/添加工具/更新入站认证/更新后端/查看网络/启动失败日志/删除。

### MCP 工具集（MCPToolset）
- 把多个 MCP 服务的工具聚合为一个工具集，支持**语义检索**（按用户意图动态选工具）。
- 操作：创建/调试/获取调用示例/添加移除工具/更新入站认证/更新工具调用模式/查看网络/删除。
- 语义检索工具索引计费：0.014 元/万个/小时。

### 模型服务
- 在网关层代理火山方舟模型，支持 Proxy API Key 维度与模型维度的 Token 用量管控（2026-09-10）。

## 接入已有 MCP Server 关键步骤

来源：connect-existing-mcp-server-to-[PRODUCT]-gateway
1. 准备后端 MCP Server（支持 Streamable HTTP）。
2. 在 [PRODUCT] 创建 MCP 服务，选择"接入已有 MCP Server"，填后端 Endpoint、认证方式。
3. 网关生成 MCP 服务 Endpoint + ApiKey（Bearer Token）。
4. 在 Runtime 关联该 MCP 服务/工具集；Agent 经网关调用。
5. 私网场景可用私网域名调试（2026-09-10）。

## REST/OpenAPI 转 MCP
- 上传 OpenAPI 3.x 规范文件，网关自动生成 MCP 工具 schema，映射鉴权参数。

## 协议版本兼容性
来源：MCPprotocolversioncompatibilityinstructions
- 网关支持 MCP Streamable HTTP 传输；版本兼容矩阵见该页（未逐字摘录）。

## 在 Agent 中集成 MCP（SDK）

来源：https://<INTERNAL_HOST>.com/docs/[PRODUCT]/mcp?lang=zh
```python
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StreamableHTTPConnectionParams
mcp_toolset = MCPToolset(connection_params=StreamableHTTPConnectionParams(
    url=os.getenv("MCP_ENDPOINT"),
    headers={"Authorization": f"Bearer {os.getenv('MCP_AUTH_KEY')}"}))
agent = Agent(name="ecs_helper", model_name="doubao-1-5-pro-256k-250115",
              instruction="...", tools=[mcp_toolset])
```
环境变量：`MCP_ENDPOINT`、`MCP_AUTH_KEY`、方舟 `API_KEY`。

## MCP API 清单
CreateMCPService/ListMCPServices/GetMCPService/UpdateMCPService/UpdateMCPTools/DeleteMCPService；CreateMCPToolset/ListMCPToolsets/GetMCPToolset/UpdateMCPToolset/DeleteMCPToolset/ListMCPToolsetTools；TagResources/UntagResources/ListTagsForResources。
