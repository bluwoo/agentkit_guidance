#!/usr/bin/env python3
"""AgentKit control-plane OpenAPI helper (V4 signed)."""
import os, sys, json, requests
from volcenginesdkcore.signv4 import SignerV4

HOST = "open.volcengineapi.com"
REGION = "cn-beijing"
SERVICE = "agentkit"
VERSION = "2025-10-30"

def call(action, body: dict):
    ak = os.environ["VOLCENGINE_ACCESS_KEY"]
    sk = os.environ["VOLCENGINE_SECRET_KEY"]
    body_str = json.dumps(body, separators=(",", ":"))
    headers = {
        "Host": HOST,
        "Content-Type": "application/json",
    }
    query = {"Action": action, "Version": VERSION}
    SignerV4.sign("/", "POST", headers, body_str, {}, query, ak, sk, REGION, SERVICE)
    url = f"https://{HOST}/"
    r = requests.post(url, params=query, headers=headers, data=body_str, timeout=30)
    try:
        return r.status_code, r.json()
    except Exception:
        return r.status_code, {"_raw": r.text}

if __name__ == "__main__":
    action = sys.argv[1]
    body = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    code, resp = call(action, body)
    print(json.dumps({"http": code, "resp": resp}, ensure_ascii=False, indent=2))
