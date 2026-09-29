#!/tmp/agentkit_verify_venv/bin/python
from __future__ import annotations

import base64
import io
import json
import os
import time
import zipfile
from pathlib import Path

from volcenginesdkapig import (
    APIGApi,
    UpdateUpstreamRequest,
    UpstreamSpecForUpdateUpstreamInput,
    VeFaasForUpdateUpstreamInput,
)
from volcenginesdkcore import ApiClient, Configuration
from volcenginesdkvefaas import (
    CreateFunctionRequest,
    EnvForCreateFunctionInput,
    GetReleaseStatusRequest,
    ListFunctionsRequest,
    ReleaseRequest,
    VEFAASApi,
    VpcConfigForCreateFunctionInput,
)

ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / "deployment-state" / "frontdoor.json"
RUNTIME_PATH = ROOT / "deployment-state" / "runtime-v2.json"
SECRETS_PATH = ROOT / "deployment-state" / "e2e-secrets.env"
SOURCE_PATH = ROOT / "deploy" / "frontdoor_function" / "index.py"
FUNCTION_NAME = "agentkit-wizard-frontdoor-handler-v2"
# Cloud networking / role identity come from the environment; no account id,
# vpc, subnet or security group is baked into the repo.
ROLE = os.environ["VEADK_FRONTEND_ROLE"]
VPC_ID = os.environ["VPC_ID"]
SUBNET_IDS = [s.strip() for s in os.environ["SUBNET_IDS"].split(",") if s.strip()]
SECURITY_GROUP_IDS = [
    s.strip() for s in os.environ.get("SECURITY_GROUP_IDS", "").split(",") if s.strip()
]


def config() -> Configuration:
    cfg = Configuration()
    cfg.ak = os.environ["VOLCENGINE_ACCESS_KEY"]
    cfg.sk = os.environ["VOLCENGINE_SECRET_KEY"]
    cfg.region = "cn-beijing"
    return cfg


def read_env_file(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key] = value
    return result


def save_state(state: dict) -> None:
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    os.chmod(tmp, 0o600)
    os.replace(tmp, STATE_PATH)


def zip_source() -> str:
    buffer = io.BytesIO()
    source = SOURCE_PATH.read_bytes()
    info = zipfile.ZipInfo("index.py")
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(info, source)
    return base64.b64encode(buffer.getvalue()).decode()


def main() -> None:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    runtime = json.loads(RUNTIME_PATH.read_text(encoding="utf-8"))
    secrets = read_env_file(SECRETS_PATH)
    faas = VEFAASApi(ApiClient(config()))
    functions = faas.list_functions(ListFunctionsRequest(page_number=1, page_size=100)).items or []
    matches = [item for item in functions if getattr(item, "name", None) == FUNCTION_NAME]
    if matches:
        function_id = matches[0].id
    else:
        envs = [
            EnvForCreateFunctionInput(key="WIZARD_UPSTREAM_ORIGIN", value=runtime["endpoint"]),
            EnvForCreateFunctionInput(key="WIZARD_UPSTREAM_AUTH_HEADER", value="Authorization"),
            EnvForCreateFunctionInput(
                key="WIZARD_UPSTREAM_AUTH_VALUE",
                value="Bearer " + secrets["NEW_RUNTIME_API_KEY"],
            ),
        ]
        request = CreateFunctionRequest(
            name=FUNCTION_NAME,
            description="Restricted browser BFF for AgentKit Wizard",
            runtime="python3.12/v1",
            source_type="zip",
            source=zip_source(),
            exclusive_mode=False,
            request_timeout=180,
            max_concurrency=100,
            memory_mb=4096,
            cpu_milli=2000,
            project_name="default",
            role=ROLE,
            envs=envs,
            vpc_config=VpcConfigForCreateFunctionInput(
                enable_vpc=True,
                vpc_id=VPC_ID,
                subnet_ids=SUBNET_IDS,
                security_group_ids=SECURITY_GROUP_IDS,
                enable_shared_internet_access=True,
            ),
            enable_apmplus=True,
        )
        function_id = faas.create_function(request).id
    state["handler_function_id"] = function_id
    save_state(state)
    faas.release(ReleaseRequest(
        function_id=function_id,
        revision_number=0,
        target_traffic_weight=100,
        rolling_step=100,
        min_instance=1,
        max_instance=2,
        description="Wizard browser front door handler",
    ))
    status = ""
    for _ in range(120):
        release = faas.get_release_status(GetReleaseStatusRequest(function_id=function_id))
        status = getattr(release, "status", "")
        if status == "done":
            break
        if status == "failed":
            raise SystemExit("handler release failed: " + str(getattr(release, "error_code", "")))
        time.sleep(5)
    if status != "done":
        raise SystemExit("handler release timed out")
    upstream_id = state["upstream_id"]
    APIGApi(ApiClient(config())).update_upstream(UpdateUpstreamRequest(
        id=upstream_id,
        name="agentkit-wizard-frontdoor",
        source_type="VeFaas",
        protocol="HTTP",
        comments="Restricted browser BFF event function",
        upstream_spec=UpstreamSpecForUpdateUpstreamInput(
            ve_faas=VeFaasForUpdateUpstreamInput(function_id=function_id),
        ),
    ))
    state.update({
        "function_id": function_id,
        "function_status": "released",
        "upstream_function_type": "python3.12",
    })
    save_state(state)
    print(json.dumps({
        "function_id": function_id,
        "release_status": status,
        "upstream_id": upstream_id,
        "updated": True,
    }))


if __name__ == "__main__":
    main()
