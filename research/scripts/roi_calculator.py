#!/usr/bin/env python3
"""ROI Calculator — measures return on investment for each token spent."""

import json, os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from usage_tracker import load_ledger, compute_summary

TEMUCLAUDE = Path(os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude"))
ROI_FILE = TEMUCLAUDE / "research" / "roi_report.json"
CHANGELOG = TEMUCLAUDE / "research" / "CHANGELOG.md"
FINDINGS_DIR = TEMUCLAUDE / "research" / "findings"

def count_outcomes():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    outcomes = {"research_reports": 0, "implementations_success": 0, "implementations_failed": 0,
                "bugs_fixed": 0, "model_swaps": 0}
    if FINDINGS_DIR.exists():
        outcomes["research_reports"] = len([f for f in FINDINGS_DIR.glob("deep_research_*.md") if f.stat().st_mtime > cutoff.timestamp()])
    if CHANGELOG.exists():
        for line in CHANGELOG.read_text().split("\n"):
            if "IMPLEMENTED:" in line: outcomes["implementations_success"] += 1
            elif "REVERTED:" in line: outcomes["implementations_failed"] += 1
            if "fix:" in line.lower(): outcomes["bugs_fixed"] += 1
            if "model pool upgrade" in line.lower(): outcomes["model_swaps"] += 1
    return outcomes

def compute_roi():
    summary = compute_summary()
    outcomes = count_outcomes()
    total = summary.get("total_spent", 0)
    roi = {"timestamp": datetime.now(timezone.utc).isoformat(), "total_spent_24h": total,
           "outcomes": outcomes, "cost_per_metric": {}, "daemon_roi": {}, "recommendations": []}
    if outcomes["research_reports"] > 0:
        roi["cost_per_metric"]["research_report"] = total / outcomes["research_reports"]
    if outcomes["implementations_success"] > 0:
        roi["cost_per_metric"]["implementation"] = total / outcomes["implementations_success"]
    for daemon, stats in summary.get("by_daemon", {}).items():
        count = stats.get("count", 0)
        cost = stats.get("cost", 0)
        roi["daemon_roi"][daemon] = {"cost_24h": cost, "count": count}
    with open(ROI_FILE, 'w') as f:
        json.dump(roi, f, indent=2)
    return roi

if __name__ == "__main__":
    print(json.dumps(compute_roi(), indent=2))
