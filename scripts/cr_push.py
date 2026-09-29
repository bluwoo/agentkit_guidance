#!/usr/bin/env python3
"""CR login helper. Reads AK/SK + registry identity from env.

Security:
  * The CR temporary credential (username/token) is NEVER printed and NEVER
    written to a temp file. It is piped to `docker login --password-stdin`
    over an in-memory stdin pipe only.
  * docker persists credentials under $DOCKER_CONFIG. The caller MUST point
    DOCKER_CONFIG at a task-scoped, throwaway directory and remove it when
    finished. We refuse to run against the default (~/.docker) config so a
    short-lived token cannot leak into the user's long-lived docker config.
"""
import os
import subprocess
import sys

from volcenginesdkcore import Configuration, ApiClient
from volcenginesdkcr import CRApi
from volcenginesdkcr.models.get_authorization_token_request import (
    GetAuthorizationTokenRequest,
)

REGION = os.environ.get("VOLCENGINE_REGION", "cn-beijing")
# Registry identity is supplied by the environment; no account id is baked in.
REGISTRY_ID = os.environ["CR_REGISTRY_ID"]
REGISTRY = os.environ["CR_REGISTRY"]


def main() -> int:
    config = Configuration()
    config.ak = os.environ["VOLCENGINE_ACCESS_KEY"]
    config.sk = os.environ["VOLCENGINE_SECRET_KEY"]
    config.region = REGION
    api = CRApi(ApiClient(config))

    tok = api.get_authorization_token(GetAuthorizationTokenRequest(registry=REGISTRY_ID))
    uname = getattr(tok, "username", None)
    token = getattr(tok, "token", None)
    if not uname or not token:
        raise RuntimeError("CR temporary credential response is incomplete")

    # Refuse to persist the short-lived token into the user's default docker
    # config (~/.docker/config.json). Callers must isolate DOCKER_CONFIG.
    docker_config = os.environ.get("DOCKER_CONFIG", "")
    if not docker_config:
        raise RuntimeError(
            "Set DOCKER_CONFIG to a task-scoped throwaway directory before running; "
            "it must be deleted after the push. Refusing to touch ~/.docker."
        )
    if docker_config == os.path.expanduser("~/.docker"):
        raise RuntimeError("DOCKER_CONFIG must not be ~/.docker (would persist token).")

    # Token travels only over stdin; it never appears in argv, logs, or disk.
    subprocess.run(
        ["docker", "login", REGISTRY, "--username", uname, "--password-stdin"],
        input=token,
        text=True,
        check=True,
    )
    # Do NOT print the token; registry + ok status only.
    print(f"docker login ok for {REGISTRY} (credentials held only in {docker_config})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
