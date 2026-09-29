"""Unit tests: 14-component catalog completeness."""
from __future__ import annotations

from server.wizard.components.catalog import COMPONENTS, get_component, list_components

EXPECTED_IDS = {
    "runtime:agentkit", "function:agentkit-sdk", "agent:veadk",
    "agent:adk-workflow", "knowledge_base:vikingdb", "a2a:registry",
    "skill:agentkit-skills", "gateway:mcp", "identity:permission",
    "guardrails:firewall", "function:evaluation", "observability:apmplus",
    "sandbox:code", "memory:session",
}


def test_exactly_fourteen_cards():
    cards = list_components()
    assert len(cards) == 14
    assert {c["component_id"] for c in cards} == EXPECTED_IDS


def test_card_shape():
    for c in COMPONENTS:
        for field in ("component_id", "name", "kind", "purpose",
                      "prerequisites", "permissions", "config_schema", "skill_ref"):
            assert field in c, f"missing {field} in {c.get('component_id')}"
        assert c["purpose"]


def test_get_component_lookup():
    assert get_component("runtime:agentkit")["name"] == "agentkit-runtime"
    assert get_component("does-not-exist") is None
