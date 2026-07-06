"""
Unified Routing + Cascading Module

Combines model selection (routing) + quality escalation (cascading) into
a single unified strategy.

Based on:
- arXiv:2410.10347 (ICLR 2025): "Consistently outperforms either approach alone"
- RouteLLM (arXiv:2406.18665): 2x cost reduction with preference-data routing
- BEST-Route: 60% cost reduction with adaptive sample count

The unified strategy:
1. Route: Classify query difficulty → select initial model tier
2. Generate: Get response from routed model
3. Verify: Score response quality (self-QA)
4. Cascade: If quality < threshold, escalate to stronger model
5. Repeat: Until quality passes or max cascade depth reached

This is different from the existing adaptive.py which only does routing.
The cascade (step 4) is the key addition — it's the escalation mechanism.
"""
import asyncio
from typing import Callable, Awaitable, Optional
from dataclasses import dataclass


# Difficulty tiers and their model assignments
TIER_MODELS = {
    "trivial": "gpt-oss-120b",        # Cheapest — free or $0.03/M
    "medium": "glm-5.2",               # Mid-tier — $0.06/M on Ollama
    "hard": "deepseek-v4-pro",         # Premium — strong reasoning
    "extreme": "kimi-k2.6",            # Most capable — agentic
}

# Cascade chain: if trivial fails → medium → hard → extreme
CASCADE_CHAIN = ["trivial", "medium", "hard", "extreme"]

# Quality threshold for accepting a response (from self_qa.py)
DEFAULT_QUALITY_THRESHOLD = 8  # Out of 10

# Maximum cascade depth (how many times to escalate)
MAX_CASCADE_DEPTH = 3


@dataclass
class UnifiedRoutingResult:
    """Result of unified routing + cascading."""
    answer: str
    model_used: str
    tier_used: str
    cascade_depth: int  # 0 = first try succeeded, 1 = escalated once, etc.
    quality_score: float
    all_attempts: list  # List of {model, tier, score, answer} dicts
    total_tokens: int = 0


def classify_difficulty(question: str) -> str:
    """Classify query difficulty into a tier.
    
    This is a simplified classifier. In production, this would use the
    preference-data trained router from preference_router.py.
    
    Args:
        question: The user's question
    
    Returns:
        One of 'trivial', 'medium', 'hard', 'extreme'
    """
    q = question.lower().strip()
    
    # Trivial: short, simple factual or greeting
    if len(q) < 50 and any(q.startswith(w) for w in ["hi", "hello", "hey", "what is", "who is", "when is"]):
        return "trivial"
    
    # Extreme: very long, multi-step, or explicitly complex
    if len(q) > 500 or any(w in q for w in ["step by step", "multi-step", "complex", "algorithm", "implement", "architecture"]):
        return "extreme"
    
    # Hard: math, code, reasoning
    if any(w in q for w in ["calculate", "solve", "prove", "code", "function", "debug", "optimize", "compare", "analyze"]):
        return "hard"
    
    # Medium: default
    return "medium"


async def unified_route_and_cascade(
    question: str,
    call_model_func: Callable[..., Awaitable[str]],
    verify_func: Optional[Callable] = None,
    system_prompt: str = "You are Temuclaude, a helpful AI assistant.",
    quality_threshold: float = DEFAULT_QUALITY_THRESHOLD,
    max_cascade_depth: int = MAX_CASCADE_DEPTH,
    model_pool: dict = None,
) -> UnifiedRoutingResult:
    """Unified routing + cascading strategy.
    
    1. Classify difficulty → route to initial model
    2. Generate response
    3. Verify quality (self-QA)
    4. If quality < threshold, cascade to next stronger model
    5. Repeat until quality passes or max depth reached
    
    Args:
        question: The user's question
        call_model_func: Async function to call a model
        verify_func: Optional async function to verify quality (self_qa_gate)
        system_prompt: System prompt
        quality_threshold: Minimum quality score to accept (0-10)
        max_cascade_depth: Maximum number of cascade escalations
        model_pool: Optional dict of {tier: model_name} overrides
    
    Returns:
        UnifiedRoutingResult with final answer and cascade info
    """
    # Use provided model pool or defaults
    pool = model_pool or TIER_MODELS
    
    # Step 1: Classify and route
    difficulty = classify_difficulty(question)
    start_tier_idx = CASCADE_CHAIN.index(difficulty) if difficulty in CASCADE_CHAIN else 1
    
    all_attempts = []
    total_tokens = 0
    
    # Step 2-5: Generate, verify, cascade
    for depth in range(max_cascade_depth + 1):
        tier_idx = min(start_tier_idx + depth, len(CASCADE_CHAIN) - 1)
        tier = CASCADE_CHAIN[tier_idx]
        model = pool.get(tier, pool.get("medium", "glm-5.2"))
        
        # Generate
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]
        
        try:
            answer = await call_model_func(model, messages, max_tokens=4096)
        except Exception as e:
            all_attempts.append({
                "model": model,
                "tier": tier,
                "score": 0.0,
                "answer": "",
                "error": str(e),
            })
            continue
        
        # Verify quality
        score = 0.0
        if verify_func:
            try:
                verify_result = await verify_func(question, answer, model, call_model_func)
                score = verify_result.get("score", 0.0)
            except Exception:
                score = 5.0  # Neutral if verification fails
        else:
            # Without verifier, accept first response
            score = quality_threshold
        
        all_attempts.append({
            "model": model,
            "tier": tier,
            "score": score,
            "answer": answer,
        })
        
        # Check if quality passes
        if score >= quality_threshold:
            return UnifiedRoutingResult(
                answer=answer,
                model_used=model,
                tier_used=tier,
                cascade_depth=depth,
                quality_score=score,
                all_attempts=all_attempts,
                total_tokens=total_tokens,
            )
        
        # Quality too low — cascade to next tier
        if depth < max_cascade_depth:
            continue
    
    # Max cascade reached — return best attempt
    best_attempt = max(all_attempts, key=lambda a: a.get("score", 0)) if all_attempts else {
        "model": "", "tier": "", "score": 0, "answer": ""
    }
    
    return UnifiedRoutingResult(
        answer=best_attempt.get("answer", ""),
        model_used=best_attempt.get("model", ""),
        tier_used=best_attempt.get("tier", ""),
        cascade_depth=len(all_attempts) - 1,
        quality_score=best_attempt.get("score", 0),
        all_attempts=all_attempts,
        total_tokens=total_tokens,
    )