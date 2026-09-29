#!/usr/bin/env python3
"""Shared helpers for snapshot lifecycle verification."""
import os
import sys
import json
import time
import requests

# The signed OpenAPI helper lives in a per-run work directory; point to it via
# OPENAPI_WORKDIR (no machine-specific absolute path is baked in).
_workdir = os.environ.get("OPENAPI_WORKDIR")
if _workdir:
    sys.path.insert(0, _workdir)
from openapi import call  # noqa: E402

# Tool id is supplied by the environment; no real tool id is baked in.
TOOL_ID = os.environ["SANDBOX_TOOL_ID"]

def get_tool():
    code, resp = call("GetTool", {"ToolId": TOOL_ID})
    return code, resp

def wait_tool_ready(timeout=180):
    t0 = time.time()
    while time.time() - t0 < timeout:
        code, resp = get_tool()
        r = resp.get("Result") or {}
        st = r.get("Status")
        print(f"  [wait_tool] status={st} enableSnapshot={r.get('EnableSnapshot')} project={r.get('ProjectName')}")
        if st == "Ready":
            return r
        if st in ("Failed", "Error"):
            print("  TOOL FAILED:", json.dumps(resp, ensure_ascii=False))
            return r
        time.sleep(5)
    return None

def create_session(user_session_id=None):
    body = {"ToolId": TOOL_ID}
    if user_session_id:
        body["UserSessionId"] = user_session_id
    return call("CreateSession", body)

def get_session(sid):
    return call("GetSession", {"ToolId": TOOL_ID, "SessionId": sid})

def list_sessions():
    return call("ListSessions", {"ToolId": TOOL_ID, "MaxResults": 100})

def wait_session_ready(sid, timeout=180):
    t0 = time.time()
    while time.time() - t0 < timeout:
        code, resp = get_session(sid)
        r = resp.get("Result") or {}
        st = r.get("Status")
        ep = r.get("Endpoint")
        print(f"  [wait_session] sid={sid} status={st}")
        if st in ("Running", "Ready") and ep:
            return r
        time.sleep(4)
    return None

def bash_exec(endpoint, command, timeout=60):
    """POST a command into the sandbox session's bash/exec endpoint."""
    from urllib.parse import urlsplit, urlunsplit
    parts = urlsplit(endpoint.strip())
    p = parts.path.rstrip("/")
    exec_path = f"{p}/v1/bash/exec" if p else "/v1/bash/exec"
    url = urlunsplit((parts.scheme, parts.netloc, exec_path, parts.query, parts.fragment))
    body = {"command": command, "timeout": timeout, "hard_timeout": timeout + 15}
    r = requests.post(url, json=body, timeout=timeout + 30)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, {"_raw": r.text}

def create_snapshot(sid):
    return call("CreateSessionSnapshot", {"ToolId": TOOL_ID, "SessionId": sid})

def get_snapshot(snap_id):
    return call("GetSessionSnapshot", {"ToolId": TOOL_ID, "SnapshotId": snap_id})

def wait_snapshot_ready(snap_id, timeout=300):
    t0 = time.time()
    while time.time() - t0 < timeout:
        code, resp = get_snapshot(snap_id)
        sn = (resp.get("Result") or {}).get("Snapshot") or {}
        st = sn.get("Status")
        print(f"  [wait_snapshot] snap={snap_id} status={st}")
        if st == "Ready":
            return sn
        if st in ("Failed", "Invalid", "Error"):
            return sn
        time.sleep(6)
    return None

def delete_session(sid):
    return call("DeleteSession", {"ToolId": TOOL_ID, "SessionId": sid})

def restore_from_snapshot(snap_id):
    return call("ResumeSessionFromSnapshot", {"ToolId": TOOL_ID, "SnapshotId": snap_id, "CreateNewInstance": True})

def delete_snapshot(snap_id):
    return call("DeleteSessionSnapshot", {"ToolId": TOOL_ID, "SnapshotId": snap_id})

def delete_tool():
    return call("DeleteTool", {"ToolId": TOOL_ID})

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "wait_tool":
        r = wait_tool_ready()
        print(json.dumps(r, ensure_ascii=False, indent=2))
