"""Component: **agentkit-runtime** (hosted Agent service).

Per the Skill: Runtime publishes a container image as a callable online service;
region ``cn-beijing``; two control-plane / tool-execution domains; invocation is
``POST /invoke`` with Header user_id/session_id and Body {"prompt": ...}.

This Harness models a Runtime as an immutable descriptor and records the OpenAPI
surface. Actually creating / releasing / invoking a cloud Runtime needs AK/SK and a
CR image — that is a documented CloudBoundary; we never deploy.
"""
from __future__ import annotations

import dataclasses

REGION = "cn-beijing"
CONTROL_PLANE_ENDPOINT = "agentkit.cn-beijing.volcengineapi.com"   # OpenAPI control plane
TOOL_EXEC_ENDPOINT = "agentkit.cn-beijing.volces.com"             # InvokeTool/AsyncExecCommand

# Runtime OpenAPI surface (Version 2025-10-30) — recorded, not invoked.
RUNTIME_APIS = [
    "CreateRuntime", "UpdateRuntime", "ReleaseRuntime", "DeleteRuntime",
    "GetRuntime", "ListRuntimes", "GetRuntimeVersion", "ListRuntimeVersions",
    "GetRuntimeInstanceLogs", "ListRuntimeInstances", "UpdateRuntimeRelease",
    "AbortRuntimeRelease", "GetRuntimeReleaseStatus", "ListRuntimeReleaseRecords",
    "GetRuntimeWebshellEndpoint",
]


@dataclasses.dataclass
class RuntimeDescriptor:
    name: str
    image: str
    model: str = "doubao-seed-2-1-pro-260628"
    endpoint: str = ""          # returned by GetRuntime.Endpoint in the cloud
    enable_observability: bool = True
    enable_guardrails: bool = False
    region: str = REGION

    def invoke_curl(self) -> str:
        return (
            f"curl -X POST https://{self.endpoint or '<runtime-domain>'}/invoke "
            f"-H 'Content-Type: application/json' -H 'user_id: test-user' "
            f"-H 'session_id: test-session' -d '{{\"prompt\": \"hello\"}}'"
        )


class CloudRuntimeClient:
    """Documents where the real cloud Runtime attaches; never calls it."""

    def __init__(self, desc: RuntimeDescriptor):
        self.desc = desc

    def create_or_release(self):
        from .contract import CloudBoundary
        raise CloudBoundary(
            "CreateRuntime/ReleaseRuntime need VOLCENGINE AK/SK + a CR image; "
            "Harness stops here (no cloud write)."
        )
