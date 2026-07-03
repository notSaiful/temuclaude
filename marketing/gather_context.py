#!/usr/bin/env python3
"""
Timuclaude Context Gatherer — collects real project data for agent-generated tweets.
Run this before crafting a post. Outputs structured context the agent uses.

Usage:
  python gather_context.py
  python gather_context.py --json  (machine-readable output)
"""

import argparse
import json
import os
import subprocess
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_cmd(cmd, cwd=None):
    """Run a shell command and return output."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=10, cwd=cwd or PROJECT_ROOT
        )
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"


def get_git_activity():
    """Get recent git commits."""
    since = (datetime.now() - timedelta(hours=24)).strftime("%Y-%m-%d")
    output = run_cmd(f'git log --oneline --since="{since}" --no-merges 2>/dev/null')
    if not output or "fatal" in output.lower():
        return {"commits_24h": [], "count": 0}

    lines = output.split("\n")
    commits = []
    for line in lines[:10]:
        parts = line.split(" ", 1)
        if len(parts) == 2:
            commits.append({"hash": parts[0], "message": parts[1]})

    # Also get total commit count
    total = run_cmd("git rev-list --count HEAD 2>/dev/null")

    return {
        "commits_24h": commits,
        "count": len(commits),
        "total_commits": total if total.isdigit() else "unknown",
    }


def get_research_findings():
    """Check for new research findings."""
    research_dir = os.path.join(PROJECT_ROOT, "research", "raw")
    findings = []
    if os.path.exists(research_dir):
        for f in os.listdir(research_dir):
            if f.endswith(".json"):
                filepath = os.path.join(research_dir, f)
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                if mtime > datetime.now() - timedelta(hours=48):
                    findings.append({
                        "file": f,
                        "modified": mtime.isoformat(),
                        "age_hours": (datetime.now() - mtime).total_seconds() / 3600,
                    })

    # Check tracker
    tracker_path = os.path.join(PROJECT_ROOT, "research", "TRACKER.md")
    tracker_exists = os.path.exists(tracker_path)

    return {
        "new_findings_48h": findings,
        "count": len(findings),
        "tracker_exists": tracker_exists,
    }


def get_benchmark_results():
    """Check for new benchmark results."""
    results_dir = os.path.join(PROJECT_ROOT, "benchmarks", "results")
    results = []
    if os.path.exists(results_dir):
        for root, dirs, files in os.walk(results_dir):
            for f in files:
                if f.endswith(".json"):
                    filepath = os.path.join(root, f)
                    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    results.append({
                        "file": os.path.relpath(filepath, results_dir),
                        "modified": mtime.isoformat(),
                        "age_hours": (datetime.now() - mtime).total_seconds() / 3600,
                    })

    # Try to read the most recent result
    latest_summary = None
    if results:
        latest = sorted(results, key=lambda x: x["modified"])[-1]
        filepath = os.path.join(results_dir, latest["file"])
        try:
            with open(filepath) as fh:
                data = json.load(fh)
                latest_summary = {
                    "model": data.get("model_name", "unknown"),
                    "accuracy": f"{data.get('accuracy', 0):.1%}",
                    "correct": data.get("correct", 0),
                    "total": data.get("total_questions", 0),
                    "avg_latency_ms": data.get("avg_latency_ms", 0),
                }
        except Exception:
            pass

    return {
        "all_results": results,
        "count": len(results),
        "latest": latest_summary,
    }


def get_project_stats():
    """Get overall project statistics."""
    py_files = run_cmd("find src benchmarks tests -name '*.py' 2>/dev/null | wc -l")
    test_suites = run_cmd("ls tests/test_*.py 2>/dev/null | wc -l")

    # Check GitHub stars via git remote
    remote = run_cmd("git remote get-url origin 2>/dev/null")

    return {
        "python_files": int(py_files) if py_files.isdigit() else 0,
        "test_suites": int(test_suites) if test_suites.isdigit() else 0,
        "repo_url": remote,
    }


def get_github_stars():
    """Try to get GitHub star count via API."""
    # Extract owner/repo from git remote
    remote = run_cmd("git remote get-url origin 2>/dev/null")
    if "github.com" not in remote:
        return {"stars": None, "error": "not a github repo"}

    # Try to extract owner/repo
    import re
    match = re.search(r'github\.com[:/]([^/]+)/([^/\s.]+)', remote)
    if not match:
        return {"stars": None, "error": "could not parse repo"}

    owner, repo = match.group(1), match.group(2)
    output = run_cmd(f'curl -s "https://api.github.com/repos/{owner}/{repo}" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get(\'stargazers_count\',0))" 2>/dev/null')

    try:
        stars = int(output)
    except (ValueError, TypeError):
        stars = None

    return {"stars": stars, "repo": f"{owner}/{repo}"}


def get_recent_content_log():
    """Check what we've already posted to avoid repetition."""
    log_file = os.path.join(os.path.dirname(__file__), "posted_log.json")
    if os.path.exists(log_file):
        with open(log_file) as f:
            return json.load(f)
    return {"posted": [], "last_slot": {}}


