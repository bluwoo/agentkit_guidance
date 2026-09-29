"""全功能 Agent：显式持久化 ShortTermMemory(DatabaseSessionService) + content_safety 4回调 + OTEL。

修复点（vs旧版）：
1. 显式配置 DatabaseSessionService 作为 ShortTermMemory backend，
   通过 db_url="sqlite+aiosqlite:////data/sessions.db" 触发 model_post_init
   构造 DatabaseSessionService（而非 InMemorySessionService 或 SQLiteSTMBackend）。
   注意：auto_save_session=True 不足以证明跨请求持久化，必须显式传入 short_term_memory。
2. user_id/session_id 从 headers 显式获取，缺失时返回 400 JSONResponse，
   不回落 "default"，不生成随机标识，避免不同请求聚合到同一会话。
3. 支持 SQLite（本地/容器 /data/sessions.db）和 PostgreSQL（云端）两种持久化 backend。
4. 会话隔离：不同 user_id/session_id 严格隔离，由 DatabaseSessionService 保证。
5. 保留 OTEL APMPlusExporter span processor 注册、content_safety 条件加载、
   skills 字段支持、LongTermMemory/KnowledgeBase 条件加载。
"""
import os
from pathlib import Path

# ========== OTEL APMPlus Exporter 直接注册 ==========
# 平台K8s mutating webhook注入的auto-instrumentation创建了指向localhost:4318的
# 全局TracerProvider。veADK OpentelemetryTracer检测到已有provider后跳过注册自己的
# APMPlusExporter(gRPC 4317)。此处直接将APMPlusExporter的span processor添加到
# 现有TracerProvider，确保trace上报到APMPlus。
try:
    from opentelemetry import trace as _otel_trace
    from veadk.tracing.telemetry.exporters.apmplus_exporter import APMPlusExporter as _APMExp
    _tp = _otel_trace.get_tracer_provider()
    if hasattr(_tp, 'add_span_processor'):
        _apm_exp = _APMExp()
        if _apm_exp.processor:
            _tp.add_span_processor(_apm_exp.processor)
            print("[OTEL-FIX] APMPlusExporter span processor added to existing TracerProvider")
    del _otel_trace, _APMExp, _tp
except Exception as _e:
    print(f"[OTEL-FIX] Failed to register APMPlusExporter: {_e}")

from starlette.responses import JSONResponse
from veadk import Agent, Runner
from agentkit.apps import AgentkitSimpleApp
from veadk.memory.short_term_memory import ShortTermMemory, DatabaseSessionService

# 不加载.env
os.environ.pop("VEADK_CONFIG", None)

# ========== 会话持久化配置（DatabaseSessionService） ==========
# veadk 1.1.13: ShortTermMemory 通过 db_url 触发 model_post_init 构造 DatabaseSessionService。
# 不使用 backend="sqlite"（那会走 SQLiteSTMBackend，不是 DatabaseSessionService）。
# 不依赖 auto_save_session=True（仅控制是否自动保存，不指定持久化backend）。
#
# SQLite URL 格式（绝对路径）：sqlite+aiosqlite:////data/sessions.db
# PostgreSQL URL 格式：       postgresql+asyncpg://user:pass@host:5432/db
# 优先使用完整数据库 URL；其次接受本地 SQLite 文件路径。
# 本地默认写当前目录，生产容器如需 /data 必须显式设置 SESSION_SQLITE_PATH=/data/sessions.db，
# 避免模块导入阶段尝试创建无权限的根目录。
SESSION_DB_URL = os.getenv("SESSION_DB_URL", "").strip()
_session_sqlite_path = os.getenv("SESSION_SQLITE_PATH", "").strip()
_session_backend = "database-url"

if not SESSION_DB_URL:
    session_path = Path(_session_sqlite_path or "./.sessions.db").expanduser()
    session_path.parent.mkdir(parents=True, exist_ok=True)
    SESSION_DB_URL = f"sqlite+aiosqlite:///{session_path.resolve()}"
    _session_backend = "sqlite"

