"""Contract checks for the customer-facing OpenAI-compatible model list."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_models_endpoint_advertises_pro_and_lite_with_api_key_authentication():
    route = (ROOT / "website" / "app" / "v1" / "models" / "route.ts").read_text()

    assert "temuclaude/temuclaude-pro" in route
    assert "temuclaude/temuclaude-lite" in route
    assert "validateApiKeyAsync" in route
    assert "Missing API key" in route
    assert "API access requires a Developer, Pro, Max, or Enterprise plan" in route
