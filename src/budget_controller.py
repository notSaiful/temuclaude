"""
Shadow active budget controller for TemuClaude orchestration.

The controller converts runtime state into a recommended next action without
changing orchestration behavior. Runtime gates should consume these decisions
only after benchmark promotion passes.
"""
from dataclasses import asdict, dataclass
from typing import Optional


CONTROLLER_ACTIONS = {
    "continue",
    "verify",
    "debate",
    "stop",
    "escalate",
    "cheap_draft",
}

RECOVERABLE_FAILURES = {
    "model_timeout",
    "model_error",
    "search_failed",
}

DISAGREEMENT_FAILURES = {
    "logical_contradiction",
    "verification_failed",
    "unresolved_debate",
}


@dataclass(frozen=True)
class ControllerDecision:
    action: str
    confidence: float
    reason: str
    cost_risk: str

    def as_dict(self) -> dict:
        return asdict(self)


def _clip01(value: Optional[float], default: float) -> float:
    if not isinstance(value, (int, float)):
        return default
    return max(0.0, min(1.0, float(value)))


def estimate_cost_risk(
    *,
    tier: str,
    remaining_budget_ratio: Optional[float],
    uncertainty: Optional[float],
) -> str:
    """Classify whether another expensive step is budget-risky."""
    ratio = _clip01(remaining_budget_ratio, 1.0)
    unc = _clip01(uncertainty, 0.35)
    if ratio <= 0.15:
        return "critical"
    if ratio <= 0.3 and unc >= 0.55:
        return "high"
    if tier == "hard" and ratio <= 0.4:
        return "medium"
    return "low"


def recommend_controller_action(
    *,
    task_type: str = "unknown",
    tier: str = "unknown",
    step_type: str = "unknown",
    remaining_budget_ratio: Optional[float] = None,
    progress_delta: Optional[float] = None,
    uncertainty: Optional[float] = None,
    failure_label: Optional[str] = None,
    prm_label: Optional[str] = None,
    prm_confidence: Optional[float] = None,
    verifier_passed: Optional[bool] = None,
    success: Optional[bool] = None,
) -> ControllerDecision:
    """Recommend an orchestration action for shadow logging.

    This is deliberately heuristic and conservative. It should be used for
    telemetry and evaluation before any runtime gate acts on it.
    """
    ratio = _clip01(remaining_budget_ratio, 1.0)
    progress = max(-1.0, min(1.0, float(progress_delta))) if isinstance(progress_delta, (int, float)) else 0.0
    unc = _clip01(uncertainty, 0.35)
    prm_conf = _clip01(prm_confidence, 0.0)
    label = (failure_label or "").strip().lower()
    prm = (prm_label or "").strip().lower()
    cost_risk = estimate_cost_risk(tier=tier, remaining_budget_ratio=ratio, uncertainty=unc)

    if verifier_passed is True:
        return ControllerDecision("stop", 0.9, "verifier_passed", cost_risk)

    if prm in {"correct", "valid", "complete"} and prm_conf >= 0.8 and unc <= 0.3:
        return ControllerDecision("stop", 0.82, "high_confidence_prm_accept", cost_risk)

    if label in DISAGREEMENT_FAILURES:
        if ratio >= 0.25 and tier == "hard":
            return ControllerDecision("debate", 0.78, f"resolve_{label}", cost_risk)
        return ControllerDecision("verify", 0.68, f"recheck_{label}", cost_risk)

    if label in RECOVERABLE_FAILURES:
        if tier == "hard" and ratio >= 0.35:
            return ControllerDecision("escalate", 0.75, f"recover_{label}", cost_risk)
        return ControllerDecision("cheap_draft", 0.66, f"budget_recover_{label}", cost_risk)

    if ratio <= 0.15 and progress <= 0:
        if success:
            return ControllerDecision("stop", 0.7, "low_budget_success_no_more_spend", cost_risk)
        return ControllerDecision("cheap_draft", 0.62, "low_budget_no_progress", cost_risk)

    if unc >= 0.65:
        return ControllerDecision("verify", 0.72, "high_uncertainty", cost_risk)

    if prm in {"incorrect", "invalid", "incomplete", "ambiguous"} and prm_conf >= 0.55:
        return ControllerDecision("verify", 0.7, f"prm_{prm}", cost_risk)

    if success and progress >= 0.35 and unc <= 0.25:
        return ControllerDecision("stop", 0.76, "good_progress_low_uncertainty", cost_risk)

    if step_type in {"search", "fusion", "consistency"} and ratio >= 0.3:
        return ControllerDecision("continue", 0.58, "state_allows_continuation", cost_risk)

    if task_type in {"math", "coding", "reasoning"} and unc >= 0.45:
        return ControllerDecision("verify", 0.6, "reasoning_needs_check", cost_risk)

    return ControllerDecision("continue", 0.5, "default_shadow_continue", cost_risk)
