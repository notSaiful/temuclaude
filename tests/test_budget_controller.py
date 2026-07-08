from src.benchmark_promotion import evaluate_promotion, summarize_controller_distribution
from src.budget_controller import recommend_controller_action


def test_controller_stops_after_verified_low_uncertainty_state():
    decision = recommend_controller_action(
        task_type="math",
        tier="hard",
        step_type="verification",
        remaining_budget_ratio=0.5,
        progress_delta=0.5,
        uncertainty=0.1,
        verifier_passed=True,
        success=True,
    )

    assert decision.action == "stop"
    assert decision.confidence >= 0.8
    assert decision.cost_risk == "low"


def test_controller_debates_contradictions_when_budget_remains():
    decision = recommend_controller_action(
        task_type="reasoning",
        tier="hard",
        step_type="formal_verification",
        remaining_budget_ratio=0.4,
        uncertainty=0.7,
        failure_label="logical_contradiction",
    )

    assert decision.action == "debate"
    assert decision.cost_risk == "medium"


def test_controller_uses_cheap_draft_when_budget_is_critical():
    decision = recommend_controller_action(
        task_type="coding",
        tier="hard",
        step_type="search",
        remaining_budget_ratio=0.05,
        progress_delta=-0.2,
        uncertainty=0.5,
        success=False,
    )

    assert decision.action == "cheap_draft"
    assert decision.cost_risk == "critical"


def test_benchmark_promotion_blocks_regressions():
    result = evaluate_promotion(
        baseline={"quality_score": 0.8, "cost_per_query": 1.0, "latency_ms": 1000, "failure_rate": 0.05},
        candidate={"quality_score": 0.75, "cost_per_query": 0.95, "latency_ms": 1300, "failure_rate": 0.08},
    )

    assert result["promote"] is False
    assert "quality_regression" in result["blockers"]
    assert "latency_regression" in result["blockers"]
    assert "failure_rate_regression" in result["blockers"]


def test_benchmark_promotion_accepts_cost_saving_non_regression():
    result = evaluate_promotion(
        baseline={"quality_score": 0.8, "cost_per_query": 1.0, "latency_ms": 1000, "failure_rate": 0.05},
        candidate={"quality_score": 0.805, "cost_per_query": 0.75, "latency_ms": 980, "failure_rate": 0.045},
    )

    assert result["promote"] is True
    assert result["deltas"]["cost_reduction"] == 0.25


def test_controller_distribution_summary():
    summary = summarize_controller_distribution([
        {"controller_action": "verify"},
        {"controller_action": "verify"},
        {"controller_action": "stop"},
        {},
    ])

    assert summary["total_controller_events"] == 3
    assert summary["top_action"] == "verify"
