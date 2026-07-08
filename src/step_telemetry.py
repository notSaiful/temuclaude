"""
Step-level orchestration telemetry.

Frontier orchestration systems improve by learning which model or agent should
act at each state of a task, not only which model should handle the whole query.
This module records compact, privacy-light step events that can later train a
state-aware router without changing runtime routing behavior.
"""
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Optional


STEP_TELEMETRY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "step_telemetry.json"
)

MAX_EVENTS = 1000


STEP_ALIASES = {
    "semantic_cache_hit": "cache",
    "mrcr_chunk_and_retrieve_loop": "long_context_retrieval",
    "loop_engine": "ui_ux_loop",
    "direct_frontier_deepseek_v4_pro": "direct_answer",
    "direct_specialist": "direct_answer",
    "direct_worker_fallback": "direct_answer",
    "shepherded_savings": "shepherding",
    "tree_of_thoughts": "search",
    "tot_fallback": "direct_answer",
    "mcts_step_search": "search",
    "self_play_correction": "repair",
    "fusion_3L_MoA": "fusion",
    "step_verify": "verification",
    "code_verify": "verification",
    "prm_consistency": "consistency",
    "usva_qa_passed": "qa_gate",
    "medium_qa_passed": "qa_gate",
    "medium_qa_retried": "qa_gate",
    "debate_escalation": "debate",
    "s1_budget_forcing": "budget_forcing",
    "z3_verified": "formal_verification",
    "z3_contradiction": "formal_verification",
    "debate_z3": "debate",
    "simplified": "postprocess",
}


def _query_hash(query: str) -> str:
    return hashlib.sha256(query.encode("utf-8")).hexdigest()[:16]


def _load() -> dict:
    if not os.path.isfile(STEP_TELEMETRY_FILE):
        return {"events": [], "total_events": 0, "last_updated": None}
    try:
        with open(STEP_TELEMETRY_FILE) as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("step telemetry root must be an object")
        data.setdefault("events", [])
        data.setdefault("total_events", len(data["events"]))
        data.setdefault("last_updated", None)
        return data
    except (OSError, json.JSONDecodeError, ValueError):
        return {"events": [], "total_events": 0, "last_updated": None}


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(STEP_TELEMETRY_FILE), exist_ok=True)
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(STEP_TELEMETRY_FILE, "w") as f:
        json.dump(data, f, indent=2)


def normalize_step_name(raw_step: str) -> str:
    """Map a strategy fragment into a stable training label."""
    raw = (raw_step or "").strip()
    if not raw:
        return "unknown"

    base = raw.split("(", 1)[0]
    for marker, label in STEP_ALIASES.items():
        if marker in base:
            return label
    return base[:64] or "unknown"


def split_strategy(strategy: str) -> list:
    """Split the orchestrator strategy string into ordered step fragments."""
    if not strategy:
        return ["unknown"]
    return [part.strip() for part in strategy.split("+") if part.strip()] or ["unknown"]


