"""
Temuclaude Pareto Efficiency Tracker
Tracks the trade-off between token savings and accuracy loss.

Based on:
- ATTS (2025): 28% token savings with 2% accuracy cost → Pareto improvement
- BEST-Route: 60% cost reduction with <1% performance drop
- The principle: maintain savings > 20%, loss < 5% to stay on Pareto frontier

This module:
1. Tracks every query's token usage and outcome (correct/incorrect/unknown)
2. Calculates running token_savings vs a baseline (always-use-maximum-compute)
3. Calculates running accuracy_loss vs baseline
4. Auto-tunes thresholds to maintain Pareto improvement
5. If accuracy drops too much, increases compute allocation
6. If savings drop too much, decreases compute allocation

Data is saved to config/pareto_metrics.json for persistence.
"""
import json
import os
from datetime import datetime, timezone
from collections import defaultdict
from typing import Optional


METRICS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "pareto_metrics.json"
)

# Pareto targets
TARGET_SAVINGS_MIN = 20.0  # Must save at least 20% tokens
TARGET_LOSS_MAX = 5.0      # Must not lose more than 5% accuracy
ADJUSTMENT_FACTOR = 0.1    # How much to adjust budgets when off-target

# Baseline: always use maximum compute (hard tier, max tokens, max samples)
BASELINE_TOKENS = {
    "trivial": 8192,   # Baseline: always max tokens
    "medium": 8192,     # Baseline: always max tokens
    "hard": 8192,       # Baseline: already max
}

# Current adaptive budgets (what we actually use)
CURRENT_BUDGETS = {
    "trivial": 500,
    "medium": 4096,
    "hard": 8192,
}


def load_metrics() -> dict:
    """Load persisted Pareto metrics."""
    if not os.path.isfile(METRICS_FILE):
        return {
            "queries": [],
            "total_queries": 0,
            "total_tokens_used": 0,
            "total_tokens_baseline": 0,
            "correct": 0,
            "incorrect": 0,
            "unknown": 0,
            "tier_stats": defaultdict(lambda: {"count": 0, "tokens": 0, "baseline": 0, "correct": 0}),
            "last_updated": None,
        }
    try:
        with open(METRICS_FILE) as f:
            data = json.load(f)
        # Convert tier_stats back to defaultdict
        if "tier_stats" in data and isinstance(data["tier_stats"], dict):
            ts = defaultdict(lambda: {"count": 0, "tokens": 0, "baseline": 0, "correct": 0})
            ts.update(data["tier_stats"])
            data["tier_stats"] = ts
        return data
    except (json.JSONDecodeError, IOError):
        return {
            "queries": [], "total_queries": 0, "total_tokens_used": 0,
            "total_tokens_baseline": 0, "correct": 0, "incorrect": 0, "unknown": 0,
            "tier_stats": defaultdict(lambda: {"count": 0, "tokens": 0, "baseline": 0, "correct": 0}),
            "last_updated": None,
        }


def save_metrics(metrics: dict) -> None:
    """Persist Pareto metrics."""
    os.makedirs(os.path.dirname(METRICS_FILE), exist_ok=True)
    # Convert defaultdict to regular dict for JSON
    if isinstance(metrics.get("tier_stats"), defaultdict):
        metrics["tier_stats"] = dict(metrics["tier_stats"])
    metrics["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(METRICS_FILE, "w") as f:
        json.dump(metrics, f, indent=2, default=str)


def record_query(
    tier: str,
    tokens_used: int,
    correct: Optional[bool] = None,
    task_type: str = "",
    strategy: str = "",
) -> None:
    """Record a single query's metrics.
    
    Args:
        tier: Difficulty tier (trivial, medium, hard)
        tokens_used: Actual tokens consumed by this query
        correct: Whether the answer was correct (None = unknown)
        task_type: The classified task type
        strategy: The orchestration strategy used
    """
    metrics = load_metrics()
    
    baseline_tokens = BASELINE_TOKENS.get(tier, 8192)
    
    # Update totals
    metrics["total_queries"] += 1
    metrics["total_tokens_used"] += tokens_used
    metrics["total_tokens_baseline"] += baseline_tokens
    
    # Update accuracy tracking
    if correct is True:
        metrics["correct"] += 1
    elif correct is False:
        metrics["incorrect"] += 1
    else:
        metrics["unknown"] += 1
    
    # Update per-tier stats
    ts = metrics["tier_stats"]
    if isinstance(ts, dict):
        ts = defaultdict(lambda: {"count": 0, "tokens": 0, "baseline": 0, "correct": 0})
        ts.update(metrics["tier_stats"])
    
    if tier not in ts:
        ts[tier] = {"count": 0, "tokens": 0, "baseline": 0, "correct": 0}
    
    ts[tier]["count"] += 1
    ts[tier]["tokens"] += tokens_used
    ts[tier]["baseline"] += baseline_tokens
    if correct is True:
        ts[tier]["correct"] += 1
    
    metrics["tier_stats"] = ts
    
    # Record individual query (keep last 100 to avoid bloat)
    metrics["queries"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tier": tier,
        "tokens_used": tokens_used,
        "baseline_tokens": baseline_tokens,
        "correct": correct,
        "task_type": task_type,
        "strategy": strategy,
    })
    if len(metrics["queries"]) > 100:
        metrics["queries"] = metrics["queries"][-100:]
    
    save_metrics(metrics)


