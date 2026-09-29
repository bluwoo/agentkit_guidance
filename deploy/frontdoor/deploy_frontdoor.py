#!/tmp/agentkit_verify_venv/bin/python
"""Deploy the browser front door without exposing machine credentials."""
from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

import httpx
from volcenginesdkapig import (
    APIGApi,
    AuthSpecForCreateGatewayServiceInput,
    CreateGatewayServiceRequest,
    CreateUpstreamRequest,
    GetGatewayServiceRequest,
    ListGatewayServicesRequest,
    ListUpstreamsRequest,
    UpstreamSpecForCreateUpstreamInput,
    VeFaasForCreateUpstreamInput,
)
from volcenginesdkcore import ApiClient, Configuration
from volcenginesdkvefaas import (
    CreateFunctionRequest,
    EnvForCreateFunctionInput,
    GetFunctionRequest,
    GetReleaseStatusRequest,
    ListFunctionsRequest,
    ReleaseRequest,
    VEFAASApi,
    VpcConfigForCreateFunctionInput,
)

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "deployment-state" / "frontdoor.json"
SECRETS = ROOT / "deployment-state" / "e2e-secrets.env"
RUNTIME_STATE = ROOT / "deployment-state" / "runtime-v2.json"
# Image reference and networking come from the environment; no registry host,
# vpc, subnet or security group is baked into the repo.
IMAGE = os.environ["FRONTDOOR_IMAGE"]
FUNCTION_NAME = "agentkit-wizard-frontdoor"
SERVICE_NAME = "agentkit-wizard-human"
UPSTREAM_NAME = "agentkit-wizard-frontdoor"
VPC_ID = os.environ["VPC_ID"]
SUBNET_IDS = [s.strip() for s in os.environ["SUBNET_IDS"].split(",") if s.strip()]
SECURITY_GROUP_IDS = [
    s.strip() for s in os.environ.get("SECURITY_GROUP_IDS", "").split(",") if s.strip()
]


def _config() -> Configuration:
    cfg = Configuration()
    cfg.ak = os.environ.get("VOLCENGINE_ACCESS_KEY", "")
    cfg.sk = os.environ.get("VOLCENGINE_SECRET_KEY", "")
    cfg.region = "cn-beijing"
    if not cfg.ak or not cfg.sk:
        raise SystemExit("control-plane credentials unavailable")
    return cfg


def _read_secret(name: str) -> str:
    if not SECRETS.exists():
        raise SystemExit("deployment-state/secrets.env is missing")
    for raw in SECRETS.read_text(encoding="utf-8").splitlines():
        if raw.startswith(name + "="):
            value = raw.split("=", 1)[1].strip().strip("'\"")
            if value:
                return value
    raise SystemExit(f"required secret {name} is unavailable")


