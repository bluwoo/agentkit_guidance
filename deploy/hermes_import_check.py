#!/usr/bin/env python3
"""Offline import-only check for the RealHermesBridge dependency surface.

This is the build-time / CI substitute for "docker build runs inside the image":
the docker daemon is not always available on the dev box, so we verify, in the
project venv, that the exact import paths the shim uses CAN be resolved once
``vendor/hermes-agent`` is on ``sys.path``.

What it checks (and only this — it must NEVER call an LLM or hit the network):
  * ``import run_agent``                          (module root)
  * ``import agent.conversation_loop``           (conversation loop module)
  * ``run_agent.AIAgent`` is importable/callable
  * ``agent.conversation_loop.run_conversation`` exists

It does NOT construct ``AIAgent(...)`` because that can open memory/log/network
handles; the shim constructs it lazily at first real turn. Import-level success
is the contract: every package in deploy/requirements.txt (Hermes core deps) is
present and compatible with the pinned pydantic/openai.

Run (from repo root):
    python deploy/hermes_import_check.py
    # or, if HERMES_VENDOR_ROOT differs:
    HERMES_VENDOR_ROOT=/path/to/hermes-agent python deploy/hermes_import_check.py

Exit code 0 == imports OK; 1 == a required symbol/module is missing (usually a
missing pip dependency — install it into the verify venv, see deploy/requirements.txt).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def main() -> int:
    here = Path(__file__).resolve().parent
    root = Path(
        os.environ.get(
            "HERMES_VENDOR_ROOT",
            str(here.parent / "vendor" / "hermes-agent"),
        )
    )
    if not (root / "run_agent.py").exists():
        print(f"FAIL: vendor hermes not found at {root}")
        return 1
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    errors: list[str] = []
    run_agent_ok = False

    # 1) module root
    try:
        import run_agent
    except Exception as e:
        errors.append(f"import run_agent failed: {type(e).__name__}: {e}")
    else:
        run_agent_ok = True
        print("OK import run_agent")

    # 2) conversation loop
    try:
        import agent.conversation_loop as cl  # noqa: F401
    except Exception as e:
        errors.append(f"import agent.conversation_loop failed: {type(e).__name__}: {e}")
    else:
        print("OK import agent.conversation_loop")

    # 3) required symbols (the exact surface RealHermesBridge uses).
    #    `run_agent` is only inspected if step 1 actually bound the name.
    if run_agent_ok:
        if not hasattr(run_agent, "AIAgent"):
            errors.append("run_agent has no attribute AIAgent")
        else:
            print("OK run_agent.AIAgent present")

    try:
        from agent.conversation_loop import run_conversation
        if not callable(run_conversation):
            errors.append("agent.conversation_loop.run_conversation is not callable")
        else:
            print("OK agent.conversation_loop.run_conversation callable")
    except Exception as e:
        errors.append(f"from agent.conversation_loop import run_conversation failed: {e}")

    # 4) sanity: the pydantic pin Hermes requires (2.13.4) is active.
    try:
        import pydantic

        print(f"INFO pydantic={pydantic.VERSION}")
        if pydantic.VERSION != "2.13.4":
            errors.append(
                f"pydantic is {pydantic.VERSION}; Hermes pins 2.13.4. "
                "Reinstall deploy/requirements.txt into the venv."
            )
    except Exception as e:
        errors.append(f"cannot import pydantic: {e}")

    if errors:
        print("\nIMPORT CHECK FAILED:")
        for e in errors:
            print("  -", e)
        return 1
    print("\nIMPORT CHECK PASSED (no LLM call made; offline).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
