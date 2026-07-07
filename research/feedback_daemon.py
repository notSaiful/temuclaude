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
            "daemon_roi": {},
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

        # Daemon ROI — track which daemons are producing value
        metrics["daemon_roi"] = self._compute_daemon_roi()

        return metrics

    def _compute_daemon_roi(self) -> dict:
        """Compute ROI for each daemon based on log activity and output."""
        roi = {}
        state_dir = Path("/tmp/temuclaude_daemons")

        # Count outputs per daemon from shared intelligence events
        try:
            sys.path.insert(0, str(TEMUCLAUDE / "research"))
            import share_intelligence as si
            events = si.get_events(limit=200)
        except Exception:
            events = []

        daemon_events = {}
        for evt in events:
            d = evt.get("daemon", "unknown")
            daemon_events[d] = daemon_events.get(d, 0) + 1

        # Count log lines per daemon (activity proxy)
        for daemon_name in [
            "scout_daemon", "distiller_daemon", "research_daemon_1",
            "research_daemon_2", "research_daemon_3", "integrator_daemon",
            "coordinator_daemon", "cyber_daemon", "efficiency_daemon",
            "media_daemon", "marketing_daemon", "feedback_daemon",
            "meta_auditor_daemon", "swot_daemon", "website_daemon",
            "industry_radar_daemon", "model_optimizer_daemon",
            "cost_efficiency_daemon", "revenue_daemon", "growth_daemon",
            "competitive_dominance_daemon", "self_expansion_daemon",
            "super_intelligence_daemon",
        ]:
            log_file = state_dir / f"{daemon_name}.log"
            log_lines = 0
            error_count = 0
            if log_file.exists():
                try:
                    content = log_file.read_text()
                    lines = content.strip().split("\n")
                    log_lines = len(lines)
                    error_count = sum(1 for l in lines if "ERROR" in l or "Exception" in l)
                except Exception:
                    pass

            events_count = daemon_events.get(daemon_name, 0)

            # ROI classification: HIGH (producing value), MEDIUM (active), LOW (idle/broken)
            if log_lines == 0 and events_count == 0:
                roi_class = "IDLE"
            elif error_count > 10:
                roi_class = "BROKEN"
            elif events_count > 5 or log_lines > 100:
                roi_class = "HIGH"
            elif events_count > 0 or log_lines > 20:
                roi_class = "MEDIUM"
            else:
                roi_class = "LOW"

            roi[daemon_name] = {
                "log_lines": log_lines,
                "errors": error_count,
                "events_broadcast": events_count,
                "roi_class": roi_class,
            }

        return roi

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
        # Log ROI summary
        roi = metrics.get("daemon_roi", {})
        if roi:
            high = sum(1 for v in roi.values() if v["roi_class"] == "HIGH")
            medium = sum(1 for v in roi.values() if v["roi_class"] == "MEDIUM")
            low = sum(1 for v in roi.values() if v["roi_class"] in ("LOW", "IDLE"))
            broken = sum(1 for v in roi.values() if v["roi_class"] == "BROKEN")
            self.logger.info(
                f"Daemon ROI: {high} HIGH, {medium} MEDIUM, {low} LOW/IDLE, {broken} BROKEN"
            )
            # Warn about broken daemons
            for name, info in roi.items():
                if info["roi_class"] == "BROKEN":
                    self.logger.warning(f"Daemon {name} is BROKEN: {info['errors']} errors in log")
                elif info["roi_class"] == "IDLE":
                    self.logger.warning(f"Daemon {name} is IDLE: 0 log lines, 0 events")
        if adjustments.get("recommendations"):
            for rec in adjustments["recommendations"]:
                self.logger.warning(f"Recommendation: {rec}")


def main():
    daemon = FeedbackDaemon()
    daemon.run(interval=3600)  # 1 hour


if __name__ == "__main__":
    main()
