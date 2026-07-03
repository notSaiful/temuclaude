"""
Timuclaude Self-Consistency Module
Samples N responses from the same model, votes on the final answer.

Based on published research:
- Wang et al., 2022: "Self-Consistency Improves Chain-of-Thought"
  Sample 20-40 responses at temperature 0.7, majority vote. +10-20% math.
- OmegaPRM (Google, 2024): Weighted self-consistency — PRM scores each
  solution, vote is weighted by PRM score instead of uniform. +18.4% MATH.
- ATTS (2025): Adaptive sample count — easy=N=1, medium=N=3, hard=N=10+.
  60% cost reduction with <1% performance drop.
"""
import asyncio
import re
from collections import Counter, defaultdict
from typing import Optional, Callable, Awaitable


DEFAULT_N_SAMPLES = 20
DEFAULT_TEMPERATURE = 0.7

# Adaptive sample counts based on difficulty (ATTS / BEST-Route research)
ADAPTIVE_N_SAMPLES = {
    "trivial": 1,   # No need for multiple samples
    "medium": 3,    # Small panel for medium difficulty
    "hard": 10,     # Full self-consistency for hard problems
    "extreme": 20,  # Maximum samples for hardest problems
}


def extract_answer(response: str) -> str:
    """Extract the final answer from a model response.
    
    Looks for 'Answer: X' pattern at the end of the response.
    Falls back to the last line if no pattern found.
    """
    # Try to find "Answer: X" pattern (case-insensitive)
    matches = re.findall(r'[Aa]nswer:\s*(.+?)(?:\n|$)', response)
    if matches:
        # Take the last match (the final answer)
        return matches[-1].strip()
    
    # Try "The answer is X" pattern
    matches = re.findall(r'[Tt]he answer is\s+(.+?)(?:\n|\.|$)', response)
    if matches:
        return matches[-1].strip().rstrip('.')
    
    # Try "X" at the end after "equals" or "is"
    # e.g., "25 multiplied by 4 equals 100" → "100"
    matches = re.findall(r'(?:equals|is)\s+(.+?)(?:\n|$)', response)
    if matches:
        return matches[-1].strip().rstrip('.')
    
    # Fallback: take the last non-empty line
    lines = [l.strip() for l in response.strip().split('\n') if l.strip()]
    if lines:
        return lines[-1]
    
    return response.strip()


def majority_vote(answers: list) -> Optional[str]:
    """Vote on the most common answer.
    
    Normalizes answers for comparison (strip whitespace, lowercase for text).
    Returns the most common answer, or None if no clear winner.
    """
    if not answers:
        return None
    
    # Normalize for voting (strip, but keep case for numbers)
    normalized = [a.strip().lower() if not a.replace('.', '').replace('-', '').isdigit() 
                 else a.strip() for a in answers]
    
    # Count occurrences
    counter = Counter(normalized)
    most_common, count = counter.most_common(1)[0]
    
    # Return the original-form version of the most common answer
    for i, norm in enumerate(normalized):
        if norm == most_common:
            return answers[i]
    
    return answers[0]  # fallback


def prm_weighted_vote(answers: list, prm_scores: list) -> Optional[str]:
    """PRM-weighted majority vote (OmegaPRM pattern).
    
    Instead of uniform majority vote, weight each solution by its PRM score.
    answer = argmax_a Σ_i PRM(solution_i) * [answer_i == a]
    
    Args:
        answers: List of extracted answers
        prm_scores: List of PRM scores (0.0-1.0) for each response
    
    Returns:
        The answer with highest weighted vote count
    """
    if not answers or not prm_scores:
        return majority_vote(answers)
    
    # Normalize answers for comparison
    normalized = [a.strip().lower() if not a.replace('.', '').replace('-', '').isdigit()
                 else a.strip() for a in answers]
    
    # Weighted vote: sum PRM scores for each unique answer
    weighted_counts = defaultdict(float)
    answer_map = {}  # norm -> original answer
    
    for i, norm in enumerate(normalized):
        score = prm_scores[i] if i < len(prm_scores) else 0.5
        weighted_counts[norm] += score
        answer_map[norm] = answers[i]
    
    # Find answer with highest weighted count
    best_norm = max(weighted_counts, key=lambda k: weighted_counts[k])
    return answer_map.get(best_norm, answers[0])


