"""
Temuclaude Benchmark Results Reporter
Loads, displays, and compares benchmark results.
"""
import json
from typing import Optional


def load_results(file_path: str) -> dict:
    """Load benchmark results from JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


def print_report(results: dict) -> str:
    """Print a human-readable report. Returns the report as string."""
    lines = []
    lines.append("=" * 60)
    lines.append(f"BENCHMARK RESULTS — {results.get('model_name', 'unknown')}")
    lines.append("=" * 60)
    lines.append(f"Total questions: {results['total_questions']}")
    lines.append(f"Correct: {results['correct']}")
    lines.append(f"Accuracy: {results['accuracy']:.1%}")
    lines.append(f"Avg latency: {results['avg_latency_ms']}ms")
    lines.append(f"Total latency: {results['total_latency_ms']}ms")
    lines.append("")
    
    by_cat = results.get("by_category", {})
    if by_cat:
        lines.append("By category:")
        for cat, data in sorted(by_cat.items()):
            lines.append(f"  {cat:20} {data['accuracy']:5.1%} ({data['correct']}/{data['total']})")
        lines.append("")
    
    # Per-question details
    lines.append("Per-question:")
    for r in results.get("results", []):
        status = "✓" if r["correct"] else "✗"
        lines.append(f"  {status} Q{r['id']:>3} [{r['category']:10}] expected: {r['correct_answer'][:30]}")
        if not r["correct"]:
            lines.append(f"       got: {r.get('extracted_answer', '')[:50]}")
    
    report = "\n".join(lines)
    print(report)
    return report


def compare_results(baseline: dict, temuclaude: dict) -> str:
    """Compare two benchmark runs. Returns the comparison as string."""
    lines = []
    lines.append("=" * 60)
    lines.append("BENCHMARK COMPARISON")
    lines.append("=" * 60)
    lines.append(f"Baseline:   {baseline.get('model_name', 'unknown'):20} {baseline['accuracy']:5.1%} ({baseline['correct']}/{baseline['total_questions']})")
    lines.append(f"Temuclaude:  {temuclaude.get('model_name', 'unknown'):20} {temuclaude['accuracy']:5.1%} ({temuclaude['correct']}/{temuclaude['total_questions']})")
    lines.append("")
    
    diff = temuclaude["accuracy"] - baseline["accuracy"]
    if diff > 0:
        lines.append(f"Improvement: +{diff:.1%} ← Temuclaude wins")
    elif diff < 0:
        lines.append(f"Improvement: {diff:.1%} ← Baseline wins")
    else:
        lines.append(f"Improvement: 0.0% ← Tie")
    
    lines.append("")
    
    # Per-category comparison
    base_cats = baseline.get("by_category", {})
    tc_cats = temuclaude.get("by_category", {})
    all_cats = sorted(set(base_cats.keys()) | set(tc_cats.keys()))
    
    if all_cats:
        lines.append("By category:")
        lines.append(f"  {'Category':20} {'Baseline':>10} {'Temuclaude':>10} {'Diff':>8}")
        lines.append(f"  {'-'*20} {'-'*10} {'-'*10} {'-'*8}")
        
        for cat in all_cats:
            b_acc = base_cats.get(cat, {}).get("accuracy", 0.0)
            t_acc = tc_cats.get(cat, {}).get("accuracy", 0.0)
            d = t_acc - b_acc
            sign = "+" if d > 0 else ""
            lines.append(f"  {cat:20} {b_acc:>9.1%} {t_acc:>10.1%} {sign}{d:>6.1%}")
    
    # Latency comparison
    lines.append("")
    lines.append(f"Latency: baseline={baseline['avg_latency_ms']}ms, temuclaude={temuclaude['avg_latency_ms']}ms")
    
    report = "\n".join(lines)
    print(report)
    return report


def compare_files(baseline_path: str, temuclaude_path: str) -> str:
    """Load two result files and compare them."""
    baseline = load_results(baseline_path)
    temuclaude = load_results(temuclaude_path)
    return compare_results(baseline, temuclaude)