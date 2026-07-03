#!/usr/bin/env python3
"""
Auto-Integrator: Reads research findings, implements improvements into timuclaude.
This is the HANDS of the swarm. It reads what the scouts found, evaluates it
against the current codebase, writes patches, tests them, and commits.

This script is called by the cron job with no_agent=False (LLM-powered).
The LLM reads findings and makes actual code changes.
"""
import json
import os
import glob
from datetime import datetime, timezone
from dedup import filter_new, get_seen_count

TIMUCLAUDE_DIR = os.path.expanduser("~/timuclaude")
RESEARCH_DIR = os.path.join(TIMUCLAUDE_DIR, "research")
FINDINGS_DIR = os.path.join(RESEARCH_DIR, "findings")
RAW_DIR = os.path.join(RESEARCH_DIR, "raw")
CHANGELOG = os.path.join(RESEARCH_DIR, "CHANGELOG.md")

def load_latest_findings():
    """Load the most recent distilled findings and raw findings."""
    findings = []
    
    # Load distilled findings
    for fpath in sorted(glob.glob(os.path.join(FINDINGS_DIR, "*.json")), reverse=True)[:3]:
        try:
            with open(fpath) as f:
                data = json.load(f)
                findings.extend(data.get("top_findings", data.get("all_findings", [])))
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load {fpath}: {e}")
    
    # Load raw web scout findings
    for fpath in sorted(glob.glob(os.path.join(RAW_DIR, "*.json")), reverse=True)[:5]:
        try:
            with open(fpath) as f:
                data = json.load(f)
                if data.get("scout") == "web-daily":
                    findings.extend(data.get("findings", []))
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load {fpath}: {e}")
    
    return findings

def load_deep_reports():
    """Load deep research reports (markdown files)."""
    reports = []
    for fpath in sorted(glob.glob(os.path.join(FINDINGS_DIR, "deep_research_*.md")), reverse=True)[:5]:
        try:
            with open(fpath) as f:
                reports.append({"file": fpath, "content": f.read()[:5000]})
        except IOError as e:
            print(f"Warning: Could not read {fpath}: {e}")
    return reports

def get_current_source():
    """Get a summary of current timuclaude source files."""
    src_dir = os.path.join(TIMUCLAUDE_DIR, "src")
    files = {}
    for fpath in sorted(glob.glob(os.path.join(src_dir, "*.py"))):
        try:
            with open(fpath) as f:
                content = f.read()
            files[os.path.basename(fpath)] = content[:2000]  # First 2000 chars
        except IOError as e:
            print(f"Warning: Could not read {fpath}: {e}")
    return files

def append_changelog(entry):
    """Append to the changelog."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(CHANGELOG, "a") as f:
        f.write(f"\n## {ts}\n{entry}\n")

# This script is run BY the LLM cron agent — it uses these functions
# to gather context, then the LLM decides what to implement and writes code.
if __name__ == "__main__":
    findings = load_latest_findings()
    reports = load_deep_reports()
    source = get_current_source()
    
    print(f"=== AUTO-INTEGRATOR CONTEXT ===")
    
    # Filter to only NEW findings not yet reviewed
    # Ensure all findings have an id field for dedup
    for f in findings:
        if "id" not in f or not f["id"]:
            f["id"] = f.get("url", f.get("title", f.get("name", f.get("model_id", ""))))
    
    findings_before = len(findings)
    findings = filter_new(findings, "integrator_reviewed", "id")
    findings_after = len(findings)
    already_reviewed = get_seen_count("integrator_reviewed")
    
    print(f"Findings: {findings_after} new (already reviewed {already_reviewed}, fetched {findings_before})")
    print(f"Deep reports: {len(reports)}")
    print(f"Source files: {len(source)}")
    print(f"Source files: {list(source.keys())}")
    
    # Output findings for the LLM to process
    if findings:
        print(f"\n=== TOP FINDINGS ===")
        for f in findings[:20]:
            title = f.get("title", f.get("name", f.get("model_id", "unknown")))
            score = f.get("relevance_score", f.get("relevance", "unknown"))
            print(f"  [score={score}] {title}")
    
    # The LLM cron agent will read this output and decide what to implement
    print(f"\n=== INSTRUCTIONS FOR LLM AGENT ===")
    print("1. Read the findings above and the deep research reports in findings/")
    print("2. Read the current source files in src/")
    print("3. Identify the TOP 1-3 improvements that can be implemented NOW")
    print("4. Write the code changes to the appropriate src/*.py files")
    print("5. Run tests: cd ~/timuclaude && python tests/test_orchestrator.py && python tests/test_phase2.py && python tests/test_phase3.py && python tests/test_phase4.py && python tests/test_phase5.py && python tests/test_phase5b.py")
    print("6. If ALL tests pass: git add -A && git commit -m 'auto-improve: <description>' && git push")
    print("7. If tests FAIL: revert changes, log failure in CHANGELOG.md, do NOT commit")
    print("8. Log what you did in ~/timuclaude/research/CHANGELOG.md")
    print("9. Update ~/timuclaude/research/TRACKER.md with new integration status")
    print("")
    print("RULES:")
    print("- Only implement Tier 1 techniques (low risk, high impact)")
    print("- NEVER break existing tests")
    print("- ALWAYS run tests before committing")
    print("- If unsure, log it as a recommendation instead of implementing")
    print("- Small, incremental changes only — one technique at a time")
    print("- Write clean, typed, documented code matching existing style")