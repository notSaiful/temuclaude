#!/usr/bin/env python3
"""
Distiller: Process raw scout findings, evaluate relevance, extract actionables.
Reads all raw/*.json files, deduplicates, scores, and outputs distilled findings.
"""
import json
import os
import glob
from datetime import datetime, timezone
from collections import defaultdict
from dedup import filter_new

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "raw")
FINDINGS_DIR = os.path.join(os.path.dirname(__file__), "..", "findings")
os.makedirs(FINDINGS_DIR, exist_ok=True)

# Scoring keywords — higher weight = more relevant to timuclaude
HIGH_VALUE_KEYWORDS = {
    # Orchestration core
    "orchestration": 10, "fusion": 10, "panel": 8, "judge": 8, "aggregator": 10,
    "routing": 9, "cascade": 8, "ensemble": 9, "multi-model": 10,
    "mixture of agents": 10, "moa": 8, "layered aggregation": 9,
    # Reasoning
    "mcts": 9, "tree search": 9, "process reward": 9, "prm": 9,
    "self-consistency": 10, "chain-of-thought": 7, "self-refine": 8,
    "test-time compute": 9, "best-of-n": 8, "verification": 8,
    "step-by-step": 6, "reasoning": 6, "tree of thoughts": 9,
    "graph of thoughts": 8, "reflection": 8,
    # Multi-agent
    "multi-agent": 9, "debate": 8, "consensus": 8, "swarm": 8,
    "collaborative": 6, "voting": 7, "society of minds": 9,
    # Cost/efficiency
    "cost-efficient": 8, "cost reduction": 8, "speculative decoding": 7,
    "early exit": 7, "caching": 6, "flat rate": 7, "50x": 8,
    # Prompt optimization
    "opro": 9, "prompt optim": 9, "evolutionary prompt": 9,
    "meta-prompt": 8, "gepa": 10, "prompt-of-thought": 8,
    "dspy": 9, "miprov2": 9, "compiled prompt": 8, "mipro": 8,
    # Model combination
    "model merge": 8, "mixture of experts": 7, "moe": 7,
    "weight interpolation": 7, "task arithmetic": 7, "ties merging": 7,
    # Benchmarks
    "mmlu": 7, "hle": 8, "gdpval": 9, "scicode": 9, "mrcr": 7,
    "benchmark": 5, "frontier": 6, "swe-bench": 8, "gpqa": 7,
    "arena-hard": 6, "alpacaeval": 6, "math benchmark": 7,
    "humaneval": 6, "livecodebench": 6, "agentbench": 6,
    # Verification
    "code execution": 8, "ground truth": 8, "hallucination": 6,
    "self-evaluation": 7, "quality gate": 8, "z3": 7, "smt solver": 7,
    # Breakthroughs
    "breakthrough": 9, "state-of-the-art": 7, "sota": 7,
    "novel": 6, "outperform": 7, "surpass": 7, "beat": 6,
    # Agent architecture
    "react": 6, "planning agent": 8, "tool-use": 7, "agentic": 7,
    "agent framework": 7, "skill extraction": 9, "voyager": 9,
    "self-improving": 9, "meta-learning": 7, "continual learning": 7,
    "experience replay": 7, "memory augmented": 7,
    # Coding agents
    "claude code": 8, "codex": 7, "kilo": 6, "aider": 6,
    "coding agent": 7, "code generation": 6,
    # Open weight models
    "open weight": 7, "open source model": 7, "ollama": 6,
    "llama": 5, "deepseek": 6, "qwen": 5, "mistral": 5,
    "gemma": 5, "phi-4": 6, "hermes": 7, "kimi": 6,
    "nemotron": 6, "minimax": 5, "gpt-oss": 6,
}

def score_relevance(text):
    text_lower = text.lower()
    score = 0
    matched = []
    for kw, weight in HIGH_VALUE_KEYWORDS.items():
        if kw in text_lower:
            score += weight
            matched.append(kw)
    return score, matched

def load_raw_findings():
    """Load all raw JSON files."""
    all_findings = []
    for fpath in sorted(glob.glob(os.path.join(RAW_DIR, "*.json"))):
        try:
            with open(fpath) as f:
                data = json.load(f)
            all_findings.append(data)
        except Exception as e:
            print(f"Error loading {fpath}: {e}")
    return all_findings

def process_arxiv(raw):
    papers = raw.get("papers", [])
    results = []
    for p in papers:
        text = p.get("title", "") + " " + p.get("abstract", "")
        score, matched = score_relevance(text)
        if score < 10:  # Skip irrelevant
            continue
        results.append({
            "type": "arxiv_paper",
            "id": p.get("arxiv_id", ""),
            "title": p.get("title", ""),
            "abstract": p.get("abstract", "")[:500],
            "authors": p.get("authors", []),
            "published": p.get("published", ""),
            "relevance_score": score,
            "matched_keywords": matched,
            "url": p.get("arxiv_id", ""),
        })
    return results

