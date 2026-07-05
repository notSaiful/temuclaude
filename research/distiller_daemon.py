#!/usr/bin/env python3
"""
Distiller Daemon - Continuous processing of raw findings.
Watches raw/ directory, processes new files immediately.
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
from queue import pop_raw_file, push_findings, push_raw_file

RAW_DIR = Path("/Users/saiful/temuclaude/research/raw")
FINDINGS_DIR = Path("/Users/saiful/temuclaude/research/findings")
FINDINGS_DIR.mkdir(exist_ok=True)

# Load distiller - it's now on sys.path
import distiller


class DistillerDaemon(DaemonBase):
    """Continuous distiller daemon - watches for new raw files."""
    
    def __init__(self):
        super().__init__("distiller_daemon")
        self.processed = set()
        self._load_processed()
    
    def _load_processed(self):
        """Load already processed files from state."""
        state_file = Path("/tmp/temuclaude_daemons/distiller_processed.json")
        if state_file.exists():
            try:
                with open(state_file) as f:
                    self.processed = set(json.load(f))
            except Exception:
                pass
    
    def _save_processed(self):
        """Save processed files to state."""
        state_file = Path("/tmp/temuclaude_daemons/distiller_processed.json")
        with open(state_file, 'w') as f:
            json.dump(list(self.processed), f)
    
    def run_once(self) -> bool:
        """Process any new raw files from queue."""
        # Check queue for new raw files
        raw_file = pop_raw_file()
        if raw_file:
            if raw_file in self.processed:
                self.logger.info(f"Already processed: {raw_file}")
                return True
            
            self.logger.info(f"Processing raw file: {raw_file}")
            try:
                # Run distiller on this specific file
                # The distiller module reads ALL raw files and processes new ones
                distiller.main()
                
                # Find new distilled files
                distilled_files = sorted(FINDINGS_DIR.glob("distilled_*.json"), reverse=True)
                if distilled_files:
                    latest = distilled_files[0]
                    push_findings([str(latest)])
                    self.logger.info(f"Distilled: {latest.name}, pushed to research queue")
                
                self.processed.add(raw_file)
                self._save_processed()
                
            except Exception as e:
                self.logger.exception(f"Distiller failed on {raw_file}: {e}")
        else:
            # Also check raw dir directly for any files not in queue
            for raw_path in RAW_DIR.glob("*.json"):
                if str(raw_path) not in self.processed and not raw_path.name.startswith("_"):
                    push_raw_file(str(raw_path))
        
        return True


def main():
    daemon = DistillerDaemon()
    # Poll every 30 seconds
    daemon.run(interval=30)


if __name__ == "__main__":
    main()