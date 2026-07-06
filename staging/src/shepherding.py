"""
LLM Shepherding — Cost-efficient SLM-LLM collaboration

Breakthrough technique from arXiv:2601.22132 "Pay for Hints, Not Answers".
Reduces inference costs by 42-94% relative to LLM-only, and 2.8x vs
state-of-the-art routing/cascading — while matching accuracy.

How it works:
  Traditional routing: query → cheap model OR expensive model (all-or-nothing)
  Traditional cascading: query → cheap model → if low confidence → expensive model

  Shepherding: query → expensive model generates a SHORT HINT (10-30% of
  full response) → cheap model uses the hint to complete the full response.

  The expensive model provides "direction" (the hint), the cheap model does
  the "work" (completing the response). This is like a senior engineer
  providing a quick outline and a junior engineer filling in the details.

  Cost: 10-30% of the expensive model's normal cost (only generates a prefix)
  + 100% of the cheap model's cost (generates the rest, but cheap model is 10-100x cheaper)
  = 42-94% total cost reduction with matching accuracy

  Verified on: GSM8K (math), CNK12 (math), HumanEval (code), MBPP (code)

Usage in Temuclaude:
  For medium-tier queries where routing alone would use an expensive model:
  1. Call the expensive model with max_tokens = 10-30% of normal budget
  2. Take that "hint" prefix and append it to the prompt for the cheap model
  3. Call the cheap model to complete the response
  4. The combined output (hint + completion) is the final answer

  Quality: matches LLM-only accuracy (verified in the paper)
  Cost: 42-94% reduction

When to use shepherding:
  - Medium-tier queries where the cheap model alone might miss nuance
  - Math/reasoning tasks where a "direction hint" helps the cheap model
  - Code generation where a "structure hint" helps the cheap model
  - NOT for trivial queries (just use the cheap model directly)
  - NOT for hard queries (use the full expensive model — hints aren't enough)
"""
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Default hint size as a percentage of the normal token budget
DEFAULT_HINT_PERCENTAGE = 0.20  # 20% of normal max_tokens for the hint
MIN_HINT_TOKENS = 50  # Minimum hint size to be useful
MAX_HINT_TOKENS = 500  # Maximum hint size (don't over-pay for hints)

# Models that are good "shepherds" (provide good hints)
# These are the expensive, high-quality models
SHEPHERD_MODELS = ["glm-5.2", "deepseek-v4-pro", "claude-sonnet-5"]

# Models that are good "workers" (complete from hints)
# These are the cheap, fast models
WORKER_MODELS = ["gpt-oss-120b", "deepseek-v4-flash", "qwen3-235b-moe"]


def should_shepherd(
    task_type: str,
    tier: str,
    confidence: float = 0.5,
) -> bool:
    """Decide whether to use shepherding for this query.

    Shepherding is optimal for MEDIUM-tier queries where:
    - The cheap model alone might miss nuance (confidence < 0.7)
    - The expensive model is overkill (it's not a hard query)
    - A hint from the expensive model would help the cheap model succeed

    NOT for:
    - Trivial tier (just use the cheap model — no hint needed)
    - Hard tier (use the full expensive model — a hint isn't enough)
    - Very high confidence cheap model results (don't waste the hint call)

    Args:
        task_type: The classified task type (math, coding, reasoning, etc.)
        tier: The difficulty tier (trivial, medium, hard)
        confidence: The cheap model's confidence score (0.0-1.0) if known

    Returns:
        True if shepherding should be used, False otherwise
    """
    # Only shepherd medium-tier queries
    if tier != "medium":
        return False

    # Only shepherding for medium-tier queries where the cheap model alone
    # might miss nuance. Shepherding works best for math and coding (verified
    # in the paper). Reasoning was NOT verified — excluded for zero quality risk.
    if task_type not in ("math", "coding"):
        return False

    # If the cheap model is already confident, don't shepherd
    if confidence >= 0.8:
        return False

    return True


def calculate_hint_tokens(
    normal_max_tokens: int,
    hint_percentage: float = DEFAULT_HINT_PERCENTAGE,
) -> int:
    """Calculate how many tokens to request from the shepherd model.

    The hint should be 10-30% of the normal response length.
    Too short: not enough direction. Too long: defeats the cost savings.

    Args:
        normal_max_tokens: The normal token budget for a full response.
        hint_percentage: What fraction of the normal budget to use for the hint.

    Returns:
        Number of tokens to request from the shepherd model.
    """
    hint_tokens = int(normal_max_tokens * hint_percentage)
    return max(MIN_HINT_TOKENS, min(hint_tokens, MAX_HINT_TOKENS))


