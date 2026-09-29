"""Component: **agentkit-identity-permission** (identity, authN/authZ, credentials).

Per the Skill:
  * Inbound: API Key (Bearer) or OAuth JWT (User Access Token). ``user_id`` header is a
    routing/session label, NOT a trusted identity.
  * Authorization: Cedar policy -> Permission Gateway PEP; decision Allow/Deny.
  * Outbound credentials are managed by a Credential Provider (never hard-coded).
  * Security acceptance matrix: no creds -> 401; expired token -> 401; authorized user -> 200;
    authenticated-but-unauthorized user can chat but tool call -> 403.

We implement the inbound verification + Cedar decision locally. Real UserPool/SSO/JWKS and
credential injection are a CloudBoundary.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class Principal:
    user: str
    roles: set[str] = field(default_factory=set)


class AuthError(Exception):
    def __init__(self, status: int, detail: str):
        self.status = status
        super().__init__(f"{status}: {detail}")


@dataclass
class Token:
    value: str
    subject: Principal
    expires_at: float  # epoch seconds


class IdentityManager:
    """Local stand-in for UserPool + Permission Gateway (Cedar)."""

    def __init__(self):
        self._tokens: dict[str, Token] = {}
        self._allow: set[tuple[str, str]] = set()  # (role, action)

    def issue(self, value: str, subject: Principal, ttl_seconds: int = 3600) -> Token:
        tok = Token(value=value, subject=subject, expires_at=time.time() + ttl_seconds)
        self._tokens[value] = tok
        return tok

    def grant(self, role: str, action: str):
        self._allow.add((role, action))

    def authenticate(self, authorization: str | None) -> Principal:
        if not authorization:
            raise AuthError(401, "missing Authorization header")
        # expect "Bearer <token>"
        parts = authorization.split()
        if len(parts) != 2 or parts[0] != "Bearer":
            raise AuthError(401, "malformed bearer")
        tok = self._tokens.get(parts[1])
        if tok is None:
            raise AuthError(401, "unknown token")
        if tok.expires_at < time.time():
            raise AuthError(401, "token expired")
        return tok.subject

    def authorize(self, subject: Principal, action: str) -> bool:
        return any((role, action) in self._allow for role in subject.roles)

    def enforce_tool(self, authorization: str | None, action: str) -> Principal:
        subject = self.authenticate(authorization)        # 401 on bad/missing
        if not self.authorize(subject, action):
            raise AuthError(403, f"principal {subject.user} may not {action}")
        return subject
