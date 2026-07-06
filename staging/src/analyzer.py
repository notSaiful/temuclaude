"""
Temuclaude Query Log Analyzer
Analyzes past query logs to find patterns: which task types have lowest success,
which models perform best per task type.

This is the data-driven self-improvement foundation — it tells us WHERE
Temuclaude is weak and WHICH model is best for each task.
"""
import json
import os
from collections import defaultdict
from typing import Optional
from pathlib import Path


def analyze_logs(log_dir: Optional[str] = None) -> dict:
    """
    Analyze all query logs in the log directory.
    
    Args:
        log_dir: Path to logs directory. Default: ../logs relative to this file.
    
    Returns:
        Dict with analysis:
        - 'total_queries': Total number of queries
        - 'success_rate': Overall success rate (0.0-1.0)
        - 'by_task_type': {task_type: {count, success_rate, best_model}}
        - 'by_model': {model: {count, success_rate}}
        - 'by_strategy': {strategy: {count, success_rate}}
        - 'weakest_task': Task type with lowest success rate
        - 'best_models': {task_type: best_model_name}
    """
    if log_dir is None:
        log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    
    log_dir_path = Path(log_dir) if log_dir else Path(os.path.join(os.path.dirname(__file__), "..", "logs"))
    if not log_dir_path.exists():
        return {
            "total_queries": 0,
            "success_rate": 0.0,
            "by_task_type": {},
            "by_model": {},
            "by_strategy": {},
            "weakest_task": None,
            "best_models": {},
            "message": "No logs found",
        }
    
    # Read all log files
    all_queries = []
    for log_file in log_dir_path.glob("queries_*.jsonl"):
        with open(log_file, "r") as f:
            for line in f:
                try:
                    all_queries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    
    if not all_queries:
        return {
            "total_queries": 0,
            "success_rate": 0.0,
            "by_task_type": {},
            "by_model": {},
            "by_strategy": {},
            "weakest_task": None,
            "best_models": {},
            "message": "No queries in logs",
        }
    
    # Overall stats
    total = len(all_queries)
    successful = sum(1 for q in all_queries if q.get("success", False))
    success_rate = successful / total if total > 0 else 0.0
    
    # By task type
    by_task_type = defaultdict(lambda: {"count": 0, "success": 0, "models": defaultdict(lambda: {"count": 0, "success": 0})})
    for q in all_queries:
        task_type = q.get("task_type", "unknown")
        by_task_type[task_type]["count"] += 1
        if q.get("success", False):
            by_task_type[task_type]["success"] += 1
        # Track which models were used
        for model in q.get("models_used", []):
            # Strip suffixes like "+code" or "+consistency"
            clean_model = model.split("+")[0]
            by_task_type[task_type]["models"][clean_model]["count"] += 1
            if q.get("success", False):
                by_task_type[task_type]["models"][clean_model]["success"] += 1
    
    # Calculate success rates and best models per task type
    task_analysis = {}
    best_models = {}
    weakest_task = None
    weakest_rate = 1.0
    
    for task_type, data in by_task_type.items():
        rate = data["success"] / data["count"] if data["count"] > 0 else 0.0
        task_analysis[task_type] = {
            "count": data["count"],
            "success_rate": rate,
        }
        
        # Find best model for this task type
        best_model = None
        best_model_rate = 0.0
        for model, mdata in data["models"].items():
            m_rate = mdata["success"] / mdata["count"] if mdata["count"] > 0 else 0.0
            if m_rate > best_model_rate and mdata["count"] >= 2:  # Need at least 2 samples
                best_model_rate = m_rate
                best_model = model
        
        if best_model:
            best_models[task_type] = {
                "model": best_model,
                "success_rate": best_model_rate,
                "count": data["models"][best_model]["count"],
            }
            task_analysis[task_type]["best_model"] = best_model
        
        # Track weakest task type
        if rate < weakest_rate:
            weakest_rate = rate
            weakest_task = task_type
    
    # By model (overall)
    by_model = defaultdict(lambda: {"count": 0, "success": 0})
    for q in all_queries:
        for model in q.get("models_used", []):
            clean_model = model.split("+")[0]
            by_model[clean_model]["count"] += 1
            if q.get("success", False):
                by_model[clean_model]["success"] += 1
    
    model_analysis = {}
    for model, data in by_model.items():
        model_analysis[model] = {
            "count": data["count"],
            "success_rate": data["success"] / data["count"] if data["count"] > 0 else 0.0,
        }
    
    # By strategy
    by_strategy = defaultdict(lambda: {"count": 0, "success": 0})
    for q in all_queries:
        strategy = q.get("strategy", "unknown")
        by_strategy[strategy]["count"] += 1
        if q.get("success", False):
            by_strategy[strategy]["success"] += 1
    
    strategy_analysis = {}
    for strategy, data in by_strategy.items():
        strategy_analysis[strategy] = {
            "count": data["count"],
            "success_rate": data["success"] / data["count"] if data["count"] > 0 else 0.0,
        }
    
    return {
        "total_queries": total,
        "success_rate": success_rate,
        "by_task_type": task_analysis,
        "by_model": model_analysis,
        "by_strategy": strategy_analysis,
        "weakest_task": weakest_task,
        "best_models": best_models,
    }


def print_report(analysis: dict) -> str:
    """Print a human-readable analysis report. Returns the report as string."""
    lines = []
    lines.append("=" * 60)
    lines.append("TEMUCLAUDE — QUERY LOG ANALYSIS REPORT")
    lines.append("=" * 60)
    lines.append(f"Total queries: {analysis['total_queries']}")
    lines.append(f"Overall success rate: {analysis['success_rate']:.1%}")
    lines.append("")
    
    if analysis.get("weakest_task"):
        lines.append(f"Weakest task type: {analysis['weakest_task']}")
        lines.append("")
    
    lines.append("By task type:")
    for task, data in analysis.get("by_task_type", {}).items():
        rate = data["success_rate"]
        count = data["count"]
        best = data.get("best_model", "—")
        lines.append(f"  {task:15} {rate:5.1%} ({count} queries, best: {best})")
    lines.append("")
    
    lines.append("By model:")
    for model, data in analysis.get("by_model", {}).items():
        rate = data["success_rate"]
        count = data["count"]
        lines.append(f"  {model:25} {rate:5.1%} ({count} queries)")
    lines.append("")
    
    lines.append("By strategy:")
    for strategy, data in analysis.get("by_strategy", {}).items():
        rate = data["success_rate"]
        count = data["count"]
        lines.append(f"  {strategy:40} {rate:5.1%} ({count} queries)")
    lines.append("")
    
    if analysis.get("best_models"):
        lines.append("Best models per task type:")
        for task, info in analysis["best_models"].items():
            lines.append(f"  {task:15} → {info['model']} ({info['success_rate']:.1%})")
        lines.append("")
    
    report = "\n".join(lines)
    print(report)
    return report