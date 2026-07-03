"""
Timuclaude Adaptive Routing
Adjusts which model is used for each task type based on performance data.

Based on log analysis: if a different model performs better than the default
for a given task type, switch to that model.

This is data-driven self-improvement — the system learns from its own results.
"""
import json
import os
from typing import Optional
from .models import TASK_MODEL_MAP


ADAPTIVE_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "adaptive_routing.json")


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
        return adaptive[task_type]
    
    # Fall back to default
    return TASK_MODEL_MAP.get(task_type, "glm-5.2")


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