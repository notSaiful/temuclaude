import json
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import step_telemetry


def test_split_and_normalize_strategy():
    strategy = "mcts_step_search+self_play_correction+step_verify(2/3)+z3_verified"

    assert step_telemetry.split_strategy(strategy) == [
        "mcts_step_search",
        "self_play_correction",
        "step_verify(2/3)",
        "z3_verified",
    ]
    assert step_telemetry.normalize_step_name("mcts_step_search") == "search"
    assert step_telemetry.normalize_step_name("step_verify(2/3)") == "verification"
    assert step_telemetry.normalize_step_name("z3_verified") == "formal_verification"


def test_record_strategy_steps_and_summary(tmp_path, monkeypatch):
    telemetry_file = tmp_path / "step_telemetry.json"
    monkeypatch.setattr(step_telemetry, "STEP_TELEMETRY_FILE", str(telemetry_file))

    step_telemetry.record_strategy_steps(
        query="Solve 2+2 and verify the result.",
        task_type="math",
        tier="hard",
        strategy="mcts_step_search+step_verify(1/1)+prm_consistency(n=3)",
        models_used=["deepseek-v4-pro", "deepseek-v4-pro+step", "nemotron-3-ultra"],
        success=True,
        latency_ms=1234,
        tokens_used=256,
        quality_score=0.92,
    )

    data = json.loads(telemetry_file.read_text())
    assert data["total_events"] == 3
    assert [event["step_type"] for event in data["events"]] == [
        "search",
        "verification",
        "consistency",
    ]
    assert data["events"][0]["query_hash"] != "Solve 2+2 and verify the result."
    assert data["events"][0]["sequence_index"] == 0

    summary = step_telemetry.summarize_step_performance()
    assert summary["search"]["count"] == 1
    assert summary["search"]["success_rate"] == 1.0
    assert summary["verification"]["top_model"] == "deepseek-v4-pro+step"
    assert summary["consistency"]["avg_tokens"] == 256


def test_event_history_is_bounded(tmp_path, monkeypatch):
    telemetry_file = tmp_path / "step_telemetry.json"
    monkeypatch.setattr(step_telemetry, "STEP_TELEMETRY_FILE", str(telemetry_file))
    monkeypatch.setattr(step_telemetry, "MAX_EVENTS", 2)

    for idx in range(3):
        step_telemetry.record_step_event(
            query=f"query {idx}",
            task_type="knowledge",
            tier="medium",
            step_type="direct_specialist",
            model="glm-5.2",
            strategy="direct_specialist",
            success=True,
            sequence_index=idx,
        )

    data = json.loads(telemetry_file.read_text())
    assert data["total_events"] == 3
    assert len(data["events"]) == 2
    assert data["events"][0]["sequence_index"] == 1
    assert data["events"][1]["sequence_index"] == 2


def test_step_dataset_and_route_recommendations(tmp_path, monkeypatch):
    telemetry_file = tmp_path / "step_telemetry.json"
    monkeypatch.setattr(step_telemetry, "STEP_TELEMETRY_FILE", str(telemetry_file))

    for _ in range(3):
        step_telemetry.record_step_event(
            query="debug failing python test",
            task_type="coding",
            tier="hard",
            step_type="step_verify(1/1)",
            model="deepseek-v4-pro",
            strategy="mcts_step_search+step_verify(1/1)",
            success=True,
            latency_ms=1200,
            tokens_used=300,
            quality_score=0.9,
            initial_budget=1000,
            remaining_budget=700,
            budget_spent=300,
            progress_delta=0.4,
            uncertainty=0.1,
        )
    step_telemetry.record_step_event(
        query="debug failing python test",
        task_type="coding",
        tier="hard",
        step_type="step_verify(1/1)",
        model="slow-premium-model",
        strategy="mcts_step_search+step_verify(1/1)",
        success=True,
        latency_ms=8000,
        tokens_used=1200,
        quality_score=0.9,
        progress_delta=0.1,
        uncertainty=0.2,
    )
    step_telemetry.record_step_event(
        query="debug failing python test",
        task_type="coding",
        tier="hard",
        step_type="step_verify(1/1)",
        model="cheap-weak-model",
        strategy="mcts_step_search+step_verify(1/1)",
        success=False,
        latency_ms=200,
        tokens_used=50,
        quality_score=0.2,
        initial_budget=1000,
        remaining_budget=100,
        budget_spent=900,
        progress_delta=-0.3,
        uncertainty=0.8,
        failure_label="Verification Proxy Mismatch",
    )

    dataset = step_telemetry.get_step_dataset()
    assert len(dataset) == 5
    assert dataset[0]["context_key"] == "coding:hard:verification"
    assert dataset[0]["remaining_budget_ratio"] == 0.7
    assert dataset[-1]["failure_label"] == "verification_proxy_mismatch"
    assert len(step_telemetry.get_step_dataset(success_only=True)) == 4

    recommendations = step_telemetry.get_step_route_recommendations(min_count=3)
    rec = recommendations["coding:hard:verification"]
    assert rec["recommendation"] == "use_observed_best"
    assert rec["recommended_model"] == "deepseek-v4-pro"
    assert rec["candidates"][0]["success_rate"] == 1.0
    assert rec["candidates"][0]["avg_progress_delta"] == 0.4
    assert rec["candidates"][-1]["top_failure_label"] == "verification_proxy_mismatch"


