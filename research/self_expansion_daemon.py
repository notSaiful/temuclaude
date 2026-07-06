#!/usr/bin/env python3
"""
Self-Expansion Daemon — the system grows its own workforce.
Creates new daemons when gaps are identified.
"""

import json, time, os, sys
from pathlib import Path

sys.path.insert(0, os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"))
sys.path.insert(0, os.path.join(os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"), "scripts"))

from daemon_base import DaemonBase
from shared_memory import read_all_states, get_recent_events
from unlimited_memory import remember

class SelfExpansionDaemon(DaemonBase):
    def __init__(self):
        super().__init__("self_expansion_daemon")

    def run_once(self) -> bool:
        states = read_all_states()
        current = set(states.get("daemons", {}).keys())
        swot_events = get_recent_events(limit=20, event_type="swot")
        for event in swot_events:
            weaknesses = event.get("extra", {}).get("weaknesses", [])
            for w in weaknesses:
                area = w.get("area", "")
                if area and not any(area in d for d in current):
                    try:
                        from daemon_generator import generate_daemon
                        daemon_name = f"{area}_daemon"
                        filepath = generate_daemon(daemon_name, w.get("action", area), area)
                        self.logger.info(f"Created new daemon: {filepath}")
                        remember("expansion", "self_expansion_daemon",
                                 f"Created {daemon_name}", {"daemon": daemon_name, "file": filepath})
                    except Exception as e:
                        self.logger.exception(f"Failed to create daemon: {e}")
        return True

def main():
    daemon = SelfExpansionDaemon()
    daemon.run(interval=43200)  # 12 hours

if __name__ == "__main__":
    main()