def record_step_event(
    *,
    query: str,
    task_type: str,
    tier: str,
    step_type: str,
    model: str,
    strategy: str,
    success: bool,
    latency_ms: Optional[int] = None,
    tokens_used: Optional[int] = None,
    quality_score: Optional[float] = None,
    initial_budget: Optional[float] = None,
    remaining_budget: Optional[float] = None,
    budget_spent: Optional[float] = None,
    progress_delta: Optional[float] = None,
    uncertainty: Optional[float] = None,
    failure_label: Optional[str] = None,
    controller_action: Optional[str] = None,
    controller_confidence: Optional[float] = None,
    controller_reason: Optional[str] = None,
    cost_risk: Optional[str] = None,
    verifier_state: Optional[str] = None,
    prm_label: Optional[str] = None,
    prm_confidence: Optional[float] = None,
    sequence_index: int = 0,
) -> None:
    """Persist a single step event for later router and Pareto analysis."""
    data = _load()
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query_hash": _query_hash(query),
        "query_length": len(query),
        "query_words": len(query.split()),
        "task_type": task_type,
        "tier": tier,
        "step_type": normalize_step_name(step_type),
        "raw_step": step_type[:160] if step_type else "",
        "model": model or "unknown",
        "strategy": strategy[:240] if strategy else "",
        "success": bool(success),
        "latency_ms": latency_ms,
        "tokens_used": tokens_used,
        "quality_score": quality_score,
        "initial_budget": initial_budget,
        "remaining_budget": remaining_budget,
        "budget_spent": budget_spent,
        "remaining_budget_ratio": calculate_remaining_budget_ratio(initial_budget, remaining_budget),
        "progress_delta": progress_delta,
        "uncertainty": uncertainty,
        "failure_label": normalize_failure_label(failure_label),
        "controller_action": controller_action,
        "controller_confidence": controller_confidence,
        "controller_reason": controller_reason,
        "cost_risk": cost_risk,
        "verifier_state": verifier_state,
        "prm_label": normalize_failure_label(prm_label),
        "prm_confidence": prm_confidence,
        "sequence_index": sequence_index,
    }
    data["events"].append(event)
    data["total_events"] = int(data.get("total_events", 0)) + 1
    if len(data["events"]) > MAX_EVENTS:
        data["events"] = data["events"][-MAX_EVENTS:]
    _save(data)


def record_strategy_steps(
    *,
    query: str,
    task_type: str,
    tier: str,
    strategy: str,
    models_used: list,
    success: bool,
    latency_ms: Optional[int] = None,
    tokens_used: Optional[int] = None,
    quality_score: Optional[float] = None,
    initial_budget: Optional[float] = None,
    remaining_budget: Optional[float] = None,
    budget_spent: Optional[float] = None,
    progress_delta: Optional[float] = None,
    uncertainty: Optional[float] = None,
    failure_label: Optional[str] = None,
    controller_action: Optional[str] = None,
    controller_confidence: Optional[float] = None,
    controller_reason: Optional[str] = None,
    cost_risk: Optional[str] = None,
    verifier_state: Optional[str] = None,
    prm_label: Optional[str] = None,
    prm_confidence: Optional[float] = None,
) -> None:
    """Record one event per strategy fragment from an orchestrator run."""
    steps = split_strategy(strategy)
    if not models_used:
        models_used = ["unknown"]
    for idx, step in enumerate(steps):
        model = models_used[min(idx, len(models_used) - 1)]
        record_step_event(
            query=query,
            task_type=task_type,
            tier=tier,
            step_type=step,
            model=model,
            strategy=strategy,
            success=success,
            latency_ms=latency_ms,
            tokens_used=tokens_used,
            quality_score=quality_score,
            initial_budget=initial_budget,
            remaining_budget=remaining_budget,
            budget_spent=budget_spent,
            progress_delta=progress_delta,
            uncertainty=uncertainty,
            failure_label=failure_label,
            controller_action=controller_action,
            controller_confidence=controller_confidence,
            controller_reason=controller_reason,
            cost_risk=cost_risk,
            verifier_state=verifier_state,
            prm_label=prm_label,
            prm_confidence=prm_confidence,
            sequence_index=idx,
        )


def calculate_remaining_budget_ratio(
    initial_budget: Optional[float],
    remaining_budget: Optional[float],
) -> Optional[float]:
    """Return remaining / initial budget, clipped to [0, 1] when available."""
    if not isinstance(initial_budget, (int, float)) or not isinstance(remaining_budget, (int, float)):
        return None
    if initial_budget <= 0:
        return None
    return round(max(0.0, min(1.0, remaining_budget / initial_budget)), 4)


def normalize_failure_label(label: Optional[str]) -> Optional[str]:
    """Normalize failure labels for future failure-attribution training."""
    if not label:
        return None
    normalized = "".join(ch.lower() if ch.isalnum() else "_" for ch in label.strip())
    normalized = "_".join(part for part in normalized.split("_") if part)
    return normalized[:64] or None


