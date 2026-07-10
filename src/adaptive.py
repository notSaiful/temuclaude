"""
Temuclaude Adaptive Routing
Adjusts which model is used for each task type based on performance data.

Based on log analysis: if a different model performs better than the default
for a given task type, switch to that model.

This is data-driven self-improvement — the system learns from its own results.
"""
import json
import os
from typing import Optional
from .models import AGGREGATOR_MAP, TASK_MODEL_MAP, get_runtime_model


ADAPTIVE_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "adaptive_routing.json")


STEP_MODEL_DEFAULTS = {
    "cache": "cache",
    "long_context_retrieval": "minimax-m3",
    "ui_ux_loop": "gemini-3.5-flash",
    "direct_answer": None,  # Task-specific fallback.
    "shepherding": "deepseek-v4-flash",
    "search": "deepseek-v4-pro",
    "repair": "grok-4.5",
    "fusion": "glm-5.2",
    "verification": "nemotron-3-ultra",
    "consistency": None,  # Aggregator-specific fallback.
    "qa_gate": "nemotron-3-ultra",
    "debate": "glm-5.2",
    "premium_escalation": "gpt-5.6-luna",
    "frontier_fallback": "gpt-5.6-terra",
    "budget_forcing": None,
    "formal_verification": "z3",
    "postprocess": "glm-5.2",
}


def get_adaptive_routing() -> dict:
    """
    Load adaptive routing overrides from config file.
    
    Returns:
        Dict mapping task_type → model_name for any task types
        where the default routing should be overridden.
        Empty dict if no overrides exist.
    """
    if not os.path.isfile(ADAPTIVE_CONFIG_PATH):
        return {}
    
    try:
        with open(ADAPTIVE_CONFIG_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def get_model_for_task(task_type: str) -> str:
    """
    Get the best model for a task type, considering adaptive overrides.
    
    Checks adaptive routing first (learned from performance data).
    Falls back to the default TASK_MODEL_MAP.
    
    Args:
        task_type: The classified task type
    
    Returns:
        Model name to use for this task type
    """
    adaptive = get_adaptive_routing()
    
    # Check if adaptive routing has an override for this task type
    if task_type in adaptive:
        return get_runtime_model(adaptive[task_type])
    
    # Fall back to default
    return get_runtime_model(TASK_MODEL_MAP.get(task_type, "glm-5.2"))


def update_adaptive_routing(analysis: dict) -> dict:
    """
    Update adaptive routing based on log analysis.
    
    If the analysis shows a different model performs better than the default
    for a task type (with at least 5 samples), update the override.
    
    Args:
        analysis: Output from analyzer.analyze_logs()
    
    Returns:
        Dict of changes made: {task_type: {old: model, new: model, reason: str}}
    """
    changes = {}
    best_models = analysis.get("best_models", {})
    
    for task_type, info in best_models.items():
        best_model = info["model"]
        best_rate = info["success_rate"]
        count = info["count"]
        
        # Need at least 5 samples to trust the data
        if count < 5:
            continue
        
        # Need at least 80% success rate to switch
        if best_rate < 0.80:
            continue
        
        current_model = TASK_MODEL_MAP.get(task_type, "glm-5.2")
        
        # Only switch if the best model is different from the default
        if best_model != current_model:
            changes[task_type] = {
                "old": current_model,
                "new": best_model,
                "success_rate": best_rate,
                "sample_count": count,
                "reason": f"{best_model} achieved {best_rate:.1%} success over {count} queries vs default {current_model}",
            }
    
    # Save updated routing
    if changes:
        adaptive = get_adaptive_routing()
        for task_type, change in changes.items():
            adaptive[task_type] = change["new"]
        
        # Ensure config directory exists
        config_dir = os.path.dirname(ADAPTIVE_CONFIG_PATH)
        os.makedirs(config_dir, exist_ok=True)
        
        with open(ADAPTIVE_CONFIG_PATH, "w") as f:
            json.dump(adaptive, f, indent=2)
    
    return changes


def reset_adaptive_routing() -> None:
    """Reset adaptive routing to defaults (delete the config file)."""
    if os.path.isfile(ADAPTIVE_CONFIG_PATH):
        os.remove(ADAPTIVE_CONFIG_PATH)


def get_model_for_task_with_router(query: str, task_type: str, tier: str) -> tuple:
    """Get the best model for a task using the trained preference-data router (RouteLLM pattern).
    
    Returns:
        (model_name: str, used_trained_router: bool, router_confidence: float)
    """
    # For trivial tier, always use cheap model
    if tier == "trivial":
        return (get_runtime_model("deepseek-v4-flash"), False, 1.0)
    
    # Try to use trained router
    from .preference_router import route_with_trained_model
    model, confidence, used_trained = route_with_trained_model(query, task_type, tier)
    
    if used_trained and model:
        return (get_runtime_model(model), True, confidence)
    
    # Fall back to default adaptive routing
    model = TASK_MODEL_MAP.get(task_type, "glm-5.2")
    return (get_runtime_model(model), False, 0.0)


def get_fallback_model_for_step(task_type: str, step_type: str) -> str:
    """Return a role-aware fallback model for an orchestration step."""
    try:
        from .step_telemetry import normalize_step_name
    except Exception:
        normalize_step_name = lambda value: value  # noqa: E731

    normalized_step = normalize_step_name(step_type)
    if normalized_step == "verification" and task_type in ("math", "coding"):
        return get_runtime_model(TASK_MODEL_MAP.get(task_type, "deepseek-v4-pro"))
    if normalized_step == "prm_verification":
        return get_runtime_model("nemotron-3-ultra")

    configured = STEP_MODEL_DEFAULTS.get(normalized_step)
    if configured:
        return get_runtime_model(configured)

    if normalized_step == "direct_answer":
        return get_model_for_task(task_type)
    if normalized_step == "consistency":
        return get_runtime_model(AGGREGATOR_MAP.get(task_type, AGGREGATOR_MAP.get("default", "glm-5.2")))
    if normalized_step == "budget_forcing":
        return get_runtime_model(TASK_MODEL_MAP.get(task_type, "deepseek-v4-pro"))
    return get_runtime_model(TASK_MODEL_MAP.get(task_type, "glm-5.2"))


def get_model_for_step(
    task_type: str,
    tier: str,
    step_type: str,
    min_count: int = 3,
) -> tuple:
    """Select a model for a specific orchestration step.

    Uses step telemetry recommendations when enough evidence exists, then falls
    back to role-aware defaults. This is the first bridge from passive telemetry
    to state-aware model selection.

    Returns:
        (model_name, used_step_router, confidence)
    """
    fallback = get_fallback_model_for_step(task_type, step_type)

    try:
        from .step_telemetry import get_step_route_recommendations, normalize_step_name
        normalized_step = normalize_step_name(step_type)
        context_key = f"{task_type}:{tier}:{normalized_step}"
        recommendations = get_step_route_recommendations(min_count=min_count)
        rec = recommendations.get(context_key, {})
        if rec.get("recommendation") == "use_observed_best" and rec.get("recommended_model"):
            candidates = rec.get("candidates", [])
            confidence = 0.0
            if candidates:
                confidence = max(0.0, min(1.0, float(candidates[0].get("utility", 0.0))))
            return get_runtime_model(rec["recommended_model"]), True, round(confidence, 3)
    except Exception:
        pass

    return fallback, False, 0.0
