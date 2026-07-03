#!/usr/bin/env python3
"""
Timuclaude Benchmark — Baseline Runner
Runs a single model on a benchmark dataset.

Usage:
  python benchmarks/run_baseline.py --model glm-5.2 --dataset sample --sample 10
  python benchmarks/run_baseline.py --model deepseek-v4-pro --dataset hle --sample 50 --text-only
  python benchmarks/run_baseline.py --model glm-5.2 --dataset path/to/custom.json
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
from src.orchestrator import Timuclaude


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run baseline benchmark")
    parser.add_argument("--model", required=True, help="Model name (e.g., glm-5.2, deepseek-v4-pro)")
    parser.add_argument("--dataset", required=True, help="Dataset name ('hle', 'mrcr', 'sample') or path to JSON")
    parser.add_argument("--sample", type=int, default=None, help="Limit to N questions")
    parser.add_argument("--text-only", action="store_true", help="For HLE: text-only questions")
    parser.add_argument("--output", default=None, help="Output file path (default: results/{model}_{dataset}.json)")
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
    print(f"Running baseline with model: {args.model}")
    print(f"Judge: {'exact match' if args.exact_match else f'LLM ({args.judge_model})'}")
    print()
    
    # Create orchestrator
    tc = Timuclaude()
    
    # Run benchmark
    results = await run_benchmark(
        dataset=dataset,
        model_func=tc.call_model_with_fallback,
        model_name=args.model,
        judge_model=args.judge_model if not args.exact_match else None,
        call_model_for_judge=tc.call_model_with_fallback if not args.exact_match else None,
        use_exact_match=args.exact_match,
        max_tokens=8192,
        timeout_per_question=120,
    )
    
    # Save results
    output_path = args.output or f"benchmarks/results/{args.model}_{args.dataset}.json"
    save_results(results, output_path)
    
    # Print summary
    print(f"\nAccuracy: {results['accuracy']:.1%} ({results['correct']}/{results['total_questions']})")


if __name__ == "__main__":
    asyncio.run(main())