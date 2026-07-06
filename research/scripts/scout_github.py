#!/usr/bin/env python3
"""
Scout: GitHub Repository Search
Searches GitHub for new repos related to LLM orchestration, reasoning, multi-agent.
Outputs raw findings as JSON.
"""
import json
import urllib.request
import urllib.parse
import os
import ssl
import certifi
from datetime import datetime, timezone
from dedup import filter_new, get_seen_count

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "raw")
os.makedirs(OUT_DIR, exist_ok=True)

_ssl_ctx = ssl.create_default_context(cafile=certifi.where())

QUERIES = [
    "LLM orchestration fusion multi-model",
    "LLM ensemble routing aggregation",
    "MCTS tree search LLM reasoning",
    "process reward model LLM verification",
    "self-consistency LLM chain-of-thought",
    "multi-agent LLM debate swarm",
    "LLM benchmark evaluation frontier",
    "prompt optimization OPRO automatic",
    "LLM inference cost reduction routing",
    "model merging mixture experts inference",
    "LLM verifier self-check code execution",
    "test-time compute LLM scaling",
    "LLM skill extraction Voyager library",
    "self-improving LLM system automatic",
    "AI agent framework tool-use planning",
    "LLM speculative decoding draft verify",
    "DSPy prompt optimization compiled",
    "mixture of agents layered aggregation LLM",
    "coding agent architecture Claude Code",
    "Tree of Thoughts Graph of Thoughts reasoning",
    "LLM reflection self-refine iterative",
    "open weight model release 2025 2026",
    # === CYBERSECURITY (added 2026-07-06) ===
    "LLM jailbreak defense guardrail",
    "prompt injection defense AI safety",
    "cognitive firewall zero-trust LLM",
    "constitutional classifier safety guardrail",
    "self-healing injection defense retrain",
    "adversarial robustness LLM alignment",
    "backdoor attack detection model",
    "model supply chain poisoning security",
    "autonomous red team AI cybersecurity",
    "agentic AI security tool-use attack",
    "MCP protocol security vulnerability",
    "multi-agent cyber offense defense",
    "AI agent red teaming framework",
    "LLM vulnerability detection code scan",
    "self-healing code patch generation",
    "logic vulnerability detection repository",
    "exploit chain construction autonomous",
    "LLM runtime safety monitoring",
    "AI model integrity supply chain",
    "OWASP LLM top 10 agentic security",
    "MITRE ATLAS adversarial AI threat",
    # === EFFICIENCY (added 2026-07-06) ===
    "speculative decoding LLM inference speedup",
    "KV cache prefix caching LLM efficiency",
    "vLLM continuous batching PagedAttention",
    "MoE mixture experts efficient inference",
    "structured output constrained generation LLM",
    "LLM cascade routing cost reduction quality",
    "semantic caching LLM duplicate query",
    "model quantization AWQ lossless",
    "early exit adaptive computation LLM",
    "teacher student distillation LLM cost",
    "prompt caching API provider efficiency",
    "context compression lossless token reduction",
    "adaptive token budget LLM Pareto",
    "DFlash draft model speculative decoding",
    "model weight merging TIES task arithmetic",
    "EAGLE Medusa speculative decoding",
    "DSPy MIPROv2 prompt optimization efficiency",
    "LLM inference cost reduction production",
    "token reduction LLM no quality loss",
]

GITHUB_API = "https://api.github.com/search/repositories"

def search_github(query, sort="updated", per_page=10):
    params = urllib.parse.urlencode({
        "q": query,
        "sort": sort,
        "order": "desc",
        "per_page": per_page,
    })
    url = f"{GITHUB_API}?{params}"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Temuclaude-Research/1.0",
    }
    # Use GitHub token if available for higher rate limits (60/hour → 5000/hour)
    github_token = os.environ.get("GITHUB_TOKEN", "")
    if github_token:
        headers["Authorization"] = f"token {github_token}"
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30, context=_ssl_ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"ERROR fetching '{query}': {e}")
        return []

    repos = []
    for item in data.get("items", []):
        repos.append({
            "repo_id": item.get("id"),
            "name": item.get("full_name", ""),
            "url": item.get("html_url", ""),
            "description": item.get("description", "") or "",
            "stars": item.get("stargazers_count", 0),
            "language": item.get("language", ""),
            "updated_at": item.get("updated_at", ""),
            "topics": item.get("topics", []),
            "query": query,
            "source": "github",
        })
    return repos

def main():
    import time
    
    all_repos = []
    seen_ids = set()  # In-run dedup
    for q in QUERIES:
        repos = search_github(q, per_page=8)
        for r in repos:
            if r["repo_id"] not in seen_ids:
                all_repos.append(r)
                seen_ids.add(r["repo_id"])
        time.sleep(3)
    
    # Cross-run dedup: only keep repos we haven't seen before
    before = len(all_repos)
    all_repos = filter_new(all_repos, "github", "repo_id")
    after = len(all_repos)
    already_seen = get_seen_count("github")
    
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    out_file = os.path.join(OUT_DIR, f"github_{ts}.json")
    with open(out_file, "w") as f:
        json.dump({
            "scout": "github",
            "timestamp": ts,
            "queries": QUERIES,
            "total_found": len(all_repos),
            "total_fetched": before,
            "already_seen": already_seen,
            "new_findings": after,
            "repos": all_repos,
        }, f, indent=2)
    
    print(f"Scout-GitHub: Fetched {before}, {after} new (already seen {already_seen}) -> {out_file}")

if __name__ == "__main__":
    main()