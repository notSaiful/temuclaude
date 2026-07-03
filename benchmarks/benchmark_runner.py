"""
Timuclaude Benchmark Runner
Runs a model on a dataset, scores each response, tracks results.

Universal: works with any Q&A dataset in {id, question, answer, category} format.
"""
import asyncio
import json
import time
import os
from typing import Callable, Awaitable, Optional
from .datasets import load_dataset_by_name, create_sample_dataset
from .judges import llm_judge, exact_match_judge


async def run_benchmark(
    dataset: list,
    model_func: Callable[..., Awaitable[str]],
    judge_func: Optional[Callable] = None,
    model_name: str = "unknown",
    judge_model: Optional[str] = None,
    call_model_for_judge: Optional[Callable[..., Awaitable[str]]] = None,
    max_tokens: int = 8192,
    timeout_per_question: int = 120,
    use_exact_match: bool = False,
) -> dict:
    """
    Run a benchmark: for each question, call model_func, score with judge_func.
    
    Args:
        dataset: List of {id, question, answer, category}
        model_func: Async function (model_name, messages, max_tokens) -> response
        judge_func: Scoring function (question, response, answer) -> {correct, ...}
        model_name: Name of the model being tested (for logging)
        judge_model: Model name for LLM judge (if using LLM judge)
        call_model_for_judge: Async function for judge model calls
        max_tokens: Max tokens for model responses
        timeout_per_question: Timeout per question in seconds
        use_exact_match: Use exact_match_judge instead of LLM judge
    
    Returns:
        {
            model_name: str,
            total_questions: int,
            correct: int,
            accuracy: float,
            results: [{id, question, answer, response, correct, ...}],
            by_category: {category: {total, correct, accuracy}},
            total_latency_ms: int,
            avg_latency_ms: int,
        }
    """
    results = []
    correct_count = 0
    total_latency = 0
    
    for i, item in enumerate(dataset):
        question = item["question"]
        correct_answer = item["answer"]
        category = item.get("category", "unknown")
        qid = item.get("id", str(i + 1))
        
        start = time.time()
        
        try:
            # Call the model
            messages = [
                {"role": "system", "content": "You are Timuclaude, a helpful AI assistant. Answer the following question. At the end, write 'Answer: ' followed by your final answer."},
                {"role": "user", "content": question},
            ]
            
            response = await asyncio.wait_for(
                model_func(model_name, messages, max_tokens=max_tokens),
                timeout=timeout_per_question,
            )
            
            latency = int((time.time() - start) * 1000)
            total_latency += latency
            
            # Score the response
            if use_exact_match:
                judgment = exact_match_judge(response, correct_answer)
            elif judge_func:
                judgment = judge_func(question, response, correct_answer)
            elif judge_model and call_model_for_judge:
                judgment = await llm_judge(
                    question, response, correct_answer,
                    judge_model, call_model_for_judge,
                )
            else:
                # Default: exact match
                judgment = exact_match_judge(response, correct_answer)
            
            is_correct = judgment["correct"]
            if is_correct:
                correct_count += 1
            
            results.append({
                "id": qid,
                "question": question[:200],
                "correct_answer": correct_answer,
                "response": response[:500],
                "correct": is_correct,
                "extracted_answer": judgment.get("extracted_answer", ""),
                "category": category,
                "latency_ms": latency,
            })
            
            print(f"  Q{i+1}/{len(dataset)} [{category}] {'✓' if is_correct else '✗'} ({latency}ms) — {correct_answer[:30]}")
            
        except asyncio.TimeoutError:
            latency = int((time.time() - start) * 1000)
            total_latency += latency
            results.append({
                "id": qid,
                "question": question[:200],
                "correct_answer": correct_answer,
                "response": "[TIMEOUT]",
                "correct": False,
                "extracted_answer": "",
                "category": category,
                "latency_ms": latency,
            })
            print(f"  Q{i+1}/{len(dataset)} [{category}] ✗ TIMEOUT ({latency}ms)")
            
        except Exception as e:
            latency = int((time.time() - start) * 1000)
            total_latency += latency
            results.append({
                "id": qid,
                "question": question[:200],
                "correct_answer": correct_answer,
                "response": f"[ERROR: {str(e)[:100]}]",
                "correct": False,
                "extracted_answer": "",
                "category": category,
                "latency_ms": latency,
            })
            print(f"  Q{i+1}/{len(dataset)} [{category}] ✗ ERROR: {str(e)[:50]}")
    
    # Calculate stats
    total = len(results)
    accuracy = correct_count / total if total > 0 else 0.0
    
    # Per-category breakdown
    by_category = {}
    for r in results:
        cat = r["category"]
        if cat not in by_category:
            by_category[cat] = {"total": 0, "correct": 0}
        by_category[cat]["total"] += 1
        if r["correct"]:
            by_category[cat]["correct"] += 1
    
    for cat in by_category:
        by_category[cat]["accuracy"] = by_category[cat]["correct"] / by_category[cat]["total"]
    
    avg_latency = total_latency // total if total > 0 else 0
    
    return {
        "model_name": model_name,
        "total_questions": total,
        "correct": correct_count,
        "accuracy": accuracy,
        "results": results,
        "by_category": by_category,
        "total_latency_ms": total_latency,
        "avg_latency_ms": avg_latency,
    }


def save_results(results: dict, output_path: str) -> None:
    """Save benchmark results to JSON file."""
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {output_path}")