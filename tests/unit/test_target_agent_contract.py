from __future__ import annotations

import ast
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2] / "deploy" / "target-agent" / "app.py"


def test_target_agent_is_a_separate_service():
    tree = ast.parse(SOURCE.read_text())
    text = SOURCE.read_text()
    assert 'SERVICE_NAME = "support-triage-agent"' in text
    assert "AgentkitSimpleApp" in text
    assert "@app.entrypoint" in text
    assert 'client.chat.completions.create' in text
    assert 'start_as_current_span("invoke_agent")' in text
    assert 'start_as_current_span("call_llm")' in text
    assert "APMPlusExporter" in text
    assert not any(isinstance(node, ast.ImportFrom) and node.module == "server.wizard.main" for node in ast.walk(tree))
