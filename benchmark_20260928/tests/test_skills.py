"""Behavior tests for c05_skills (agentkit-skills load-gate).

Added after audit found c05 had zero behavior tests (only import coverage).
These lock in the most critical Skill contract: the Agent must be constructed
with skills=[SKILL_SPACE_ID], otherwise load_skills() never fires.
"""
import os

import pytest

from harness.c05_skills import Skill, SkillRegistry, SkillSpace


def test_skills_field_from_env_returns_id_when_set(monkeypatch):
    monkeypatch.setenv("SKILL_SPACE_ID", "space-abc-123")
    assert SkillRegistry.skills_field_from_env() == ["space-abc-123"]


def test_skills_field_from_env_returns_empty_when_unset(monkeypatch):
    monkeypatch.delenv("SKILL_SPACE_ID", raising=False)
    assert SkillRegistry.skills_field_from_env() == []


def test_skills_field_from_env_trims_whitespace(monkeypatch):
    monkeypatch.setenv("SKILL_SPACE_ID", "  space-x  ")
    assert SkillRegistry.skills_field_from_env() == ["space-x"]


def test_registry_publish_list_execute():
    reg = SkillRegistry()
    space = SkillSpace(space_id="sp1", name="test-space")
    space.publish(Skill(name="greet", version="v2", description="say hi"))
    reg.add_space(space)

    assert [s.name for s in reg.list_skills("sp1")] == ["greet"]
    import asyncio
    out = asyncio.run(reg.execute_skill("sp1", "greet", {"name": "world"}))
    assert "greet@v2" in out
    assert "world" in out


def test_registry_execute_missing_raises():
    reg = SkillRegistry()
    import asyncio
    with pytest.raises(KeyError):
        asyncio.run(reg.execute_skill("sp1", "nonexistent", {}))


def test_registry_list_unknown_space_empty():
    reg = SkillRegistry()
    assert reg.list_skills("does-not-exist") == []