def build_shepherd_messages(
    messages: list,
    hint_tokens: int,
) -> list:
    """Build the messages for the shepherd (expensive) model.

    The shepherd gets the same messages but with a reduced max_tokens.
    We also add a system instruction to provide a concise hint/outline.
    """
    shepherd_messages = list(messages)

    # Add a hint instruction at the start if there's a system message
    hint_instruction = (
        "Provide a concise outline/hint for the answer. "
        f"Keep it to ~{hint_tokens} tokens. Include: key approach, "
        "main steps, critical formulas or code structure. "
        "Do NOT write the full answer — just the direction."
    )

    # If there's a system message, append to it; otherwise add one
    if shepherd_messages and shepherd_messages[0].get("role") == "system":
        shepherd_messages[0] = {
            **shepherd_messages[0],
            "content": shepherd_messages[0]["content"] + "\n\n" + hint_instruction,
        }
    else:
        shepherd_messages.insert(0, {"role": "system", "content": hint_instruction})

    return shepherd_messages


def build_worker_messages(
    messages: list,
    hint: str,
) -> list:
    """Build the messages for the worker (cheap) model.

    The worker gets the original messages plus the hint from the shepherd,
    instructing it to use the hint to complete the full response.
    """
    worker_messages = list(messages)

    hint_context = (
        f"\n\n[HINT FROM SENIOR MODEL — use this as direction to complete the answer]\n"
        f"{hint}\n"
        f"[END HINT — Now write the complete answer using this direction]"
    )

    # Append the hint to the last user message
    for i in range(len(worker_messages) - 1, -1, -1):
        if worker_messages[i].get("role") == "user":
            worker_messages[i] = {
                **worker_messages[i],
                "content": worker_messages[i]["content"] + hint_context,
            }
            break

    return worker_messages


def combine_hint_and_completion(hint: str, completion: str) -> str:
    """Combine the shepherd's hint with the worker's completion.

    If the worker's completion naturally continues from the hint, we
    just return the completion (it already includes the hint's direction).

    If the completion seems to restart from scratch, we prepend the hint
    as context.
    """
    # If the completion is substantial and self-contained, just use it
    # (the worker was instructed to use the hint as direction, so its output
    # should already incorporate the hint's guidance)
    if len(completion) > len(hint) * 2:
        return completion

    # If the completion is short, prepend the hint for context
    return f"{hint}\n\n{completion}"


def estimate_cost_savings(
    shepherd_cost_per_m: float,
    worker_cost_per_m: float,
    hint_tokens: int,
    full_response_tokens: int,
) -> Dict[str, Any]:
    """Estimate the cost savings from shepherding vs LLM-only.

    Args:
        shepherd_cost_per_m: Cost per million tokens for the shepherd (expensive) model
        worker_cost_per_m: Cost per million tokens for the worker (cheap) model
        hint_tokens: Number of tokens generated by the shepherd
        full_response_tokens: Total tokens in the final response

    Returns:
        Dict with cost breakdown and savings percentage
    """
    # Shepherding cost: shepherd generates hint + worker generates full response
    shepherd_cost = (hint_tokens / 1_000_000) * shepherd_cost_per_m
    worker_cost = (full_response_tokens / 1_000_000) * worker_cost_per_m
    shepherding_total = shepherd_cost + worker_cost

    # LLM-only cost: shepherd generates the full response
    llm_only_cost = (full_response_tokens / 1_000_000) * shepherd_cost_per_m

    savings = llm_only_cost - shepherding_total
    savings_pct = (savings / llm_only_cost * 100) if llm_only_cost > 0 else 0.0

    return {
        "shepherding_cost": shepherding_total,
        "llm_only_cost": llm_only_cost,
        "savings_usd": savings,
        "savings_percent": savings_pct,
        "shepherd_cost": shepherd_cost,
        "worker_cost": worker_cost,
        "hint_tokens": hint_tokens,
        "full_response_tokens": full_response_tokens,
    }