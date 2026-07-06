#!/usr/bin/env python3
"""Radar Scorer — scores industry signals by relevance and novelty."""

import json, os
from pathlib import Path
from datetime import datetime, timezone

RELEVANCE_KEYWORDS = {
    "orchestration": 30, "routing": 25, "cascading": 25, "fusion": 25,
    "cost_reduction": 30, "free_model": 25, "quantization": 20,
    "speculative_decoding": 30, "kv_cache": 20, "caching": 15,
    "benchmark": 25, "mmlu": 20, "hle": 25, "reasoning": 20,
    "jailbreak": 20, "prompt_injection": 20, "guardrail": 20,
    "vllm": 25, "litellm": 25, "openrouter": 25, "huggingface": 15,
    "agent": 15, "autonomous": 20, "self_improving": 25,
    "function_calling": 20, "rag": 15,
}

SEEN_FILE = Path(os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude") + "/research/radar_seen.json")

def load_seen():
    if SEEN_FILE.exists():
        with open(SEEN_FILE) as f:
            return json.load(f)
    return {}

def save_seen(seen):
    if len(seen) > 1000:
        items = sorted(seen.items(), key=lambda x: x[1], reverse=True)
        seen = dict(items[:1000])
    with open(SEEN_FILE, 'w') as f:
        json.dump(seen, f, indent=2)

def score_signal(signal):
    text = (signal.get("title", "") + " " + signal.get("description", "")).lower()
    relevance = 0
    matched = []
    for kw, weight in RELEVANCE_KEYWORDS.items():
        if kw in text:
            relevance += weight
            matched.append(kw)
    source = signal.get("source", "")
    if "huggingface" in source: relevance += 10
    if "vllm_releases" in source or "litellm_releases" in source: relevance += 15
    if "hackernews" in source: relevance += min(signal.get("score", 0) / 10, 20)
    action = "monitor"
    if relevance >= 50: action = "research_task"
    elif relevance >= 30: action = "priority_boost"
    elif relevance >= 15: action = "track"
    return {**signal, "score": relevance, "matched_keywords": matched, "action": action}

def filter_novel(signals, seen):
    novel = []
    for s in signals:
        key = f"{s.get('source', '')}:{s.get('title', '')}"
        if key in seen:
            continue
        novel.append(s)
        seen[key] = datetime.now(timezone.utc).isoformat()
    return novel

def score_and_filter(signals):
    seen = load_seen()
    novel = filter_novel(signals, seen)
    save_seen(seen)
    scored = [score_signal(s) for s in novel]
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored

if __name__ == "__main__":
    from radar_sources import scan_all_sources
    scored = score_and_filter(scan_all_sources())
    for s in scored[:10]:
        print(f"[{s['score']}] {s['source']}: {s['title'][:80]}")
