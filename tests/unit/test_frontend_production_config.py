from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_production_frontend_disables_mock_api():
    values = {}
    for raw in (ROOT / "web" / ".env.production").read_text().splitlines():
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            values[key] = value
    assert values.get("VITE_USE_MOCK") in {"", "0"}
