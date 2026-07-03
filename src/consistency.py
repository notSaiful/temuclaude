"""
Timuclaude Self-Consistency Module
Samples N responses from the same model, votes on the final answer.

Based on published research:
- Wang et al., 2022: "Self-Consistency Improves Chain-of-Thought"
- Sample 20-40 responses at temperature 0.7
- Extract final answer from each
- Majority vote determines the answer
- Proven: +10-20% on math/reasoning benchmarks
"""
import asyncio
import re
from collections import Counter
from typing import Optional, Callable, Awaitable


DEFAULT_N_SAMPLES = 20
DEFAULT_TEMPERATURE = 0.7


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


async def self_consistency(
    question: str,
    model: str,
    call_model_func: Callable[..., Awaitable[str]],
    n_samples: int = DEFAULT_N_SAMPLES,
    temperature: float = DEFAULT_TEMPERATURE,
    max_tokens: int = 8192,
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
    
    Returns:
        Dict with:
        - 'answer': The voted answer
        - 'confidence': Fraction of samples that agreed (0.0-1.0)
        - 'all_answers': All extracted answers
        - 'all_responses': All raw responses
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

    # Vote
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
    }