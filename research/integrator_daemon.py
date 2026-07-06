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
        """Implement a finding in STAGING ONLY. Never touch the main codebase.
        All code changes go to /staging/. Ggs reviews and deploys manually."""
        max_attempts = 2
        
        STAGING_DIR = TEMUCLAUDE_DIR / "staging"
        STAGING_DIR.mkdir(parents=True, exist_ok=True)
        
        for attempt in range(max_attempts):
            try:
                with open(finding_file) as f:
                    content = f.read()
                
                self.logger.info(f"Attempt {attempt+1}/{max_attempts}: {Path(finding_file).name}")
                
                # Copy the finding to staging for reference
                staging_finding = STAGING_DIR / Path(finding_file).name
                with open(staging_finding, 'w') as f:
                    f.write(content)
                
                # Run auto-integrator in STAGING directory only
                # Create a staging copy of src if it doesn't exist
                staging_src = STAGING_DIR / "src"
                if not staging_src.exists():
                    subprocess.run(["cp", "-r", str(SRC_DIR), str(staging_src)], timeout=30)
                
                result = subprocess.run([
                    sys.executable,
                    "/Users/saiful/temuclaude/research/scripts/auto_integrator.py"
                ], capture_output=True, text=True, timeout=1200, cwd=str(STAGING_DIR))  # Run in staging
                
                self.logger.info(f"Auto-integrator output (in staging): {result.stdout[:500]}")
                
                if result.returncode != 0:
                    self.logger.error(f"Auto-integrator stderr: {result.stderr[:1000]}")
                    if attempt < max_attempts - 1:
                        self.logger.info("Retrying in 30s...")
                        time.sleep(30)
                        continue
                    return False
                
                # Check if any changes were made IN STAGING (not main codebase)
                git_status = subprocess.run(
                    ["git", "status", "--porcelain"],
                    capture_output=True, text=True, cwd=str(STAGING_DIR)
                )
                
                if not git_status.stdout.strip():
                    self.logger.info("No changes made by integrator in staging")
                    return True  # Not a failure, just nothing to do
                
                self.logger.info(f"Changes made in staging: {git_status.stdout[:200]}")
                
                # Commit in STAGING only — never touch main codebase
                subprocess.run(["git", "add", "-A"], cwd=str(STAGING_DIR))
                commit_msg = f"staging: {Path(finding_file).stem}"
                subprocess.run(["git", "commit", "-m", commit_msg], cwd=str(STAGING_DIR))
                # Do NOT push — Ggs reviews staging and deploys manually
                
                self._log_changelog(f"STAGED (not deployed): {finding_file} - waiting for Ggs approval")
                self._update_tracker(finding_file, "staged")
                
                self.logger.info(f"Finding staged in /staging/. Awaiting Ggs approval for deployment.")
                
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