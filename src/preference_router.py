"""
Temuclaude Preference-Data Router
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
            "success": True,  # All records in dataset are successful
            "latency_ms": rec.get("latency_ms", 0),
        })
    
    return dataset


# ============================================================
# ROUTE-LLM STYLE PREFERENCE-DATA TRAINED ROUTER
# ============================================================

def extract_features(query: str) -> dict:
    """Extract features from a query for routing classification.
    
    Returns a dict of features that can be used to train a classifier.
    """
    words = query.lower().split()
    query_length = len(query)
    word_count = len(words)
    
    # Keyword features (1 if present, 0 otherwise)
    math_keywords = ["calculate", "solve", "equation", "prove", "integral", "derivative",
                     "matrix", "theorem", "algebra", "geometry", "probability", "statistics",
                     "sum", "product", "factor", "prime", "polynomial", "function", "limit",
                     "series", "differential", "vector", "tensor", "topology", "math"]
    coding_keywords = ["code", "function", "debug", "python", "javascript", "java", "react",
                       "typescript", "rust", "golang", "sql", "algorithm", "compile",
                       "error:", "bug", "docker", "kubernetes", "api", "rest", "graphql"]
    reasoning_keywords = ["compare", "analyze", "evaluate", "why", "how", "explain",
                          "trade-off", "tradeoff", "consequence", "implication",
                          "difference between", "analyze", "evaluate"]
    knowledge_keywords = ["what is", "who is", "when did", "where is", "history of",
                          "define", "definition", "meaning of", "capital of",
                          "largest", "smallest", "tallest"]
    creative_keywords = ["write a poem", "write a story", "write an essay", "write a blog",
                         "write a script", "compose", "screenplay", "generate a",
                         "create a story", "write a song", "write a letter"]
    agentic_keywords = ["deploy", "setup", "install", "configure", "run", "execute",
                        "build a", "automate", "pipeline", "workflow"]
    
    features = {
        "query_length": query_length,
        "word_count": word_count,
        "has_math_expr": 1 if any(c in query for c in "+-*/^=") and any(c.isdigit() for c in query) else 0,
        "starts_with_what_is": 1 if query.lower().startswith("what is ") else 0,
        "starts_with_how": 1 if query.lower().startswith("how ") else 0,
        "starts_with_why": 1 if query.lower().startswith("why ") else 0,
    }
    
    # Add keyword features
    for kw in math_keywords:
        features[f"kw_{kw.replace(' ', '_').replace('-', '_')}"] = 1 if kw in query.lower() else 0
    for kw in coding_keywords:
        features[f"kw_{kw.replace(' ', '_').replace('-', '_')}"] = 1 if kw in query.lower() else 0
    for kw in reasoning_keywords:
        features[f"kw_{kw.replace(' ', '_').replace('-', '_')}"] = 1 if kw in query.lower() else 0
    for kw in knowledge_keywords:
        features[f"kw_{kw.replace(' ', '_').replace('-', '_')}"] = 1 if kw in query.lower() else 0
    for kw in creative_keywords:
        features[f"kw_{kw.replace(' ', '_').replace('-', '_')}"] = 1 if kw in query.lower() else 0
    for kw in agentic_keywords:
        features[f"kw_{kw.replace(' ', '_').replace('-', '_')}"] = 1 if kw in query.lower() else 0
    
    return features


def train_router_model(preference_data: list) -> dict:
    """Train a simple routing model from preference data.
    
    This implements the RouteLLM pattern: learn which queries need strong models
    vs which can use cheap models based on historical performance data.
    
    Uses a simple linear model with gradient descent (no external dependencies).
    
    Returns:
        Dict with model weights and metadata
    """
    if not preference_data or len(preference_data) < 10:
        return {"trained": False, "reason": "insufficient_data", "min_samples": 10}
    
    # Build feature matrix and labels
    # Label: 1 = needs strong model (hard tier success), 0 = weak model suffices (trivial/medium success)
    X = []  # feature vectors
    y = []  # labels
    
    for rec in preference_data:
        query = rec.get("query", "")
        tier = rec.get("tier", "")
        success = rec.get("success", False)
        
        if not success:
            continue  # Skip failures
        
        features = extract_features(query)
        
        # Convert features to vector (sorted keys for consistency)
        feature_keys = sorted(features.keys())
        feature_vector = [features[k] for k in feature_keys]
        
        # Label: 1 if hard tier (needs strong model), 0 if trivial/medium
        label = 1 if tier == "hard" else 0
        
        X.append(feature_vector)
        y.append(label)
    
    if len(X) < 5:
        return {"trained": False, "reason": "insuccessful_samples", "successful_count": len(X)}
    
    # Simple gradient descent for logistic regression
    import random
    random.seed(42)
    
    n_features = len(X[0])
    weights = [random.uniform(-0.1, 0.1) for _ in range(n_features)]
    bias = 0.0
    
    learning_rate = 0.01
    epochs = 1000
    
    for epoch in range(epochs):
        # Forward pass
        predictions = []
        for i, x in enumerate(X):
            z = sum(w * xi for w, xi in zip(weights, x)) + bias
            # Sigmoid
            pred = 1 / (1 + pow(2.71828, -z))
            predictions.append(pred)
        
        # Compute gradients
        dw = [0.0] * n_features
        db = 0.0
        
        for i, x in enumerate(X):
            error = predictions[i] - y[i]
            for j in range(n_features):
                dw[j] += error * x[j]
            db += error
        
        # Update weights
        for j in range(n_features):
            weights[j] -= learning_rate * dw[j] / len(X)
        bias -= learning_rate * db / len(X)
    
    # Evaluate training accuracy
    correct = 0
    for i, x in enumerate(X):
        z = sum(w * xi for w, xi in zip(weights, x)) + bias
        pred = 1 / (1 + pow(2.71828, -z))
        pred_label = 1 if pred >= 0.5 else 0
        if pred_label == y[i]:
            correct += 1
    
    accuracy = correct / len(X)
    
    # Feature importance (absolute weight values)
    feature_keys = sorted(extract_features("").keys())
    feature_importance = {k: abs(w) for k, w in zip(feature_keys, weights)}
    # Sort by importance
    feature_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
    
    return {
        "trained": True,
        "weights": weights,
        "bias": bias,
        "feature_keys": feature_keys,
        "accuracy": accuracy,
        "training_samples": len(X),
        "feature_importance": feature_importance,
        "model_type": "logistic_regression",
    }


def predict_strong_model_needed(query: str, trained_model: dict) -> tuple:
    """Predict whether a query needs a strong model (hard tier) or weak model (trivial/medium).
    
    Returns:
        (needs_strong: bool, confidence: float 0-1)
    """
    if not trained_model.get("trained", False):
        return (False, 0.5)  # Default to weak model if not trained
    
    features = extract_features(query)
    feature_keys = trained_model["feature_keys"]
    weights = trained_model["weights"]
    bias = trained_model["bias"]
    
    feature_vector = [features.get(k, 0) for k in feature_keys]
    
    z = sum(w * xi for w, xi in zip(weights, feature_vector)) + bias
    prob = 1 / (1 + pow(2.71828, -z))
    
    needs_strong = prob >= 0.5
    confidence = prob if needs_strong else (1 - prob)
    
    return (needs_strong, confidence)


def get_trained_router() -> dict:
    """Load or train the router model from preference data."""
    prefs = load_preferences()
    dataset = get_preference_dataset()
    
    # Try to load cached model
    model_cache_path = os.path.join(
        os.path.dirname(PREFS_FILE), "trained_router.json"
    )
    
    if os.path.isfile(model_cache_path):
        try:
            with open(model_cache_path) as f:
                cached = json.load(f)
            # Check if we have new data since last training
            if cached.get("training_samples") == len(dataset):
                return cached
        except (json.JSONDecodeError, IOError):
            pass
    
    # Train new model
    model = train_router_model(dataset)
    
    if model.get("trained", False):
        # Cache the model
        os.makedirs(os.path.dirname(model_cache_path), exist_ok=True)
        with open(model_cache_path, "w") as f:
            json.dump(model, f, indent=2)
    
    return model


def route_with_trained_model(query: str, task_type: str, tier: str) -> tuple:
    """Route a query using the trained preference-data router.
    
    Returns:
        (model: str, confidence: float, used_trained_router: bool)
    """
    # For trivial tier, always use cheap model (no need for router)
    if tier == "trivial":
        return ("gpt-oss-120b", 1.0, False)
    
    # Get trained router
    trained_model = get_trained_router()
    
    if not trained_model.get("trained", False):
        # Fall back to default routing
        return (None, 0.0, False)
    
    # Predict if strong model needed
    needs_strong, confidence = predict_strong_model_needed(query, trained_model)
    
    if needs_strong:
        # Strong model needed - use task-specific specialist
        from .models import TASK_MODEL_MAP
        model = TASK_MODEL_MAP.get(task_type, "glm-5.2")
    else:
        # Weak model suffices - use cheap model
        model = "gpt-oss-120b"
    
    return (model, confidence, True)


if __name__ == "__main__":
    recs = get_routing_recommendations()
    print(json.dumps(recs, indent=2))
    
    # Test trained router
    print("\n=== TRAINED ROUTER ===")
    model = get_trained_router()
    print(f"Trained: {model.get('trained')}")
    if model.get("trained"):
        print(f"Accuracy: {model.get('accuracy', 0):.2%}")
        print(f"Training samples: {model.get('training_samples', 0)}")
        print(f"Top 10 features:")
        for k, v in list(model.get("feature_importance", {}).items())[:10]:
            print(f"  {k}: {v:.4f}")