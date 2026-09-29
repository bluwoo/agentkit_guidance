"""Encrypted, compare-and-swap authentication state in TOS (no filesystem mount).

Every operation reads the authoritative object. Mutations commit with If-Match;
conflicts retry against fresh state. Missing/corrupt state fails closed. The
bootstrap object must be provisioned explicitly, never recreated by the app.
"""
from __future__ import annotations

import json
import os
import secrets
import threading
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from server.wizard.auth import STATE_VERSION, AuthErrorState, UserStore


class RuntimeCredentials:
    """Reload the platform-managed temporary credential on each signed request."""

    def get_credentials(self):
        from tos.credential import Credentials
        try:
            data = json.loads(Path('/var/run/secrets/iam/credential').read_text())
            return Credentials(data['access_key_id'], data['secret_access_key'], data.get('session_token'))
        except (FileNotFoundError, KeyError, ValueError, OSError, TypeError):
            raise AuthErrorState('runtime storage credentials unavailable') from None


class TosBackend:
    def __init__(self, client, bucket: str, key: str):
        self.client, self.bucket, self.key = client, bucket, key

    def read(self) -> tuple[bytes, str]:
        from tos.exceptions import TosError

        try:
            result = self.client.get_object(self.bucket, self.key)
            if result.content_length > 4 * 1024 * 1024:
                raise AuthErrorState('authentication state exceeds size limit')
            return result.read(), result.etag
        except AuthErrorState:
            raise
        except TosError:
            raise AuthErrorState('authentication storage unavailable') from None

    def compare_and_swap(self, data: bytes, etag: str) -> bool:
        from tos.exceptions import TosError

        try:
            self.client.put_object(
                self.bucket, self.key, content=data, if_match=etag,
                content_type='application/octet-stream', cache_control='no-store',
            )
            return True
        except TosError as exc:
            if getattr(exc, 'status_code', None) == 412:
                return False
            raise AuthErrorState('authentication storage write failed') from None


class _MemoryStore(UserStore):
    def __init__(self, state: dict, setup_token: str):
        self._state = state
        self.setup_token = setup_token
        self._lock = threading.RLock()
        self._fails = state.setdefault('login_failures', {})
        self.dirty = False

    def _save(self):
        self.dirty = True


def empty_auth_state() -> dict:
    return {
        'version': STATE_VERSION, 'secret': secrets.token_hex(32),
        'users': {}, 'sessions': {}, 'login_failures': {},
    }


class PersistentUserStore:
    """UserStore-compatible facade with durable, encrypted CAS transactions."""

    def __init__(self, backend, encryption_key: str, setup_token: str):
        self.backend = backend
        self.setup_token = setup_token
        try:
            self.cipher = Fernet(encryption_key.encode('ascii'))
        except (ValueError, TypeError):
            raise AuthErrorState('invalid authentication encryption configuration') from None
        self._apply('owner_bound')  # fail closed during startup

    def _decode(self, data: bytes) -> dict:
        try:
            state = json.loads(self.cipher.decrypt(data))
            if not isinstance(state, dict) or state.get('version') != STATE_VERSION:
                raise ValueError('version')
            if not isinstance(state.get('secret'), str) or len(state['secret']) < 32:
                raise ValueError('signing key')
            for key in ('users', 'sessions', 'login_failures'):
                if not isinstance(state.get(key), dict):
                    raise TypeError('state map')
            for username, user in state['users'].items():
                if not isinstance(user, dict) or user.get('role') not in ('owner', 'test'):
                    raise ValueError('user')
                if user['role'] == 'owner' and username != 'owner':
                    raise ValueError('owner')
                if len(bytes.fromhex(user['salt'])) != 16 or len(bytes.fromhex(user['hash'])) != 32:
                    raise ValueError('password hash')
                if not isinstance(user.get('enabled'), bool) or not isinstance(user.get('epoch'), int):
                    raise TypeError('user state')
            return state
        except (InvalidToken, ValueError, KeyError, TypeError):
            raise AuthErrorState('authentication state invalid') from None

    def _apply(self, method: str, *args):
        for _ in range(8):
            data, etag = self.backend.read()
            store = _MemoryStore(self._decode(data), self.setup_token)
            target = getattr(store, method)
            result = target(*args) if callable(target) else target
            if method in ('locked', 'record_fail', 'clear_fails'):
                store.dirty = True
                # Bound persisted lockout metadata without resetting live limits.
                if len(store._fails) > 10000:
                    raise AuthErrorState('authentication rate-limit capacity reached')
            if not store.dirty:
                return result
            sealed = self.cipher.encrypt(json.dumps(store._state, separators=(',', ':')).encode())
            if self.backend.compare_and_swap(sealed, etag):
                return result
        raise AuthErrorState('authentication storage busy; retry')

    @property
    def owner_bound(self):
        return self._apply('owner_bound')

    def setup_owner(self, password, token):
        return self._apply('setup_owner', password, token)

    def create_test_user(self, username, password, token):
        return self._apply('create_test_user', username, password, token)

    def disable_user(self, username, token):
        return self._apply('disable_user', username, token)

    def verify(self, username, password):
        return self._apply('verify', username, password)

    def issue(self, username):
        return self._apply('issue', username)

    def identity(self, token):
        if not token:
            return None
        return self._apply('identity', token)

    def check(self, token):
        return self.identity(token) is not None

    def revoke(self, token):
        return self._apply('revoke', token)

    def locked(self, key):
        return self._apply('locked', key)

    def record_fail(self, key):
        return self._apply('record_fail', key)

    def clear_fails(self, key):
        return self._apply('clear_fails', key)


def make_persistent_store(setup_token: str):
    import tos
    required = ('WIZARD_AUTH_TOS_BUCKET', 'WIZARD_AUTH_TOS_KEY', 'WIZARD_AUTH_ENCRYPTION_KEY')
    if any(not os.environ.get(k) for k in required):
        raise AuthErrorState('persistent authentication configuration incomplete')
    client = tos.TosClientV2(
        endpoint='https://tos-cn-beijing.volces.com', region='cn-beijing',
        credentials_provider=RuntimeCredentials(), max_retry_count=0,
        connection_time=5, socket_timeout=10, request_timeout=15,
    )
    backend = TosBackend(client, os.environ[required[0]], os.environ[required[1]])
    return PersistentUserStore(backend, os.environ[required[2]], setup_token)
