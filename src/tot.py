"""
Temuclaude Tree of Thoughts Module
Explores multiple reasoning paths as a tree using BFS with LLM self-evaluation.

Based on:
- Tree of Thoughts (Princeton, arXiv:2305.10601)
  Generalizes CoT to explore multiple reasoning paths. LM generates "thoughts"
  (intermediate steps), self-evaluates them, and uses BFS to search.
  Game of 24: GPT-4 CoT solves 4%, ToT achieves 74% (+70pp).
- Graph of Thoughts (arXiv:2308.09687)
  Extends ToT to graph structure with merge/refine/feedback operations.
  +62% over ToT, 31% cost reduction.

This is used for MEDIUM tier problems that need search but don't need full MCTS.
For HARD tier, the orchestrator uses 3-layer MoA + self-consistency + code verification.
"""
import asyncio
import re
from typing import Optional, Callable, Awaitable, List


DEFAULT_MAX_DEPTH = 3
DEFAULT_BRANCHING = 3
DEFAULT_MAX_NODES = 15  # Limit total nodes to control cost


def build_thought_generation_prompt(question: str, current_thoughts: list, depth: int) -> list:
    """Build prompt to generate the next thought(s) in the reasoning tree.
    
    Args:
        question: The original question
        current_thoughts: List of thoughts generated so far (the path to this node)
        depth: Current depth in the tree (0 = root)
    
    Returns:
        Messages list for the model
    """
    thoughts_text = ""
    if current_thoughts:
        thoughts_text = "\n\nPrevious reasoning steps:\n"
        for i, thought in enumerate(current_thoughts, 1):
            thoughts_text += f"Step {i}: {thought}\n"
    
    system_prompt = (
        "You are a reasoning engine. Break down the problem into intermediate "
        "thinking steps. Generate the NEXT thinking step that moves toward the answer. "
        "Be specific and logical. Do NOT jump to the final answer — just the next step. "
        "If this is the final step, write 'FINAL ANSWER: X' at the end."
    )
    
    user_prompt = (
        f"Question: {question}\n"
        f"{thoughts_text}\n"
        f"Generate the next reasoning step (step {depth + 1}):"
    )
    
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_evaluation_prompt(question: str, thought: str, current_thoughts: list) -> list:
    """Build prompt to evaluate a single thought (self-evaluation).
    
    The LLM evaluates whether this thought is a good step toward the answer.
    Returns a score from 0.0 to 1.0.
    """
    thoughts_text = ""
    if current_thoughts:
        thoughts_text = "\n\nFull reasoning so far:\n"
        for i, t in enumerate(current_thoughts, 1):
            thoughts_text += f"Step {i}: {t}\n"
    
    system_prompt = (
        "You are a reasoning evaluator. Score the given thinking step on a scale "
        "of 0.0 to 1.0 where:\n"
        "1.0: Excellent step — correct, logical, moves toward the answer\n"
        "0.7-0.9: Good step — mostly correct with minor issues\n"
        "0.4-0.6: Mediocre step — partially useful but unclear or incomplete\n"
        "0.0-0.3: Bad step — incorrect, illogical, or counterproductive\n\n"
        "Respond with ONLY a number between 0.0 and 1.0."
    )
    
    user_prompt = (
        f"Question: {question}\n"
        f"{thoughts_text}\n"
        f"Step to evaluate: {thought}\n\n"
        f"Score (0.0-1.0):"
    )
    
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def extract_score(response: str) -> float:
    """Extract a float score from the model's response."""
    match = re.search(r'(\d+\.?\d*)', response)
    if match:
        score = float(match.group(1))
        return max(0.0, min(1.0, score))
    return 0.5  # Default neutral


def is_final_answer(thought: str) -> bool:
    """Check if a thought contains a final answer."""
    return bool(re.search(r'FINAL ANSWER:', thought, re.IGNORECASE))


