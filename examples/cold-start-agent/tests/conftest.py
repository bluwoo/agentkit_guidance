"""pytest 公共夹具。

每个测试会话把 SESSION_DB_URL 指到临时 sqlite，避免污染仓库默认库。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# 让 tests 能 import 工程根的模块（app.py / workflow.py / ...）
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture()
def app_container(tmp_path, monkeypatch):
    """导入 app 模块，使用临时持久化库，返回 (container, runner, db_path)。"""
    db = tmp_path / "test_sessions.db"
    monkeypatch.setenv("SESSION_DB_URL", f"sqlite+aiosqlite:///{db}")

    import importlib

    import app as app_module

    importlib.reload(app_module)
    return app_module.app_container, app_module.runner, db
