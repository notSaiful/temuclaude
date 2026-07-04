#!/usr/bin/env python3
"""
Temuclaude Benchmark — Full Temuclaude Runner
Runs full Temuclaude (with Fusion, self-consistency, code verify, Self-QA) on a benchmark.

Usage:
  python benchmarks/run_temuclaude.py --dataset sample --sample 10
  python benchmarks/run_temuclaude.py --dataset hle --sample 50 --text-only
  python benchmarks/run_temuclaude.py --dataset path/to/custom.json --exact-match
"""
import argparse
import asyncio
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from benchmarks.datasets import load_dataset_by_name, create_sample_dataset
from benchmarks.benchmark_runner import run_benchmark, save_results
from src.orchestrator import Temuclaude


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run full Temuclaude benchmark")
    parser.add_argument("--dataset", required=True, help="Dataset name ('hle', 'mrcr', 'sample') or path to JSON")
    parser.add_argument("--sample", type=int, default=None, help="Limit to N questions")
    parser.add_argument("--text-only", action="store_true", help="For HLE: text-only questions")
    parser.add_argument("--output", default=None, help="Output file path")
    parser.add_argument("--exact-match", action="store_true", help="Use exact match judge (no LLM judge)")
    parser.add_argument("--judge-model", default="gpt-oss-120b", help="Model for LLM judge")
    
    args = parser.parse_args()
    
    # Load dataset
    if args.dataset == "sample":
        dataset = create_sample_dataset()
        if args.sample:
            dataset = dataset[:args.sample]
    else:
        dataset = load_dataset_by_name(args.dataset, sample_size=args.sample, text_only=args.text_only)
    
    print(f"Loaded {len(dataset)} questions from '{args.dataset}'")
    print(f"Running full Temuclaude (Fusion + Self-QA + skills)")
    print(f"Judge: {'exact match' if args.exact_match else f'LLM ({args.judge_model})'}")
    print()
    
    # Create orchestrator
    tc = Temuclaude()
    
    # Define model function that uses full Temuclaude (complete method)
    async def temuclaude_model_func(model_name: str, messages: list, max_tokens: int = 8192, temperature: float = 0.0, timeout: int = 120) -> str:
        # Extract question from messages
        question = ""
        for msg in messages:
            if msg["role"] == "user":
                question = msg["content"]
                break
        
        # Use full Temuclaude complete() method
        answer = await asyncio.wait_for(tc.complete(question), timeout=timeout)
        return answer
    
    # Run benchmark
    results = await run_benchmark(
        dataset=dataset,
        model_func=temuclaude_model_func,
        model_name="temuclaude",
        judge_model=args.judge_model if not args.exact_match else None,
        call_model_for_judge=tc.call_model_with_fallback if not args.exact_match else None,
        use_exact_match=args.exact_match,
        max_tokens=8192,
        timeout_per_question=300,  # Temuclaude is slower (Fusion + Self-QA)
    )
    
    # Save results
    output_path = args.output or f"benchmarks/results/temuclaude_{args.dataset}.json"
    save_results(results, output_path)
    
    # Print summary
    print(f"\nAccuracy: {results['accuracy']:.1%} ({results['correct']}/{results['total_questions']})")


if __name__ == "__main__":
    asyncio.run(main())