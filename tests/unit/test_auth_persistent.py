"""Durable auth-store tests: encryption, restart, CAS conflict and corruption."""
from __future__ import annotations

import json

import pytest
from cryptography.fernet import Fernet

from server.wizard.auth import AuthErrorState
from server.wizard.auth_persistent import PersistentUserStore, empty_auth_state


class FakeBackend:
    def __init__(self, cipher, state=None):
        self.cipher = cipher
        self.data = cipher.encrypt(json.dumps(state or empty_auth_state()).encode())
        self.rev = 1
        self.conflict_once = False

    def read(self):
        return self.data, str(self.rev)

    def compare_and_swap(self, data, etag):
        if self.conflict_once:
            self.conflict_once = False
            return False
        if etag != str(self.rev):
            return False
        self.data = data
        self.rev += 1
        return True


def make():
    key = Fernet.generate_key()
    return FakeBackend(Fernet(key)), key.decode()


def test_state_is_encrypted_and_survives_independent_store_restart():
    backend, key = make()
    one = PersistentUserStore(backend, key, 'bootstrap')
    one.setup_owner('long-enough-password', 'bootstrap')
    assert b'owner' not in backend.data and b'long-enough-password' not in backend.data
    two = PersistentUserStore(backend, key, 'bootstrap')
    assert two.owner_bound and two.verify('owner', 'long-enough-password')
    token = two.issue('owner')
    assert PersistentUserStore(backend, key, 'bootstrap').identity(token)['role'] == 'owner'


def test_conditional_conflict_retries_without_losing_owner():
    backend, key = make()
    store = PersistentUserStore(backend, key, 'bootstrap')
    backend.conflict_once = True
    store.setup_owner('long-enough-password', 'bootstrap')
    assert PersistentUserStore(backend, key, 'bootstrap').owner_bound


def test_corrupt_or_wrong_key_fails_closed():
    backend, key = make()
    backend.data = b'plaintext-or-corrupt'
    with pytest.raises(AuthErrorState):
        PersistentUserStore(backend, key, 'bootstrap')
    backend, _ = make()
    with pytest.raises(AuthErrorState):
        PersistentUserStore(backend, Fernet.generate_key().decode(), 'bootstrap')


def test_bootstrap_required_and_setup_is_single_use():
    backend, key = make()
    store = PersistentUserStore(backend, key, 'bootstrap')
    with pytest.raises(PermissionError):
        store.setup_owner('long-enough-password', 'wrong')
    store.setup_owner('long-enough-password', 'bootstrap')
    with pytest.raises(PermissionError):
        store.setup_owner('another-long-password', 'bootstrap')
