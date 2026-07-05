#!/usr/bin/env python3
"""
Scout Daemon - Continuous paper/repo/model discovery.
Runs forever, cycling through arXiv, GitHub, HuggingFace.
"""

import json
import time
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add research dir to path
sys.path.insert(0, "/Users/saiful/temuclaude/research")
sys.path.insert(0, "/Users/saiful/temuclaude/research/scripts")

from daemon_base import DaemonBase
from queue import push_raw_file

RAW_DIR = Path("/Users/saiful/temuclaude/research/raw")
RAW_DIR.mkdir(exist_ok=True)

# Import scout modules directly (they're now on sys.path)
import scout_arxiv
import scout_github
import scout_huggingface


class ScoutDaemon(DaemonBase):
    """Continuous discovery daemon."""
    
    def __init__(self):
        super().__init__("scout_daemon")
        self.sources = [
            ("arxiv", scout_arxiv),
            ("github", scout_github),
            ("huggingface", scout_huggingface),
        ]
        self.cycle = 0
    
    def run_once(self) -> bool:
        """Run one complete scout cycle."""
        self.cycle += 1
        self.logger.info(f"=== Scout cycle {self.cycle} started ===")
        
        for name, module in self.sources:
            try:
                self.logger.info(f"Running {name} scout...")
                start = time.time()
                
                # Call the scout's main function - it writes to raw/
                module.main()
                
                # Find the latest raw file for this scout
                raw_files = sorted(RAW_DIR.glob(f"{name}_*.json"), reverse=True)
                if raw_files:
                    latest = raw_files[0]
                    push_raw_file(str(latest))
                    self.logger.info(f"{name}: wrote {latest.name}, pushed to queue")
                
                elapsed = time.time() - start
                self.logger.info(f"{name} completed in {elapsed:.1f}s")
                
            except Exception as e:
                self.logger.exception(f"{name} scout failed: {e}")
        
        self.logger.info(f"=== Scout cycle {self.cycle} complete ===")
        return True  # Continue running


def main():
    daemon = ScoutDaemon()
    # Run every 6 hours = 21600 seconds
    daemon.run(interval=21600)


if __name__ == "__main__":
    main()