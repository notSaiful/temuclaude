#!/usr/bin/env python3
"""
Feedback Daemon — evaluates swarm performance every hour.
Metrics: implementation success rate, test count trend, research saturation.
Outputs: feedback_adjustments.json consumed by dynamic_priorities.py.
"""

import json, time, os, sys, subprocess
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"))

from daemon_base import DaemonBase

TEMUCLAUDE = Path(os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude"))
FEEDBACK_FILE = TEMUCLAUDE / "research" / "feedback_adjustments.json"
CHANGELOG = TEMUCLAUDE / "research" / "CHANGELOG.md"


class FeedbackDaemon(DaemonBase):
    def __init__(self):
        super().__init__("feedback_daemon")
        self.history = []

    def run_once(self) -> bool:
        metrics = self._collect_metrics()
        adjustments = self._compute_adjustments(metrics)
        self._save_adjustments(adjustments)
        self._log_summary(metrics, adjustments)
        return True

    def _collect_metrics(self) -> dict:
        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "implementations_success": 0,
            "implementations_failed": 0,
            "test_count": 0,
            "git_commits_24h": 0,
            "research_reports": 0,
        }

        # Count from CHANGELOG
        if CHANGELOG.exists():
            content = CHANGELOG.read_text()
            for line in content.split("\n"):
                if "IMPLEMENTED:" in line:
                    metrics["implementations_success"] += 1
                elif "REVERTED:" in line:
                    metrics["implementations_failed"] += 1

        # Test count
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "--co", "-q"],
                capture_output=True, text=True, timeout=30, cwd=TEMUCLAUDE
            )
            for line in result.stdout.split("\n"):
                if "collected" in line.lower():
                    import re
                    nums = re.findall(r'\d+', line)
                    if nums:
                        metrics["test_count"] = int(nums[0])
                    break
        except Exception:
            pass

        # Git commits in last 24h
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "--since=24 hours ago"],
                capture_output=True, text=True, timeout=10, cwd=TEMUCLAUDE
            )
            metrics["git_commits_24h"] = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0
        except Exception:
            pass

        # Research reports
        findings_dir = TEMUCLAUDE / "research" / "findings"
        if findings_dir.exists():
            metrics["research_reports"] = len(list(findings_dir.glob("deep_research_*.md")))

        return metrics

    def _compute_adjustments(self, metrics: dict) -> dict:
        total = metrics["implementations_success"] + metrics["implementations_failed"]
        success_rate = metrics["implementations_success"] / total if total > 0 else 0

        adjustments = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "success_rate": success_rate,
            "total_attempts": total,
            "priority_adjustments": [],
            "recommendations": [],
        }

        if total > 0 and success_rate < 0.5:
            adjustments["recommendations"].append(
                f"Implementation success rate is {success_rate*100:.0f}% — below 50%. Boost research on failing topics."
            )
            adjustments["priority_adjustments"].append({
                "topic": "implementation_quality",
                "boost": 30,
                "reason": "Low success rate",
            })

        if metrics["test_count"] > 0:
            adjustments["test_count"] = metrics["test_count"]

        if metrics["git_commits_24h"] == 0:
            adjustments["recommendations"].append("No commits in last 24h — check if integrator is working.")
            adjustments["priority_adjustments"].append({
                "topic": "integrator_health",
                "boost": 20,
                "reason": "No recent commits",
            })

        return adjustments

    def _save_adjustments(self, adjustments: dict):
        with open(FEEDBACK_FILE, 'w') as f:
            json.dump(adjustments, f, indent=2)

    def _log_summary(self, metrics: dict, adjustments: dict):
        self.logger.info(
            f"Metrics: {metrics['implementations_success']} success, "
            f"{metrics['implementations_failed']} failed, "
            f"{metrics['test_count']} tests, "
            f"{metrics['git_commits_24h']} commits/24h"
        )
        if adjustments.get("recommendations"):
            for rec in adjustments["recommendations"]:
                self.logger.warning(f"Recommendation: {rec}")


def main():
    daemon = FeedbackDaemon()
    daemon.run(interval=3600)  # 1 hour


if __name__ == "__main__":
    main()
