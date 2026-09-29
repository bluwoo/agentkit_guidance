#!/usr/bin/env /tmp/agentkit_verify_venv/bin/python
"""One-shot: create the Wizard Runtime on AgentKit (cn-beijing/default).

Reuses the signed HTTP helpers from cloud_deploy.py. Reads ambient WIZARD_LLM_*
(allowlisted) and ARK key. Never prints secrets. Persists ClientToken + result
to deployment-state/ so retries are idempotent.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cloud_deploy as cd

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "deployment-state"
STATE.mkdir(exist_ok=True)
STATE_FILE = STATE / "runtime.json"

IMAGE = os.environ["WIZARD_IMAGE"]
NAME = "agentkit-wizard"


def main() -> int:
    # 1. dynamic sample RoleName (no hard-coded ID)
    sample = cd._sample_runtime_shape()
    if not sample or not sample.get("role_name"):
        print("ERROR: could not sample an existing runtime RoleName", file=sys.stderr)
        return 1
    role = sample["role_name"]
    print(f"sampled RoleName: {role}")

    # 2. persistent ClientToken
    if STATE_FILE.exists():
        prev = json.loads(STATE_FILE.read_text())
        token = prev.get("client_token")
        runtime_id = prev.get("runtime_id")
        print(f"resuming state: runtime_id={runtime_id}")
    else:
        token = cd.uuid.uuid4().hex[:64]
        runtime_id = None

    # 3. create or resume
    if not runtime_id:
        payload = cd.build_runtime_payload(
            IMAGE, NAME, role_name=role,
        )
        payload["ClientToken"] = token
        print(f"creating runtime (image={IMAGE}) ...")
        try:
            out = cd._call("CreateRuntime", payload)
        except Exception as e:  # surface non-secret message
            print("CreateRuntime failed:", str(e)[:300], file=sys.stderr)
            return 2
        runtime_id = out.get("RuntimeId") or out.get("Runtime", {}).get("RuntimeId")
        if not runtime_id:
            print("no RuntimeId in response:", json.dumps(out)[:300], file=sys.stderr)
            return 2
        print(f"created RuntimeId: {runtime_id}")
        STATE_FILE.write_text(json.dumps({"client_token": token, "runtime_id": runtime_id}, indent=2))
    else:
        print("reusing existing runtime_id from state")

    # 4. poll status, ReleaseRuntime if needed
    endpoint = None
    for i in range(60):
        try:
            g = cd._call("GetRuntime", {"ProjectName": cd.PROJECT, "RuntimeId": runtime_id})
        except Exception as e:
            print("GetRuntime err:", str(e)[:200], file=sys.stderr); time.sleep(5); continue
        r = g.get("Runtime", g)
        st = r.get("Status") or r.get("StatusDetail")
        endpoint = r.get("Endpoint") or r.get("Domain") or endpoint
        print(f"  poll {i}: status={st} endpoint={endpoint}")
        if st == "Ready":
            break
        if st in ("UnReleased", "Creating"):
            try:
                rel = cd._call("ReleaseRuntime", {"ProjectName": cd.PROJECT, "RuntimeId": runtime_id, "VersionNumber": 0})
                print("  ReleaseRuntime called:", json.dumps(rel)[:150])
            except Exception as e:
                msg = str(e)
                if "already" not in msg.lower() and "ready" not in msg.lower():
                    print("  ReleaseRuntime note:", msg[:150])
        time.sleep(5)

    result = {
        "runtime_id": runtime_id,
        "endpoint": endpoint,
        "status": st,
        "image": IMAGE,
        "model": os.environ.get("WIZARD_LLM_MODEL", ""),
        "hermes_version": "0.21.3",
    }
    (STATE / "runtime-result.json").write_text(json.dumps(result, indent=2))
    print("FINAL:", json.dumps({k: v for k, v in result.items() if k != "endpoint"}))
    print("endpoint:", endpoint)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
