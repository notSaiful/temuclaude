"""Regression tests for the 2026 role-based model stack.

These tests are intentionally offline: they validate provider gating and route
selection without making a billable model call.
"""

from src.models import (
    DIRECT_MODEL_PROVIDERS,
    TASK_MODEL_MAP,
    UPDATED_MODEL_STACK,
    get_direct_model_provider,
    get_runtime_model,
)
from src.fusion import get_panel
from src.ui_ux.screenshot_feedback import ScreenshotFeedback, ScreenshotResult


def test_updated_stack_has_ten_active_roles_and_frontier_sol():
    assert len(UPDATED_MODEL_STACK) == 10
    assert "gpt-5.6-luna" in UPDATED_MODEL_STACK
    assert "gpt-5.6-sol" in UPDATED_MODEL_STACK
    assert "gpt-5.6-terra" not in UPDATED_MODEL_STACK


def test_task_defaults_keep_open_cost_effective_core():
    assert TASK_MODEL_MAP["simple"] == "deepseek-v4-flash"
    assert TASK_MODEL_MAP["math"] == "deepseek-v4-pro"
    assert TASK_MODEL_MAP["agentic"] == "glm-5.2"
    assert TASK_MODEL_MAP["vision"] == "gemini-3.5-flash"
    assert TASK_MODEL_MAP["ui_ux"] == "kimi-k2.6"
    assert TASK_MODEL_MAP["long_context"] == "minimax-m3"


def test_premium_routes_are_unavailable_without_their_own_credentials():
    assert get_direct_model_provider("gemini-3.5-flash", {}) is None
    assert get_direct_model_provider("gpt-5.6-luna", {}) is None
    assert get_direct_model_provider("gpt-5.6-sol", {}) is None
    assert get_direct_model_provider("grok-4.5", {}) is None
    assert get_direct_model_provider("gpt-5.6-terra", {}) is None

    assert get_runtime_model("gemini-3.5-flash", {}) == "minimax-m3"
    assert get_runtime_model("gpt-5.6-luna", {}) == "glm-5.2"
    assert get_runtime_model("gpt-5.6-sol", {}) == "glm-5.2"
    assert get_runtime_model("grok-4.5", {}) == "glm-5.2"
    assert get_runtime_model("gpt-5.6-terra", {}) == "glm-5.2"


def test_premium_routes_require_explicit_provider_access():
    assert get_runtime_model("gemini-3.5-flash", {"GOOGLE_API_KEY": "test"}) == "gemini-3.5-flash"
    assert get_runtime_model("gpt-5.6-luna", {"OPENAI_API_KEY": "test"}) == "gpt-5.6-luna"
    assert get_runtime_model("gpt-5.6-sol", {"OPENAI_API_KEY": "test"}) == "gpt-5.6-sol"
    assert get_runtime_model("grok-4.5", {"XAI_API_KEY": "test"}) == "grok-4.5"

    # Terra remains unavailable with an OpenAI key alone.
    assert get_runtime_model("gpt-5.6-terra", {"OPENAI_API_KEY": "test"}) == "gpt-5.6-sol"
    assert get_runtime_model(
        "gpt-5.6-terra",
        {"OPENAI_API_KEY": "test", "TEMUCLAUDE_ENABLE_TERRA_FALLBACK": "true"},
    ) == "gpt-5.6-terra"


def test_openrouter_makes_frontier_aliases_routable_without_native_keys():
    env = {"OPENROUTER_API_KEY": "configured"}
    assert get_runtime_model("gpt-5.6-luna", env) == "gpt-5.6-luna"
    assert get_runtime_model("gpt-5.6-sol", env) == "gpt-5.6-sol"
    assert get_runtime_model("grok-4.5", env) == "grok-4.5"
    assert get_runtime_model("gemini-3.5-flash", env) == "gemini-3.5-flash"


def test_fusion_panel_is_deduplicated_and_budget_bounded(monkeypatch):
    for key in ("OPENROUTER_API_KEY", "OPENAI_API_KEY", "XAI_API_KEY", "GOOGLE_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    panel = get_panel("coding", panel_size=3)
    assert 1 <= len(panel) <= 3
    assert len(panel) == len(set(panel))
    assert "deepseek-v4-pro" in panel
    assert "glm-5.2" in panel


def test_configured_frontier_models_join_quality_first_fusion(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test")
    monkeypatch.setenv("XAI_API_KEY", "test")

    assert "grok-4.5" in get_panel("coding", panel_size=9)
    assert "grok-4.5" in get_panel("agentic", panel_size=9)
    assert "gemini-3.5-flash" in get_panel("vision", panel_size=9)
    assert "gemini-3.5-flash" in get_panel("ui_ux", panel_size=9)


def test_screenshot_feedback_uses_a_vision_payload_when_available(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test")
    feedback = ScreenshotFeedback()

    async def captured(*_args, **_kwargs):
        return ScreenshotResult(captured=True, screenshot_base64="ZmFrZQ==", console_errors=[], render_errors=[])

    calls = []

    async def call_model(model, messages, **_kwargs):
        calls.append((model, messages))
        return "Fix the button contrast."

    monkeypatch.setattr(feedback, "capture_screenshot", captured)

    import asyncio
    result = asyncio.run(feedback.get_visual_feedback("<button>Go</button>", None, call_model))

    assert result
    assert calls[0][0] == "gemini-3.5-flash"
    content = calls[0][1][1]["content"]
    assert isinstance(content, list)
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_all_direct_routes_have_a_provider_contract():
    for model in ("gemini-3.5-flash", "gpt-5.6-luna", "gpt-5.6-sol", "grok-4.5", "gpt-5.6-terra"):
        provider = DIRECT_MODEL_PROVIDERS[model]
        assert provider["env"]
        assert provider["base_url"].startswith("https://")
        assert provider["model"]
