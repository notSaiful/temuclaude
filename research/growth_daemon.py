#!/usr/bin/env python3
"""
Growth Daemon — automated user acquisition at scale.
Generates SEO content, tracks referrals, monitors acquisition.
"""

import json, time, os, sys
from pathlib import Path

sys.path.insert(0, os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"))
sys.path.insert(0, os.path.join(os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"), "scripts"))

from daemon_base import DaemonBase
from unlimited_memory import remember

class GrowthDaemon(DaemonBase):
    def __init__(self):
        super().__init__("growth_daemon")
        self.pages_generated = 0

    def run_once(self) -> bool:
        try:
            from seo_content_generator import generate_all_content
            new_pages = generate_all_content()
            if new_pages:
                self.logger.info(f"Generated {len(new_pages)} new SEO pages")
                self.pages_generated += len(new_pages)
                remember("growth", "growth_daemon", f"Generated {len(new_pages)} SEO pages",
                         {"pages": new_pages, "total": self.pages_generated})
        except Exception as e:
            self.logger.exception(f"Growth failed: {e}")
        return True

def main():
    daemon = GrowthDaemon()
    daemon.run(interval=7200)

if __name__ == "__main__":
    main()