def infer_failure_label(success: bool, strategy: str = "", answer: str = "") -> Optional[str]:
    """Infer a coarse failure label from runtime artifacts.

    This is intentionally conservative. It is a bootstrap signal for later
    failure-attribution training, not a final verifier judgment.
    """
    if success:
        return None

    text = f"{strategy}\n{answer}".lower()
    if not answer or not answer.strip():
        return "empty_answer"
    if "timed out" in text or "timeout" in text:
        return "model_timeout"
    if "[error" in text or " failed:" in text:
        return "model_error"
    if "z3_contradiction" in text or "contradiction" in text:
        return "logical_contradiction"
    if "step_verify" in text or "code_verify" in text or "verification" in text:
        return "verification_failed"
    if "tree_of_thoughts" in text or "mcts_step_search" in text:
        return "search_failed"
    if "debate" in text:
        return "unresolved_debate"
    return "unknown_failure"


def infer_progress_delta(success: bool, strategy: str = "", answer: str = "") -> float:
    """Infer a coarse progress signal in [-1, 1] from observed run metadata."""
    text = f"{strategy}\n{answer}".lower()
    if not success:
        if "empty_answer" in infer_failure_label(False, strategy, answer) or not answer.strip():
            return -0.8
        return -0.5

    progress = 0.2
    positive_markers = [
        "qa_passed", "code_verify", "step_verify", "z3_verified",
        "self_play_correction", "prm_consistency", "simplified",
    ]
    progress += 0.1 * sum(1 for marker in positive_markers if marker in text)
    if "debate_escalation" in text or "qa_retried" in text:
        progress -= 0.05
    if "[error" in text or "contradiction" in text:
        progress -= 0.3
    return round(max(-1.0, min(1.0, progress)), 4)


def infer_uncertainty(success: bool, strategy: str = "", answer: str = "") -> float:
    """Infer a coarse uncertainty score in [0, 1] from strategy and answer."""
    text = f"{strategy}\n{answer}".lower()
    if not success:
        return 0.9 if "[error" in text or not answer.strip() else 0.75
    if "z3_verified" in text or "code_verify" in text or "step_verify" in text:
        return 0.15
    if "qa_passed" in text or "prm_consistency" in text:
        return 0.25
    if "debate" in text or "qa_retried" in text or "contradiction" in text:
        return 0.55
    return 0.35


def build_runtime_step_metadata(
    *,
    token_budget: Optional[int],
    tokens_used: Optional[int],
    success: bool,
    strategy: str = "",
    answer: str = "",
) -> dict:
    """Build coarse budget/progress/failure metadata from an orchestrator run."""
    initial_budget = token_budget if isinstance(token_budget, (int, float)) else None
    spent = tokens_used if isinstance(tokens_used, (int, float)) else None
    remaining = None
    if initial_budget is not None and spent is not None:
        remaining = max(0, initial_budget - spent)
    progress_delta = infer_progress_delta(success, strategy, answer)
    uncertainty = infer_uncertainty(success, strategy, answer)
    failure_label = infer_failure_label(success, strategy, answer)
    remaining_ratio = calculate_remaining_budget_ratio(initial_budget, remaining)
    verifier_state = "passed" if any(marker in (strategy or "") for marker in ("step_verify", "code_verify", "z3_verified", "qa_passed")) else None
    try:
        from .budget_controller import recommend_controller_action
        decision = recommend_controller_action(
            tier="unknown",
            step_type="unknown",
            remaining_budget_ratio=remaining_ratio,
            progress_delta=progress_delta,
            uncertainty=uncertainty,
            failure_label=failure_label,
            verifier_passed=verifier_state == "passed",
            success=success,
        )
        controller = decision.as_dict()
    except Exception:
        controller = {}

    return {
        "initial_budget": initial_budget,
        "remaining_budget": remaining,
        "budget_spent": spent,
        "progress_delta": progress_delta,
        "uncertainty": uncertainty,
        "failure_label": failure_label,
        "controller_action": controller.get("action"),
        "controller_confidence": controller.get("confidence"),
        "controller_reason": controller.get("reason"),
        "cost_risk": controller.get("cost_risk"),
        "verifier_state": verifier_state,
    }


