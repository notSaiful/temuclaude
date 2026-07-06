#!/usr/bin/env python3
"""
Competitive Dominance Daemon — active market beating.
Benchmarks vs competitors, publishes public scoreboard.
"""

import json, time, os, sys
from pathlib import Path

sys.path.insert(0, os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"))
sys.path.insert(0, os.path.join(os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"), "scripts"))

from daemon_base import DaemonBase
from model_benchmarker import benchmark_model
from unlimited_memory import remember

TEMUCLAUDE = Path(os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude"))
SCOREBOARD_FILE = TEMUCLAUDE / "website" / "content" / "benchmarks.md"

COMPETITORS = ["openai/gpt-oss-120b", "deepseek/deepseek-chat", "meta/llama-3.3-70b-instruct"]

class CompetitiveDominanceDaemon(DaemonBase):
    def __init__(self):
        super().__init__("competitive_dominance_daemon")

    def run_once(self) -> bool:
        our_result = benchmark_model("openai/gpt-oss-120b:free")
        competitor_results = {}
        for comp in COMPETITORS[:2]:
            r = benchmark_model(comp)
            competitor_results[comp] = {"pass_rate": r.get("pass_rate", 0)}
        self._publish_scoreboard(our_result, competitor_results)
        remember("competitive", "competitive_dominance_daemon",
                 "Benchmarked vs competitors", {"our": our_result, "competitors": competitor_results}, importance=9)
        return True

    def _publish_scoreboard(self, our, competitors):
        SCOREBOARD_FILE.parent.mkdir(parents=True, exist_ok=True)
        md = f"# Temuclaude vs The World\n\n| Model | Pass Rate |\n|-------|-----------|\n"
        md += f"| **Temuclaude** | **{our.get('pass_rate', 0)*100:.0f}%** |\n"
        for comp, r in competitors.items():
            md += f"| {comp} | {r.get('pass_rate', 0)*100:.0f}% |\n"
        SCOREBOARD_FILE.write_text(md)
        self.logger.info("Public scoreboard updated")

def main():
    daemon = CompetitiveDominanceDaemon()
    daemon.run(interval=14400)

if __name__ == "__main__":
    main()
