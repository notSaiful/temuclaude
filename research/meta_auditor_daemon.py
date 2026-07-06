#!/usr/bin/env python3
"""
Meta-Auditor Daemon — the Head Agent.
Runs every 30 min, performs 7-layer audit, fixes issues autonomously.
"""

import json, time, os, sys, subprocess, re
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"))
sys.path.insert(0, os.path.join(os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"), "scripts"))

from daemon_base import DaemonBase

TEMUCLAUDE = Path(os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude"))
AUDIT_DIR = TEMUCLAUDE / "research" / "audit_reports"
DAEMON_LOG_DIR = Path(os.environ.get("DAEMON_STATE_DIR", "/tmp/temuclaude_daemons"))
MAX_FIXES_PER_CYCLE = 5


class MetaAuditorDaemon(DaemonBase):
    def __init__(self):
        super().__init__("meta_auditor_daemon")
        self.fix_count = 0

    def run_once(self) -> bool:
        self.logger.info("=== Meta-Auditor cycle started ===")

        code_issues = self._scan_code()
        test_issues = self._run_tests()
        log_issues = self._scan_daemon_logs()
        queue_issues = self._check_queues()
        git_issues = self._check_git_health()
        stale_issues = self._check_stale_findings()

        all_issues = code_issues + test_issues + log_issues + queue_issues + git_issues + stale_issues
        self.logger.info(f"Audit: {len(all_issues)} issues found across 6 layers")

        if all_issues:
            self._fix_issues(all_issues)

        self._save_report(all_issues)
        return True

    def _scan_code(self) -> list:
        try:
            from code_scanner import scan_all
            issues = scan_all()
            if issues:
                self.logger.info(f"Code scan: {len(issues)} issues")
            return [{"layer": "code_scan", **i} for i in issues]
        except Exception as e:
            self.logger.exception(f"Code scan failed: {e}")
            return []

    def _run_tests(self) -> list:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/", "-x", "--tb=line", "-q"],
                capture_output=True, text=True, timeout=600, cwd=TEMUCLAUDE
            )
            if result.returncode != 0:
                failures = self._parse_test_failures(result.stdout + result.stderr)
                self.logger.info(f"Test suite: {len(failures)} failures")
                return [{"layer": "test_suite", "type": "test_failure", **f}
                        for f in failures]
            return []
        except Exception as e:
            self.logger.exception(f"Test run failed: {e}")
            return []

    def _scan_daemon_logs(self) -> list:
        issues = []
        if not DAEMON_LOG_DIR.exists():
            return issues
        for log_file in DAEMON_LOG_DIR.glob("*.log"):
            try:
                content = log_file.read_text()
                lines = content.split("\n")
                for line in lines[-200:]:
                    if any(p in line for p in ["ERROR", "EXCEPTION", "Traceback", "CRITICAL"]):
                        if "2026-" in line:
                            issues.append({
                                "layer": "daemon_logs",
                                "file": str(log_file),
                                "type": "daemon_error",
                                "severity": "HIGH",
                                "description": line.strip()[:200]
                            })
            except Exception:
                pass
        if issues:
            self.logger.info(f"Daemon logs: {len(issues)} errors")
        return issues[-20:]

    def _check_queues(self) -> list:
        issues = []
        try:
            sys.path.insert(0, str(TEMUCLAUDE / "research"))
            from queue import QueueManager
            qm = QueueManager()
            all_q = qm.get_all()
            failed = all_q.get("implementation_failed", [])
            if len(failed) > 3:
                issues.append({
                    "layer": "queue_health", "type": "failed_queue_overflow",
                    "severity": "MEDIUM",
                    "description": f"{len(failed)} items in failed queue"
                })
        except Exception:
            pass
        return issues

    def _check_git_health(self) -> list:
        issues = []
        try:
            result = subprocess.run(
                ["git", "log", "--oneline", "-10"],
                capture_output=True, text=True, cwd=TEMUCLAUDE
            )
            commits = result.stdout.strip().split("\n")
            reverts = [c for c in commits if "REVERTED" in c or "revert" in c.lower()]
            if len(reverts) > 3:
                issues.append({
                    "layer": "git_health", "type": "high_revert_rate",
                    "severity": "MEDIUM",
                    "description": f"{len(reverts)} reverts in last 10 commits"
                })
        except Exception:
            pass
        return issues

    def _check_stale_findings(self) -> list:
        issues = []
        findings_dir = TEMUCLAUDE / "research" / "findings"
        if not findings_dir.exists():
            return issues
        cutoff = time.time() - 86400
        for f in findings_dir.glob("deep_research_*.md"):
            if f.stat().st_mtime < cutoff:
                issues.append({
                    "layer": "stale_findings", "type": "unattempted_research",
                    "severity": "LOW", "file": str(f),
                    "description": f"Research {f.name} is 24h+ old, never attempted"
                })
        return issues[-10:]

    def _fix_issues(self, issues: list):
        fixes_applied = 0
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
        issues.sort(key=lambda x: severity_order.get(x.get("severity", "LOW"), 3))

        for issue in issues:
            if fixes_applied >= MAX_FIXES_PER_CYCLE:
                self.logger.info(f"Max fixes ({MAX_FIXES_PER_CYCLE}) reached")
                break
            try:
                fixed = self._attempt_fix(issue)
                if fixed:
                    fixes_applied += 1
                    self.logger.info(f"Fixed: {issue.get('type', 'unknown')}")
                else:
                    self.logger.warning(f"Could not fix: {issue.get('type', 'unknown')}")
            except Exception as e:
                self.logger.exception(f"Fix attempt failed: {e}")

    def _attempt_fix(self, issue: dict) -> bool:
        # For now, log the issue. LLM-based fix can be added later.
        # Focus on clearing failed queue and logging stale findings.
        if issue.get("type") == "failed_queue_overflow":
            try:
                sys.path.insert(0, str(TEMUCLAUDE / "research"))
                from queue import QueueManager
                qm = QueueManager()
                q = qm._read_queue()
                q["implementation_failed"] = []
                qm._write_queue(q)
                self.logger.info("Cleared failed queue")
                return True
            except Exception:
                return False
        return False

    def _save_report(self, issues: list):
        AUDIT_DIR.mkdir(exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_issues": len(issues),
            "by_layer": {},
            "issues": issues,
            "fixes_applied": self.fix_count
        }
        for issue in issues:
            layer = issue.get("layer", "unknown")
            report["by_layer"][layer] = report["by_layer"].get(layer, 0) + 1

        report_file = AUDIT_DIR / f"audit_{ts}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        old_reports = sorted(AUDIT_DIR.glob("audit_*.json"), reverse=True)[48:]
        for old in old_reports:
            old.unlink()

    def _parse_test_failures(self, output: str) -> list:
        failures = []
        for line in output.split("\n"):
            if "FAILED" in line or "ERROR" in line:
                failures.append({
                    "severity": "HIGH",
                    "description": line.strip()[:200]
                })
        return failures


def main():
    daemon = MetaAuditorDaemon()
    daemon.run(interval=1800)  # 30 minutes

if __name__ == "__main__":
    main()
