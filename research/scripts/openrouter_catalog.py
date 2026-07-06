#!/usr/bin/env python3
"""OpenRouter Catalog — fetches all models, filters for candidates."""

import json, os, time
from pathlib import Path
from urllib.request import urlopen, Request

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
CURRENT_MODELS_FILE = Path(os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude") + "/config/litellm.yaml")

def get_current_model_ids():
    if not CURRENT_MODELS_FILE.exists():
        return []
    content = CURRENT_MODELS_FILE.read_text()
    models = []
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("model: openrouter/"):
            models.append(line.replace("model: openrouter/", "").strip())
    return models

def fetch_all_models():
    try:
        req = Request(OPENROUTER_MODELS_URL, headers={"User-Agent": "TemuclaudeOptimizer/1.0", "Accept": "application/json"})
        with urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8")).get("data", [])
    except Exception:
        return []

def parse_model(model):
    pricing = model.get("pricing", {})
    prompt_cost = float(pricing.get("prompt", "0") or "0")
    completion_cost = float(pricing.get("completion", "0") or "0")
    return {
        "id": model.get("id", ""), "name": model.get("name", ""),
        "context_length": model.get("context_length", 0),
        "prompt_cost_per_1m": prompt_cost * 1_000_000,
        "is_free": prompt_cost == 0 and completion_cost == 0,
    }

def rank_candidates(all_models, current_ids):
    candidates = []
    for model in all_models:
        p = parse_model(model)
        if p["id"] in current_ids or p["context_length"] < 4096:
            continue
        score = 0
        if p["is_free"]: score += 100
        if p["prompt_cost_per_1m"] < 0.50: score += 30
        if p["prompt_cost_per_1m"] < 0.10: score += 20
        if p["context_length"] >= 128000: score += 20
        if p["context_length"] >= 32000: score += 10
        p["score"] = score
        candidates.append(p)
    candidates.sort(key=lambda x: x["score"], reverse=True)
    return candidates

def get_top_candidates(limit=10):
    current = get_current_model_ids()
    all_models = fetch_all_models()
    return rank_candidates(all_models, current)[:limit]

if __name__ == "__main__":
    current = get_current_model_ids()
    print(f"Current: {len(current)} models")
    for c in get_top_candidates(5):
        cost = "FREE" if c["is_free"] else f"${c['prompt_cost_per_1m']:.2f}/1M"
        print(f"  [{c['score']}] {c['id']} (ctx: {c['context_length']}, cost: {cost})")
