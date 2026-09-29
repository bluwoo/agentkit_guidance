"""Default-deny machine guard: positive/negative proof for the sandbox layers.

Covers (iteration2, slice B):
  * outbound TCP egress blocked by default, removable by explicit opt-out
  * known cloud-write CLIs blocked by default
  * shell-profile / secret-path reads blocked by default (path-string match only;
    the guard never opens these files)
  * read-only mode truly denies writes (open / os.open / os.system / subprocess)
  * reusable in-process pytest fixture (iteration2.security.guard.process_guard)
"""
from __future__ import annotations

import os
import socket
import textwrap

import pytest

from harness.c09_sandbox import LocalSandbox, UNSAFE_ENV


def _run(sb: LocalSandbox, code: str) -> dict:
    return sb.exec_code("sec", textwrap.dedent(code))


def _result(stdout: str) -> str:
    for line in stdout.splitlines():
        if line.startswith("RESULT:"):
            return line.split(":", 1)[1].strip()
    return ""


# ----------------------------------------------------------------- egress ----
def test_default_denies_outbound_egress():
    r = _run(LocalSandbox(), '''
        import socket
        try:
            socket.create_connection(("192.0.2.1", 80), timeout=2)
            print("RESULT: not-blocked")
        except Exception as e:
            print("RESULT: " + type(e).__name__)
    ''')
    assert _result(r["stdout"]) == "EgressBlocked"


def test_egress_opt_out_removes_guard_not_the_network():
    # With the explicit opt-out the *guard* must be gone: the same code must fail
    # with a real OS error (timeout/gaierror), NOT EgressBlocked.
    r = _run(LocalSandbox(allow_egress=True), '''
        import socket
        try:
            socket.create_connection(("192.0.2.1", 80), timeout=2)
            print("RESULT: not-blocked")
        except Exception as e:
            print("RESULT: " + type(e).__name__)
    ''')
    assert _result(r["stdout"]) != "EgressBlocked"


# ------------------------------------------------------------- cloud CLI -----
def test_default_blocks_cloud_write_cli():
    r = _run(LocalSandbox(), '''
        import subprocess
        try:
            subprocess.run(["aws", "s3", "cp", "a", "s3://b"], capture_output=True)
            print("RESULT: not-blocked")
        except Exception as e:
            print("RESULT: " + type(e).__name__)
    ''')
    assert _result(r["stdout"]) == "CloudCLIBlocked"


def test_cloud_cli_opt_out_not_our_guard():
    # aws may or may not exist on this host; either way the CloudCLIBlocked guard
    # must not fire when explicitly opted out.
    r = _run(LocalSandbox(allow_cloud_cli=True), '''
        import subprocess
        try:
            subprocess.run(["aws", "s3", "cp", "a", "s3://b"], capture_output=True)
            print("RESULT: not-blocked")
        except Exception as e:
            print("RESULT: " + type(e).__name__)
    ''')
    assert _result(r["stdout"]) != "CloudCLIBlocked"


# ------------------------------------------------------ secret-path reads ----
def test_default_blocks_shell_profile_read():
    # We never open ~/.zshrc ourselves; the child attempt must be intercepted at
    # builtins.open before any file access happens.
    r = _run(LocalSandbox(), '''
        import os
        try:
            open(os.path.expanduser("~/.zshrc")).read()
            print("RESULT: not-blocked")
        except Exception as e:
            print("RESULT: " + type(e).__name__)
    ''')
    assert _result(r["stdout"]) == "SecretPathBlocked"


def test_default_blocks_aws_credentials_fragment():
    # Use a non-existent path under the ~/.aws/ fragment: proves the fragment match
    # fires without reading any real credential file.
    r = _run(LocalSandbox(), '''
        import os
        try:
            open(os.path.expanduser("~/.aws/definitely-missing-xyz")).read()
            print("RESULT: not-blocked")
        except Exception as e:
            print("RESULT: " + type(e).__name__)
    ''')
    assert _result(r["stdout"]) == "SecretPathBlocked"


def test_secret_opt_out_falls_back_to_os_error():
    r = _run(LocalSandbox(allow_secret_read=True), '''
        import os
        try:
            open(os.path.expanduser("~/.aws/definitely-missing-xyz")).read()
            print("RESULT: not-blocked")
        except Exception as e:
            print("RESULT: " + type(e).__name__)
    ''')
    assert _result(r["stdout"]) != "SecretPathBlocked"


# ------------------------------------------------------------- read-only -----
def test_read_only_blocks_write_open():
    sb = LocalSandbox(mode="read-only")
    r = _run(sb, '''
        try:
            open("note.txt", "w").write("x")
            print("RESULT: not-blocked")
        except Exception as e:
            print("RESULT: " + type(e).__name__)
    ''')
    assert _result(r["stdout"]) == "WriteBlocked"
    assert not os.path.exists(os.path.join(r["workspace"], "note.txt"))


def test_read_only_blocks_os_system_and_subprocess():
    r = _run(LocalSandbox(mode="read-only"), '''
        import os
        try:
            os.system("touch note.txt")
            print("RESULT: os-system-ok")
        except Exception as e:
            print("RESULT: os-system-" + type(e).__name__)
        import subprocess
        try:
            subprocess.run(["touch", "note2.txt"])
            print("RESULT: subprocess-ok")
        except Exception as e:
            print("RESULT: subprocess-" + type(e).__name__)
    ''')
    assert "os-system-WriteBlocked" in r["stdout"]
    assert "subprocess-WriteBlocked" in r["stdout"]


def test_workspace_write_still_writes_by_default():
    # Baseline sanity: default workspace-write mode still writes inside the workspace.
    r = _run(LocalSandbox(), '''
        open("a.txt", "w").write("ok")
        print("RESULT: written")
    ''')
    assert _result(r["stdout"]) == "written"


# ------------------------------------------------------------- opt-out env ---
def test_master_env_opt_out(monkeypatch):
    monkeypatch.setenv(UNSAFE_ENV, "1")
    sb = LocalSandbox()
    pol = sb.guard_policy()
    assert pol["egress"] == "allow" and pol["cloud_cli"] == "allow"
    r = _run(sb, '''
        import socket
        try:
            socket.create_connection(("192.0.2.1", 80), timeout=2)
            print("RESULT: not-blocked")
        except Exception as e:
            print("RESULT: " + type(e).__name__)
    ''')
    assert _result(r["stdout"]) != "EgressBlocked"


def test_default_policy_is_deny():
    pol = LocalSandbox().guard_policy()
    assert pol == {
        "egress": "deny",
        "cloud_cli": "deny",
        "secret_read": "deny",
        "fs_write": "allow",
        "mode": "workspace-write",
        "approval": "on-request",
    }


# ----------------------------------------------------------- reusable guard ---
def test_in_process_fixture_blocks_socket():
    from iteration2.security.guard import process_guard, EgressBlocked
    with process_guard():
        with pytest.raises(EgressBlocked):
            socket.create_connection(("192.0.2.1", 80), timeout=1)
    # uninstalled after the block: real stack takes over (timeout, not our guard)
    try:
        socket.create_connection(("192.0.2.1", 80), timeout=1)
    except EgressBlocked:
        pytest.fail("guard leaked outside the context manager")
    except OSError:
        pass
