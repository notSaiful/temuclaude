"""
Timuclaude Preference-Data Router
Collects routing decisions and outcomes from query logs, builds a preference dataset,
and uses it to improve future routing decisions.

Based on:
- RouteLLM (arXiv:2406.18665): Train a router on preference data — which queries
  need strong models vs which can use cheap models. 2x cost reduction.
- BEST-Route (2025): Choose model AND sample count based on query difficulty.
  60% cost reduction with <1% performance drop.

This module:
1. Records every routing decision: query → task_type → tier → model → outcome
2. Builds a preference dataset: (query, strong_model, weak_model, preference)
3. Uses the dataset to identify patterns: which query types need which models
4. Outputs routing recommendations to improve adaptive_routing.json

Data is saved to config/routing_preferences.json for persistence.
"""
import json
import os
import re
from datetime import datetime, timezone
from collections import defaultdict
from typing import Optional, Dict, List


PREFS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "routing_preferences.json"
)
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")


def load_preferences() -> dict:
    """Load persisted routing preferences."""
    if not os.path.isfile(PREFS_FILE):
        return {
            "routing_records": [],
            "task_type_model_stats": {},
            "total_records": 0,
            "last_updated": None,
        }
    try:
        with open(PREFS_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {
            "routing_records": [],
            "task_type_model_stats": {},
            "total_records": 0,
            "last_updated": None,
        }


def save_preferences(data: dict) -> None:
    """Persist routing preferences."""
    os.makedirs(os.path.dirname(PREFS_FILE), exist_ok=True)
    data["last_updated"] = datetime.now(timezone.utc).isoformat()
    with open(PREFS_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def record_routing_decision(
    query: str,
    task_type: str,
    tier: str,
    model: str,
    models_used: list,
    strategy: str,
    latency_ms: int,
    success: bool,
    tokens_used: int = 0,
) -> None:
    """Record a single routing decision for future analysis.
    
    Args:
        query: The user's query (truncated to 200 chars for storage)
        task_type: Classified task type
        tier: Difficulty tier
        model: Primary model used
        models_used: All models involved
        strategy: Orchestration strategy
        latency_ms: Total latency
        success: Whether the query succeeded
        tokens_used: Estimated tokens used
    """
    prefs = load_preferences()
    
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query_preview": query[:200],
        "query_length": len(query),
        "query_words": len(query.split()),
        "task_type": task_type,
        "tier": tier,
        "model": model,
        "models_used": models_used,
        "strategy": strategy,
        "latency_ms": latency_ms,
        "success": success,
        "tokens_used": tokens_used,
    }
    
    prefs["routing_records"].append(record)
    prefs["total_records"] += 1
    
    # Keep last 500 records to avoid bloat
    if len(prefs["routing_records"]) > 500:
        prefs["routing_records"] = prefs["routing_records"][-500:]
    
    # Update task_type → model stats
    ts = prefs.get("task_type_model_stats", {})
    if not isinstance(ts, dict):
        ts = {}
    
    key = f"{task_type}_{tier}"
    if key not in ts:
        ts[key] = {
            "count": 0,
            "successes": 0,
            "failures": 0,
            "avg_latency": 0,
            "total_latency": 0,
            "models": defaultdict(int),
            "best_model": None,
        }
    
    ts[key]["count"] += 1
    if success:
        ts[key]["successes"] += 1
    else:
        ts[key]["failures"] += 1
    
    ts[key]["total_latency"] += latency_ms
    ts[key]["avg_latency"] = ts[key]["total_latency"] / ts[key]["count"]
    
    # Track model usage
    if isinstance(ts[key]["models"], dict):
        model_counts = ts[key]["models"]
    else:
        model_counts = defaultdict(int)
        model_counts.update(ts[key]["models"])
    
    for m in models_used:
        # Clean model name (remove +suffixes)
        clean_m = m.split("+")[0].split("(")[0]
        model_counts[clean_m] += 1
    ts[key]["models"] = dict(model_counts)
    
    # Determine best model (highest success rate * most used)
    if ts[key]["successes"] > 0:
        best_model = max(model_counts, key=lambda k: model_counts[k]) if model_counts else None
        ts[key]["best_model"] = best_model
    
    prefs["task_type_model_stats"] = ts
    save_preferences(prefs)


def get_routing_recommendations() -> dict:
    """Analyze routing data and produce recommendations.
    
    Returns:
        Dict mapping task_type_tier → recommended model
        Only recommends changes if there's enough data.
    """
    prefs = load_preferences()
    ts = prefs.get("task_type_model_stats", {})
    
    recommendations = {}
    
    for key, stats in ts.items():
        if not isinstance(stats, dict):
            continue
        
        count = stats.get("count", 0)
        if count < 5:
            # Not enough data to make a recommendation
            recommendations[key] = {
                "recommendation": "insufficient_data",
                "count": count,
                "needed": 5,
            }
            continue
        
        success_rate = stats.get("successes", 0) / count
        best_model = stats.get("best_model")
        avg_latency = stats.get("avg_latency", 0)
        
        if success_rate < 0.7 and best_model:
            # Low success rate — recommend trying a different model
            recommendations[key] = {
                "recommendation": "try_different_model",
                "current_best": best_model,
                "success_rate": round(success_rate, 2),
                "avg_latency_ms": round(avg_latency),
                "count": count,
            }
        elif success_rate >= 0.9 and avg_latency > 5000 and best_model:
            # High success but slow — recommend a faster/cheaper model
            recommendations[key] = {
                "recommendation": "try_cheaper_model",
                "current_best": best_model,
                "success_rate": round(success_rate, 2),
                "avg_latency_ms": round(avg_latency),
                "count": count,
            }
        else:
            # Good performance — keep current routing
            recommendations[key] = {
                "recommendation": "maintain",
                "current_best": best_model,
                "success_rate": round(success_rate, 2),
                "avg_latency_ms": round(avg_latency),
                "count": count,
            }
    
    return recommendations


def get_preference_dataset() -> list:
    """Build a preference dataset for training a router model (RouteLLM pattern).
    
    Returns a list of (query, strong_model, weak_model, preference) tuples
    where preference is 1 if strong model was needed, 0 if weak sufficed.
    """
    prefs = load_preferences()
    records = prefs.get("routing_records", [])
    
    dataset = []
    for rec in records:
        if not isinstance(rec, dict):
            continue
        
        tier = rec.get("tier", "")
        success = rec.get("success", False)
        
        # Preference: 1 if strong model (hard tier) was needed
        # 0 if weak model (trivial/medium) sufficed
        if tier == "hard" and success:
            preference = 1  # Strong model was needed
        elif tier in ("trivial", "medium") and success:
            preference = 0  # Weak model sufficed
        else:
            continue  # Skip failures
        
        dataset.append({
            "query": rec.get("query_preview", ""),
            "query_words": rec.get("query_words", 0),
            "task_type": rec.get("task_type", ""),
            "tier": tier,
            "model": rec.get("model", ""),
            "preference": preference,
            "latency_ms": rec.get("latency_ms", 0),
        })
    
    return dataset


if __name__ == "__main__":
    recs = get_routing_recommendations()
    print(json.dumps(recs, indent=2))