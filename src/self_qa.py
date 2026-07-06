"""
Temuclaude Self-QA Gate
After generating a response, a verifier model scores it 0-10.
If below threshold (8), retry with feedback. Max 3 retries.

Based on:
- GDPval-RealWorks repo (hyeonsangjeon/gdpval-realworks)
  Self-QA scores each output on a 0-10 scale using rubric-based self-evaluation
- ATTS (2025): USVA 4-rubric verification — LC (Logical Coherence), FC (Factual
  Correctness), CM (Completeness), GA (Goal Alignment). More granular than
  single 0-10 score. 28% token savings with 2% accuracy cost.
- Reflexion (arXiv:2303.11366): Verbal self-reflection on failures stored in
  memory for retry. 91% HumanEval (vs GPT-4's 80%). +10-20% on hard problems.
"""
import asyncio
import re
from typing import Callable, Awaitable, Optional


DEFAULT_THRESHOLD = 8
DEFAULT_MAX_RETRIES = 3

# USVA 5-rubric scoring (extended from ATTS framework)
# Original 4 rubrics: LC, FC, CM, GA
# Added 5th rubric: CL (Clarity) — based on research arXiv:2407.19825, 2312.02065
# Clarity rubric ensures responses are concise, simple, and accessible
USVA_RUBRICS = {
    "LC": "Logical Coherence — Is the reasoning internally consistent and logical?",
    "FC": "Factual Correctness — Are the facts and claims accurate?",
    "CM": "Completeness — Does the answer address all parts of the question?",
    "GA": "Goal Alignment — Does the answer meet the user's actual goal?",
    "CL": "Clarity — Is the answer clear, concise, and accessible? Short sentences, simple words, no unnecessary jargon, no filler?",
}


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


def build_usva_prompt(question: str, answer: str) -> list:
    """Build the USVA 5-rubric evaluation prompt (extended ATTS pattern).
    
    Instead of a single 0-10 score, the verifier scores on 5 rubrics:
    - LC (Logical Coherence): 0.0-1.0
    - FC (Factual Correctness): 0.0-1.0
    - CM (Completeness): 0.0-1.0
    - GA (Goal Alignment): 0.0-1.0
    - CL (Clarity): 0.0-1.0 — is the answer concise, simple, and accessible?
    
    Overall score = average of 5 rubrics × 10. More granular than single score.
    """
    system_prompt = (
        "You are a quality evaluator using the USVA 5-rubric framework. "
        "Score the answer on 5 dimensions, each from 0.0 to 1.0:\n\n"
        f"LC (Logical Coherence): {USVA_RUBRICS['LC']}\n"
        f"FC (Factual Correctness): {USVA_RUBRICS['FC']}\n"
        f"CM (Completeness): {USVA_RUBRICS['CM']}\n"
        f"GA (Goal Alignment): {USVA_RUBRICS['GA']}\n"
        f"CL (Clarity): {USVA_RUBRICS['CL']}\n\n"
        "Respond in EXACTLY this format:\n"
        "LC: X.X\n"
        "FC: X.X\n"
        "CM: X.X\n"
        "GA: X.X\n"
        "CL: X.X\n"
        "Reason: Brief explanation of the weakest area\n"
    )
    
    user_prompt = (
        f"Question: {question}\n\n"
        f"Answer: {answer}\n\n"
        f"Score on all 5 rubrics:"
    )
    
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def extract_usva_score(response: str) -> tuple:
    """Extract USVA 5-rubric scores from verifier response.
    
    Returns (overall_score: float 0-10, weakest_area: str, reasoning: str).
    """
    scores = {}
    for rubric in ["LC", "FC", "CM", "GA", "CL"]:
        match = re.search(rf'{rubric}:\s*(\d+\.?\d*)', response)
        if match:
            scores[rubric] = float(match.group(1))
    
    if not scores:
        # Fallback to single score
        score, reasoning = extract_score(response)
        return (score, "unknown", reasoning)
    
    # Overall = average × 10
    overall = (sum(scores.values()) / len(scores)) * 10
    
    # Find weakest area
    weakest = min(scores, key=lambda k: scores[k])
    
    # Extract reasoning
    reason_match = re.search(r'[Rr]eason:\s*(.+?)(?:\n|$)', response, re.DOTALL)
    reasoning = reason_match.group(1).strip() if reason_match else f"Weakest: {weakest}"
    
    return (overall, weakest, reasoning)


