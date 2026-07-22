"""Regression coverage for the Modal completion deadline policy."""

import asyncio
import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("modal_app", ROOT / "modal_app.py")
assert SPEC and SPEC.loader
modal_service = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = modal_service
SPEC.loader.exec_module(modal_service)


def test_full_orchestration_is_used_when_it_finishes_before_deadline(monkeypatch):
    async def full_pipeline(*_args):
        return {
            "content": "fused answer", "tokens": 17, "tier": "hard", "time": 10,
            "completed_models": list(modal_service.REQUIRED_QUALITY_MODELS),
        }

    async def should_not_run(*_args):
        raise AssertionError("rescue must not race a healthy orchestration")

    monkeypatch.setattr(modal_service, "orchestrate", full_pipeline)
    monkeypatch.setattr(modal_service, "call_model", should_not_run)

    result = asyncio.run(modal_service.complete_with_rescue(None, [], 0.6, 64))

    assert result["content"] == "fused answer"
    assert result["tier"] == "hard"


def test_timeout_refuses_a_partial_panel_after_orchestration_deadline(monkeypatch):
    async def slow_pipeline(*_args):
        await asyncio.sleep(0.05)
        return {"content": "late fused answer", "tokens": 17, "tier": "hard", "time": 50}

    monkeypatch.setattr(modal_service, "ORCHESTRATION_DEADLINE_SECONDS", 0.001)
    monkeypatch.setattr(modal_service, "FALLBACK_DEADLINE_SECONDS", 1)
    monkeypatch.setattr(modal_service, "orchestrate", slow_pipeline)
    result = asyncio.run(modal_service.complete_with_rescue(None, [], 0.6, 64))

    assert result["content"] == ""
    assert result["tier"] == "full-panel-unavailable"


def test_empty_orchestration_result_is_not_returned_as_a_success(monkeypatch):
    async def empty_pipeline(*_args):
        return {"content": "   ", "tokens": 0, "tier": "hard", "time": 10}

    async def failed_rescue(*_args):
        return modal_service.Result(False, "", 0)

    monkeypatch.setattr(modal_service, "orchestrate", empty_pipeline)
    result = asyncio.run(modal_service.complete_with_rescue(None, [], 0.6, 64))

    assert not modal_service.has_usable_content(result)


def test_hard_modal_panel_uses_documented_quality_roles():
    source = (ROOT / "modal_app.py").read_text()

    for model in ("M_GLM", "M_DEEPSEEK", "M_KIMI", "M_MINIMAX", "M_GEMINI", "M_LUNA", "M_KIMI_FRONTIER", "M_GROK", "M_NEMOTRON"):
        assert model in source
    assert "async def run_quality_first_panel" in source
    assert "Hard-Pro panel: all documented specialists propose" in source
    assert "M_SOL" not in source


def test_modal_retries_the_same_model_through_openrouter_provider_fallbacks():
    source = (ROOT / "modal_app.py").read_text()

    assert "for attempt in range(2):" in source
    assert '"allow_fallbacks": True' in source
    assert '"sort": "throughput"' in source
    assert '"model": model' in source


def test_production_code_generation_uses_the_full_quality_panel():
    assert modal_service.classify("Generate a complete accessible browser action shooter game") == "hard"
    assert modal_service.is_code_artifact_request("Generate a complete accessible browser action shooter game")


def test_code_artifacts_get_a_dedicated_kimi_delivery_pass_after_the_panel(monkeypatch):
    events = []

    async def full_panel(*_args):
        events.append("panel")
        return "reviewed game design", 9, [modal_service.M_GLM]

    async def artifact_delivery(*_args):
        events.append("artifact")
        return modal_service.Result(True, "<!doctype html><title>Game</title>", 11)

    async def passing_qa(*_args):
        events.append("qa")
        return 9.0, 1, "", True

    monkeypatch.setattr(modal_service, "run_quality_first_panel", full_panel)
    monkeypatch.setattr(modal_service, "generate_code_artifact", artifact_delivery)
    monkeypatch.setattr(modal_service, "qa_gate", passing_qa)

    result = asyncio.run(modal_service.orchestrate(
        None,
        [{"role": "user", "content": "Build a browser action shooter game"}],
        0.2,
        4096,
    ))

    assert result["content"].startswith("<!doctype html>")
    assert events == ["panel", "artifact", "qa"]


def test_pro_trivial_prompt_still_requests_the_full_model_panel(monkeypatch):
    async def full_panel(*_args):
        return "fused answer", 9, [modal_service.M_GLM, modal_service.M_DEEPSEEK]

    async def passing_qa(*_args):
        return 9.0, 1, "", True

    monkeypatch.setattr(modal_service, "run_quality_first_panel", full_panel)
    monkeypatch.setattr(modal_service, "qa_gate", passing_qa)

    result = asyncio.run(modal_service.orchestrate(None, [{"role": "user", "content": "Hi"}], 0.2, 64))

    assert result["content"] == "fused answer"
    assert result["tier"] == "hard-quality-panel"
    assert result["requested_models"] == [
        modal_service.M_GLM,
        modal_service.M_DEEPSEEK,
        modal_service.M_KIMI,
        modal_service.M_MINIMAX,
        modal_service.M_GEMINI,
        modal_service.M_LUNA,
        modal_service.M_KIMI_FRONTIER,
        modal_service.M_GROK,
        modal_service.M_NEMOTRON,
    ]


def test_modal_returns_execution_telemetry_not_a_static_model_count():
    source = (ROOT / "modal_app.py").read_text()

    assert '"requested_models": result.get("requested_models"' in source
    assert '"completed_models": result.get("completed_models"' in source
    assert '"telemetry_version": 1' in source


def test_modal_refuses_to_emit_a_partial_quality_panel():
    source = (ROOT / "modal_app.py").read_text()

    assert "def has_complete_quality_panel" in source
    assert "if has_complete_quality_panel(result):" in source
    assert "len(candidates) != len(role_models)" in source
    assert '"tier": "full-panel-unavailable"' in source


def test_max_plan_has_direct_modal_api_access():
    assert modal_service.PLAN_MONTHLY_LIMITS["max"] == 1000000