def summarize_step_performance() -> dict:
    """Aggregate step telemetry into success, latency, and token summaries."""
    data = _load()
    summary = {}
    for event in data.get("events", []):
        key = event.get("step_type", "unknown")
        if key not in summary:
            summary[key] = {
                "count": 0,
                "successes": 0,
                "total_latency_ms": 0,
                "latency_count": 0,
                "total_tokens": 0,
                "token_count": 0,
                "progress_values": [],
                "budget_ratios": [],
                "failure_labels": {},
                "controller_actions": {},
                "models": {},
            }
        row = summary[key]
        row["count"] += 1
        if event.get("success"):
            row["successes"] += 1
        latency = event.get("latency_ms")
        if isinstance(latency, int):
            row["total_latency_ms"] += latency
            row["latency_count"] += 1
        tokens = event.get("tokens_used")
        if isinstance(tokens, int):
            row["total_tokens"] += tokens
            row["token_count"] += 1
        model = event.get("model") or "unknown"
        row["models"][model] = row["models"].get(model, 0) + 1
        progress = event.get("progress_delta")
        if isinstance(progress, (int, float)):
            row["progress_values"].append(progress)
        budget_ratio = event.get("remaining_budget_ratio")
        if isinstance(budget_ratio, (int, float)):
            row["budget_ratios"].append(budget_ratio)
        failure_label = event.get("failure_label")
        if failure_label:
            row["failure_labels"][failure_label] = row["failure_labels"].get(failure_label, 0) + 1
        controller_action = event.get("controller_action")
        if controller_action:
            row["controller_actions"][controller_action] = row["controller_actions"].get(controller_action, 0) + 1

    for row in summary.values():
        count = row["count"] or 1
        row["success_rate"] = round(row["successes"] / count, 3)
        row["avg_latency_ms"] = (
            round(row["total_latency_ms"] / row["latency_count"])
            if row["latency_count"] else None
        )
        row["avg_tokens"] = (
            round(row["total_tokens"] / row["token_count"])
            if row["token_count"] else None
        )
        row["top_model"] = max(row["models"], key=row["models"].get) if row["models"] else None
        row["avg_progress_delta"] = (
            round(sum(row["progress_values"]) / len(row["progress_values"]), 4)
            if row["progress_values"] else None
        )
        row["avg_remaining_budget_ratio"] = (
            round(sum(row["budget_ratios"]) / len(row["budget_ratios"]), 4)
            if row["budget_ratios"] else None
        )
        row["top_failure_label"] = (
            max(row["failure_labels"], key=row["failure_labels"].get)
            if row["failure_labels"] else None
        )
        row["top_controller_action"] = (
            max(row["controller_actions"], key=row["controller_actions"].get)
            if row["controller_actions"] else None
        )
    return summary


def get_step_dataset(success_only: bool = False) -> list:
    """Return normalized state-action-outcome rows for router training.

    Each row represents one orchestration step. The `context_key` is intentionally
    simple so early data remains usable before a learned state encoder exists.
    """
    data = _load()
    dataset = []
    for event in data.get("events", []):
        if success_only and not event.get("success"):
            continue
        task_type = event.get("task_type") or "unknown"
        tier = event.get("tier") or "unknown"
        step_type = event.get("step_type") or "unknown"
        dataset.append({
            "context_key": f"{task_type}:{tier}:{step_type}",
            "task_type": task_type,
            "tier": tier,
            "step_type": step_type,
            "model": event.get("model") or "unknown",
            "success": bool(event.get("success")),
            "timestamp": event.get("timestamp"),
            "latency_ms": event.get("latency_ms"),
            "tokens_used": event.get("tokens_used"),
            "quality_score": event.get("quality_score"),
            "initial_budget": event.get("initial_budget"),
            "remaining_budget": event.get("remaining_budget"),
            "budget_spent": event.get("budget_spent"),
            "remaining_budget_ratio": event.get("remaining_budget_ratio"),
            "progress_delta": event.get("progress_delta"),
            "uncertainty": event.get("uncertainty"),
            "failure_label": event.get("failure_label"),
            "controller_action": event.get("controller_action"),
            "controller_confidence": event.get("controller_confidence"),
            "controller_reason": event.get("controller_reason"),
            "cost_risk": event.get("cost_risk"),
            "verifier_state": event.get("verifier_state"),
            "prm_label": event.get("prm_label"),
            "prm_confidence": event.get("prm_confidence"),
            "sequence_index": event.get("sequence_index", 0),
            "query_words": event.get("query_words", 0),
            "query_length": event.get("query_length", 0),
        })
    return dataset


