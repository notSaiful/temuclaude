#!/usr/bin/env python3
"""
Scout: HuggingFace Papers + Model Hub
Searches HuggingFace for new papers, models, and spaces related to LLM orchestration.
Also tracks frontier model releases and open-weight alternatives.
"""
import json
import urllib.request
import urllib.parse
import os
import ssl
import certifi
from datetime import datetime, timezone

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "raw")
os.makedirs(OUT_DIR, exist_ok=True)

_ssl_ctx = ssl.create_default_context(cafile=certifi.where())

HF_API = "https://huggingface.co/api"

def fetch_json(url, timeout=30):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Timuclaude-Research/1.0",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"ERROR fetching {url}: {e}")
        return None

def search_hf_papers():
    """Search HuggingFace daily papers for relevant topics."""
    # HF daily papers endpoint
    data = fetch_json(f"{HF_API}/papers/daily", timeout=30)
    if not data:
        return []
    
    keywords = [
        "orchestration", "fusion", "ensemble", "routing", "multi-agent",
        "multi-model", "mcts", "tree search", "process reward", "prm",
        "self-consistency", "verification", "test-time", "speculative",
        "prompt optim", "model merge", "mixture of experts", "cascade",
        "judge", "aggregator", "debate", "consensus", "swarm",
        "reasoning", "chain-of-thought", "self-refine", "best-of-n",
    ]
    
    papers = []
    for paper in data:
        title = paper.get("title", "").lower()
        abstract = paper.get("paper", {}).get("abstract", "").lower() if isinstance(paper.get("paper"), dict) else ""
        text = title + " " + abstract
        if any(kw in text for kw in keywords):
            papers.append({
                "paper_id": paper.get("paper", {}).get("id", "") if isinstance(paper.get("paper"), dict) else paper.get("id", ""),
                "title": paper.get("title", ""),
                "abstract": paper.get("paper", {}).get("abstract", "") if isinstance(paper.get("paper"), dict) else "",
                "upvotes": paper.get("paper", {}).get("upvotes", 0) if isinstance(paper.get("paper"), dict) else paper.get("upvotes", 0),
                "url": f"https://huggingface.co/papers/{paper.get('paper', {}).get('id', '')}" if isinstance(paper.get("paper"), dict) else "",
                "source": "huggingface",
            })
    return papers

def search_hf_models():
    """Search HuggingFace for trending models in reasoning/orchestration space."""
    searches = [
        ("reasoning", 10),
        ("orchestration", 10),
        ("verification", 10),
        ("math reasoning", 10),
    ]
    
    models = []
    for query, limit in searches:
        params = urllib.parse.urlencode({
            "search": query,
            "sort": "downloads",
            "direction": "-1",
            "limit": limit,
        })
        data = fetch_json(f"{HF_API}/models?{params}")
        if not data:
            continue
        for m in data:
            models.append({
                "model_id": m.get("modelId", ""),
                "downloads": m.get("downloads", 0),
                "likes": m.get("likes", 0),
                "tags": m.get("tags", []),
                "pipeline_tag": m.get("pipeline_tag", ""),
                "query": query,
                "source": "huggingface-models",
            })
    return models

def main():
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    
    papers = search_hf_papers()
    models = search_hf_models()
    
    out_file = os.path.join(OUT_DIR, f"huggingface_{ts}.json")
    with open(out_file, "w") as f:
        json.dump({
            "scout": "huggingface",
            "timestamp": ts,
            "total_papers": len(papers),
            "total_models": len(models),
            "papers": papers,
            "models": models,
        }, f, indent=2)
    
    print(f"Scout-HuggingFace: {len(papers)} papers, {len(models)} models -> {out_file}")

if __name__ == "__main__":
    main()