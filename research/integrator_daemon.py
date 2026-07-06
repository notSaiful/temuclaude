#!/usr/bin/env python3
"""
Auto-Integrator Daemon - Continuous implementation of research findings.
Reads findings, writes code, runs tests, commits on success.
"""

import json
import time
import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime, timezone

# Add research dir to path
sys.path.insert(0, "/Users/saiful/temuclaude/research")
sys.path.insert(0, "/Users/saiful/temuclaude/research/scripts")

from daemon_base import DaemonBase
from queue import pop_implementation, mark_implementation_complete

TEMUCLAUDE_DIR = Path("/Users/saiful/temuclaude")
SRC_DIR = TEMUCLAUDE_DIR / "src"
TESTS_DIR = TEMUCLAUDE_DIR / "tests"
FINDINGS_DIR = TEMUCLAUDE_DIR / "research" / "findings"
CHANGELOG = TEMUCLAUDE_DIR / "research" / "CHANGELOG.md"
TRACKER = TEMUCLAUDE_DIR / "research" / "TRACKER.md"


class IntegratorDaemon(DaemonBase):
    """Continuous auto-integrator daemon."""
    
    def __init__(self):
        super().__init__("integrator_daemon")
        self.implemented = set()
        self._load_state()
    
    def _load_state(self):
        state_file = Path("/tmp/temuclaude_daemons/integrator_state.json")
        if state_file.exists():
            try:
                with open(state_file) as f:
                    data = json.load(f)
                    self.implemented = set(data.get("implemented", []))
            except Exception:
                pass
    
    def _save_state(self):
        state_file = Path("/tmp/temuclaude_daemons/integrator_state.json")
        with open(state_file, 'w') as f:
            json.dump({"implemented": list(self.implemented)}, f)
    
    def run_once(self) -> bool:
        """Process one implementation task."""
        task_file = pop_implementation()
        if not task_file:
            return True
        
        if task_file in self.implemented:
            self.logger.info(f"Already implemented: {task_file}")
            mark_implementation_complete(task_file, True)
            return True
        
        self.logger.info(f"Implementing: {task_file}")
        
        try:
            success = self._implement_finding(task_file)
            mark_implementation_complete(task_file, success)
            
            if success:
                self.implemented.add(task_file)
                self._save_state()
                self.logger.info(f"Successfully implemented: {task_file}")
            else:
                self.logger.warning(f"Implementation failed: {task_file}")
                
        except Exception as e:
            self.logger.exception(f"Integrator error on {task_file}: {e}")
            mark_implementation_complete(task_file, False)
        
        return True
    
    def _implement_finding(self, finding_file: str) -> bool:
        """Implement a finding with retry. Returns True on success."""
        max_attempts = 2
        
        for attempt in range(max_attempts):
            try:
                with open(finding_file) as f:
                    content = f.read()
                
                self.logger.info(f"Attempt {attempt+1}/{max_attempts}: {Path(finding_file).name}")
                
                result = subprocess.run([
                    sys.executable,
                    "/Users/saiful/temuclaude/research/scripts/auto_integrator.py"
                ], capture_output=True, text=True, timeout=1200, cwd=TEMUCLAUDE_DIR)  # 20 min
                
                self.logger.info(f"Auto-integrator output: {result.stdout[:500]}")
                
                if result.returncode != 0:
                    self.logger.error(f"Auto-integrator stderr: {result.stderr[:1000]}")
                    if attempt < max_attempts - 1:
                        self.logger.info("Retrying in 30s...")
                        time.sleep(30)
                        continue
                    return False
                
                # Check if any changes were made
                git_status = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True, text=True, cwd=TEMUCLAUDE_DIR
                )
                
                if not git_status.stdout.strip():
                    self.logger.info("No changes made by integrator")
                    return True  # Not a failure, just nothing to do
                
                # Run tests
                self.logger.info("Running tests...")
                test_result = subprocess.run([
                    sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-x"
                ], capture_output=True, text=True, timeout=600, cwd=TEMUCLAUDE_DIR)  # 10 min
                
                self.logger.info(f"Tests: {test_result.stdout[-1000:]}")
                
                if test_result.returncode != 0:
                    self.logger.error(f"Tests failed:\n{test_result.stdout[-2000:]}")
                    self.logger.error(f"Test stderr:\n{test_result.stderr[-1000:]}")
                    subprocess.run(["git", "checkout", "."], cwd=TEMUCLAUDE_DIR)
                    self._log_changelog(f"REVERTED: {finding_file} - Tests failed (attempt {attempt+1})")
                    if attempt < max_attempts - 1:
                        self.logger.info("Retrying in 30s...")
                        time.sleep(30)
                        continue
                    return False
                
                # Benchmark regression guard — verify quality didn't drop
                self.logger.info("Running benchmark regression guard...")
                bench_result = subprocess.run(
                    [sys.executable, "/Users/saiful/temuclaude/research/scripts/benchmark_guard.py"],
                    capture_output=True, text=True, timeout=600, cwd=TEMUCLAUDE_DIR
                )
                if bench_result.returncode != 0:
                    self.logger.error(f"Benchmark regression — reverting. {bench_result.stdout[:300]}")
                    subprocess.run(["git", "checkout", "."], cwd=TEMUCLAUDE_DIR)
                    self._log_changelog(f"REVERTED: {finding_file} - Benchmark regression (attempt {attempt+1})")
                    if attempt < max_attempts - 1:
                        time.sleep(30)
                        continue
                    return False
                self.logger.info("Benchmark guard passed — no regression")
                
                # Commit and push
                subprocess.run(["git", "add", "-A"], cwd=TEMUCLAUDE_DIR)
                commit_msg = f"auto-improve: {Path(finding_file).stem}"
                subprocess.run(["git", "commit", "-m", commit_msg], cwd=TEMUCLAUDE_DIR)
                subprocess.run(["git", "push"], cwd=TEMUCLAUDE_DIR)
                
                self._log_changelog(f"IMPLEMENTED: {finding_file} - {commit_msg}")
                self._update_tracker(finding_file, "implemented")
                
                return True
                
            except subprocess.TimeoutExpired:
                self.logger.error(f"Implementation timed out (attempt {attempt+1})")
                if attempt < max_attempts - 1:
                    self.logger.info("Retrying in 60s...")
                    time.sleep(60)
                    continue
                return False
            except Exception as e:
                self.logger.exception(f"Implementation error: {e}")
                return False
        
        return False
    
    def _log_changelog(self, entry: str):
        """Append to CHANGELOG.md"""
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        with open(CHANGELOG, "a") as f:
            f.write(f"\n## {ts}\n{entry}\n")
    
    def _update_tracker(self, finding_file: str, status: str):
        """Update TRACKER.md with integration status"""
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        entry = f"\n- [{ts}] {Path(finding_file).name}: {status}\n"
        with open(TRACKER, "a") as f:
            f.write(entry)


def main():
    daemon = IntegratorDaemon()
    # Check every 2 minutes
    daemon.run(interval=120)


if __name__ == "__main__":
    main()