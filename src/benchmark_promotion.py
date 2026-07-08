"""
Benchmark promotion gate for TemuClaude routing and controller changes.

This module keeps risky model/orchestration changes in shadow mode until local
quality, cost, latency, and failure metrics satisfy conservative thresholds.
"""
from typing import Optional


DEFAULT_THRESHOLDS = {
    "max_quality_drop": 0.02,
    "min_cost_reduction": 0.15,
    "max_latency_increase": 0.10,
    "max_failure_rate_increase": 0.01,
}


def _num(metrics: dict, key: str) -> Optional[float]:
    value = metrics.get(key)
    if isinstance(value, (int, float)):
        return float(value)
    return None


def evaluate_promotion(
    baseline: dict,
    candidate: dict,
    thresholds: Optional[dict] = None,
) -> dict:
    """Return whether a candidate orchestration change can be promoted."""
    limits = dict(DEFAULT_THRESHOLDS)
    if thresholds:
        limits.update(thresholds)

    blockers = []
    deltas = {}

    base_quality = _num(baseline, "quality_score")
    cand_quality = _num(candidate, "quality_score")
    if base_quality is not None and cand_quality is not None:
        quality_delta = cand_quality - base_quality
        deltas["quality_delta"] = round(quality_delta, 4)
        if quality_delta < -limits["max_quality_drop"]:
            blockers.append("quality_regression")

    base_cost = _num(baseline, "cost_per_query")
    cand_cost = _num(candidate, "cost_per_query")
    if base_cost is not None and cand_cost is not None and base_cost > 0:
        cost_reduction = (base_cost - cand_cost) / base_cost
        deltas["cost_reduction"] = round(cost_reduction, 4)
        if cost_reduction < limits["min_cost_reduction"] and cand_quality <= (base_quality or cand_quality):
            blockers.append("insufficient_cost_reduction")

    base_latency = _num(baseline, "latency_ms")
    cand_latency = _num(candidate, "latency_ms")
    if base_latency is not None and cand_latency is not None and base_latency > 0:
        latency_change = (cand_latency - base_latency) / base_latency
        deltas["latency_change"] = round(latency_change, 4)
        if latency_change > limits["max_latency_increase"]:
            blockers.append("latency_regression")

    for key in ("failure_rate", "timeout_rate", "model_error_rate", "contradiction_rate"):
        base_rate = _num(baseline, key)
        cand_rate = _num(candidate, key)
        if base_rate is not None and cand_rate is not None:
            delta = cand_rate - base_rate
            deltas[f"{key}_delta"] = round(delta, 4)
            if delta > limits["max_failure_rate_increase"]:
                blockers.append(f"{key}_regression")

    return {
        "promote": not blockers,
        "blockers": blockers,
        "deltas": deltas,
        "thresholds": limits,
    }


def summarize_controller_distribution(rows: list) -> dict:
    """Summarize controller actions from step telemetry rows."""
    counts = {}
    total = 0
    for row in rows:
        action = row.get("controller_action")
        if not action:
            continue
        counts[action] = counts.get(action, 0) + 1
        total += 1
    return {
        "total_controller_events": total,
        "actions": counts,
        "top_action": max(counts, key=counts.get) if counts else None,
    }
