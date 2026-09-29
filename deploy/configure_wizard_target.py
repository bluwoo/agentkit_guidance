#!/tmp/agentkit_verify_venv/bin/python
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "deploy"))
import cloud_deploy as cd

STATE = ROOT / "deployment-state"


def main() -> None:
    wizard = json.loads((STATE / "runtime-v2.json").read_text())
    target = json.loads((STATE / "target-runtime.json").read_text())
    w = cd._call("GetRuntime", {"RuntimeId": wizard["runtime_id"]}).get("Result", {})
    t = cd._call("GetRuntime", {"RuntimeId": target["runtime_id"]}).get("Result", {})
    target_key = (t.get("AuthorizerConfiguration") or {}).get("KeyAuth", {}).get("ApiKey", "")
    if not target_key:
        raise SystemExit("target runtime key unavailable")
    envs = [e for e in w.get("Envs", []) if e.get("Key") not in {
        "WIZARD_RUNTIME_ENDPOINTS", "WIZARD_RUNTIME_AUTH", "WIZARD_PUBLIC_ORIGIN"
    }]
    envs.extend([
        {"Key": "WIZARD_RUNTIME_ENDPOINTS", "Value": json.dumps({target["runtime_id"]: target["endpoint"]})},
        {"Key": "WIZARD_RUNTIME_AUTH", "Value": json.dumps({target["runtime_id"]: {"header": "Authorization", "value": "Bearer " + target_key}})},
        {"Key": "WIZARD_PUBLIC_ORIGIN", "Value": os.environ.get("WIZARD_PUBLIC_ORIGIN", "")},
    ])
    body = {
        "RuntimeId": wizard["runtime_id"],
        "ArtifactType": w.get("ArtifactType", "image"),
        "ArtifactUrl": w["ArtifactUrl"],
        "Command": w.get("Command"),
        "Envs": envs,
        "ReleaseEnable": True,
        "Tags": w.get("Tags", []),
        "ApmplusEnable": True,
        "MinInstance": 1,
        "MaxInstance": w.get("MaxInstance", 2),
        "MaxConcurrency": w.get("MaxConcurrency", 100),
        "CpuMilli": w.get("CpuMilli", 2000),
        "MemoryMb": w.get("MemoryMb", 4096),
    }
    result = cd._call("UpdateRuntime", body)
    error = (result.get("ResponseMetadata") or {}).get("Error")
    if error:
        raise SystemExit(f"UpdateRuntime failed: {error.get('Code')} {error.get('Message')}")
    status = ""
    for _ in range(120):
        current = cd._call("GetRuntime", {"RuntimeId": wizard["runtime_id"]}).get("Result", {})
        status = current.get("Status", "")
        if status == "Ready":
            wizard.update({"status": status, "endpoint": current.get("Endpoint", wizard.get("endpoint"))})
            tmp = STATE / ".runtime-v2.tmp"
            tmp.write_text(json.dumps(wizard, indent=2))
            os.chmod(tmp, 0o600)
            os.replace(tmp, STATE / "runtime-v2.json")
            print(json.dumps({"runtime_id": wizard["runtime_id"], "status": status, "target_runtime_id": target["runtime_id"]}))
            return
        if status == "Error":
            raise SystemExit("updated Wizard Runtime entered Error")
        time.sleep(5)
    raise SystemExit("updated Wizard Runtime did not become Ready: " + status)


if __name__ == "__main__":
    main()