def extract_final_answer(thought: str) -> str:
    """Extract the final answer from a thought."""
    match = re.search(r'FINAL ANSWER:\s*(.+?)(?:\n|$)', thought, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    # Fallback: try "Answer: X"
    match = re.search(r'[Aa]nswer:\s*(.+?)(?:\n|$)', thought)
    if match:
        return match.group(1).strip()
    return thought.strip()


async def tree_of_thoughts(
    question: str,
    model: str,
    call_model_func: Callable[..., Awaitable[str]],
    max_depth: int = DEFAULT_MAX_DEPTH,
    branching: int = DEFAULT_BRANCHING,
    max_nodes: int = DEFAULT_MAX_NODES,
    max_tokens: int = 4096,
) -> dict:
    """
    Run Tree of Thoughts search for the given question.
    
    Uses BFS with LLM self-evaluation:
    1. Generate K candidate thoughts at each step
    2. Evaluate each thought (0.0-1.0)
    3. Keep the top-scoring thoughts
    4. Repeat until final answer found or max depth reached
    
    Args:
        question: The user's question
        model: Which model to use for thinking and evaluation
        call_model_func: Async function to call a model
        max_depth: Maximum depth of the reasoning tree
        branching: Number of candidate thoughts per node
        max_nodes: Maximum total nodes (cost control)
        max_tokens: Max tokens per model call
    
    Returns:
        Dict with:
        - 'answer': The final answer (or best thought if no final found)
        - 'found': Whether a final answer was reached
        - 'path': The reasoning path that led to the answer
        - 'nodes_explored': Total nodes explored
        - 'best_score': Best evaluation score achieved
    """
    nodes_explored = 0
    best_score = 0.0
    
    # BFS queue: (thoughts_so_far, score)
    queue = [([], 0.0)]
    
    while queue and nodes_explored < max_nodes:
        current_thoughts, current_score = queue.pop(0)  # BFS
        depth = len(current_thoughts)
        
        if depth >= max_depth:
            continue
        
        # Generate K candidate thoughts
        gen_messages = build_thought_generation_prompt(question, current_thoughts, depth)
        gen_tasks = [
            call_model_func(model, gen_messages, temperature=0.7, max_tokens=max_tokens)
            for _ in range(branching)
        ]
        candidate_thoughts = await asyncio.gather(*gen_tasks)
        nodes_explored += branching
        
        # Evaluate each candidate
        eval_tasks = []
        for thought in candidate_thoughts:
            eval_messages = build_evaluation_prompt(question, thought, current_thoughts)
            eval_tasks.append(call_model_func(model, eval_messages, max_tokens=100))
        eval_responses = await asyncio.gather(*eval_tasks)
        
        scored_thoughts = []
        for thought, eval_resp in zip(candidate_thoughts, eval_responses):
            score = extract_score(eval_resp)
            scored_thoughts.append((thought, score))
            if score > best_score:
                best_score = score
        
        # Sort by score, keep top candidates
        scored_thoughts.sort(key=lambda x: x[1], reverse=True)
        top_thoughts = scored_thoughts[:2]  # Keep top 2
        
        for thought, score in top_thoughts:
            new_path = current_thoughts + [thought]
            
            # Check if this thought contains a final answer
            if is_final_answer(thought):
                answer = extract_final_answer(thought)
                return {
                    "answer": answer,
                    "found": True,
                    "path": new_path,
                    "nodes_explored": nodes_explored,
                    "best_score": best_score,
                }
            
            # Add to queue for further exploration
            queue.append((new_path, score))
    
    # No final answer found — return best thought from queue
    if queue:
        best_path, _ = max(queue, key=lambda x: x[1])
        last_thought = best_path[-1] if best_path else ""
        return {
            "answer": last_thought,
            "found": False,
            "path": best_path,
            "nodes_explored": nodes_explored,
            "best_score": best_score,
        }
    
    return {
        "answer": "",
        "found": False,
        "path": [],
        "nodes_explored": nodes_explored,
        "best_score": best_score,
    }