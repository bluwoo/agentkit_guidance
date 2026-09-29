#!/tmp/agentkit_verify_venv/bin/python
"""Cloud deploy helper for the AgentKit Wizard (cn-beijing / default project).

HOW TO RUN
    This script MUST be run with the project venv that has httpx + volcengine
    installed:

        /tmp/agentkit_verify_venv/bin/python deploy/cloud_deploy.py --check

    (The shebang above already points at that interpreter, so
    `./deploy/cloud_deploy.py --check` also works.) If httpx is missing you get a
    clear error telling you to use that interpreter instead of the system python.

CREDENTIALS
    Control-plane calls use the long-term AK/SK already in the environment
    (VOLCENGINE_ACCESS_KEY / VOLCENGINE_SECRET_KEY). Those creds are used ONLY
    for the AgentKit control plane and the read-only CR probe. They are NEVER
    copied into the container Envs -- the container runs with the Runtime's own
    service role and must never see the control-plane AK/SK.

KEYAUTH RESPONSIBILITY
    The in-bound KeyAuth (header API key) is verified by the AgentKit platform
    gateway. The container application (AgentkitSimpleApp) does NOT re-verify an
    inbound key, so we intentionally do NOT set RUNTIME_API_KEY (or any key
    value) in the container Envs, and the app does not self-check it.
    AuthorizerConfiguration.KeyAuth on CreateRuntime only declares the header
    NAME that the gateway should expect.

OFFICIAL FIELD CONTRACT (AgentKit, Version 2025-10-30,
host agentkit.cn-beijing.volcengineapi.com; verified in
docs/volcengine-official/shard1-results.md):
  * CreateRuntime required: Name, ArtifactType="image", ArtifactUrl, RoleName.
    AuthorizerConfiguration is one of KeyAuth{ApiKeyLocation=Header,
    ApiKeyName} or CustomJwtAuthorizer{...}. Envs.N.Key is required (Value
    optional). NetworkConfiguration is one of {EnablePublicNetwork:true} or
    {EnablePrivateNetwork:true,VpcId,SubnetIds}. ClientToken <=64 ASCII.
    There is NO "Port" field.
  * GetRuntime.Status enum: Creating / UnReleased / Releasing / Ready / Error
    / Updating / Deleting / Deleted. A freshly created runtime may need
    ReleaseRuntime(RuntimeId, VersionNumber=0) before it serves traffic.
  * MCP is a SEPARATE service. CreateMCPService fields verified in
    docs/volcengine-official/shard2-results.md (section 56); see
    build_mcp_payload() and deploy/mcp_payload.contract.json.

WHAT THIS SCRIPT DOES NOT DO
  * It never hard-codes a RuntimeId or RoleName. --check dynamically samples the
    first existing runtime to learn the live shape.
  * --apply does NOT call CreateRuntime yet (the image is not pushed). It only
    builds the payload and writes the two contract JSON files.
  * It never prints ApiKey / Env values / AccessToken / AK / SK.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import uuid

# --- httpx guard ---------------------------------------------------------- #
# The system python3 may not have httpx. Fail loudly with the exact fix.
try:
    import httpx
except ImportError:  # pragma: no cover - exercised only on wrong interpreter
    sys.stderr.write(
        "\n[cloud_deploy] FATAL: import httpx failed.\n"
        "This script must run with the project venv that has httpx installed:\n"
        "    /tmp/agentkit_verify_venv/bin/python deploy/cloud_deploy.py --check\n"
        "Current interpreter: " + sys.executable + "\n\n"
    )
    raise SystemExit(2)

API_HOST = "agentkit.cn-beijing.volcengineapi.com"
SERVICE = "agentkit"
REGION = "cn-beijing"
VERSION = "2025-10-30"
PROJECT = "default"

# Envs that are copied from the ambient environment into the container, by an
# explicit allowlist. Anything NOT in this list (including VOLCENGINE_ACCESS_KEY
# / VOLCENGINE_SECRET_KEY, which are control-plane long-term creds) is never
# propagated into the container.
ENV_ALLOWLIST = (
    "WIZARD_LLM_BASE_URL",
    "WIZARD_LLM_API_KEY",
    "WIZARD_LLM_MODEL",
    "WIZARD_ALLOWED_ORIGINS",
    "OTEL_EXPORTER_OTLP_ENDPOINT",
)
# Env values that must be redacted on print / in the contract dump.
SENSITIVE_ENV_KEYS = frozenset({"WIZARD_LLM_API_KEY"})

# Statuses that mean "still provisioning"; anything else terminal/unknown is
# treated as failure unless it is Ready.
_RUNNING = {"Creating", "UnReleased", "Releasing", "Updating"}
_FAILED = {"Error", "Deleting", "Deleted"}


# --------------------------------------------------------------------------- #
# Signed control-plane calls (AgentKit)
# --------------------------------------------------------------------------- #
def _sign_post(action: str, body: dict) -> tuple[str, dict, bytes]:
    from volcengine.auth.SignerV4 import SignerV4
    from volcengine.base.Request import Request
    from volcengine.Credentials import Credentials

    ak = os.environ.get("VOLCENGINE_ACCESS_KEY", "")
    sk = os.environ.get("VOLCENGINE_SECRET_KEY", "")
    if not ak or not sk:
        raise SystemExit("VOLCENGINE_ACCESS_KEY / VOLCENGINE_SECRET_KEY not set")
    raw = json.dumps(body).encode()
    req = Request()
    req.set_method("POST")
    req.set_host(API_HOST)
    req.set_path("/")
    req.set_schema("https")
    req.set_query({"Action": action, "Version": VERSION})
    req.set_headers({"Content-Type": "application/json; charset=utf-8"})
    req.body = raw
    SignerV4.sign(req, Credentials(ak, sk, SERVICE, REGION))
    url = f"https://{API_HOST}/?Action={action}&Version={VERSION}"
    return url, dict(req.headers), raw


def _call(action: str, body: dict) -> dict:
    url, headers, raw = _sign_post(action, body)
    r = httpx.post(url, headers=headers, content=raw, timeout=20.0)
    try:
        return r.json()
    except ValueError:
        return {"_http_status": r.status_code, "_body": r.text[:500]}


# --------------------------------------------------------------------------- #
# Read-only inspection (--check)
# --------------------------------------------------------------------------- #
def _summarize_authorizer(ac: dict) -> str:
    """Describe the authorizer type WITHOUT leaking secrets.

    KeyAuth -> report the header NAME (ApiKeyName), never a token.
    CustomJwtAuthorizer -> report the DiscoveryUrl, never AccessToken.
    """
    if not isinstance(ac, dict):
        return "<none>"
    key_auth = ac.get("KeyAuth")
    if isinstance(key_auth, dict) and key_auth:
        name = key_auth.get("ApiKeyName", "<unset>")
        where = key_auth.get("ApiKeyLocation", "?")
        return f"KeyAuth (location={where}, header-name={name})"
    jwt = ac.get("CustomJwtAuthorizer") or ac.get("CustomJwt")
    if isinstance(jwt, dict) and jwt:
        disc = jwt.get("DiscoveryUrl", "<unset>")
        return f"CustomJwtAuthorizer (DiscoveryUrl={disc})"
    return "<none>"


def _summarize_network(ncs) -> str:
    if not isinstance(ncs, list):
        return "<none>"
    bits = []
    for nc in ncs:
        if not isinstance(nc, dict):
            continue
        ntype = nc.get("NetworkType", "?")
        # Only the type; never the VpcId/SubnetIds/Endpoint values.
        bits.append(ntype)
    return ",".join(bits) if bits else "<none>"


def _sample_runtime_shape() -> dict | None:
    """ListRuntimes -> take the first runtime -> GetRuntime its shape.

    Returns a small dict of NON-sensitive shape attributes, or None if it
    could not be sampled. Never prints or returns Env values / ApiKey.
    """
    res = _call("ListRuntimes", {"ProjectName": PROJECT, "PageSize": 5})
    rms = res.get("Result", {}).get("AgentKitRuntimes", [])
    if not rms:
        return None
    sample_id = rms[0].get("RuntimeId")
    g = _call("GetRuntime", {"RuntimeId": sample_id})
    r = g.get("Result", g)
    if "RuntimeId" not in r:
        return None
    return {
        "runtime_id": sample_id,
        "status": r.get("Status"),
        "role_name": r.get("RoleName"),
        "gateway_mode": r.get("GatewayMode"),
        "authorizer": _summarize_authorizer(r.get("AuthorizerConfiguration", {})),
        "network": _summarize_network(r.get("NetworkConfigurations")),
    }


def check() -> int:
    rc = 0
    print("== control-plane creds (read-only ListRuntimes) ==")
    try:
        res = _call("ListRuntimes", {"ProjectName": PROJECT, "PageSize": 5})
    except Exception as e:
        print("  FAIL:", type(e).__name__, e)
        return 1
    rms = res.get("Result", {}).get("AgentKitRuntimes", [])
    print(f"  OK, existing runtimes in {PROJECT}/{REGION}: {len(rms)}")

    print("== dynamic sample (first runtime -> GetRuntime shape) ==")
    sample = None
    try:
        sample = _sample_runtime_shape()
    except Exception as e:
        print("  FAIL sampling runtime:", type(e).__name__, e)
        rc = 1
    if sample is None:
        print("  no existing runtime to sample (or GetRuntime failed);")
        print("  RoleName for --apply must be supplied via --role-name.")
        rc = 1
    else:
        # NOTE: runtime_id is a resource ID, not a secret; we print it only to
        # show WHICH runtime was sampled, never its Envs/ApiKey.
        print(f"  sampled RuntimeId : {sample['runtime_id']}")
        print(f"  Status            : {sample['status']}")
        print(f"  RoleName          : {sample['role_name']}  (use --role-name=<that> on --apply)")
        print(f"  GatewayMode       : {sample['gateway_mode']}")
        print(f"  Authorizer        : {sample['authorizer']}")
        print(f"  Network           : {sample['network']}")
        print("  (Envs / AccessToken / ApiKey intentionally NOT printed)")

    print("== docker daemon ==")
    if shutil.which("docker") is None:
        print("  docker CLI not found")
        rc = 1
    else:
        d = subprocess.run(["docker", "info"], capture_output=True, text=True, check=False)
        if d.returncode != 0:
            print("  BLOCKED: docker daemon not running:",
                  (d.stderr or d.stdout).strip().splitlines()[0])
            print("  -> Start Docker Desktop, then re-run. Image not built/pushed.")
            if rc == 0:
                rc = 2
        else:
            print("  OK docker daemon up")

    print("== CR registry endpoint (read-only CR OpenAPI) ==")
    print("  ", probe_cr_registry())

    print("== MCP ==")
    print("  CreateMCPService fields verified from")
    print("  docs/volcengine-official/shard2-results.md section 56;")
    print("  see deploy/mcp_payload.contract.json and build_mcp_payload().")

    print("\nCHECK", "PASSED" if rc == 0 else "INCOMPLETE (see above)")
    return rc


# --------------------------------------------------------------------------- #
# CR read-only probe (volcenginesdkcr, V4 signed)
# --------------------------------------------------------------------------- #
def probe_cr_registry() -> str:
    """Read-only lookup of the project CR registry via the official CR SDK.

    The registry name is supplied by ``CR_REGISTRY_NAME``. We use
    ListRegistries to find it, then ListNamespaces to enumerate its namespaces
    and ListDomains for its login endpoint. We never print robot accounts /
    passwords / robot tokens. If the SDK is unavailable or the registry is absent
    we report "unverified" rather than substituting another registry.
    """
    ak = os.environ.get("VOLCENGINE_ACCESS_KEY", "")
    sk = os.environ.get("VOLCENGINE_SECRET_KEY", "")
    if not ak or not sk:
        return "unverified (VOLCENGINE_ACCESS_KEY/SECRET_KEY not set)"
    registry_name = os.environ.get("CR_REGISTRY_NAME", "")
    if not registry_name:
        return "unverified (CR_REGISTRY_NAME not set)"
    try:
        from volcenginesdkcore import ApiClient, Configuration
        from volcenginesdkcr import CRApi
        from volcenginesdkcr.models import (
            ListDomainsRequest,
            ListNamespacesRequest,
            ListRegistriesRequest,
        )
    except Exception as e:  # pragma: no cover - depends on venv
        return f"unverified (volcenginesdkcr import failed: {e})"

    try:
        cfg = Configuration()
        cfg.ak = ak
        cfg.sk = sk
        cfg.region = REGION
        api = CRApi(ApiClient(cfg))
        regs = api.list_registries(ListRegistriesRequest()).items or []
        match = [r for r in regs if getattr(r, "name", None) == registry_name]
        if not match:
            names = [getattr(r, "name", "?") for r in regs]
            return (
                f"unverified: no registry named {registry_name!r} among "
                f"{names}; do NOT substitute another CR URL"
            )
        reg = match[0]
        # namespaces
        ns = api.list_namespaces(
            ListNamespacesRequest(registry=reg.name, page_number=1, page_size=50)
        )
        ns_names = [getattr(n, "name", "?") for n in (ns.items or [])]
        # login domain (read-only)
        dom = api.list_domains(ListDomainsRequest(registry=reg.name))
        endpoint = None
        for d in (dom.items or []):
            if getattr(d, "default", False) or getattr(d, "type", "") == "System":
                endpoint = getattr(d, "domain", None)
                break
        if endpoint is None and dom.items:
            endpoint = getattr(dom.items[0], "domain", None)
        return (
            f"verified: registry={reg.name} project={reg.project} "
            f"endpoint={endpoint or '?'} namespaces={ns_names}"
        )
    except Exception as e:
        return f"unverified ({type(e).__name__}: {e}); do NOT substitute another CR URL"


# --------------------------------------------------------------------------- #
# Envs: ambient -> allowlist -> container, with redaction
# --------------------------------------------------------------------------- #
def _collect_envs() -> list[dict]:
    """Map allowed ambient env vars into CreateRuntime Envs.

    - WIZARD_MODE is forced to "production" (fail-closed at runtime).
    - Only keys in ENV_ALLOWLIST are pulled from os.environ.
    - VOLCENGINE_ACCESS_KEY / VOLCENGINE_SECRET_KEY are NEVER propagated.
    - RUNTIME_API_KEY is intentionally absent: inbound KeyAuth is the platform
      gateway's job; the container app does not self-verify.
    - Static, non-sensitive app paths are added explicitly below.
    """
    envs: list[dict] = [
        {"Key": "WIZARD_MODE", "Value": "production"},
        {"Key": "SERVE_FRONTEND_DIST", "Value": "/app/web/dist"},
        {"Key": "WIZARD_DATA_DIR", "Value": "/app/wizard_data"},
    ]
    for key in ENV_ALLOWLIST:
        if key == "WIZARD_MODE":
            continue  # already forced above
        val = os.environ.get(key)
        if val:
            envs.append({"Key": key, "Value": val})
    return envs


def _redact_envs(envs: list[dict]) -> list[dict]:
    out = []
    for e in envs:
        if e.get("Key") in SENSITIVE_ENV_KEYS:
            out.append({"Key": e["Key"], "Value": "<redacted>"})
        else:
            out.append(e)
    return out


# --------------------------------------------------------------------------- #
# CreateRuntime payload (official fields)
# --------------------------------------------------------------------------- #
def build_runtime_payload(
    image: str,
    name: str,
    *,
    role_name: str,
    auth_header_name: str = "X-Api-Key",
    cpu_milli: int = 2000,
    memory_mb: int = 4096,
    max_instance: int = 3,
) -> dict:
    """Build the CreateRuntime request body strictly per the 2025-10-30 contract.

    There is intentionally NO "Port" field. RoleName is required and MUST be
    passed in by the caller (no hard-coded default). KeyAuth carries only the
    header location + name (the secret key value is enforced by the platform
    gateway, never baked into this payload or into Envs).
    """
    if not role_name:
        raise SystemExit("--role-name is required (no hard-coded default); "
                         "run --check to discover a suitable RoleName.")
    client_token = uuid.uuid4().hex[:64]  # <=64 ASCII
    return {
        "ProjectName": PROJECT,
        "Name": name,
        "Description": "AgentKit Wizard (Hermes 0.21.3 + FastAPI shim)",
        "ArtifactType": "image",
        "ArtifactUrl": image,
        "RoleName": role_name,
        "AuthorizerConfiguration": {
            "KeyAuth": {
                "ApiKeyLocation": "Header",
                "ApiKeyName": auth_header_name,
            }
        },
        "Envs": _collect_envs(),
        "NetworkConfiguration": {"EnablePublicNetwork": True},
        "ClientToken": client_token,
        "CpuMilli": cpu_milli,
        "MemoryMb": memory_mb,
        "MaxInstance": max_instance,
        "ApmplusEnable": True,
        "Tags": [
            {"Key": "managed_by", "Value": "agentkit-wizard", "Type": "custom"},
            {"Key": "hermes_version", "Value": "0.21.3", "Type": "custom"},
        ],
    }


# --------------------------------------------------------------------------- #
# CreateMCPService payload (fields verified in shard2-results.md section 56)
# --------------------------------------------------------------------------- #
def build_mcp_payload(
    *,
    name: str,
    path: str,
    role_name: str,
    backend_type: str = "CustomPublic",
    gateway_mode: str = "Shared",
) -> dict:
    """Build a CreateMCPService request skeleton.

    Source: docs/volcengine-official/shard2-results.md section 56
    (https://docs.volcengine.com/docs/AgentKit/CreateMCPService-CreatesMCPservice).

    Verified required fields: BackendType, BackendConfiguration (one of
    FunctionConfiguration / CustomConfiguration / EcsConfiguration /
    VkeConfiguration / CustomMcpConfiguration), Name (4-64 chars), Path,
    ProtocolType (HTTP | MCP). Optional: ProjectName, RoleName,
    ProtocolConfiguration.HttpApiConfiguration{Type=Swagger,
    Configuration=base64 swagger}, InboundAuthorizerConfiguration{AuthorizerType,
    Authorizer{KeyAuth|CustomJwtAuthorizer}},
    OutboundAuthorizerConfiguration{AuthorizerType, Authorizer{...}},
    NetworkConfiguration{EnablePublicNetwork|EnablePrivateNetwork},
    ClientToken (<=64 ASCII), Tags, GatewayMode (Shared|Exclusive;
    GatewayInstanceId required when Exclusive), BackendAccessType (Public|Private).

    Lifecycle:
      1. CreateMCPService -> MCPServiceId
      2. GetMCPService / ListMCPServices until Status == Ready
      3. CreateMCPToolset(MCPServices=[{MCPServiceId, IsAllTools}]) -> MCPToolsetId
      4. CreateRuntime / UpdateRuntime with MCPToolsetId=<that> to bind tools.
    """
    client_token = uuid.uuid4().hex[:64]
    return {
        "_doc_source": (
            "docs/volcengine-official/shard2-results.md section 56 "
            "(CreateMCPService)"
        ),
        "ProjectName": PROJECT,
        "Name": name,
        "Path": path,
        "RoleName": role_name,
        # BackendType is one of Function/Domain/ECS/VKE/CustomPublic/CustomPrivate.
        # For the wizard's own HTTP service we expect CustomPublic + a
        # CustomConfiguration{Domain,Port,ProtocolType,TlsSettings}; the exact
        # Domain/Port are filled in once the Runtime endpoint is known.
        "BackendType": backend_type,
        "BackendConfiguration": {
            "_note": (
                "exactly one sub-config required by BackendType; "
                "CustomConfiguration{Domain,Port,ProtocolType,TlsSettings} "
                "for a public HTTP backend"
            ),
            "CustomConfiguration": {
                "Domain": "<runtime-endpoint>.volcengineapi.com",
                "Port": 443,
                "ProtocolType": "HTTPS",
                "TlsSettings": {"TlsMode": "SIMPLE"},
            },
        },
        # ProtocolType: HTTP = HTTP-to-MCP conversion, MCP = direct MCP.
        "ProtocolType": "HTTP",
        "ProtocolConfiguration": {
            "HttpApiConfiguration": {
                "Type": "Swagger",
                "Configuration": "<base64-encoded Swagger JSON>",
            }
        },
        # In-bound auth on the MCP gateway side; the container itself does not
        # re-verify (same KeyAuth responsibility split as the Runtime).
        "InboundAuthorizerConfiguration": {
            "AuthorizerType": "ApiKey",
            "Authorizer": {
                "KeyAuth": {
                    "ApiKeyLocation": "Header",
                    "ApiKeyName": "X-Api-Key",
                    "_pending": "ApiKeys.N.Name/Key filled out-of-band; never hard-coded here",
                }
            },
        },
        "OutboundAuthorizerConfiguration": {
            "_pending": "not needed for a public backend; omit until official use",
        },
        "NetworkConfiguration": {"EnablePublicNetwork": True},
        "GatewayMode": gateway_mode,
        "ClientToken": client_token,
        "Tags": [
            {"Key": "managed_by", "Value": "agentkit-wizard", "Type": "custom"},
        ],
    }


# --------------------------------------------------------------------------- #
# Contract writers (--apply does NOT create; it only writes the contracts)
# --------------------------------------------------------------------------- #
def _deploy_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def write_contracts(runtime_payload: dict, mcp_payload: dict) -> None:
    runtime_path = os.path.join(_deploy_dir(), "deploy_payload.contract.json")
    mcp_path = os.path.join(_deploy_dir(), "mcp_payload.contract.json")
    with open(runtime_path, "w", encoding="utf-8") as f:
        json.dump(_redact_envs_payload(runtime_payload), f, ensure_ascii=False, indent=2)
    with open(mcp_path, "w", encoding="utf-8") as f:
        json.dump(mcp_payload, f, ensure_ascii=False, indent=2)
    print("wrote", runtime_path)
    print("wrote", mcp_path)


def _redact_envs_payload(payload: dict) -> dict:
    p = dict(payload)
    if isinstance(p.get("Envs"), list):
        p["Envs"] = _redact_envs(p["Envs"])
    return p


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description="AgentKit Runtime control-plane helper")
    ap.add_argument("--check", action="store_true",
                    help="read-only preflight (creds, dynamic runtime shape, CR registry)")
    ap.add_argument("--apply", action="store_true",
                    help="build payloads and write contract JSON (does NOT call CreateRuntime)")
    ap.add_argument("--print-payload", action="store_true",
                    help="print the redacted CreateRuntime payload and exit (no API call)")
    ap.add_argument("--image", help="CR image:tag, e.g. <REGISTRY>/agentkit/agentkit-wizard:0.21.3")
    ap.add_argument("--name", default="agentkit-wizard")
    ap.add_argument("--role-name", default=None,
                    help="Runtime service role name; REQUIRED for --apply/--print-payload "
                         "(no hard-coded default; discover via --check)")
    ap.add_argument("--auth-header-name", default="X-Api-Key")
    args = ap.parse_args()

    if args.check:
        return check()

    if args.print_payload:
        if not args.image:
            print("--image required for --print-payload")
            return 1
        if not args.role_name:
            print("--role-name required for --print-payload "
                  "(run --check to discover the RoleName; no hard-coded default)")
            return 1
        payload = build_runtime_payload(
            args.image, args.name,
            role_name=args.role_name,
            auth_header_name=args.auth_header_name,
        )
        print(json.dumps(_redact_envs_payload(payload), ensure_ascii=False, indent=2))
        return 0

    if args.apply:
        if not args.image:
            print("--image required for --apply")
            return 1
        if not args.role_name:
            print("--role-name required for --apply "
                  "(no hard-coded default; run --check to discover a RoleName)")
            return 1
        runtime_payload = build_runtime_payload(
            args.image, args.name,
            role_name=args.role_name,
            auth_header_name=args.auth_header_name,
        )
        mcp_payload = build_mcp_payload(
            name=args.name + "-mcp",
            path="/" + args.name + "/mcp",
            role_name=args.role_name,
        )
        # IMPORTANT: --apply does NOT call CreateRuntime yet (image not pushed).
        # It only validates the args and writes the two contract files.
        write_contracts(runtime_payload, mcp_payload)
        print("--apply completed WITHOUT calling CreateRuntime (image not pushed).")
        return 0

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())


# === security hardening (rotation incident) ===
_REDACT_KEYS = {
    "apikey", "api_key", "accesstoken", "access_token", "secret", "secretkey",
    "secret_key", "password", "credential", "token", "privatekey", "private_key",
    "authorization",
}


def redact(obj):
    """Recursively replace secret-like values with <redacted>. Safe to print."""
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if str(k).lower() in _REDACT_KEYS and isinstance(v, str):
                out[k] = "<redacted>"
            else:
                out[k] = redact(v)
        return out
    if isinstance(obj, list):
        return [redact(x) for x in obj]
    return obj


def safe_dump(obj) -> str:
    return json.dumps(redact(obj), ensure_ascii=False, default=str)