short_term_memory = ShortTermMemory(db_url=SESSION_DB_URL)

# 断言：确保使用的是 DatabaseSessionService（持久化），而非 InMemorySessionService
if not isinstance(short_term_memory.session_service, DatabaseSessionService):
    raise RuntimeError(
        f"short_term_memory.session_service is {type(short_term_memory.session_service).__name__}, "
        f"expected DatabaseSessionService. Check SESSION_DB_URL={SESSION_DB_URL}"
    )
print(f"[SESSION] Persistent backend: DatabaseSessionService, db_url={SESSION_DB_URL}")

# ========== 条件加载 content_safety（需 TOOL_LLM_SHIELD_APP_ID） ==========
content_safety = None
if os.getenv("TOOL_LLM_SHIELD_APP_ID"):
    from veadk.tools.builtin_tools.llm_shield import content_safety

# ========== 长期记忆（viking backend） ==========
ltm = None
if os.getenv("ENABLE_MEMORY", "false").lower() == "true":
    from veadk.memory import LongTermMemory
    ltm = LongTermMemory(backend="viking", backend_config={}, app_name="full_feature_app")

# ========== 知识库（viking backend） ==========
kb = None
if os.getenv("ENABLE_KB", "false").lower() == "true":
    from veadk.knowledgebase import KnowledgeBase
    kb = KnowledgeBase(
        backend="viking",
        name=os.getenv("DATABASE_VIKING_COLLECTION", "default"),
        index=os.getenv("DATABASE_VIKING_COLLECTION", ""),
        backend_config={}
    )

# ========== 构造 Agent ==========
# 注意：不再设置 auto_save_session=True——它仅控制保存时机，不指定持久化backend，
# 不足以证明跨请求持久化。持久化由 Runner(short_term_memory=...) 显式传入。
agent_kwargs = dict(
    name="full_feature_agent",
    model_name=os.getenv("MODEL_AGENT_MODEL", "<model-name>"),
    instruction="你是一个全功能测试Agent，支持记忆、知识库、安全围栏、持久化会话。",
    long_term_memory=ltm,
    knowledgebase=kb,
)

# ========== Skills 加载（local 模式：从 SkillSpace 下载 SKILL.md + 代码） ==========
# 设置 SKILL_SPACE_ID 后，Agent 自动进入 local 模式（无 AGENTKIT_TOOL_ID 时），
# 通过 ListSkillsBySpaceId 拉取 space 内已发布的 skill，注册为 SkillsToolset。
# 容器内 AK/SK 由 VeFaaS IAM sidecar 自动注入，无需手动配置。
_skill_space_id = os.getenv("SKILL_SPACE_ID", "").strip()
if _skill_space_id:
    agent_kwargs["skills"] = [_skill_space_id]
    print(f"[SKILLS] skills configured: {agent_kwargs['skills']} (local mode, no AGENTKIT_TOOL_ID)")

if content_safety:
    agent_kwargs.update({
        "before_model_callback": content_safety.before_model_callback,
        "after_model_callback": content_safety.after_model_callback,
        "before_tool_callback": content_safety.before_tool_callback,
        "after_tool_callback": content_safety.after_tool_callback,
    })

agent = Agent(**agent_kwargs)

# Runner 显式传入持久化 ShortTermMemory（DatabaseSessionService backend）
runner = Runner(
    agent=agent,
    short_term_memory=short_term_memory,
    app_name="full_feature_app",
)

app = AgentkitSimpleApp()


@app.entrypoint
async def run(payload, headers):
    # 显式从 headers 获取 user_id / session_id。
    # 缺失时拒绝请求（400），不回落 "default"，不生成随机标识——
    # 避免不同用户/请求聚合到同一会话造成数据泄漏。
    user_id = headers.get("user_id")
    session_id = headers.get("session_id")

    if not user_id or not session_id:
        return JSONResponse(
            status_code=400,
            content={"error": "user_id and session_id headers are required"},
        )

    result = await runner.run(
        messages=payload["prompt"],
        user_id=user_id,
        session_id=session_id,
    )
    return result


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