def calculate_pareto() -> dict:
    """Calculate current Pareto efficiency metrics.
    
    Returns:
        Dict with:
        - 'token_savings_pct': How much we're saving vs baseline
        - 'accuracy_pct': Estimated accuracy (correct / (correct + incorrect))
        - 'accuracy_loss_pct': Estimated loss vs 100% baseline
        - 'is_pareto_improvement': True if savings > 20% AND loss < 5%
        - 'recommendation': What to adjust if off-target
    """
    metrics = load_metrics()
    
    if metrics["total_queries"] == 0:
        return {
            "token_savings_pct": 0.0,
            "accuracy_pct": 100.0,
            "accuracy_loss_pct": 0.0,
            "is_pareto_improvement": True,
            "recommendation": "No data yet — collecting metrics",
            "total_queries": 0,
        }
    
    # Token savings
    if metrics["total_tokens_baseline"] > 0:
        savings = (1 - metrics["total_tokens_used"] / metrics["total_tokens_baseline"]) * 100
    else:
        savings = 0.0
    
    # Accuracy (only count queries with known correctness)
    known = metrics["correct"] + metrics["incorrect"]
    if known > 0:
        accuracy = (metrics["correct"] / known) * 100
    else:
        accuracy = 100.0  # Assume good if we can't measure
    
    loss = 100.0 - accuracy
    
    # Pareto check
    is_pareto = savings >= TARGET_SAVINGS_MIN and loss <= TARGET_LOSS_MAX
    
    # Recommendation
    if savings < TARGET_SAVINGS_MIN and loss <= TARGET_LOSS_MAX:
        recommendation = "Increase savings: reduce token budgets for trivial/medium tiers"
    elif savings >= TARGET_SAVINGS_MIN and loss > TARGET_LOSS_MAX:
        recommendation = "Reduce loss: increase token budgets or sample counts"
    elif savings < TARGET_SAVINGS_MIN and loss > TARGET_LOSS_MAX:
        recommendation = "WARNING: Off Pareto frontier — both savings and accuracy are poor. Review routing."
    else:
        recommendation = "On Pareto frontier — maintain current settings"
    
    # Per-tier breakdown
    tier_breakdown = {}
    ts = metrics.get("tier_stats", {})
    if isinstance(ts, defaultdict):
        ts = dict(ts)
    
    for tier, stats in ts.items():
        if isinstance(stats, dict) and stats.get("count", 0) > 0:
            tier_savings = (1 - stats["tokens"] / stats["baseline"]) * 100 if stats["baseline"] > 0 else 0
            tier_accuracy = (stats["correct"] / stats["count"]) * 100 if stats["count"] > 0 else 100
            tier_breakdown[tier] = {
                "queries": stats["count"],
                "token_savings_pct": round(tier_savings, 1),
                "accuracy_pct": round(tier_accuracy, 1),
            }
    
    return {
        "token_savings_pct": round(savings, 1),
        "accuracy_pct": round(accuracy, 1),
        "accuracy_loss_pct": round(loss, 1),
        "is_pareto_improvement": is_pareto,
        "recommendation": recommendation,
        "total_queries": metrics["total_queries"],
        "tier_breakdown": tier_breakdown,
    }


def get_adjusted_budgets() -> dict:
    """Get dynamically adjusted token budgets based on Pareto metrics.
    
    If accuracy is too low, increase budgets.
    If savings are too low, decrease budgets.
    """
    pareto = calculate_pareto()
    budgets = dict(CURRENT_BUDGETS)
    
    if pareto["total_queries"] < 10:
        # Not enough data — use defaults
        return budgets
    
    # Adjust based on Pareto status
    if pareto["accuracy_loss_pct"] > TARGET_LOSS_MAX:
        # Accuracy too low — increase budgets
        for tier in budgets:
            budgets[tier] = int(budgets[tier] * (1 + ADJUSTMENT_FACTOR))
    elif pareto["token_savings_pct"] < TARGET_SAVINGS_MIN:
        # Savings too low — decrease budgets (but not below 256)
        for tier in budgets:
            budgets[tier] = max(256, int(budgets[tier] * (1 - ADJUSTMENT_FACTOR)))
    
    return budgets


if __name__ == "__main__":
    result = calculate_pareto()
    print(json.dumps(result, indent=2))