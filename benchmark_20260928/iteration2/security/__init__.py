"""Default-deny security guard for the AgentKit Benchmark (iteration2, slice B).

This package provides:

* :class:`EgressBlocked` and the in-process :func:`process_guard` context manager —
  the same socket-layer mediation used by ``harness.c09_sandbox`` inside a running
  Python interpreter, exposed so pytest suites can assert the default block without
  spawning a child.
* A pytest fixture :data:`net_guard` (import this package's conftest or use the
  context manager directly).

The child-process guard (sitecustomize injection) lives in ``harness/c09_sandbox.py``;
this module mirrors its network layer for in-process tests.
"""
from .guard import EgressBlocked, process_guard, install_process_guard

__all__ = ["EgressBlocked", "process_guard", "install_process_guard"]
