"""
Temuclaude Benchmark Judges
LLM-as-judge scoring: extracts the final answer from a model response
and compares it to the ground truth.

Based on HLE's official judge prompt (github.com/centerforaisafety/hle):
"Judge whether [response] to [question] is correct based on [correct_answer]"
"""
import re
from typing import Callable, Awaitable, Optional


# HLE-style judge prompt (from official eval code)
JUDGE_PROMPT = """Judge whether the following [response] to [question] is correct or not based on the precise and unambiguous [correct_answer] below.

[question]: {question}

[response]: {response}

Your judgement must be in the format and criteria specified below:

extracted_final_answer: The final exact answer extracted from the [response]. Put the extracted answer as 'None' if there is no exact, final answer to extract from the response.

[correct_answer]: {correct_answer}

reasoning: Explain why the extracted_final_answer is correct or incorrect based on [correct_answer], focusing only on if there are meaningful differences between [correct_answer] and the extracted_final_answer.

correct: Answer 'yes' if extracted_final_answer matches the [correct_answer] given above, or is within a small margin of error for numerical problems. Answer 'no' otherwise.

confidence: The extracted confidence score between 0% and 100% from [response]. Put 100 if there is no confidence score available."""


def extract_judgment(judge_response: str) -> dict:
    """Extract the judgment from the judge model's response.
    
    Returns: {correct: bool, extracted_answer: str, reasoning: str, confidence: int}
    """
    # Extract correct: yes/no
    correct_match = re.search(r'correct:\s*(yes|no)', judge_response, re.IGNORECASE)
    correct = bool(correct_match and correct_match.group(1).lower() == "yes")
    
    # Extract extracted_final_answer
    answer_match = re.search(r'extracted_final_answer:\s*(.+?)(?:\n|$)', judge_response)
    extracted_answer = answer_match.group(1).strip() if answer_match else ""
    
    # Extract reasoning
    reasoning_match = re.search(r'reasoning:\s*(.+?)(?:\ncorrect:|\Z)', judge_response, re.DOTALL)
    reasoning = reasoning_match.group(1).strip() if reasoning_match else ""
    
    # Extract confidence
    confidence_match = re.search(r'confidence:\s*(\d+)', judge_response)
    confidence = int(confidence_match.group(1)) if confidence_match else 100
    
    return {
        "correct": correct,
        "extracted_answer": extracted_answer,
        "reasoning": reasoning,
        "confidence": confidence,
    }


async def llm_judge(
    question: str,
    response: str,
    correct_answer: str,
    judge_model: str,
    call_model_func: Callable[..., Awaitable[str]],
    max_tokens: int = 4096,
) -> dict:
    """
    Use an LLM to judge whether a response is correct.
    
    Args:
        question: The original question
        response: The model's response to judge
        correct_answer: The ground truth answer
        judge_model: Which model acts as judge
        call_model_func: Async function to call a model
        max_tokens: Max tokens for judge response
    
    Returns:
        {correct: bool, extracted_answer: str, reasoning: str, confidence: int}
    """
    prompt = JUDGE_PROMPT.format(question=question, response=response, correct_answer=correct_answer)
    
    messages = [
        {"role": "user", "content": prompt},
    ]
    
    judge_response = await call_model_func(judge_model, messages, max_tokens=max_tokens)
    
    return extract_judgment(judge_response)


def exact_match_judge(response: str, correct_answer: str) -> dict:
    """
    Simple exact-match judge (no LLM needed).
    
    Checks if the correct answer appears in the response.
    Useful for math questions with clear numeric answers.
    
    Returns:
        {correct: bool, extracted_answer: str, reasoning: str, confidence: int}
    """
    # Normalize both
    correct_norm = correct_answer.strip().lower()
    response_norm = response.strip().lower()
    
    # Direct match
    if correct_norm in response_norm:
        return {
            "correct": True,
            "extracted_answer": correct_answer,
            "reasoning": "Exact match found in response",
            "confidence": 100,
        }
    
    # Try removing common formatting
    # e.g., "180" should match "The answer is 180" or "180.0"
    import re as re_module
    # Look for the answer as a standalone token
    pattern = r'\b' + re_module.escape(correct_norm) + r'\b'
    if re_module.search(pattern, response_norm):
        return {
            "correct": True,
            "extracted_answer": correct_answer,
            "reasoning": "Answer found as standalone token",
            "confidence": 95,
        }
    
    return {
        "correct": False,
        "extracted_answer": "",
        "reasoning": f"'{correct_answer}' not found in response",
        "confidence": 50,
    }