def get_time_context():
    """Get current time context."""
    now = datetime.now()
    return {
        "datetime": now.isoformat(),
        "day_of_week": now.strftime("%A"),
        "time": now.strftime("%H:%M"),
        "timezone": "IST (India Standard Time)",
    }


def gather_all():
    """Gather all context."""
    return {
        "time": get_time_context(),
        "git": get_git_activity(),
        "research": get_research_findings(),
        "benchmarks": get_benchmark_results(),
        "project": get_project_stats(),
        "github": get_github_stars(),
        "posting_log": get_recent_content_log(),
    }


def print_human_readable(data):
    """Print context in human-readable format for the agent."""
    print("=" * 60)
    print("TIMUCLAUDE CONTEXT REPORT")
    print("=" * 60)

    print(f"\n📅 TIME: {data['time']['day_of_week']} {data['time']['time']} {data['time']['timezone']}")

    print(f"\n🔧 GIT ACTIVITY (last 24h):")
    git = data["git"]
    if git["count"] > 0:
        print(f"  {git['count']} commits in last 24h (total: {git['total_commits']})")
        for c in git["commits_24h"][:5]:
            print(f"    {c['hash'][:8]} {c['message'][:80]}")
    else:
        print(f"  No commits in last 24h (total: {git['total_commits']})")

    print(f"\n📊 BENCHMARKS:")
    bm = data["benchmarks"]
    print(f"  {bm['count']} result files total")
    if bm["latest"]:
        print(f"  Latest: {bm['latest']['model']} — {bm['latest']['accuracy']} accuracy ({bm['latest']['correct']}/{bm['latest']['total']}), {bm['latest']['avg_latency_ms']}ms avg")

    print(f"\n🔬 RESEARCH:")
    res = data["research"]
    if res["count"] > 0:
        print(f"  {res['count']} new findings in last 48h:")
        for f in res["new_findings_48h"]:
            print(f"    {f['file']} ({f['age_hours']:.0f}h ago)")
    else:
        print(f"  No new research findings in last 48h")

    print(f"\n📦 PROJECT:")
    proj = data["project"]
    print(f"  {proj['python_files']} Python files, {proj['test_suites']} test suites")
    print(f"  Repo: {proj['repo_url']}")

    print(f"\n⭐ GITHUB:")
    gh = data["github"]
    if gh["stars"] is not None:
        print(f"  {gh['stars']} stars on {gh['repo']}")
    else:
        print(f"  Could not fetch star count")

    print(f"\n📝 POSTING LOG:")
    log = data["posting_log"]
    print(f"  Already posted: {len(log.get('posted', []))} items")
    if log.get("last_slot"):
        for slot, time in log["last_slot"].items():
            print(f"    {slot}: last posted {time}")

    print(f"\n{'=' * 60}")
    print("Use this context to craft an authentic tweet.")
    print("Rules: no links, no corporate language, specific numbers, first person.")
    print(f"{'=' * 60}")


def main():
    parser = argparse.ArgumentParser(description="Gather context for Timuclaude posts")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    data = gather_all()

    if args.json:
        print(json.dumps(data, indent=2, default=str))
    else:
        print_human_readable(data)


if __name__ == "__main__":
    main()