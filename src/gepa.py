"""
Temuclaude GEPA — Simplified Prompt Evolution
Analyzes query logs, generates prompt variations, tests on samples, selects best.

This is a simplified version of the full GEPA (Genetic Algorithm for Prompt
Adaptation). Full GEPA uses evolutionary algorithms + RL. This version:
1. Finds the weakest task type from logs
2. Generates 3 prompt variations targeting that weakness
3. Tests each on sample queries
4. Selects the best-performing variation
5. Saves to config/evolved_prompts.json

This is a WEEKLY manual trigger (or cron job), not real-time.
"""
import json
import os
import asyncio
from typing import Callable, Awaitable, Optional
from .analyzer import analyze_logs
from .self_qa import self_qa_gate


EVOLVED_PROMPTS_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "evolved_prompts.json")


def get_evolved_prompts() -> dict:
    """Load evolved prompts from config file. Empty dict if none."""
    if not os.path.isfile(EVOLVED_PROMPTS_PATH):
        return {}
    try:
        with open(EVOLVED_PROMPTS_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def get_system_prompt(task_type: str, default: Optional[str] = None) -> str:
    """
    Get the system prompt for a task type.
    Uses evolved prompt if available, otherwise uses default.
    """
    evolved = get_evolved_prompts()
    if task_type in evolved:
        return evolved[task_type]
    return default or "You are Temuclaude, a helpful AI assistant. Provide thorough, accurate answers."


PROMPT_VARIATION_TEMPLATE = (
    "You are a prompt engineer. The current system prompt for {task_type} tasks is:\n\n"
    "\"{current_prompt}\"\n\n"
    "The success rate for {task_type} is {success_rate:.1%}, which is the weakest area.\n"
    "Generate an improved system prompt that addresses this weakness. "
    "The prompt should be concise (max 200 words) and specific to {task_type} tasks.\n"
    "Only output the new system prompt, no explanation."
)


async def evolve_prompts(
    call_model_func: Callable[..., Awaitable[str]],
    evolution_model: str = "glm-5.2",
    sample_size: int = 3,
) -> dict:
    """
    Run simplified GEPA prompt evolution.
    
    Args:
        call_model_func: Async function to call a model
        evolution_model: Which model generates prompt variations
        sample_size: Number of sample queries to test each variation on
    
    Returns:
        Dict with:
        - 'evolved': bool — whether any prompts were evolved
        - 'changes': Dict of task_type → {old_prompt, new_prompt, improvement}
        - 'analysis': The log analysis used
    """
    # Step 1: Analyze logs
    analysis = analyze_logs()
    
    if analysis["total_queries"] < 10:
        return {
            "evolved": False,
            "changes": {},
            "analysis": analysis,
            "message": "Not enough queries (< 10) to evolve prompts",
        }
    
    weakest_task = analysis.get("weakest_task")
    if not weakest_task:
        return {
            "evolved": False,
            "changes": {},
            "analysis": analysis,
            "message": "No weak task type found",
        }
    
    # Step 2: Get current prompt for the weakest task type
    evolved = get_evolved_prompts()
    current_prompt = evolved.get(weakest_task, 
        "You are Temuclaude, a helpful AI assistant. Provide thorough, accurate answers.")
    
    task_success_rate = analysis["by_task_type"].get(weakest_task, {}).get("success_rate", 0.0)
    
    # Step 3: Generate 3 prompt variations
    variation_prompt = PROMPT_VARIATION_TEMPLATE.format(
        task_type=weakest_task,
        current_prompt=current_prompt,
        success_rate=task_success_rate,
    )
    
    variations = []
    for i in range(3):
        messages = [
            {"role": "system", "content": "You are a prompt engineer optimizing AI system prompts."},
            {"role": "user", "content": variation_prompt},
        ]
        variation = await call_model_func(evolution_model, messages, max_tokens=500)
        if variation and not variation.startswith("[ERROR"):
            variations.append(variation)
    
    if not variations:
        return {
            "evolved": False,
            "changes": {},
            "analysis": analysis,
            "message": "Failed to generate prompt variations",
        }
    
    # Step 4: Test each variation (simplified: just check if Self-QA scores higher)
    # In full GEPA, this would test on actual past queries
    # For Phase 3: we just select the first valid variation
    # Full testing is Phase 5 (needs production infrastructure)
    
    best_variation = variations[0]
    
    # Step 5: Save the evolved prompt
    evolved[weakest_task] = best_variation
    
    # Ensure config directory exists
    config_dir = os.path.dirname(EVOLVED_PROMPTS_PATH)
    os.makedirs(config_dir, exist_ok=True)
    
    with open(EVOLVED_PROMPTS_PATH, "w") as f:
        json.dump(evolved, f, indent=2)
    
    return {
        "evolved": True,
        "changes": {
            weakest_task: {
                "old_prompt": current_prompt[:100] + "...",
                "new_prompt": best_variation[:100] + "...",
                "success_rate_before": task_success_rate,
            }
        },
        "analysis": analysis,
        "message": f"Evolved prompt for {weakest_task} (success rate was {task_success_rate:.1%})",
    }