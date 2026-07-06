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
import time
from datetime import datetime, timezone
from dedup import filter_new, get_seen_count

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "raw")
os.makedirs(OUT_DIR, exist_ok=True)

_ssl_ctx = ssl.create_default_context(cafile=certifi.where())

HF_API = "https://huggingface.co/api"

def fetch_json(url, timeout=30):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Temuclaude-Research/1.0",
            "Accept": "application/json",
        })
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"ERROR fetching {url}: {e}")
        return None

def search_hf_papers():
    """Search HuggingFace papers for relevant topics."""
    # Try multiple HF paper endpoints
    endpoints = [
        f"{HF_API}/papers",  # Recent papers
        f"https://huggingface.co/api/papers?limit=100",
    ]
    
    data = None
    for url in endpoints:
        data = fetch_json(url, timeout=30)
        if data:
            break
    
    if not data:
        return []
    
    # Handle both list and dict responses
    if isinstance(data, dict):
        papers_list = data.get("papers", data.get("items", []))
    elif isinstance(data, list):
        papers_list = data
    else:
        return []
    
    keywords = [
        "orchestration", "fusion", "ensemble", "routing", "multi-agent",
        "multi-model", "mcts", "tree search", "process reward", "prm",
        "self-consistency", "verification", "test-time", "speculative",
        "prompt optim", "model merge", "mixture of experts", "cascade",
        "judge", "aggregator", "debate", "consensus", "swarm",
        "reasoning", "chain-of-thought", "self-refine", "best-of-n",
        # === CYBERSECURITY (added 2026-07-06) ===
        "jailbreak", "prompt injection", "adversarial", "guardrail",
        "safety classifier", "constitutional", "cognitive firewall",
        "red team", "vulnerability detection", "backdoor", "model security",
        "supply chain", "agentic security", "MCP security", "alignment",
        "robustness", "safety monitoring", "input safety",
        # === EFFICIENCY (added 2026-07-06) ===
        "speculative decoding", "KV cache", "prefix caching", "vLLM",
        "PagedAttention", "continuous batching", "MoE", "mixture of experts",
        "semantic cache", "caching", "quantization", "AWQ", "GGUF",
        "early exit", "adaptive computation", "cascade routing",
        "cost reduction", "efficiency", "throughput", "speedup",
        "lossless", "Pareto", "token reduction", "context compression",
        "distillation", "model merging", "structured output",
        # === MEDIA GENERATION (added 2026-07-06) ===
        "text-to-image", "text-to-video", "diffusion model",
        "image generation", "video generation", "FLUX", "Sora",
        "Veo", "Runway", "Midjourney", "DALL-E", "Imagen",
        "Stable Diffusion", "controlnet", "instructpix2pix",
        "text-to-3d", "world model", "VBench", "ELO arena",
        "consistency model", "flow matching", "rectified flow",
        "multi-reference", "temporal consistency", "denoising",
    ]
    
    papers = []
    for paper in papers_list:
        if not isinstance(paper, dict):
            continue
        title = paper.get("title", "").lower()
        # Abstract might be nested
        abstract = ""
        if "abstract" in paper:
            abstract = paper.get("abstract", "").lower()
        elif "paper" in paper and isinstance(paper["paper"], dict):
            abstract = paper["paper"].get("abstract", "").lower()
        
        text = title + " " + abstract
        if any(kw in text for kw in keywords):
            paper_id = paper.get("id", paper.get("paper_id", ""))
            papers.append({
                "paper_id": paper_id,
                "title": paper.get("title", ""),
                "abstract": abstract[:500],
                "upvotes": paper.get("upvotes", paper.get("likes", 0)),
                "url": f"https://huggingface.co/papers/{paper_id}" if paper_id else "",
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
        # === CYBERSECURITY (added 2026-07-06) ===
        ("jailbreak defense", 10),
        ("prompt injection guardrail", 10),
        ("safety classifier", 10),
        ("adversarial robustness", 10),
        ("red team LLM", 10),
        ("vulnerability detection", 10),
        # === EFFICIENCY (added 2026-07-06) ===
        ("speculative decoding", 10),
        ("KV cache", 10),
        ("semantic cache", 10),
        ("model quantization AWQ", 10),
        ("efficient inference", 10),
        ("model merging", 10),
        # === MEDIA GENERATION (added 2026-07-06) ===
        ("text-to-image", 10),
        ("text-to-video", 10),
        ("FLUX 2", 10),
        ("diffusion model", 10),
        ("image generation", 10),
        ("video generation", 10),
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
        time.sleep(2)  # Rate limit between model searches
    return models

def main():
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    
    papers = search_hf_papers()
    time.sleep(2)
    models = search_hf_models()
    
    # Cross-run dedup
    papers_before = len(papers)
    papers = filter_new(papers, "hf_papers", "paper_id")
    papers_after = len(papers)
    papers_seen = get_seen_count("hf_papers")
    
    models_before = len(models)
    models = filter_new(models, "hf_models", "model_id")
    models_after = len(models)
    models_seen = get_seen_count("hf_models")
    
    out_file = os.path.join(OUT_DIR, f"huggingface_{ts}.json")
    with open(out_file, "w") as f:
        json.dump({
            "scout": "huggingface",
            "timestamp": ts,
            "total_papers": len(papers),
            "total_models": len(models),
            "papers_fetched": papers_before,
            "papers_new": papers_after,
            "papers_already_seen": papers_seen,
            "models_fetched": models_before,
            "models_new": models_after,
            "models_already_seen": models_seen,
            "papers": papers,
            "models": models,
        }, f, indent=2)
    
    print(f"Scout-HuggingFace: {papers_after} new papers (seen {papers_seen}), {models_after} new models (seen {models_seen}) -> {out_file}")

if __name__ == "__main__":
    main()