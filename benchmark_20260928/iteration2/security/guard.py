"""In-process mirror of the sandbox default-deny network guard.

Used by pytest to prove that the *default* policy blocks outbound TCP, and that the
opt-out path removes the interception (without needing real internet).

Design notes
------------
* We patch ``socket.socket.connect`` / ``connect_ex`` — the single chokepoint used by
  ``socket.create_connection``, ``urllib``, ``requests``, ``httpx``, ``http.client`` and
  asyncio TCP connections.
* The guard NEVER reads shell profiles or secret files; it only matches path strings.
"""
from __future__ import annotations

from contextlib import contextmanager
import socket
from typing import Iterator


class EgressBlocked(PermissionError):
    """Outbound network egress denied by the default-deny guard."""


_orig_connect = socket.socket.connect
_orig_connect_ex = socket.socket.connect_ex
_installed = False


def _deny_connect(self, address) -> None:
    raise EgressBlocked("sandbox: outbound network egress is denied by default")


def _deny_connect_ex(self, address) -> int:
    try:
        _deny_connect(self, address)
    except EgressBlocked as exc:
        return getattr(exc, "errno", 1) or 1
    return 0


def install_process_guard() -> bool:
    """Install the in-process egress guard. Idempotent. Returns True if newly installed."""
    global _installed
    if _installed:
        return False
    socket.socket.connect = _deny_connect  # type: ignore[method-assign]
    socket.socket.connect_ex = _deny_connect_ex  # type: ignore[method-assign]
    _installed = True
    return True


def uninstall_process_guard() -> None:
    """Remove the in-process egress guard (restore the original helpers)."""
    global _installed
    socket.socket.connect = _orig_connect  # type: ignore[method-assign]
    socket.socket.connect_ex = _orig_connect_ex  # type: ignore[method-assign]
    _installed = False


@contextmanager
def process_guard() -> Iterator[None]:
    """Context manager: block outbound TCP inside the current process for the block."""
    install_process_guard()
    try:
        yield
    finally:
        uninstall_process_guard()
