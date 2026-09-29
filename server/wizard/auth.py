"""Browser authentication with revocable server-side sessions.

The browser never receives the AgentKit Runtime gateway key.  The public front
Door forwards only an allowlisted set of paths to this application and adds the
machine credential server-side.

Identity model
--------------
* ``owner`` is created only with ``WIZARD_OWNER_SETUP_TOKEN``.  There is no
  public registration path.
* Temporary test users are created/disabled only by the admin endpoints, which
  require that same bootstrap token and are deliberately not exposed by the
  front door.
* Sessions are opaque, signed IDs backed by persisted server-side records.
  Logout removes the session.  Disabling a user increments its epoch and
  removes all its sessions, so captured cookies cannot be replayed.
* Corrupt state fails closed.  Writes use fsync + atomic replace.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import tempfile
import threading
import time
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import Request
from fastapi.responses import JSONResponse, Response

from server.wizard.config import get_settings

COOKIE_NAME = "wizard_session"
SESSION_TTL_SECONDS = 12 * 3600
FAIL_WINDOW = 60
FAIL_MAX = 5
STATE_VERSION = 2


def _scrypt(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)


class AuthErrorState(RuntimeError):
    """The persisted authentication state cannot be trusted."""


class UserStore:
    """Atomic local identity store for the single-instance Wizard service."""

    def __init__(self, data_dir: str, setup_token: str = "") -> None:
        self.path = Path(data_dir) / "auth.json"
        self.setup_token = setup_token
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._state: dict = {"version": STATE_VERSION, "users": {}, "sessions": {}}
        self._fails: dict[str, list[float]] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise TypeError("root is not an object")
            # One-time migration from the initial owner-only format.
            if "hash" in data:
                data = {
                    "version": STATE_VERSION,
                    "secret": data.get("secret") or secrets.token_hex(32),
                    "users": {
                        "owner": {
                            "salt": data["salt"],
                            "hash": data["hash"],
                            "role": "owner",
                            "enabled": True,
                            "epoch": int(data.get("epoch", 0)),
                        }
                    },
                    "sessions": {},
                }
                self._state = data
                self._save()
                return
            if data.get("version") != STATE_VERSION:
                raise ValueError("unsupported auth state version")
            if not isinstance(data.get("users"), dict) or not isinstance(data.get("sessions"), dict):
                raise TypeError("missing users or sessions map")
            self._state = data
            self._prune_sessions(save=True)
        except AuthErrorState:
            raise
        except Exception as exc:
            raise AuthErrorState(f"auth state unreadable: {type(exc).__name__}") from exc

    def _save(self) -> None:
        with self._lock:
            payload = json.dumps(self._state, separators=(",", ":"), sort_keys=True)
            fd, tmp_name = tempfile.mkstemp(prefix=".auth.", dir=str(self.path.parent))
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.chmod(tmp_name, 0o600)
                os.replace(tmp_name, self.path)
            finally:
                try:
                    os.unlink(tmp_name)
                except FileNotFoundError:
                    pass

    @property
    def users(self) -> dict[str, dict]:
        return self._state.setdefault("users", {})

    @property
    def sessions(self) -> dict[str, dict]:
        return self._state.setdefault("sessions", {})

    @property
    def owner_bound(self) -> bool:
        return "owner" in self.users

    def _secret(self) -> bytes:
        if not self._state.get("secret"):
            self._state["secret"] = secrets.token_hex(32)
            self._save()
        return self._state["secret"].encode()

    def _require_admin_token(self, token: str) -> None:
        if not self.setup_token or not token or not hmac.compare_digest(token, self.setup_token):
            raise PermissionError("invalid admin token")

    def _put_user(self, username: str, password: str, *, role: str, enabled: bool = True) -> None:
        if not username or len(password) < 12:
            raise ValueError("invalid username or password")
        salt = secrets.token_bytes(16)
        previous = self.users.get(username, {})
        self.users[username] = {
            "salt": salt.hex(),
            "hash": _scrypt(password, salt).hex(),
            "role": role,
            "enabled": enabled,
            "epoch": int(previous.get("epoch", 0)) + 1,
        }
        self._revoke_user_sessions(username)
        self._save()

    def setup_owner(self, password: str, token: str) -> None:
        with self._lock:
            self._require_admin_token(token)
            if self.owner_bound:
                raise PermissionError("owner already set")
            self._put_user("owner", password, role="owner")

    def create_test_user(self, username: str, password: str, token: str) -> None:
        with self._lock:
            self._require_admin_token(token)
            if username == "owner" or not username.startswith("test-"):
                raise ValueError("temporary username must start with test-")
            self._put_user(username, password, role="test")

    def disable_user(self, username: str, token: str) -> None:
        with self._lock:
            self._require_admin_token(token)
            user = self.users.get(username)
            if not user or user.get("role") != "test":
                raise ValueError("temporary user not found")
            user["enabled"] = False
            user["epoch"] = int(user.get("epoch", 0)) + 1
            self._revoke_user_sessions(username)
            self._save()

    def verify(self, username: str, password: str) -> bool:
        user = self.users.get(username)
        if not user or not user.get("enabled", False):
            return False
        try:
            salt = bytes.fromhex(user["salt"])
            candidate = _scrypt(password, salt).hex()
        except (KeyError, ValueError):
            return False
        return hmac.compare_digest(candidate, user["hash"])

    def locked(self, key: str) -> bool:
        now = time.time()
        events = [stamp for stamp in self._fails.get(key, []) if now - stamp < FAIL_WINDOW]
        self._fails[key] = events
        return len(events) >= FAIL_MAX

    def record_fail(self, key: str) -> None:
        self._fails.setdefault(key, []).append(time.time())

    def clear_fails(self, key: str) -> None:
        self._fails.pop(key, None)

    def issue(self, username: str) -> str:
        with self._lock:
            user = self.users.get(username)
            if not user or not user.get("enabled", False):
                raise PermissionError("user disabled")
            sid = secrets.token_urlsafe(32)
            exp = int(time.time()) + SESSION_TTL_SECONDS
            self.sessions[sid] = {
                "username": username,
                "role": user["role"],
                "epoch": int(user.get("epoch", 0)),
                "expires": exp,
            }
            self._prune_sessions(save=False)
            self._save()
            sig = hmac.new(self._secret(), sid.encode(), hashlib.sha256).hexdigest()
            return f"{sid}.{sig}"

    def identity(self, token: str | None) -> dict | None:
        if not token:
            return None
        try:
            sid, sig = token.rsplit(".", 1)
        except ValueError:
            return None
        expected = hmac.new(self._secret(), sid.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sig):
            return None
        session = self.sessions.get(sid)
        if not session or time.time() > int(session.get("expires", 0)):
            return None
        username = session.get("username", "")
        user = self.users.get(username)
        if not user or not user.get("enabled", False):
            return None
        if int(session.get("epoch", -1)) != int(user.get("epoch", 0)):
            return None
        return {"username": username, "role": user.get("role", "")}

    def check(self, token: str | None) -> bool:
        return self.identity(token) is not None

    def revoke(self, token: str | None) -> None:
        if not token:
            return
        try:
            sid, _ = token.rsplit(".", 1)
        except ValueError:
            return
        with self._lock:
            if self.sessions.pop(sid, None) is not None:
                self._save()

    def _revoke_user_sessions(self, username: str) -> None:
        self._state["sessions"] = {
            sid: session for sid, session in self.sessions.items()
            if session.get("username") != username
        }

    def _prune_sessions(self, *, save: bool) -> None:
        now = time.time()
        before = len(self.sessions)
        self._state["sessions"] = {
            sid: session for sid, session in self.sessions.items()
            if int(session.get("expires", 0)) > now
        }
        if save and len(self.sessions) != before:
            self._save()


_store: UserStore | None = None


def get_store(data_dir: str | None = None) -> UserStore:
    global _store
    if _store is None:
        data_root = data_dir or os.environ.get("WIZARD_DATA_DIR", "./wizard_data")
        setup_token = os.environ.get("WIZARD_OWNER_SETUP_TOKEN", "")
        backend = os.environ.get("WIZARD_AUTH_BACKEND", "local")
        if backend == "tos":
            from server.wizard.auth_persistent import make_persistent_store
            _store = make_persistent_store(setup_token)
        elif backend == "local":
            _store = UserStore(data_root, setup_token)
        else:
            raise AuthErrorState("unsupported authentication storage backend")
    return _store


def set_store(store: UserStore | None = None) -> None:
    global _store
    _store = store


def _read_session(request: Request) -> str | None:
    return request.cookies.get(COOKIE_NAME)


def current_identity(request: Request) -> dict | None:
    store = getattr(request.app.state, "user_store", None) or get_store()
    return store.identity(_read_session(request))


def is_authenticated(request: Request) -> bool:
    return current_identity(request) is not None


def public_path(path: str) -> bool:
    p = path.rstrip("/") or "/"
    if p in ("/", "/health", "/ping", "/readiness", "/liveness"):
        return True
    if p in ("/api/auth/status", "/api/auth/login", "/api/auth/setup"):
        return True
    if p == "/favicon.ico" or p.startswith("/assets/"):
        return True
    # Runtime protocol remains protected by the platform gateway.  The public
    # browser front door does not expose these paths.
    if p in ("/invoke", "/run", "/run_sse", "/sessions") or p.startswith("/sessions/"):
        return True
    # Admin endpoints are reachable only on the protected Runtime endpoint and
    # perform their own constant-time admin-token check.
    return bool(p.startswith("/api/auth/admin/"))


def _csrf_ok(request: Request) -> bool:
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return True
    origin = request.headers.get("Origin", "").rstrip("/")
    if not origin:
        return not get_settings().production
    configured = get_settings().public_origin.rstrip("/")
    if configured:
        return hmac.compare_digest(origin, configured)
    host = request.headers.get("X-Forwarded-Host") or request.headers.get("Host", "")
    try:
        return urlsplit(origin).netloc == host
    except ValueError:
        return False


async def auth_middleware(request: Request, call_next):
    path = request.url.path
    if request.method == "OPTIONS" or public_path(path):
        return await call_next(request)
    if not _csrf_ok(request):
        return JSONResponse(status_code=403, content={"detail": "cross-origin rejected"})
    if not is_authenticated(request):
        return JSONResponse(status_code=401, content={"detail": "login required"})
    request.state.identity = current_identity(request)
    return await call_next(request)


def set_session_cookie(response: Response, token: str, secure: bool) -> Response:
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=secure,
        path="/",
    )
    return response


def clear_session_cookie(response: Response) -> Response:
    response.delete_cookie(COOKIE_NAME, path="/")
    return response
