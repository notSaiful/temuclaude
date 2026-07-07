#!/usr/bin/env python3
"""
Breakthrough Extractor — reads deep research reports and extracts
the most important findings in plain English for the Hasan UI.

Outputs: research/breakthroughs.json (consumed by sync_daemon → Vercel API)
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime

RESEARCH_DIR = Path(os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"))
FINDINGS_DIR = RESEARCH_DIR / "findings"
OUTPUT_FILE = RESEARCH_DIR / "breakthroughs.json"

# Category mapping from filename patterns
CATEGORY_MAP = {
    "orchestration": ("Orchestration", "#3b82f6"),
    "efficiency": ("Efficiency", "#10b981"),
    "routellm": ("Efficiency", "#10b981"),
    "reasoning": ("Reasoning", "#8b5cf6"),
    "agent": ("Prompt Optimization", "#f59e0b"),
    "media": ("Media", "#ec4899"),
    "cyber": ("Security", "#ef4444"),
    "cybersecurity": ("Security", "#ef4444"),
    "management": ("Strategy", "#06b6d4"),
    "mgmt": ("Strategy", "#06b6d4"),
    "planning": ("Strategy", "#06b6d4"),
}


def extract_breakthroughs():
    """Parse all deep research reports and extract breakthrough findings."""
    breakthroughs = []

    for f in sorted(FINDINGS_DIR.glob("deep_research_*.md"), reverse=True):
        content = f.read_text()
        lines = content.split("\n")
        if len(lines) < 20:
            continue

        # Extract category from filename
        fname = f.stem.lower()
        category = "General"
        cat_color = "#8b5cf6"
        for key, (cat, color) in CATEGORY_MAP.items():
            if key in fname:
                category = cat
                cat_color = color
                break

        # Extract title
        title = lines[0].replace("#", "").replace("Deep Research:", "").replace("Comprehensive Research Report:", "").strip()
        if not title:
            title = f.stem.replace("_", " ").replace("deep research", "").strip()

        # Extract executive summary
        summary = ""
        in_summary = False
        for line in lines:
            if "Executive Summary" in line:
                in_summary = True
                continue
            if in_summary and line.strip() and not line.startswith("#") and not line.startswith("**") and not line.startswith("---"):
                summary = line.strip()
                break
        if not summary:
            # Grab first substantial paragraph
            for line in lines[2:15]:
                if line.strip() and not line.startswith("#") and not line.startswith("**") and not line.startswith("---") and len(line.strip()) > 50:
                    summary = line.strip()
                    break

        # Extract key findings (### sections with substantive content)
        findings = []
        current_heading = ""
        current_content = ""
        for line in lines:
            if line.startswith("### "):
                if current_heading and current_content:
                    findings.append({
                        "name": current_heading.replace("###", "").strip(),
                        "detail": current_content.strip()[:200],
                    })
                current_heading = line
                current_content = ""
            elif current_heading and line.strip() and not line.startswith("#"):
                current_content += " " + line.strip()
        # Don't forget the last one
        if current_heading and current_content:
            findings.append({
                "name": current_heading.replace("###", "").strip(),
                "detail": current_content.strip()[:200],
            })

        # Filter to only findings with real substance (mentions papers, benchmarks, or integration)
        key_findings = []
        for fnd in findings:
            name = fnd["name"]
            detail = fnd["detail"]
            # Must have substance — not just a heading like "1.1 Why X Fails"
            if any(marker in detail.lower() for marker in ["arxiv", "benchmark", "%", "github", "paper", "result", "token", "cost", "speed", "quality", "model"]):
                # Clean up the name
                clean_name = re.sub(r"^\d+\.\d+\s+", "", name)
                clean_name = clean_name.split(" — ")[0].split(" - ")[0].split(": ")[0]
                if len(clean_name) > 5 and len(clean_name) < 80:
                    key_findings.append({
                        "name": clean_name,
                        "detail": detail[:200],
                    })

        # Limit to top 3 findings per report
        key_findings = key_findings[:3]

        # Extract impact (look for "Temuclaude integration" or "INTEGRATION")
        impact = ""
        for line in lines:
            if "Temuclaude integration" in line or "INTEGRATION:" in line or "Temuclaude," in line:
                impact = line.replace("Temuclaude integration:", "").replace("INTEGRATION:", "").replace("- **Temuclaude integration:**", "").replace("- **INTEGRATION:**", "").strip()
                if len(impact) > 10:
                    break
        if not impact and key_findings:
            impact = key_findings[0]["detail"][:150]

        # Extract source references
        sources = []
        for line in lines:
            if "arXiv:" in line:
                ids = re.findall(r'arXiv:(\d+\.\d+)', line)
                sources.extend(ids)
            if "github.com" in line:
                repos = re.findall(r'github\.com/[\w-]+/[\w-]+', line)
                sources.extend(repos)
        sources = list(set(sources))[:3]
        source_str = " · ".join(sources) if sources else "Research Swarm"

        mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d")

        breakthroughs.append({
            "title": title[:100],
            "category": category,
            "categoryColor": cat_color,
            "summary": summary[:300] if summary else "Research finding from Hasan's swarm.",
            "keyFindings": key_findings,
            "impact": impact[:200] if impact else "See full report for details.",
            "source": source_str,
            "date": mtime,
            "reportFile": f.name,
            "lines": len(lines),
        })

    # Deduplicate by title (keep first occurrence, which is newest due to sort)
    seen = set()
    unique = []
    for b in breakthroughs:
        # Normalize title for comparison
        key = b["title"].lower().strip()[:50]
        # Skip entries with no key findings and short summaries
        # Skip entries with no key findings — they're not breakthroughs, just queued stubs
        if not b["keyFindings"]:
            continue
        if key not in seen:
            seen.add(key)
            unique.append(b)
    breakthroughs = unique

    # Sort by date (newest first), then by size (bigger = more substantial)
    breakthroughs.sort(key=lambda x: (x["date"], x["lines"]), reverse=True)

    # Keep only top 12
    breakthroughs = breakthroughs[:12]

    output = {
        "breakthroughs": breakthroughs,
        "totalReports": len(list(FINDINGS_DIR.glob("deep_research_*.md"))),
        "lastUpdated": datetime.now().isoformat(),
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(output, indent=2, default=str))
    print(f"Extracted {len(breakthroughs)} breakthroughs from {output['totalReports']} reports → {OUTPUT_FILE}")
    return output


if __name__ == "__main__":
    extract_breakthroughs()