def _atomic_write(data: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".frontdoor.", dir=str(STATE.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.flush(); os.fsync(handle.fileno())
        os.chmod(tmp, 0o600); os.replace(tmp, STATE)
    finally:
        try: os.unlink(tmp)
        except FileNotFoundError: pass


def deploy_function(state: dict) -> str:
    api = VEFAASApi(ApiClient(_config()))
    existing = api.list_functions(ListFunctionsRequest(page_number=1, page_size=100)).items or []
    match = [item for item in existing if getattr(item, "name", None) == FUNCTION_NAME]
    if match:
        function_id = match[0].id
    else:
        runtime_key = _read_secret("NEW_RUNTIME_API_KEY")
        runtime_state = json.loads(RUNTIME_STATE.read_text(encoding="utf-8"))
        runtime_origin = runtime_state.get("endpoint", "").rstrip("/")
        if not runtime_origin.startswith("https://"):
            raise SystemExit("new Runtime endpoint is unavailable")
        envs = [
            EnvForCreateFunctionInput(key="WIZARD_UPSTREAM_ORIGIN", value=runtime_origin),
            EnvForCreateFunctionInput(key="WIZARD_UPSTREAM_AUTH_HEADER", value="Authorization"),
            EnvForCreateFunctionInput(key="WIZARD_UPSTREAM_AUTH_VALUE", value=f"Bearer {runtime_key}"),
        ]
        request = CreateFunctionRequest(
            name=FUNCTION_NAME,
            description="Restricted browser BFF for AgentKit Wizard",
            runtime="native/v1",
            source_type="image",
            source=IMAGE,
            command="uvicorn app:app --host 0.0.0.0 --port 8000",
            port=8000,
            request_timeout=180,
            initializer_sec=120,
            exclusive_mode=False,
            max_concurrency=100,
            memory_mb=4096,
            cpu_milli=2000,
            cpu_strategy="always",
            project_name="default",
            role=os.environ["VEADK_FRONTEND_ROLE"],
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
        function_id = api.create_function(request).id
    state["function_id"] = function_id
    _atomic_write(state)
    api.release(ReleaseRequest(function_id=function_id, revision_number=0, target_traffic_weight=100, rolling_step=100, min_instance=0, max_instance=2, description="AgentKit Wizard human front door"))
    for _ in range(120):
        result = api.get_release_status(GetReleaseStatusRequest(function_id=function_id))
        status = getattr(result, "status", "")
        if status == "done": break
        if status == "failed": raise SystemExit(f"front door release failed: {getattr(result, 'error_code', '')}")
        time.sleep(5)
    function = api.get_function(GetFunctionRequest(id=function_id))
    state["function_status"] = getattr(function, "status", "released") or "released"
    _atomic_write(state)
    return function_id


def deploy_apig(state: dict, function_id: str) -> tuple[str, str, str]:
    api = APIGApi(ApiClient(_config()))
    gateway_id = state["gateway_id"]
    services = api.list_gateway_services(ListGatewayServicesRequest(gateway_id=gateway_id, page_number=1, page_size=100)).items or []
    match = [item for item in services if getattr(item, "name", None) == SERVICE_NAME]
    if match:
        service_id = match[0].id
    else:
        service_id = api.create_gateway_service(CreateGatewayServiceRequest(
            service_name=SERVICE_NAME,
            gateway_id=gateway_id,
            protocol=["HTTPS"],
            auth_spec=AuthSpecForCreateGatewayServiceInput(enable=False),
            domain_type="DefaultDomain",
            comments="Human login front door for AgentKit Wizard",
        )).id
    upstreams = api.list_upstreams(ListUpstreamsRequest(gateway_id=gateway_id, page_number=1, page_size=100)).items or []
    match = [item for item in upstreams if getattr(item, "name", None) == UPSTREAM_NAME]
    if match:
        upstream_id = match[0].id
    else:
        upstream_id = api.create_upstream(CreateUpstreamRequest(
            name=UPSTREAM_NAME,
            gateway_id=gateway_id,
            source_type="VeFaas",
            protocol="HTTP",
            upstream_spec=UpstreamSpecForCreateUpstreamInput(
                ve_faas=VeFaasForCreateUpstreamInput(function_id=function_id)
            ),
            comments="Restricted browser BFF",
        )).id
    public = ""
    for _ in range(60):
        service = api.get_gateway_service(GetGatewayServiceRequest(id=service_id)).gateway_service
        for domain in getattr(service, "domains", None) or []:
            url = getattr(domain, "domain", "") or ""
            if url.startswith("https://"): public = url
        if getattr(service, "status", "") in ("Running", "Ready") and public: break
        time.sleep(3)
    state.update({"service_id": service_id, "upstream_id": upstream_id, "public_endpoint": public})
    _atomic_write(state)
    return service_id, upstream_id, public


def _apig_call(action: str, body: dict) -> dict:
    from volcengine.auth.SignerV4 import SignerV4
    from volcengine.base.Request import Request
    from volcengine.Credentials import Credentials

    raw = json.dumps(body).encode()
    request = Request()
    request.set_method("POST")
    request.set_host("open.volcengineapi.com")
    request.set_path("/")
    request.set_schema("https")
    request.set_query({"Action": action, "Version": "2022-11-12"})
    request.set_headers({"Content-Type": "application/json; charset=utf-8"})
    request.body = raw
    SignerV4.sign(request, Credentials(
        os.environ["VOLCENGINE_ACCESS_KEY"], os.environ["VOLCENGINE_SECRET_KEY"],
        "apig", "cn-beijing",
    ))
    response = httpx.post(
        f"https://open.volcengineapi.com/?Action={action}&Version=2022-11-12",
        headers=dict(request.headers), content=raw, timeout=30,
    )
    result = response.json()
    error = (result.get("ResponseMetadata") or {}).get("Error")
    if error:
        raise SystemExit(f"{action} failed: {error.get('Code')} {error.get('Message')}")
    return result.get("Result", {})


def ensure_route(state: dict, service_id: str, upstream_id: str) -> str:
    route_id = state.get("route_id")
    if not route_id:
        listed = _apig_call("ListRoutes", {
            "GatewayId": state["gateway_id"], "ServiceId": service_id,
            "PageNumber": 1, "PageSize": 100,
        })
        matches = [item for item in listed.get("Items", []) if item.get("Name") == "agentkit-wizard-human-root"]
        if matches:
            route_id = matches[0]["Id"]
        else:
            route_id = _apig_call("CreateRoute", {
                "Name": "agentkit-wizard-human-root",
                "ServiceId": service_id,
                "MatchRule": {
                    "Path": {"MatchType": "Prefix", "MatchContent": "/"},
                    "Method": ["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"],
                },
                "UpstreamList": [{"Weight": 100, "UpstreamId": upstream_id}],
                "Enable": True, "Priority": 100, "Scene": "Upstream",
            })["Id"]
        state["route_id"] = route_id
        _atomic_write(state)
    for _ in range(60):
        if _apig_call("CheckRouteReady", {"Id": route_id}).get("Ready") is True:
            state["route_status"] = "Ready"
            _atomic_write(state)
            return route_id
        time.sleep(3)
    raise SystemExit("front door route did not become Ready")


def main() -> None:
    state = json.loads(STATE.read_text(encoding="utf-8"))
    function_id = deploy_function(state)
    service_id, upstream_id, public = deploy_apig(state, function_id)
    route_id = ensure_route(state, service_id, upstream_id)
    print(json.dumps({"function_id": function_id, "service_id": service_id, "upstream_id": upstream_id, "route_id": route_id, "public_endpoint": public}, ensure_ascii=False))


if __name__ == "__main__":
    main()
