#!/usr/bin/env python3
"""
Website Daemon — auto-updates website with latest project state.
Runs every 2 hours. Deploys to Vercel only when something changed.
"""

import json, time, os, sys, subprocess
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"))
sys.path.insert(0, os.path.join(os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"), "scripts"))

from daemon_base import DaemonBase

class WebsiteDaemon(DaemonBase):
    def __init__(self):
        super().__init__("website_daemon")
        self.last_deploy_hash = None

    def run_once(self) -> bool:
        self.logger.info("=== Website update cycle started ===")
        try:
            from website_updater import (
                get_current_features, get_test_count, get_git_stats,
                get_model_pool, update_db_file, update_landing_page, deploy_to_vercel
            )
            features = get_current_features()
            tests = get_test_count()
            git_stats = get_git_stats()
            models = get_model_pool()
            db = update_db_file(features, tests, git_stats, models)
            landing_changed = update_landing_page(db)

            current_hash = hash(f"{db.get('feature_count', 0)}_{db.get('model_count', 0)}_{landing_changed}_{db.get('git_stats', {}).get('total_commits', 0)}")
            if current_hash == self.last_deploy_hash:
                self.logger.info("No changes detected — skipping deploy")
                return True

            self.logger.info(f"Changes detected ({len(features)} features, {len(models)} models) — deploying...")
            success = deploy_to_vercel()
            if success:
                self.last_deploy_hash = current_hash
                self.logger.info("Deployed successfully")
            else:
                self.logger.error("Deploy failed")
        except Exception as e:
            self.logger.exception(f"Website update failed: {e}")
        return True

def main():
    daemon = WebsiteDaemon()
    daemon.run(interval=7200)  # 2 hours

if __name__ == "__main__":
    main()