def get_adaptive_n_samples(difficulty: str) -> int:
    """Get adaptive sample count based on difficulty (ATTS / BEST-Route).
    
    Easy queries need fewer samples, hard queries need more.
    This reduces cost by up to 60% with <1% performance drop.
    
    Args:
        difficulty: One of 'trivial', 'medium', 'hard', 'extreme'
    
    Returns:
        Number of samples to draw
    """
    return ADAPTIVE_N_SAMPLES.get(difficulty, DEFAULT_N_SAMPLES)


async def self_consistency(
    question: str,
    model: str,
    call_model_func: Callable[..., Awaitable[str]],
    n_samples: int = DEFAULT_N_SAMPLES,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = 8192,
    use_prm_weighting: bool = False,
    verifier_model: str = "nemotron-3-ultra",
) -> dict:
    """
    Run self-consistency: sample N responses, vote on the answer.
    
    Args:
        question: The user's question
        model: Which model to sample from
        call_model_func: Async function to call a model
        n_samples: Number of samples (20-40 recommended)
        temperature: Sampling temperature (0.7 recommended)
        max_tokens: Max tokens per response
        use_prm_weighting: If True, use PRM-weighted voting (OmegaPRM pattern)
        verifier_model: Model to use for PRM scoring (if use_prm_weighting=True)
    
    Returns:
        Dict with:
        - 'answer': The voted answer
        - 'confidence': Fraction of samples that agreed (0.0-1.0)
        - 'all_answers': All extracted answers
        - 'all_responses': All raw responses
        - 'prm_scores': PRM scores if use_prm_weighting=True (else empty)
    """
    # Build messages with explicit answer format instruction
    messages = [
        {
            "role": "system",
            "content": (
                "You are Timuclaude, a helpful AI assistant. "
                "Think carefully and provide a thorough answer. "
                "At the very end of your response, write 'Answer: ' followed by your final answer."
            ),
        },
        {"role": "user", "content": question},
    ]

    # Sample N responses in parallel
    tasks = [
        call_model_func(model, messages, temperature=temperature, max_tokens=max_tokens)
        for _ in range(n_samples)
    ]
    responses = await asyncio.gather(*tasks)

    # Extract answers from each response
    all_answers = [extract_answer(r) for r in responses]

    # PRM-weighted voting (OmegaPRM pattern)
    prm_scores = []
    if use_prm_weighting and n_samples > 1:
        # Score each response with a verifier model
        scoring_tasks = [
            _score_response(question, resp, verifier_model, call_model_func)
            for resp in responses
        ]
        prm_scores = await asyncio.gather(*scoring_tasks)
        
        # PRM-weighted vote
        voted_answer = prm_weighted_vote(all_answers, prm_scores)
    else:
        # Standard majority vote
        voted_answer = majority_vote(all_answers)

    # Calculate confidence
    if voted_answer:
        voted_norm = voted_answer.strip().lower()
        agree_count = sum(1 for a in all_answers if a.strip().lower() == voted_norm)
        confidence = agree_count / len(all_answers)
    else:
        confidence = 0.0

    # Find a response that matches the voted answer (to return full reasoning)
    best_response = None
    for r in responses:
        if extract_answer(r) == voted_answer:
            best_response = r
            break
    if not best_response:
        best_response = responses[0] if responses else ""

    return {
        "answer": best_response,
        "voted_answer": voted_answer,
        "confidence": confidence,
        "all_answers": all_answers,
        "all_responses": responses,
        "prm_scores": prm_scores,
    }


async def _score_response(
    question: str,
    response: str,
    verifier_model: str,
    call_model_func: Callable[..., Awaitable[str]],
) -> float:
    """Score a single response using a verifier model (PRM pattern).
    
    Returns a score from 0.0 to 1.0.
    """
    scoring_prompt = [
        {
            "role": "system",
            "content": (
                "You are a reasoning quality evaluator. Score the following answer "
                "on a scale of 0.0 to 1.0 where:\n"
                "1.0: Perfect — correct, complete, well-reasoned\n"
                "0.8-0.9: Good — mostly correct with minor issues\n"
                "0.5-0.7: Partially correct — missing key elements\n"
                "0.0-0.4: Wrong — incorrect or irrelevant\n\n"
                "Respond with ONLY a number between 0.0 and 1.0."
            ),
        },
        {
            "role": "user",
            "content": f"Question: {question}\n\nAnswer: {response[:1500]}\n\nScore:",
        },
    ]
    
    try:
        result = await call_model_func(verifier_model, scoring_prompt, max_tokens=50)
        # Extract float from response
        import re
        match = re.search(r'(\d+\.?\d*)', result)
        if match:
            score = float(match.group(1))
            return max(0.0, min(1.0, score))
    except Exception:
        pass
    
    return 0.5  # Default neutral score if scoring fails