def _mean(values: list) -> Optional[float]:
    nums = [v for v in values if isinstance(v, (int, float))]
    if not nums:
        return None
    return sum(nums) / len(nums)


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except (TypeError, ValueError):
        return None


def _recency_weight(timestamp: Optional[str], half_life_days: Optional[float]) -> float:
    """Return exponential recency weight; 1.0 when decay is disabled."""
    if not half_life_days or half_life_days <= 0:
        return 1.0
    parsed = _parse_timestamp(timestamp)
    if parsed is None:
        return 1.0
    age_seconds = max(0.0, (datetime.now(timezone.utc) - parsed).total_seconds())
    half_life_seconds = half_life_days * 86400.0
    return 0.5 ** (age_seconds / half_life_seconds)


def _weighted_mean(values: list, weights: list) -> Optional[float]:
    pairs = [
        (value, weight)
        for value, weight in zip(values, weights)
        if isinstance(value, (int, float)) and isinstance(weight, (int, float)) and weight > 0
    ]
    if not pairs:
        return None
    total_weight = sum(weight for _, weight in pairs)
    if total_weight <= 0:
        return None
    return sum(value * weight for value, weight in pairs) / total_weight


def get_step_route_recommendations(
    min_count: int = 3,
    latency_penalty_per_second: float = 0.01,
    token_penalty_per_1k: float = 0.005,
    progress_weight: float = 0.1,
    uncertainty_penalty: float = 0.05,
    recency_half_life_days: Optional[float] = None,
) -> dict:
    """Recommend the best observed model for each `(task, tier, step)` state.

    Utility is intentionally transparent:

        success_rate - latency_penalty - token_penalty

    This creates a cheap bridge toward ParetoBandit/SeqRoute-style learned
    controllers while there is not enough telemetry for a real contextual model.
    """
    rows = get_step_dataset()
    grouped = {}

    for row in rows:
        context_key = row["context_key"]
        model = row["model"]
        grouped.setdefault(context_key, {})
        grouped[context_key].setdefault(model, {
            "count": 0,
            "successes": 0,
            "latencies": [],
            "tokens": [],
            "qualities": [],
            "progress": [],
            "uncertainties": [],
            "budget_ratios": [],
            "success_flags": [],
            "weights": [],
            "failure_labels": {},
        })
        stats = grouped[context_key][model]
        event_weight = _recency_weight(row.get("timestamp"), recency_half_life_days)
        stats["count"] += 1
        if row["success"]:
            stats["successes"] += 1
        stats["success_flags"].append(1.0 if row["success"] else 0.0)
        stats["weights"].append(event_weight)
        stats["latencies"].append(row.get("latency_ms"))
        stats["tokens"].append(row.get("tokens_used"))
        stats["qualities"].append(row.get("quality_score"))
        stats["progress"].append(row.get("progress_delta"))
        stats["uncertainties"].append(row.get("uncertainty"))
        stats["budget_ratios"].append(row.get("remaining_budget_ratio"))
        failure_label = row.get("failure_label")
        if failure_label:
            stats["failure_labels"][failure_label] = stats["failure_labels"].get(failure_label, 0) + 1

    recommendations = {}
    for context_key, model_stats in grouped.items():
        candidates = []
        total_count = sum(stats["count"] for stats in model_stats.values())
        for model, stats in model_stats.items():
            count = stats["count"]
            weights = stats["weights"]
            if recency_half_life_days:
                success_rate = _weighted_mean(stats["success_flags"], weights) or 0.0
                avg_latency = _weighted_mean(stats["latencies"], weights)
                avg_tokens = _weighted_mean(stats["tokens"], weights)
                avg_quality = _weighted_mean(stats["qualities"], weights)
                avg_progress = _weighted_mean(stats["progress"], weights)
                avg_uncertainty = _weighted_mean(stats["uncertainties"], weights)
                avg_budget_ratio = _weighted_mean(stats["budget_ratios"], weights)
            else:
                success_rate = stats["successes"] / count if count else 0.0
                avg_latency = _mean(stats["latencies"])
                avg_tokens = _mean(stats["tokens"])
                avg_quality = _mean(stats["qualities"])
                avg_progress = _mean(stats["progress"])
                avg_uncertainty = _mean(stats["uncertainties"])
                avg_budget_ratio = _mean(stats["budget_ratios"])

            latency_cost = (
                (avg_latency / 1000.0) * latency_penalty_per_second
                if avg_latency is not None else 0.0
            )
            token_cost = (
                (avg_tokens / 1000.0) * token_penalty_per_1k
                if avg_tokens is not None else 0.0
            )
            utility = success_rate - latency_cost - token_cost
            if avg_quality is not None:
                utility += max(0.0, min(avg_quality, 1.0)) * 0.05
            if avg_progress is not None:
                utility += avg_progress * progress_weight
            if avg_uncertainty is not None:
                utility -= max(0.0, min(avg_uncertainty, 1.0)) * uncertainty_penalty
            if recency_half_life_days:
                recency_confidence = min(1.0, sum(weights) / max(count, 1))
                utility *= recency_confidence

            candidates.append({
                "model": model,
                "count": count,
                "effective_count": round(sum(weights), 3) if recency_half_life_days else count,
                "success_rate": round(success_rate, 3),
                "avg_latency_ms": round(avg_latency) if avg_latency is not None else None,
                "avg_tokens": round(avg_tokens) if avg_tokens is not None else None,
                "avg_quality": round(avg_quality, 3) if avg_quality is not None else None,
                "avg_progress_delta": round(avg_progress, 4) if avg_progress is not None else None,
                "avg_uncertainty": round(avg_uncertainty, 4) if avg_uncertainty is not None else None,
                "avg_remaining_budget_ratio": round(avg_budget_ratio, 4) if avg_budget_ratio is not None else None,
                "top_failure_label": (
                    max(stats["failure_labels"], key=stats["failure_labels"].get)
                    if stats["failure_labels"] else None
                ),
                "utility": round(utility, 4),
            })

        candidates.sort(key=lambda item: (item["utility"], item["count"]), reverse=True)
        best = candidates[0] if candidates else None
        recommendations[context_key] = {
            "recommendation": "use_observed_best" if total_count >= min_count else "collect_more_data",
            "recommended_model": best["model"] if best and total_count >= min_count else None,
            "total_count": total_count,
            "needed": max(0, min_count - total_count),
            "candidates": candidates,
        }

    return recommendations


