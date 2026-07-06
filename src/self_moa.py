"""
Self-MoA Mode — when one model dominates, sample it N times instead of running a full panel.

Based on:
- arXiv:2502.00674 "Self-MoA": Sampling one top model N times can outperform
  heterogeneous panel by +6.6%. Use when one model clearly dominates a task type.
- The key insight: model diversity helps when models are roughly equal, but when
  one model is clearly better, sampling it N times gives better results than
  mixing in weaker models' outputs.

Usage:
    from src.self_moa import should_use_self_moa, self_moa_generate
    
    # Check if Self-MoA is appropriate
    if should_use_self_moa(task_type="math", model_perf=perf_data):
        result = await self_moa_generate(question, model, call_model_func, n=5)
    else:
        result = await fuse(question, ...)  # Use full panel
"""
import asyncio
from typing import Callable, Awaitable, Optional
from collections import Counter


# Task types where one model typically dominates
# → use Self-MoA (sample dominant model N times)
SELF_MOA_TASKS = {
    "math",           # DeepSeek V4 Pro dominates math
    "code",           # GLM-5.2 dominates coding
    "reasoning",      # DeepSeek V4 Pro dominates reasoning
    "translation",    # One model usually best for each language pair
}

# Task types where model diversity helps
# → use full heterogeneous panel (fusion)
DIVERSITY_TASKS = {
    "creative",       # Different models bring different styles
    "analysis",       # Multiple perspectives improve analysis
    "factual",        # Cross-checking reduces hallucination
    "general",        # Default: diversity is safer
}

# Default N for Self-MoA
DEFAULT_SELF_MOA_N = 5


def should_use_self_moa(
    task_type: str,
    model_perf: dict = None,
    dominance_threshold: float = 0.7,
) -> bool:
    """Determine if Self-MoA mode should be used.
    
    Self-MoA is appropriate when:
    1. Task type is one where single models tend to dominate (math, code, reasoning)
    2. OR historical performance data shows one model wins >70% of the time
       for this task type
    
    Args:
        task_type: The type of task (math, code, creative, analysis, etc.)
        model_perf: Optional dict of {model_name: win_rate} from historical data
        dominance_threshold: Win rate above which to use Self-MoA (default 0.7)
    
    Returns:
        True if Self-MoA should be used, False if full panel is better
    """
    # Check task type
    if task_type in SELF_MOA_TASKS:
        return True
    
    # Check historical performance data
    if model_perf:
        max_win_rate = max(model_perf.values()) if model_perf else 0
        if max_win_rate >= dominance_threshold:
            return True
    
    return False


def get_dominant_model(model_perf: dict) -> str:
    """Get the model with the highest win rate.
    
    Args:
        model_perf: Dict of {model_name: win_rate}
    
    Returns:
        Model name with highest win rate
    """
    if not model_perf:
        return ""
    return max(model_perf, key=model_perf.get)


async def self_moa_generate(
    question: str,
    model: str,
    call_model_func: Callable[..., Awaitable[str]],
    n: int = DEFAULT_SELF_MOA_N,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    system_prompt: str = "You are Temuclaude, a helpful AI assistant.",
) -> dict:
    """Generate N responses from the same model and select the best.
    
    Self-MoA pattern: sample the dominant model N times at temperature 0.7,
    then use majority voting (for factual) or the model itself as judge
    (for complex tasks) to select the best response.
    
    Args:
        question: The user's question
        model: Model to sample
        call_model_func: Async function to call a model
        n: Number of samples (default 5)
        temperature: Sampling temperature (0.7 for diversity)
        max_tokens: Max tokens per response
        system_prompt: System prompt for generation
    
    Returns:
        Dict with:
        - 'answer': The selected best answer
        - 'all_responses': All N responses
        - 'agreement': Fraction of responses that agree (0.0-1.0)
        - 'method': 'majority_vote' or 'self_judge'
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]
    
    # Generate N responses in parallel
    tasks = [
        call_model_func(model, messages, temperature=temperature, max_tokens=max_tokens)
        for _ in range(n)
    ]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions
    valid_responses = [r for r in responses if isinstance(r, str)]
    
    if not valid_responses:
        return {
            "answer": "",
            "all_responses": responses,
            "agreement": 0.0,
            "method": "self_moa",
        }
    
    # Try majority vote on the last line (for factual/math questions)
    last_lines = []
    for r in valid_responses:
        lines = r.strip().split("\n")
        last_line = lines[-1].strip() if lines else r.strip()
        last_lines.append(last_line)
    
    # Check if there's a clear majority
    counter = Counter(last_lines)
    most_common, count = counter.most_common(1)[0]
    agreement = count / len(valid_responses)
    
    if agreement >= 0.6:
        # Strong agreement — return the response with the majority answer
        for r in valid_responses:
            if r.strip().split("\n")[-1].strip() == most_common:
                return {
                    "answer": r,
                    "all_responses": valid_responses,
                    "agreement": agreement,
                    "method": "majority_vote",
                }
    
    # No clear majority — use self-judge: ask the model to pick the best
    judge_prompt = f"""You are a quality judge. You will be given {len(valid_responses)} responses to the same question.
Select the BEST response based on accuracy, completeness, and clarity.

Question: {question}

"""
    for i, r in enumerate(valid_responses):
        judge_prompt += f"\n--- Response {i+1} ---\n{r[:2000]}\n"
    
    judge_prompt += f"\n\nSelect the BEST response (1-{len(valid_responses)}). Reply with ONLY the number."
    
    judge_messages = [
        {"role": "system", "content": "You are a quality judge. Select the best response."},
        {"role": "user", "content": judge_prompt},
    ]
    
    try:
        judge_response = await call_model_func(model, judge_messages, max_tokens=10)
        # Extract number
        import re
        match = re.search(r'(\d+)', judge_response)
        if match:
            idx = int(match.group(1)) - 1
            if 0 <= idx < len(valid_responses):
                return {
                    "answer": valid_responses[idx],
                    "all_responses": valid_responses,
                    "agreement": agreement,
                    "method": "self_judge",
                }
    except Exception:
        pass
    
    # Fallback: return the first response
    return {
        "answer": valid_responses[0],
        "all_responses": valid_responses,
        "agreement": agreement,
        "method": "fallback_first",
    }