def build_reflexion_prompt(question: str, failed_answer: str, score: float, reasoning: str, reflections: list) -> list:
    """Build a reflexion prompt (Reflexion pattern, arXiv:2303.11366).
    
    When self-QA fails, generate a verbal reflection on what went wrong,
    then retry with the reflection as additional context.
    
    Args:
        question: Original question
        failed_answer: The answer that failed QA
        score: The score it received
        reasoning: Why it failed
        reflections: List of previous reflections (from earlier failed attempts)
    
    Returns:
        Messages list for the model to generate an improved answer with reflection context.
    """
    reflection_context = ""
    if reflections:
        reflection_context = "\n\nPrevious reflections:\n"
        for i, r in enumerate(reflections, 1):
            reflection_context += f"{i}. {r}\n"
    
    system_prompt = (
        "You are Temuclaude. Your previous answer was not good enough. "
        "Reflect on what went wrong and provide an improved answer.\n\n"
        f"The previous answer scored {score:.1f}/10.\n"
        f"Reason: {reasoning}\n"
        f"{reflection_context}\n"
        "Think about: What was wrong? Why did it fail? What should you do differently?\n"
        "Then provide a corrected, complete answer."
    )
    
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Original question: {question}\n\nFailed answer: {failed_answer[:2000]}\n\nProvide a corrected answer:"},
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
    use_usva: bool = True,
    use_reflexion: bool = True,
) -> dict:
    """
    Run the Self-QA gate: score the answer, retry if below threshold.
    
    Enhanced with:
    - USVA 4-rubric scoring (ATTS pattern): More granular than single 0-10
    - Reflexion memory (arXiv:2303.11366): Verbal reflection on failures, retry with context
    
    Args:
        question: The original user question
        answer: The generated answer to evaluate
        verifier_model: Which model scores the answer (e.g., nemotron-3-ultra)
        call_model_func: Async function to call a model
        threshold: Minimum acceptable score (default 8)
        max_retries: Max retry attempts before accepting (default 3)
        max_tokens: Max tokens for QA evaluation
        use_usva: If True, use 4-rubric scoring instead of single 0-10
        use_reflexion: If True, use reflexion memory on retries
    
    Returns:
        Dict with:
        - 'accepted': bool — whether the answer passed the gate
        - 'final_answer': The accepted (or last) answer
        - 'score': Final score
        - 'reasoning': Verifier's reasoning
        - 'attempts': Number of attempts made
        - 'all_scores': List of all scores from each attempt
        - 'reflections': List of reflections generated (if use_reflexion=True)
    """
    all_scores = []
    all_reasonings = []
    current_answer = answer
    attempts = 0
    last_reasoning = ""
    reflections = []  # Reflexion memory (arXiv:2303.11366)
    weakest_area = "unknown"  # Default; set by extract_usva_score when use_usva=True
    
    for attempt in range(max_retries + 1):
        attempts += 1
        
        # Score the current answer using USVA or standard
        if use_usva:
            qa_messages = build_usva_prompt(question, current_answer)
            qa_response = await call_model_func(verifier_model, qa_messages, max_tokens=max_tokens)
            score, weakest_area, reasoning = extract_usva_score(qa_response)
            # Include weakest area in reasoning for better feedback
            if weakest_area != "unknown":
                reasoning = f"Weakest area: {weakest_area}. {reasoning}"
        else:
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
                "reflections": reflections,
            }
        
        # Score too low — retry with feedback
        if attempt < max_retries:
            if use_reflexion:
                # Reflexion pattern: generate verbal reflection, store in memory, retry with context
                reflection = f"Attempt {attempt + 1} scored {score:.1f}/10. Issue: {reasoning}"
                reflections.append(reflection)
                
                # Clarity-specific feedback: if CL is the weakest rubric, add clarity guidance
                clarity_hint = ""
                if weakest_area == "CL":
                    clarity_hint = (
                        "\n\nIMPORTANT: Your answer was not clear or concise enough. "
                        "Rewrite with shorter sentences, simpler words, and no filler. "
                        "Lead with the answer. Remove unnecessary explanation."
                    )
                
                retry_messages = build_reflexion_prompt(
                    question, current_answer, score, reasoning + clarity_hint, reflections
                )
                # Use the verifier model to generate improved answer with reflection context
                current_answer = await call_model_func(verifier_model, retry_messages, max_tokens=max_tokens)
            else:
                # Standard retry with feedback (original behavior)
                feedback = (
                    f"Your previous answer was scored {score}/10 by a quality evaluator.\n"
                    f"Reason: {reasoning}\n\n"
                    f"Please improve your answer to the original question. "
                    f"Address the issues mentioned above.\n\n"
                    f"Original question: {question}\n"
                    f"Previous answer: {current_answer}\n"
                )
                
                retry_messages = [
                    {"role": "system", "content": "You are Temuclaude. Improve your previous answer based on feedback."},
                    {"role": "user", "content": feedback},
                ]
                
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
        "reflections": reflections,
    }