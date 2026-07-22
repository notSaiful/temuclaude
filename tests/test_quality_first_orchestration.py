"""Contracts for the quality-first Pro orchestration policy."""

import inspect
from pathlib import Path

from src.fusion import DEFAULT_PANEL_SIZE, get_panel
from src.orchestrator import Temuclaude


ROOT = Path(__file__).resolve().parents[1]


def test_pro_fusion_uses_task_specialist_first_with_complementary_roles(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "configured")
    assert DEFAULT_PANEL_SIZE == 9
    panel = get_panel("coding")
    assert panel == [
        "deepseek-v4-pro",
        "grok-4.5",
        "kimi-k3",
        "glm-5.2",
        "gpt-5.6-luna",
        "gemini-3.5-flash",
        "minimax-m3",
        "nemotron-3-ultra",
        "deepseek-v4-flash",
    ]


def test_openrouter_quality_panel_activates_all_nine_roles(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "configured")
    panel = get_panel("coding")
    assert panel[0] == "deepseek-v4-pro"
    assert len(panel) == DEFAULT_PANEL_SIZE
    assert set(panel) == {
        "deepseek-v4-pro",
        "grok-4.5",
        "gpt-5.6-luna",
        "glm-5.2",
        "gemini-3.5-flash",
        "kimi-k3",
        "minimax-m3",
        "nemotron-3-ultra",
        "deepseek-v4-flash",
    }


def test_python_pro_default_is_quality_first_and_savings_is_explicit():
    parameter = inspect.signature(Temuclaude.complete).parameters["budget_profile"]
    assert parameter.default == "max_quality"
    source = (ROOT / "src/orchestrator.py").read_text()
    assert 'if budget_profile in ("max_quality", "balanced"):' in source
    assert "panel_size=9, max_tokens=token_budget" in source
    # Layer 2 (2026-07-17): max_quality is difficulty-adaptive — trivial/medium
    # Pro queries honour determine_tier() and take the fast tier-dispatch path;
    # only hard Pro queries (and every `balanced` query) run the full gauntlet.
    assert 'if budget_profile == "max_quality" and tier in ("trivial", "medium"):' in source
    assert "self.get_adaptive_token_budget(tier)" in source
    assert "self.get_adaptive_n_samples(tier)" in source


def test_panel_members_receive_role_specific_instructions():
    source = (ROOT / "src/fusion.py").read_text()
    for capability in (
        "long-horizon planner",
        "math, STEM, coding",
        "coding-driven UI/UX",
        "multimodal, long-context",
        "visual UI, accessibility",
        "fast independent GPT-family proposer",
        "coding-agent and repair specialist",
        "independent verifier",
    ):
        assert capability in source


def test_api_forwards_an_explicit_quality_profile_through_security_wrapper():
    source = (ROOT / "api_server.py").read_text()
    assert 'budget_profile: Literal["max_quality", "max_savings", "balanced"] = "max_quality"' in source
    assert 'orchestrator_kwargs={"budget_profile": payload.budget_profile}' in source


def test_pro_playground_does_not_route_code_generation_to_a_single_draft():
    source = (ROOT / "website/app/api/chat/route.ts").read_text()
    assert "runQualityCodeGeneration" in source
    assert "quality-first-code-panel" in source
    assert "independent-code-review" in source
    assert "Every Pro request receives the full specialist panel" in source
    assert "pro-quality-floor" not in source
    assert "POOL.frontier" in source
    assert "POOL.codeRepair" in source
    assert "POOL.multimodal" in source


def test_openrouter_pro_provider_policy_is_not_price_weighted():
    source = (ROOT / "website/lib/openrouter.ts").read_text()
    assert "sort: 'throughput'" in source
    assert "quantizations: ['bf16', 'fp16', 'fp8']" in source
    assert "openrouter:resilience:" in source
    assert "strictQuality ?" in source
    assert "result.status !== 401 && result.status !== 403" in source
    assert "fixedSampling" in source


def test_production_container_provisions_writable_runtime_log_directory():
    dockerfile = (ROOT / "Dockerfile").read_text()

    assert "install -d -o app -g app /app/logs" in dockerfile
    assert dockerfile.index("install -d -o app -g app /app/logs") < dockerfile.index("USER app")
