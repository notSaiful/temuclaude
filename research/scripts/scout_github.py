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
    try:
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Timuclaude-Research/1.0",
        })
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
    all_repos = []
    seen_ids = set()
    for q in QUERIES:
        repos = search_github(q, per_page=8)
        for r in repos:
            if r["repo_id"] not in seen_ids:
                all_repos.append(r)
                seen_ids.add(r["repo_id"])
    
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    out_file = os.path.join(OUT_DIR, f"github_{ts}.json")
    with open(out_file, "w") as f:
        json.dump({
            "scout": "github",
            "timestamp": ts,
            "queries": QUERIES,
            "total_found": len(all_repos),
            "repos": all_repos,
        }, f, indent=2)
    
    print(f"Scout-GitHub: Found {len(all_repos)} repos -> {out_file}")

if __name__ == "__main__":
    main()