"""Browser authentication endpoints and protected test-identity administration."""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from server.wizard.auth import (
    clear_session_cookie,
    current_identity,
    get_store,
    set_session_cookie,
)
from server.wizard.config import get_settings


def _json_string(body: dict, key: str) -> str:
    value = body.get(key, "")
    return value.strip() if isinstance(value, str) else ""


def build_auth_router(settings) -> APIRouter:
    router = APIRouter(prefix="/api/auth", tags=["auth"])
    secure_cookie = settings.production

    @router.get("/status")
    async def status(request: Request):
        store = get_store(get_settings().data_dir)
        identity = current_identity(request)
        return {
            # The UI may explain that owner setup is pending, but setup still
            # requires the out-of-band bootstrap token.
            "needs_setup": not store.owner_bound,
            "authenticated": identity is not None,
            "username": identity["username"] if identity else None,
            "role": identity["role"] if identity else None,
        }

    @router.post("/setup")
    async def setup(request: Request):
        body = await request.json()
        password = _json_string(body, "password")
        setup_token = _json_string(body, "setup_token")
        if len(password) < 12:
            return JSONResponse({"detail": "password too short (>=12)"}, status_code=400)
        store = get_store(get_settings().data_dir)
        try:
            store.setup_owner(password, setup_token)
            session = store.issue("owner")
        except (PermissionError, ValueError) as exc:
            return JSONResponse({"detail": str(exc)}, status_code=403)
        response = JSONResponse({"ok": True, "username": "owner", "role": "owner"})
        set_session_cookie(response, session, secure_cookie)
        return response

    @router.post("/login")
    async def login(request: Request):
        store = get_store(get_settings().data_dir)
        body = await request.json()
        username = _json_string(body, "username") or "owner"
        password = _json_string(body, "password")
        client_ip = request.client.host if request.client else "unknown"
        lock_key = f"{client_ip}:{username}"
        if store.locked(lock_key):
            return JSONResponse({"detail": "too many attempts"}, status_code=429)
        if not store.verify(username, password):
            store.record_fail(lock_key)
            return JSONResponse({"detail": "invalid credentials"}, status_code=401)
        store.clear_fails(lock_key)
        session = store.issue(username)
        identity = store.identity(session) or {}
        response = JSONResponse({"ok": True, **identity})
        set_session_cookie(response, session, secure_cookie)
        return response

    @router.post("/logout")
    async def logout(request: Request):
        store = get_store(get_settings().data_dir)
        store.revoke(request.cookies.get("wizard_session"))
        response = JSONResponse({"ok": True})
        clear_session_cookie(response)
        return response

    @router.post("/admin/test-users")
    async def create_test_user(request: Request):
        body = await request.json()
        username = _json_string(body, "username")
        password = _json_string(body, "password")
        admin_token = request.headers.get("X-Wizard-Admin-Token", "")
        try:
            get_store(settings.data_dir).create_test_user(username, password, admin_token)
        except (PermissionError, ValueError) as exc:
            return JSONResponse({"detail": str(exc)}, status_code=403)
        return {"created": True, "username": username}

    @router.post("/admin/test-users/{username}/disable")
    async def disable_test_user(username: str, request: Request):
        admin_token = request.headers.get("X-Wizard-Admin-Token", "")
        try:
            get_store(settings.data_dir).disable_user(username, admin_token)
        except (PermissionError, ValueError) as exc:
            return JSONResponse({"detail": str(exc)}, status_code=403)
        return {"disabled": True, "username": username}

    return router
