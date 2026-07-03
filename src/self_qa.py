"""
Timuclaude Self-QA Gate
After generating a response, a verifier model scores it 0-10.
If below threshold (8), retry with feedback. Max 3 retries.

Based on: GDPval-RealWorks repo (hyeonsangjeon/gdpval-realworks)
- Self-QA scores each output on a 0-10 scale using rubric-based self-evaluation
- If score < threshold: enters reflection loop, retries
- Checks: Are all requirements met? Is output correct? Is it professional?
"""
import asyncio
from typing import Callable, Awaitable


DEFAULT_THRESHOLD = 8
DEFAULT_MAX_RETRIES = 3


def build_qa_prompt(question: str, answer: str) -> list:
    """Build the Self-QA evaluation prompt.
    
    The verifier model receives the original question and the generated answer,
    then scores it 0-10 with reasoning.
    """
    system_prompt = (
        "You are a quality evaluator. Score the following answer to the given question "
        "on a scale of 0-10 where:\n"
        "- 10: Perfect answer — correct, complete, professional\n"
        "- 8-9: Good answer — mostly correct with minor issues\n"
        "- 6-7: Acceptable answer — correct but incomplete or poorly formatted\n"
        "- 4-5: Poor answer — partially correct, missing key elements\n"
        "- 0-3: Wrong answer — incorrect or irrelevant\n\n"
        "Respond in EXACTLY this format:\n"
        "Score: X\n"
        "Reason: Y\n"
    )
    
    user_prompt = (
        f"Question: {question}\n\n"
        f"Answer: {answer}\n\n"
        f"Score this answer (0-10) and explain why:"
    )
    
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def extract_score(response: str) -> tuple:
    """Extract the score and reasoning from the verifier's response.
    
    Returns (score: int, reasoning: str). If parsing fails, returns (0, "").
    """
    import re
    
    # Look for "Score: X" pattern
    match = re.search(r'[Ss]core:\s*(\d+)', response)
    if match:
        score = int(match.group(1))
        # Clamp to 0-10
        score = max(0, min(10, score))
        
        # Extract reasoning
        reason_match = re.search(r'[Rr]eason:\s*(.+?)(?:\n|$)', response, re.DOTALL)
        reasoning = reason_match.group(1).strip() if reason_match else ""
        
        return (score, reasoning)
    
    # Try "X/10" pattern
    match = re.search(r'(\d+)\s*/\s*10', response)
    if match:
        score = int(match.group(1))
        score = max(0, min(10, score))
        return (score, response)
    
    # Parsing failed
    return (0, "")


async def self_qa_gate(
    question: str,
    answer: str,
    verifier_model: str,
    call_model_func: Callable[..., Awaitable[str]],
    threshold: int = DEFAULT_THRESHOLD,
    max_retries: int = DEFAULT_MAX_RETRIES,
    max_tokens: int = 4096,
) -> dict:
    """
    Run the Self-QA gate: score the answer, retry if below threshold.
    
    Args:
        question: The original user question
        answer: The generated answer to evaluate
        verifier_model: Which model scores the answer (e.g., nemotron-3-ultra)
        call_model_func: Async function to call a model
        threshold: Minimum acceptable score (default 8)
        max_retries: Max retry attempts before accepting (default 3)
        max_tokens: Max tokens for QA evaluation
    
    Returns:
        Dict with:
        - 'accepted': bool — whether the answer passed the gate
        - 'final_answer': The accepted (or last) answer
        - 'score': Final score
        - 'reasoning': Verifier's reasoning
        - 'attempts': Number of attempts made
        - 'all_scores': List of all scores from each attempt
    """
    all_scores = []
    all_reasonings = []
    current_answer = answer
    attempts = 0
    last_reasoning = ""
    
    for attempt in range(max_retries + 1):
        attempts += 1
        
        # Score the current answer
        qa_messages = build_qa_prompt(question, current_answer)
        qa_response = await call_model_func(verifier_model, qa_messages, max_tokens=max_tokens)
        
        score, reasoning = extract_score(qa_response)
        all_scores.append(score)
        all_reasonings.append(reasoning)
        last_reasoning = reasoning
        
        if score >= threshold:
            # Accepted!
            return {
                "accepted": True,
                "final_answer": current_answer,
                "score": score,
                "reasoning": reasoning,
                "attempts": attempts,
                "all_scores": all_scores,
            }
        
        # Score too low — retry with feedback (if we have retries left)
        if attempt < max_retries:
            feedback = (
                f"Your previous answer was scored {score}/10 by a quality evaluator.\n"
                f"Reason: {reasoning}\n\n"
                f"Please improve your answer to the original question. "
                f"Address the issues mentioned above.\n\n"
                f"Original question: {question}\n"
                f"Previous answer: {current_answer}\n"
            )
            
            retry_messages = [
                {"role": "system", "content": "You are Timuclaude. Improve your previous answer based on feedback."},
                {"role": "user", "content": feedback},
            ]
            
            # Use the verifier model to generate an improved answer
            current_answer = await call_model_func(verifier_model, retry_messages, max_tokens=max_tokens)
    
    # Max retries reached — accept the best attempt
    best_score = max(all_scores) if all_scores else 0
    return {
        "accepted": False,
        "final_answer": current_answer,
        "score": best_score,
        "reasoning": last_reasoning,
        "attempts": attempts,
        "all_scores": all_scores,
    }