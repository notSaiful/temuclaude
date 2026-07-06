#!/usr/bin/env python3
"""
Super Intelligence Daemon — makes the system actively smarter.
Evolves prompts, optimizes fusion, experiments with reasoning.
"""

import json, time, os, sys
from pathlib import Path

sys.path.insert(0, os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"))
sys.path.insert(0, os.path.join(os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"), "scripts"))

from daemon_base import DaemonBase
from prompt_evolver import evolve_prompt
from unlimited_memory import remember, recall

class SuperIntelligenceDaemon(DaemonBase):
    def __init__(self):
        super().__init__("super_intelligence_daemon")

    def run_once(self) -> bool:
        current = recall_one("orchestration_prompt", "prompt")
        base_prompt = "You are a helpful AI assistant."
        if current:
            base_prompt = current.get("content", {}).get("prompt", base_prompt)
        try:
            result = evolve_prompt(base_prompt, "orchestration", generations=2)
            if result["score"] > 0.5:
                remember("prompt", "super_intelligence_daemon",
                         f"Evolved prompt to {result['score']*100:.0f}%", result, importance=9)
                self.logger.info(f"Prompt evolved: {result['score']*100:.0f}%")
        except Exception as e:
            self.logger.exception(f"Evolution failed: {e}")
        return True

def main():
    daemon = SuperIntelligenceDaemon()
    daemon.run(interval=21600)  # 6 hours

if __name__ == "__main__":
    main()