def get_budget_alerts(
    min_count: int = 3,
    low_budget_ratio: float = 0.2,
    min_failure_rate: float = 0.5,
) -> dict:
    """Flag states where low remaining budget and failures co-occur.

    These alerts are a conservative precursor to BAGEN-style early stop or
    clarification behavior. They only inspect telemetry; they do not stop runs.
    """
    rows = get_step_dataset()
    grouped = {}
    for row in rows:
        key = row["context_key"]
        grouped.setdefault(key, {"count": 0, "failures": 0, "low_budget": 0})
        grouped[key]["count"] += 1
        if not row["success"]:
            grouped[key]["failures"] += 1
        ratio = row.get("remaining_budget_ratio")
        if isinstance(ratio, (int, float)) and ratio <= low_budget_ratio:
            grouped[key]["low_budget"] += 1

    alerts = {}
    for key, stats in grouped.items():
        count = stats["count"]
        if count < min_count:
            continue
        failure_rate = stats["failures"] / count if count else 0.0
        low_budget_rate = stats["low_budget"] / count if count else 0.0
        if failure_rate >= min_failure_rate and low_budget_rate > 0:
            alerts[key] = {
                "count": count,
                "failure_rate": round(failure_rate, 3),
                "low_budget_rate": round(low_budget_rate, 3),
                "recommendation": "consider_early_abort_or_escalation",
            }
    return alerts
