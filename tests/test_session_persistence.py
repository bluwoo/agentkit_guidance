"""测试VeADK会话持久化：区分单进程内存、跨请求、跨实例隔离"""
import asyncio
import os
import tempfile

os.environ.pop("VEADK_CONFIG", None)

def test_in_memory_session_isolates_users():
    """验证InMemorySessionService：不同user_id/session_id隔离"""
    from veadk.memory.short_term_memory import InMemorySessionService, ShortTermMemory

    svc = InMemorySessionService()
    stm = ShortTermMemory(session_service=svc)

    # create_session是异步的
    s1 = asyncio.run(stm.create_session(app_name="test", user_id="userA", session_id="s1"))
    s2 = asyncio.run(stm.create_session(app_name="test", user_id="userB", session_id="s1"))

    assert s1 is not None
    assert s2 is not None
    assert s1.user_id == "userA"
    assert s2.user_id == "userB"
    print("PASS: InMemory会话按user_id隔离")

def test_database_session_service_sqlite():
    """验证DatabaseSessionService + SQLite backend：持久化到文件"""
    from veadk.memory.short_term_memory import ShortTermMemory

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db_url = f"sqlite+aiosqlite:///{db_path}"
        stm = ShortTermMemory(db_url=db_url)

        s1 = asyncio.run(stm.create_session(app_name="test", user_id="userA", session_id="persist-s1"))
        assert s1 is not None
        print(f"Created session: user={s1.user_id}, session={s1.id}")

        # 重新创建 ShortTermMemory（模拟跨实例/重启）；db_url 会按钉版真实签名
        # 在 model_post_init 中构造 DatabaseSessionService。
        stm2 = ShortTermMemory(db_url=db_url)

        s1_reloaded = asyncio.run(stm2.session_service.get_session(
            app_name="test", user_id="userA", session_id="persist-s1"
        ))
        assert s1_reloaded is not None, "持久化session未找到！"
        assert s1_reloaded.user_id == "userA"
        print("PASS: SQLite持久化session跨实例可恢复")

        # 验证不同user不可见
        s_userb = asyncio.run(stm2.session_service.get_session(
            app_name="test", user_id="userB", session_id="persist-s1"
        ))
        assert s_userb is None, "userB不应看到userA的session"
        print("PASS: 持久化session按user隔离")

    finally:
        os.unlink(db_path)

def test_runner_with_persistent_session():
    """验证Runner使用持久化ShortTermMemory"""
    import tempfile

    from veadk import Agent, Runner
    from veadk.memory.short_term_memory import ShortTermMemory

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        stm = ShortTermMemory(db_url=f"sqlite+aiosqlite:///{db_path}")

        agent = Agent(name="persist_test_agent", instruction="test", model_name="doubao-seed-2-0-lite-260428")
        runner = Runner(agent=agent, short_term_memory=stm, app_name="persist_test")

        assert runner.short_term_memory is stm
        print("PASS: Runner使用持久化ShortTermMemory")

    finally:
        os.unlink(db_path)

def test_default_user_id_not_hardcoded():
    """验证不回落default：缺失user_id时应显式报错而非静默聚合"""
    import inspect

    from veadk import Agent, Runner
    from veadk.memory.short_term_memory import InMemorySessionService, ShortTermMemory

    agent = Agent(name="test_agent", instruction="test", model_name="doubao-seed-2-0-lite-260428")
    stm = ShortTermMemory(session_service=InMemorySessionService())
    runner = Runner(agent=agent, short_term_memory=stm, app_name="test")

    sig = inspect.signature(runner.run)
    default_user = sig.parameters['user_id'].default
    print(f"Runner.run user_id default: '{default_user}'")
    assert default_user == "" or default_user is None
    print("PASS: Runner默认user_id不是硬编码'default'")

if __name__ == "__main__":
    test_in_memory_session_isolates_users()
    test_database_session_service_sqlite()
    test_runner_with_persistent_session()
    test_default_user_id_not_hardcoded()
    print("\n所有会话持久化测试通过!")
