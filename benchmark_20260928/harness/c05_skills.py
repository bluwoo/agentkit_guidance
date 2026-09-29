"""Component: **agentkit-skills** (智能工坊 / Skills 中心).

Per the Skill:
  * A Skill is a callable capability unit; a SkillSpace is a versioned container.
  * Mounting is a *deployment-time* concern (Runtime "关联组件"); the runtime consumes it via
    the env var ``SKILLS=space:<id>`` / ``SKILL_SPACE_ID``.
  * Critical: the veadk Agent must be constructed with ``skills=[<space_id>]`` — otherwise
    ``Agent.skills == []`` and ``load_skills()`` never fires, so no ``SkillsToolset`` registers.
  * ``execute_skill`` is how an Agent invokes a loaded skill.

The real Skill upload / ListSkillsBySpaceId needs AK/SK. We model a local SkillSpace registry
and the load-gate contract.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class Skill:
    name: str
    version: str = "v1"
    description: str = ""
    schema: dict = field(default_factory=dict)


@dataclass
class SkillSpace:
    space_id: str
    name: str
    skills: dict[str, Skill] = field(default_factory=dict)

    def publish(self, skill: Skill):
        self.skills[skill.name] = skill


class SkillRegistry:
    """Local stand-in for the Skills center / SkillSpace registry."""

    def __init__(self) -> None:
        self.spaces: dict[str, SkillSpace] = {}

    def add_space(self, space: SkillSpace):
        self.spaces[space.space_id] = space

    def list_skills(self, space_id: str) -> list[Skill]:
        sp = self.spaces.get(space_id)
        return list(sp.skills.values()) if sp else []

    @staticmethod
    def skills_field_from_env() -> list[str]:
        """The exact load-gate from the Skill: read SKILL_SPACE_ID -> skills=[...].

        If empty, the Agent would be built with skills=[] and load_skills() would NOT run.
        """
        sid = os.getenv("SKILL_SPACE_ID", "").strip()
        return [sid] if sid else []

    async def execute_skill(self, space_id: str, skill_name: str, args: dict) -> str:
        skill = self.spaces.get(space_id).skills.get(skill_name) if space_id in self.spaces else None
        if skill is None:
            raise KeyError(f"skill {skill_name!r} not in space {space_id!r}")
        return f"executed {skill.name}@{skill.version} args={args}"


# CLI surface recorded from the Skill (agentkit-cli 0.52.13):
SKILL_CLI_SURFACE = [
    "agentkit skill list", "agentkit skill show <id>", "agentkit skill versions <id>",
    "agentkit skill spaces", "agentkit skills upload <dir>", "agentkit skill delete <id>",
]
