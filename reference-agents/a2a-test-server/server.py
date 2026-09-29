"""A2A Provider Server：使用正式VeADK A2A SDK，提供标准AgentCard端点和message/send协议。

与旧版的区别：
- 使用 veadk.a2a.ve_a2a_server.init_app 创建标准FastAPI应用
- 自动提供 GET /.well-known/agent-card.json（标准A2A AgentCard）
- 自动提供 POST / （标准A2A JSON-RPC message/send）
- 使用 VeADK Agent + Runner 处理真实消息，而非自创结构
- 支持标准Task/Message schema，由SDK处理
"""
import os
from veadk import Agent, Runner
from veadk.a2a.ve_a2a_server import init_app
from veadk.memory.short_term_memory import ShortTermMemory, InMemorySessionService

# 不加载.env，避免配置干扰
os.environ.pop("VEADK_CONFIG", None)

# 构造Agent（简单计算/回显Agent，不依赖外部模型）
agent = Agent(
    name=os.getenv("AGENT_NAME", "test_a2a_provider"),
    instruction="你是一个A2A测试Provider。用户问数学题时计算答案，其他问题回显确认。",
    model_name=os.getenv("MODEL_AGENT_MODEL", "<model-name>"),
)

# 配置ShortTermMemory（InMemory用于单实例测试；生产应用DatabaseSessionService）
stm = ShortTermMemory(session_service=InMemorySessionService())

# A2A server URL（部署后由Runtime endpoint填充，本地测试用占位）
SERVER_URL = os.getenv("A2A_SERVER_URL", "http://localhost:8000")

# 使用正式VeADK A2A SDK创建FastAPI应用
# init_app自动注册：
#   GET /.well-known/agent-card.json  → 标准AgentCard
#   GET /.well-known/agent.json       → 扩展AgentCard
#   POST /                            → A2A JSON-RPC (initialize/message/send/tasks/get)
app = init_app(
    server_url=SERVER_URL,
    app_name=os.getenv("APP_NAME", "test_a2a_app"),
    agent=agent,
    short_term_memory=stm,
)


class _GatewayPathRewrite:
    """AgentKit 网关把 runtime 路径（可能因 Runtime-source A2A 注册产生重复 /runtime/<id>
    前缀）转发到容器。A2A JSON-RPC 处理器只挂在 POST / 上，因此对所有 POST 请求在路由前
    把 path 重写为 /；GET（agent-card）保持原样。"""

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope.get("type") == "http" and scope.get("method") == "POST":
            scope = dict(scope)
            scope["path"] = "/"
            scope["raw_path"] = b"/"
        await self.inner(scope, receive, send)


app = _GatewayPathRewrite(app)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