def process_github(raw):
    repos = raw.get("repos", [])
    results = []
    for r in repos:
        text = r.get("name", "") + " " + r.get("description", "") + " " + " ".join(r.get("topics", []))
        score, matched = score_relevance(text)
        if score < 8:
            continue
        results.append({
            "type": "github_repo",
            "id": str(r.get("repo_id", "")),
            "name": r.get("name", ""),
            "url": r.get("url", ""),
            "description": r.get("description", ""),
            "stars": r.get("stars", 0),
            "language": r.get("language", ""),
            "updated_at": r.get("updated_at", ""),
            "relevance_score": score,
            "matched_keywords": matched,
        })
    return results

def process_huggingface(raw):
    results = []
    papers = raw.get("papers", [])
    for p in papers:
        text = p.get("title", "") + " " + p.get("abstract", "")
        score, matched = score_relevance(text)
        if score < 10:
            continue
        results.append({
            "type": "hf_paper",
            "id": p.get("paper_id", ""),
            "title": p.get("title", ""),
            "abstract": p.get("abstract", "")[:500],
            "upvotes": p.get("upvotes", 0),
            "url": p.get("url", ""),
            "relevance_score": score,
            "matched_keywords": matched,
        })
    
    models = raw.get("models", [])
    for m in models:
        text = m.get("model_id", "") + " " + " ".join(m.get("tags", []))
        score, matched = score_relevance(text)
        if score < 8:
            continue
        results.append({
            "type": "hf_model",
            "id": m.get("model_id", ""),
            "downloads": m.get("downloads", 0),
            "likes": m.get("likes", 0),
            "tags": m.get("tags", []),
            "pipeline_tag": m.get("pipeline_tag", ""),
            "relevance_score": score,
            "matched_keywords": matched,
        })
    return results

def process_marketing_research(raw):
    """Process marketing research findings."""
    results = []
    findings = raw.get("findings", [])
    for f in findings:
        if not isinstance(f, dict):
            continue
        text = f.get("title", "") + " " + f.get("description", "") + " " + f.get("implementation_notes", "")
        # Marketing findings are always relevant — don't score with technical keywords
        # Instead, include all with a base score + priority boost
        score = 5  # Base score
        priority = f.get("priority", "medium")
        if priority == "high":
            score += 5
        elif priority == "medium":
            score += 3
        if f.get("actionable_for_timuclaude", False):
            score += 3
        
        results.append({
            "type": "marketing_finding",
            "id": f.get("url", f.get("title", "")),
            "category": f.get("category", ""),
            "title": f.get("title", ""),
            "description": f.get("description", ""),
            "url": f.get("url", ""),
            "actionable_for_timuclaude": f.get("actionable_for_timuclaude", False),
            "implementation_notes": f.get("implementation_notes", ""),
            "priority": priority,
            "relevance_score": score,
            "matched_keywords": ["marketing"],
        })
    return results

def process_hermes_improvement(raw):
    """Process Hermes self-improvement + skill discovery findings."""
    results = []
    findings = raw.get("findings", [])
    for f in findings:
        if not isinstance(f, dict):
            continue
        text = f.get("title", "") + " " + f.get("description", "") + " " + f.get("implementation_notes", "") + " " + f.get("skill_name", "")
        score, matched = score_relevance(text)
        # Lower threshold — Hermes improvements are always relevant
        if score < 5:
            # Still include if it's a skill or hermes feature
            if f.get("category") in ("skill", "hermes-feature", "mcp", "best-practice"):
                score = max(score, 8)
                matched.append("hermes-improvement")
            else:
                continue
        results.append({
            "type": "hermes_improvement",
            "id": f.get("title", f.get("skill_name", "")),
            "category": f.get("category", ""),
            "title": f.get("title", ""),
            "description": f.get("description", ""),
            "applicable_to": f.get("applicable_to", ""),
            "implementation_notes": f.get("implementation_notes", ""),
            "skill_name": f.get("skill_name", ""),
            "url": f.get("url", ""),
            "relevance_score": score,
            "matched_keywords": matched,
        })
    return results