def test_step_route_recommendations_collect_more_data(tmp_path, monkeypatch):
    telemetry_file = tmp_path / "step_telemetry.json"
    monkeypatch.setattr(step_telemetry, "STEP_TELEMETRY_FILE", str(telemetry_file))

    step_telemetry.record_step_event(
        query="what is the capital of France",
        task_type="knowledge",
        tier="trivial",
        step_type="direct_specialist",
        model="glm-5.2",
        strategy="direct_specialist",
        success=True,
    )

    recommendations = step_telemetry.get_step_route_recommendations(min_count=3)
    rec = recommendations["knowledge:trivial:direct_answer"]
    assert rec["recommendation"] == "collect_more_data"
    assert rec["recommended_model"] is None
    assert rec["needed"] == 2


def test_budget_helpers_and_alerts(tmp_path, monkeypatch):
    telemetry_file = tmp_path / "step_telemetry.json"
    monkeypatch.setattr(step_telemetry, "STEP_TELEMETRY_FILE", str(telemetry_file))

    assert step_telemetry.calculate_remaining_budget_ratio(100, 25) == 0.25
    assert step_telemetry.calculate_remaining_budget_ratio(100, 200) == 1.0
    assert step_telemetry.calculate_remaining_budget_ratio(100, -1) == 0.0
    assert step_telemetry.calculate_remaining_budget_ratio(0, 1) is None
    assert step_telemetry.normalize_failure_label("Tool Loop / No Progress!") == "tool_loop_no_progress"

    for idx in range(3):
        step_telemetry.record_step_event(
            query=f"search task {idx}",
            task_type="reasoning",
            tier="hard",
            step_type="tree_of_thoughts",
            model="deepseek-v4-pro",
            strategy="tree_of_thoughts",
            success=False if idx < 2 else True,
            initial_budget=100,
            remaining_budget=10,
            failure_label="dead end" if idx < 2 else None,
        )

    summary = step_telemetry.summarize_step_performance()
    assert summary["search"]["avg_remaining_budget_ratio"] == 0.1
    assert summary["search"]["top_failure_label"] == "dead_end"

    alerts = step_telemetry.get_budget_alerts(min_count=3, low_budget_ratio=0.2, min_failure_rate=0.5)
    assert alerts["reasoning:hard:search"]["recommendation"] == "consider_early_abort_or_escalation"


def test_runtime_step_metadata_inference():
    success_meta = step_telemetry.build_runtime_step_metadata(
        token_budget=1000,
        tokens_used=250,
        success=True,
        strategy="mcts_step_search+step_verify(1/1)+z3_verified",
        answer="The verified answer is 42.",
    )
    assert success_meta["initial_budget"] == 1000
    assert success_meta["remaining_budget"] == 750
    assert success_meta["budget_spent"] == 250
    assert success_meta["progress_delta"] > 0.2
    assert success_meta["uncertainty"] == 0.15
    assert success_meta["failure_label"] is None

    failure_meta = step_telemetry.build_runtime_step_metadata(
        token_budget=500,
        tokens_used=500,
        success=False,
        strategy="tree_of_thoughts",
        answer="[ERROR: deepseek-v4-pro timed out after 120s]",
    )
    assert failure_meta["remaining_budget"] == 0
    assert failure_meta["progress_delta"] < 0
    assert failure_meta["uncertainty"] == 0.9
    assert failure_meta["failure_label"] == "model_timeout"


def test_step_route_recommendations_recency_decay(tmp_path, monkeypatch):
    telemetry_file = tmp_path / "step_telemetry.json"
    monkeypatch.setattr(step_telemetry, "STEP_TELEMETRY_FILE", str(telemetry_file))

    step_telemetry.record_step_event(
        query="verify code",
        task_type="coding",
        tier="hard",
        step_type="step_verify(1/1)",
        model="old-winner",
        strategy="step_verify(1/1)",
        success=True,
        latency_ms=100,
        tokens_used=100,
    )
    step_telemetry.record_step_event(
        query="verify code",
        task_type="coding",
        tier="hard",
        step_type="step_verify(1/1)",
        model="new-winner",
        strategy="step_verify(1/1)",
        success=True,
        latency_ms=300,
        tokens_used=100,
    )

    data = json.loads(telemetry_file.read_text())
    data["events"][0]["timestamp"] = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    data["events"][1]["timestamp"] = datetime.now(timezone.utc).isoformat()
    telemetry_file.write_text(json.dumps(data))

    no_decay = step_telemetry.get_step_route_recommendations(min_count=2)
    assert no_decay["coding:hard:verification"]["recommended_model"] == "old-winner"

    decayed = step_telemetry.get_step_route_recommendations(min_count=2, recency_half_life_days=1)
    assert decayed["coding:hard:verification"]["recommended_model"] == "new-winner"
    assert decayed["coding:hard:verification"]["candidates"][0]["effective_count"] < 2
