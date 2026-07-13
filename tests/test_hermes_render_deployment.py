"""Guardrails for the opt-in persistent Hermes Render service."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_hermes_render_blueprint_uses_persistent_authenticated_service():
    blueprint = (ROOT / "services" / "hermes" / "render.yaml").read_text()

    assert "plan: starter" in blueprint
    assert "mountPath: /opt/data" in blueprint
    assert "HERMES_DASHBOARD_BASIC_AUTH_USERNAME" in blueprint
    assert "HERMES_DASHBOARD_BASIC_AUTH_PASSWORD" in blueprint
    assert "HERMES_DASHBOARD_BASIC_AUTH_SECRET" in blueprint
    assert "generateValue: true" in blueprint
    assert "OPENROUTER_API_KEY" in blueprint
    assert "value:" not in blueprint


def test_cloud_run_container_pins_runtime_and_exposes_only_the_private_api_surface():
    dockerfile = (ROOT / "services" / "hermes" / "Dockerfile").read_text()

    assert "FROM nousresearch/hermes-agent@sha256:" in dockerfile
    assert "API_SERVER_ENABLED=true" in dockerfile
    assert "API_SERVER_MODEL_NAME=temuclaude-hermes" in dockerfile
    assert "HERMES_API_SERVER_FORCE_NON_STREAMING=true" in dockerfile
    assert "HERMES_WRITE_SAFE_ROOT=/opt/data" in dockerfile
    assert "HERMES_DASHBOARD=true" not in dockerfile
    assert 'CMD ["hermes", "--oneshot"]' not in dockerfile
    assert "hermes gateway run --no-supervise" in dockerfile
