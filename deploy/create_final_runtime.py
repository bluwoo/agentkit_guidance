#!/tmp/agentkit_verify_venv/bin/python
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "deploy"))
import cloud_deploy as cd

STATE = ROOT / "deployment-state"
IMAGE = os.environ["WIZARD_IMAGE"]


def read_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            data[key] = value
    return data


def atomic_json(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def main() -> None:
    e2e = read_env_file(STATE / "e2e-secrets.env")
    target = json.loads((STATE / "target-runtime.json").read_text(encoding="utf-8"))
    target_meta = cd._call("GetRuntime", {"RuntimeId": target["runtime_id"]}).get("Result", {})
    target_key = (target_meta.get("AuthorizerConfiguration") or {}).get("KeyAuth", {}).get("ApiKey", "")
    if not target_key:
        raise SystemExit("target key unavailable")
    # Shape-sampling runtime id is supplied by the environment; no real id baked in.
    sample = cd._call("GetRuntime", {"RuntimeId": os.environ["SAMPLE_RUNTIME_ID"]}).get("Result", {})
    model_key = os.environ.get("MODEL_AGENT_API_KEY") or os.environ.get("ARK_API_KEY")
    if not model_key:
        raise SystemExit("model key unavailable")
    state_path = STATE / "runtime-final.json"
    state: dict = {}
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
    runtime_id = state.get("runtime_id")
    if not runtime_id:
        envs = [
            {"Key": "WIZARD_MODE", "Value": "production"},
            {"Key": "SERVE_FRONTEND_DIST", "Value": "/app/web/dist"},
            {"Key": "WIZARD_DATA_DIR", "Value": "/app/wizard_data"},
            {"Key": "WIZARD_LLM_BASE_URL", "Value": "https://ark.cn-beijing.volces.com/api/v3/"},
            {"Key": "WIZARD_LLM_API_KEY", "Value": model_key},
            {"Key": "WIZARD_LLM_MODEL", "Value": "doubao-1-5-pro-32k-250115"},
            {"Key": "WIZARD_ALLOWED_ORIGINS", "Value": ""},
            {"Key": "WIZARD_PUBLIC_ORIGIN", "Value": os.environ.get("WIZARD_PUBLIC_ORIGIN", "")},
            {"Key": "WIZARD_OWNER_SETUP_TOKEN", "Value": e2e["WIZARD_OWNER_SETUP_TOKEN"]},
            {"Key": "WIZARD_RUNTIME_ENDPOINTS", "Value": json.dumps({target["runtime_id"]: target["endpoint"]})},
            {"Key": "WIZARD_RUNTIME_AUTH", "Value": json.dumps({target["runtime_id"]: {"header": "Authorization", "value": "Bearer " + target_key}})},
        ]
        body = {
            "ProjectName": "default", "Name": "agentkit-wizard-human-final",
            "Description": "AgentKit Wizard final browser deployment",
            "ArtifactType": "image", "ArtifactUrl": IMAGE, "RoleName": sample["RoleName"],
            "Command": sample.get("Command"),
            "AuthorizerConfiguration": {"KeyAuth": {"ApiKeyLocation": "Header", "ApiKeyName": "Authorization"}},
            "Envs": envs, "NetworkConfiguration": {"EnablePublicNetwork": True},
            "ClientToken": state.get("client_token") or uuid.uuid4().hex,
            "CpuMilli": 2000, "MemoryMb": 4096, "MinInstance": 1, "MaxInstance": 2,
            "MaxConcurrency": 100, "ApmplusEnable": True,
            "ModelAgentName": "doubao-1-5-pro-32k-250115",
            "Tags": [{"Key": "managed_by", "Value": "agentkit-wizard-final", "Type": "custom"}],
        }
        out = cd._call("CreateRuntime", body)
        error = (out.get("ResponseMetadata") or {}).get("Error")
        if error:
            raise SystemExit(f"CreateRuntime failed: {error.get('Code')} {error.get('Message')}")
        result = out.get("Result", {})
        runtime_id = result.get("RuntimeId") or result.get("Id")
        if not runtime_id:
            raise SystemExit("CreateRuntime missing id")
        state = {"runtime_id": runtime_id, "client_token": body["ClientToken"], "image": IMAGE}
        atomic_json(state_path, state)
    status = ""
    endpoint = state.get("endpoint", "")
    for _ in range(120):
        current = cd._call("GetRuntime", {"RuntimeId": runtime_id}).get("Result", {})
        status = current.get("Status", "")
        endpoint = current.get("Endpoint", "") or endpoint
        if status == "Ready":
            key = (current.get("AuthorizerConfiguration") or {}).get("KeyAuth", {}).get("ApiKey", "")
            if not key:
                raise SystemExit("final runtime key unavailable")
            state.update({"endpoint": endpoint, "status": status})
            atomic_json(state_path, state)
            private = read_env_file(STATE / "e2e-secrets.env")
            private["FINAL_RUNTIME_API_KEY"] = key
            secret_path = STATE / "e2e-secrets.env"
            tmp = secret_path.with_suffix(".tmp")
            tmp.write_text("".join(f"{k}={v}\n" for k, v in private.items()), encoding="utf-8")
            os.chmod(tmp, 0o600)
            os.replace(tmp, secret_path)
            print(json.dumps({"runtime_id": runtime_id, "status": status, "endpoint": endpoint}))
            return
        if status == "UnReleased":
            cd._call("ReleaseRuntime", {"RuntimeId": runtime_id, "VersionNumber": 0})
        if status == "Error":
            raise SystemExit("final Runtime entered Error")
        time.sleep(5)
    raise SystemExit("final Runtime timeout: " + status)


if __name__ == "__main__":
    main()
