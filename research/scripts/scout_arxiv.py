#!/usr/bin/env python3
"""
Scout: arXiv Paper Search
Searches arXiv for papers on LLM orchestration, reasoning, multi-agent systems.
Outputs raw findings as JSON for the Distiller to process.
"""
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import os
import ssl
import certifi

_ssl_ctx = ssl.create_default_context(cafile=certifi.where())

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "raw")
os.makedirs(OUT_DIR, exist_ok=True)

# Diverse queries for broad coverage
QUERIES = [
    # Orchestration & fusion
    "LLM orchestration multi-model fusion ensemble",
    "model panel judge aggregator routing",
    # Reasoning enhancements
    "tree search MCTS LLM reasoning step-by-step",
    "process reward model PRM verification",
    "self-consistency chain-of-thought majority vote",
    "test-time compute scaling reasoning",
    # Multi-agent
    "multi-agent LLM debate consensus collaboration",
    "LLM swarm intelligence collective",
    # Cost optimization
    "cost-efficient LLM inference routing cascade",
    "speculative decoding early exit LLM",
    # Prompt optimization
    "automated prompt optimization OPRO evolutionary",
    "prompt engineering meta-prompting",
    # Model combination
    "model merging mixture of experts inference",
    "ensemble LLM combination technique",
    # Verification
    "self-verification LLM hallucination reduction code execution",
    "LLM judge evaluator quality",
]

ARXIV_API = "http://export.arxiv.org/api/query"

def search_arxiv(query, max_results=10):
    params = urllib.parse.urlencode({
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    })
    url = f"{ARXIV_API}?{params}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Timuclaude-Research/1.0"})
        with urllib.request.urlopen(req, timeout=30, context=_ssl_ctx) as resp:
            xml_data = resp.read().decode("utf-8")
    except Exception as e:
        print(f"ERROR fetching '{query}': {e}")
        return []

    papers = []
    root = ET.fromstring(xml_data)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall("atom:entry", ns):
        title = entry.find("atom:title", ns)
        summary = entry.find("atom:summary", ns)
        published = entry.find("atom:published", ns)
        id_elem = entry.find("atom:id", ns)
        authors = [a.find("atom:name", ns).text for a in entry.findall("atom:author", ns) if a.find("atom:name", ns) is not None]
        
        papers.append({
            "arxiv_id": id_elem.text if id_elem is not None else "",
            "title": title.text.strip().replace("\n", " ") if title is not None else "",
            "abstract": summary.text.strip().replace("\n", " ") if summary is not None else "",
            "authors": authors,
            "published": published.text if published is not None else "",
            "query": query,
            "source": "arxiv",
        })
    return papers

def main():
    all_papers = []
    seen_ids = set()
    for q in QUERIES:
        papers = search_arxiv(q, max_results=8)
        for p in papers:
            if p["arxiv_id"] not in seen_ids:
                all_papers.append(p)
                seen_ids.add(p["arxiv_id"])
    
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    out_file = os.path.join(OUT_DIR, f"arxiv_{ts}.json")
    with open(out_file, "w") as f:
        json.dump({
            "scout": "arxiv",
            "timestamp": ts,
            "queries": QUERIES,
            "total_found": len(all_papers),
            "papers": all_papers,
        }, f, indent=2)
    
    print(f"Scout-arXiv: Found {len(all_papers)} papers → {out_file}")

if __name__ == "__main__":
    main()