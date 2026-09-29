"""Every one of the 14 component modules must import cleanly."""
import importlib


COMPONENTS = [
    "c01_veadk", "c02_sdk_app", "c03_runtime", "c04_workflow", "c05_skills",
    "c06_memory", "c07_mcp_gateway", "c08_a2a", "c09_sandbox", "c10_guardrails",
    "c11_identity", "c12_knowledge", "c13_observability", "c14_evaluation",
]


def test_all_components_import():
    for mod in COMPONENTS:
        m = importlib.import_module(f"harness.{mod}")
        assert m is not None


def test_app_imports():
    from harness.app import MinimalHarness
    assert MinimalHarness is not None


def test_pinned_sdks_available():
    # The pinned real SDKs should import in this venv.
    import veadk  # noqa: F401
    import google.adk  # noqa: F401
    import agentkit.apps  # noqa: F401
