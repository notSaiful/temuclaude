#!/usr/bin/env python3
"""
SWOT Daemon — strategic self-awareness.
Runs every 6 hours, conducts full SWOT analysis, creates improvement tasks.
"""

import json, time, os, sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"))
sys.path.insert(0, os.path.join(os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"), "scripts"))

from daemon_base import DaemonBase
from swot_comparator import run_swot

TEMUCLAUDE = Path(os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude"))
SWOT_DIR = TEMUCLAUDE / "research" / "swot_reports"
SWOT_DIR.mkdir(exist_ok=True)
BOOST_FILE = TEMUCLAUDE / "research" / "threat_boosts.json"


class SwotDaemon(DaemonBase):
    def __init__(self):
        super().__init__("swot_daemon")

    def run_once(self) -> bool:
        self.logger.info("=== SWOT analysis cycle started ===")
        fail_rate = self._get_fail_rate()
        swot = run_swot(fail_rate)

        self.logger.info(
            f"SWOT: {len(swot['strengths'])} strengths, "
            f"{len(swot['weaknesses'])} weaknesses, "
            f"{len(swot['opportunities'])} opportunities, "
            f"{len(swot['threats'])} threats"
        )

        tasks_created = self._weaknesses_to_tasks(swot["weaknesses"])
        self.logger.info(f"Created {tasks_created} research tasks from weaknesses")

        self._save_report(swot)
        self._apply_threat_boosts(swot["threats"])
        return True

    def _get_fail_rate(self) -> float:
        changelog = TEMUCLAUDE / "research" / "CHANGELOG.md"
        if not changelog.exists():
            return 0.0
        content = changelog.read_text()
        lines = content.split("\n")
        implemented = sum(1 for l in lines if "IMPLEMENTED:" in l)
        reverted = sum(1 for l in lines if "REVERTED:" in l)
        total = implemented + reverted
        return reverted / total if total > 0 else 0.0

    def _weaknesses_to_tasks(self, weaknesses: list) -> int:
        tasks = 0
        try:
            sys.path.insert(0, str(TEMUCLAUDE / "research"))
            from queue import QueueManager
            qm = QueueManager()
            for w in weaknesses:
                if w.get("severity") not in ("HIGH", "MEDIUM"):
                    continue
                ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
                task = json.dumps({
                    "id": f"swot_{ts}_{w.get('area', 'unknown')}",
                    "source": "swot_analysis",
                    "severity": w.get("severity"),
                    "action": w.get("action"),
                    "area": w.get("area"),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                qm.push("new_findings", [task])
                tasks += 1
        except Exception as e:
            self.logger.exception(f"Failed to create tasks: {e}")
        return tasks

    def _save_report(self, swot: dict):
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        report_file = SWOT_DIR / f"swot_{ts}.json"
        with open(report_file, 'w') as f:
            json.dump(swot, f, indent=2)

        summary_file = SWOT_DIR / "CURRENT_SWOT.md"
        with open(summary_file, 'w') as f:
            f.write(f"# Temuclaude SWOT Analysis\n")
            f.write(f"> Updated: {swot['timestamp']}\n")
            f.write(f"> Features: {swot['feature_count']}\n\n")
            f.write(f"## Strengths ({len(swot['strengths'])})\n")
            for s in swot["strengths"]:
                f.write(f"- {s}\n")
            f.write(f"\n## Weaknesses ({len(swot['weaknesses'])})\n")
            for w in swot["weaknesses"]:
                f.write(f"- [{w.get('severity', '?')}] {w.get('area', '?')}: {w.get('action', '?')}\n")
            f.write(f"\n## Opportunities ({len(swot['opportunities'])})\n")
            for o in swot["opportunities"]:
                f.write(f"- {o.get('opportunity', '?')}\n")
            f.write(f"\n## Threats ({len(swot['threats'])})\n")
            for t in swot["threats"]:
                f.write(f"- [{t.get('area', '?')}] {t.get('threat', '?')}\n")

        old = sorted(SWOT_DIR.glob("swot_*.json"), reverse=True)[28:]
        for o in old:
            o.unlink()

    def _apply_threat_boosts(self, threats: list):
        boosts = []
        for t in threats:
            area = t.get("area", "")
            if area == "competitive":
                boosts.append({"topic": "competitive_intelligence", "boost": 50})
            elif area == "technical":
                if "free model" in t.get("threat", "").lower():
                    boosts.append({"topic": "model_pool_resilience", "boost": 40})
                if "rate limit" in t.get("threat", "").lower():
                    boosts.append({"topic": "rate_limit_handling", "boost": 30})
        with open(BOOST_FILE, 'w') as f:
            json.dump(boosts, f, indent=2)


def main():
    daemon = SwotDaemon()
    daemon.run(interval=21600)  # 6 hours

if __name__ == "__main__":
    main()