def process_frontier_docs(raw):
    """Process frontier model docs research findings."""
    results = []
    findings = raw.get("findings", [])
    for f in findings:
        if not isinstance(f, dict):
            continue
        text = f.get("model", "") + " " + f.get("technique", "") + " " + f.get("description", "") + " " + f.get("integration_notes", "")
        score, matched = score_relevance(text)
        if score < 8:
            continue
        results.append({
            "type": "frontier_doc",
            "id": f.get("source_url", f.get("model", "")),
            "model": f.get("model", ""),
            "technique": f.get("technique", ""),
            "description": f.get("description", ""),
            "benchmark": f.get("benchmark", ""),
            "integrable": f.get("integrable", False),
            "integration_notes": f.get("integration_notes", ""),
            "source_url": f.get("source_url", ""),
            "relevance_score": score,
            "matched_keywords": matched,
        })
    return results

def process_web_daily(raw):
    """Process web-daily scout findings."""
    results = []
    findings = raw.get("findings", [])
    for f in findings:
        if not isinstance(f, dict):
            continue
        text = f.get("title", "") + " " + f.get("description", "") + " " + f.get("integration_notes", "")
        score, matched = score_relevance(text)
        if score < 8:
            continue
        results.append({
            "type": "web_finding",
            "id": f.get("url", f.get("title", "")),
            "title": f.get("title", ""),
            "description": f.get("description", ""),
            "url": f.get("url", ""),
            "relevance": f.get("relevance", "unknown"),
            "category": f.get("category", ""),
            "integrable": f.get("integrable", False),
            "integration_notes": f.get("integration_notes", ""),
            "source_type": f.get("source_type", ""),
            "relevance_score": score,
            "matched_keywords": matched,
        })
    return results

def deduplicate(findings):
    """Deduplicate by type+id."""
    seen = set()
    unique = []
    for f in findings:
        key = f"{f['type']}:{f['id']}"
        if key not in seen:
            seen.add(key)
            unique.append(f)
    return unique

def main():
    raw_files = load_raw_findings()
    all_findings = []
    
    for raw in raw_files:
        scout = raw.get("scout", "")
        if scout == "arxiv":
            all_findings.extend(process_arxiv(raw))
        elif scout == "github":
            all_findings.extend(process_github(raw))
        elif scout == "huggingface":
            all_findings.extend(process_huggingface(raw))
        elif scout == "web-daily":
            all_findings.extend(process_web_daily(raw))
        elif scout == "frontier-docs":
            all_findings.extend(process_frontier_docs(raw))
        elif scout == "hermes-improvement":
            all_findings.extend(process_hermes_improvement(raw))
        elif scout == "marketing-research":
            all_findings.extend(process_marketing_research(raw))
    
    # In-run deduplicate
    all_findings = deduplicate(all_findings)
    
    # Add composite type:id for cross-run dedup
    for f in all_findings:
        f["dedup_key"] = f"{f['type']}:{f['id']}"
    
    # Cross-run dedup: only keep findings not yet distilled
    before_distill = len(all_findings)
    all_findings = filter_new(all_findings, "distilled_findings", "dedup_key")
    after_distill = len(all_findings)
    
    # Sort by relevance score (descending)
    all_findings.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    # Group by type
    by_type = defaultdict(list)
    for f in all_findings:
        by_type[f["type"]].append(f)
    
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    out_file = os.path.join(FINDINGS_DIR, f"distilled_{ts}.json")
    with open(out_file, "w") as f:
        json.dump({
            "distilled_at": ts,
            "total_raw_files": len(raw_files),
            "total_findings": len(all_findings),
            "new_findings": after_distill,
            "already_distilled": before_distill - after_distill,
            "by_type": {k: len(v) for k, v in by_type.items()},
            "top_findings": all_findings[:50],  # Top 50
            "all_findings": all_findings,
        }, f, indent=2)
    
    # Clean up raw files older than 7 days (keep web-daily and frontier-docs for auto-integrator)
    import time
    now = time.time()
    for fpath in glob.glob(os.path.join(RAW_DIR, "*.json")):
        basename = os.path.basename(fpath)
        # Skip LLM-generated findings — auto-integrator needs them
        if "web-daily" in basename or "web_daily" in basename:
            continue
        if "frontier" in basename:
            continue
        if "hermes" in basename:
            continue
        if "meta-skill" in basename:
            continue
        if "marketing" in basename:
            continue
        if basename.startswith("_"):
            continue  # Don't delete _seen_state.json
        if os.path.getmtime(fpath) < now - 7 * 86400:
            os.remove(fpath)
    
    print(f"Distiller: {after_distill} new findings ({before_distill - after_distill} already distilled) from {len(raw_files)} raw files -> {out_file}")
    if all_findings:
        top = all_findings[0]
        print(f"  Top finding (score {top['relevance_score']}): {top.get('title', top.get('name', ''))}")

if __name__ == "__main__":
    main()