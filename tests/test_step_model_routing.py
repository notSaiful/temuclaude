import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import step_telemetry
from src.adaptive import get_fallback_model_for_step, get_model_for_step


def test_step_model_fallbacks():
    assert get_fallback_model_for_step("coding", "step_verify(1/1)") == "deepseek-v4-pro"
    assert get_fallback_model_for_step("reasoning", "prm_verification") == "nemotron-3-ultra"
    assert get_fallback_model_for_step("reasoning", "qa_gate") == "nemotron-3-ultra"
    assert get_fallback_model_for_step("reasoning", "tree_of_thoughts") == "deepseek-v4-pro"
    assert get_fallback_model_for_step("creative", "direct_specialist") == "minimax-m3"
    assert get_fallback_model_for_step("math", "prm_consistency(n=3)") == "deepseek-v4-pro"


def test_step_model_router_collects_more_data(tmp_path, monkeypatch):
    telemetry_file = tmp_path / "step_telemetry.json"
    monkeypatch.setattr(step_telemetry, "STEP_TELEMETRY_FILE", str(telemetry_file))

    step_telemetry.record_step_event(
        query="verify code",
        task_type="coding",
        tier="hard",
        step_type="step_verify(1/1)",
        model="deepseek-v4-pro",
        strategy="step_verify(1/1)",
        success=True,
    )

    model, used_router, confidence = get_model_for_step("coding", "hard", "step_verify(1/1)", min_count=3)
    assert model == "deepseek-v4-pro"
    assert used_router is False
    assert confidence == 0.0


def test_step_model_router_uses_observed_best(tmp_path, monkeypatch):
    telemetry_file = tmp_path / "step_telemetry.json"
    monkeypatch.setattr(step_telemetry, "STEP_TELEMETRY_FILE", str(telemetry_file))

    for _ in range(3):
        step_telemetry.record_step_event(
            query="verify code",
            task_type="coding",
            tier="hard",
            step_type="step_verify(1/1)",
            model="deepseek-v4-pro",
            strategy="step_verify(1/1)",
            success=True,
            latency_ms=900,
            tokens_used=220,
            progress_delta=0.4,
            uncertainty=0.1,
        )
    step_telemetry.record_step_event(
        query="verify code",
        task_type="coding",
        tier="hard",
        step_type="step_verify(1/1)",
        model="nemotron-3-ultra",
        strategy="step_verify(1/1)",
        success=False,
        latency_ms=300,
        tokens_used=90,
        progress_delta=-0.2,
        uncertainty=0.8,
    )

    model, used_router, confidence = get_model_for_step("coding", "hard", "step_verify(1/1)", min_count=3)
    assert model == "deepseek-v4-pro"
    assert used_router is True
    assert confidence > 0.8
