"""
Temuclaude Sequential Thinking Module
Step-by-step reasoning with revision, backtracking, and branching.

Lighter than ToT (no tree expansion), heavier than simple CoT.
Based on Anthropic's sequential thinking pattern — each step can:
- Build on previous steps (normal progression)
- Revise a previous step (correction)
- Branch from a previous step (alternative path)
- Declare completion (final answer)

Use for MEDIUM tier problems that need structured reasoning but not full search.
"""
import asyncio
import re
import json
from typing import Optional, Callable, Awaitable, List, Dict


DEFAULT_MAX_STEPS = 10
DEFAULT_MAX_BACKTRACKS = 3


def build_thought_prompt(question: str, thoughts: List[Dict], step_num: int) -> List[Dict]:
    """Build messages for generating the next thought.

    Args:
        question: The original question
        thoughts: List of thought dicts: {step, content, status, revision_of?, branch_from?}
        step_num: Current step number

    Returns:
        Messages list for the model
    """
    thoughts_text = ""
    for t in thoughts:
        if t.get("status") == "revised":
            thoughts_text += f"\n[Step {t['step']} — REVISED]: {t['content']}\n"
        elif t.get("status") == "branched":
            thoughts_text += f"\n[Step {t['step']} — BRANCH from {t.get('branch_from', '?')}]: {t['content']}\n"
        else:
            thoughts_text += f"\n[Step {t['step']}]: {t['content']}\n"

    system = (
        "You are a sequential reasoning engine. Think step by step. "
        "At each step, you either: (a) build on previous steps, (b) revise a "
        "previous step if you realize it was wrong, (c) branch from a step to "
        "explore an alternative, or (d) give the final answer. "
        "Be precise and logical. If you're confident, say FINAL ANSWER: X."
    )

    user = f"Question: {question}\n\nReasoning so far:{thoughts_text}\n\nGenerate step {step_num}."
    if not thoughts:
        user = f"Question: {question}\n\nGenerate step {step_num} (the first step)."

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def parse_thought(raw: str, step_num: int) -> Dict:
    """Parse a raw thought response into a structured thought.

    Detects:
    - FINAL ANSWER: X → marks as complete
    - REVISE step N: ... → revision
    - BRANCH from step N: ... → branch
    - Normal thought otherwise
    """
    thought: Dict = {
        "step": step_num,
        "content": raw.strip(),
        "status": "active",
        "is_final": False,
    }

    # Check for final answer
    final_match = re.search(r"FINAL ANSWER:\s*(.+)", raw, re.IGNORECASE)
    if final_match:
        thought["is_final"] = True
        thought["content"] = final_match.group(1).strip()
        thought["status"] = "final"

    # Check for revision
    revise_match = re.search(r"REVISE\s+step\s+(\d+):\s*(.+)", raw, re.IGNORECASE)
    if revise_match:
        thought["status"] = "revised"
        thought["revision_of"] = int(revise_match.group(1))
        thought["content"] = revise_match.group(2).strip()

    # Check for branch
    branch_match = re.search(r"BRANCH\s+from\s+step\s+(\d+):\s*(.+)", raw, re.IGNORECASE)
    if branch_match:
        thought["status"] = "branched"
        thought["branch_from"] = int(branch_match.group(1))
        thought["content"] = branch_match.group(2).strip()

    return thought


def evaluate_thought(thought: Dict, question: str) -> float:
    """Heuristic evaluation of a thought's quality (0.0-1.0).

    Checks:
    - Relevant to question keywords
    - Not empty or trivially short
    - Contains reasoning indicators
    """
    content = thought.get("content", "")
    if not content or len(content) < 10:
        return 0.0

    score = 0.5  # baseline

    # Check for reasoning indicators
    reasoning_words = ["because", "therefore", "since", "thus", "hence",
                       "so", "if", "then", "assume", "suppose", "consider",
                       "however", "but", "although", "first", "next", "finally"]
    content_lower = content.lower()
    for word in reasoning_words:
        if word in content_lower:
            score += 0.05
    score = min(score, 0.9)

    # Check relevance to question keywords
    q_words = set(question.lower().split())
    c_words = set(content_lower.split())
    overlap = len(q_words & c_words) / max(len(q_words), 1)
    score = min(score + overlap * 0.2, 1.0)

    return score


async def sequential_think(
    question: str,
    model_fn: Optional[Callable[[List[Dict]], Awaitable[str]]] = None,
    max_steps: int = DEFAULT_MAX_STEPS,
    max_backtracks: int = DEFAULT_MAX_BACKTRACKS,
) -> Dict:
    """Run sequential thinking on a question.

    Args:
        question: The question to reason about
        model_fn: Async function that takes messages list and returns response text
        max_steps: Maximum reasoning steps
        max_backtracks: Maximum backtracks/revisions

    Returns:
        Dict with: thoughts (list), final_answer (str), steps_used (int)
    """
    thoughts: List[Dict] = []
    backtracks_used = 0

    for step_num in range(1, max_steps + 1):
        messages = build_thought_prompt(question, thoughts, step_num)

        if model_fn:
            raw = await model_fn(messages)
        else:
            # Fallback: simple text generation placeholder
            raw = f"Step {step_num}: Analyzing the question."

        thought = parse_thought(raw, step_num)
        thought["score"] = evaluate_thought(thought, question)

        # If low score and backtracks available, try to revise
        if thought["score"] < 0.3 and backtracks_used < max_backtracks and thoughts:
            backtracks_used += 1
            # Revise the weakest previous thought
            weakest = min(thoughts, key=lambda t: t.get("score", 0.5))
            thought["status"] = "revised"
            thought["revision_of"] = weakest["step"]

        thoughts.append(thought)

        if thought["is_final"]:
            break

    final_answer = None
    for t in reversed(thoughts):
        if t.get("is_final"):
            final_answer = t["content"]
            break

    return {
        "thoughts": thoughts,
        "final_answer": final_answer or thoughts[-1]["content"] if thoughts else "",
        "steps_used": len(thoughts),
        "backtracks_used": backtracks_used,
    }


def sequential_think_sync(
    question: str,
    model_fn: Optional[Callable[[List[Dict]], str]] = None,
    max_steps: int = DEFAULT_MAX_STEPS,
    max_backtracks: int = DEFAULT_MAX_BACKTRACKS,
) -> Dict:
    """Synchronous version of sequential_think."""
    thoughts: List[Dict] = []
    backtracks_used = 0

    for step_num in range(1, max_steps + 1):
        messages = build_thought_prompt(question, thoughts, step_num)

        if model_fn:
            raw = model_fn(messages)
        else:
            raw = f"Step {step_num}: Analyzing the question."

        thought = parse_thought(raw, step_num)
        thought["score"] = evaluate_thought(thought, question)

        if thought["score"] < 0.3 and backtracks_used < max_backtracks and thoughts:
            backtracks_used += 1
            weakest = min(thoughts, key=lambda t: t.get("score", 0.5))
            thought["status"] = "revised"
            thought["revision_of"] = weakest["step"]

        thoughts.append(thought)

        if thought["is_final"]:
            break

    final_answer = None
    for t in reversed(thoughts):
        if t.get("is_final"):
            final_answer = t["content"]
            break

    return {
        "thoughts": thoughts,
        "final_answer": final_answer or thoughts[-1]["content"] if thoughts else "",
        "steps_used": len(thoughts),
        "backtracks_used": backtracks_used,
    }