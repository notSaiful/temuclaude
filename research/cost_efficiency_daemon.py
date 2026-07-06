#!/usr/bin/env python3
"""
Cost Efficiency Daemon — financial intelligence for the swarm.
Runs every hour. Monitors credits, computes ROI, throttles spending.
"""

import json, time, os, sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"))
sys.path.insert(0, os.path.join(os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"), "scripts"))

from daemon_base import DaemonBase
from usage_tracker import fetch_credits, get_burn_rate, should_throttle
from roi_calculator import compute_roi

TEMUCLAUDE = Path(os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude"))
COST_ADJUSTMENTS_FILE = TEMUCLAUDE / "research" / "cost_adjustments.json"
THROTTLE_FILE = TEMUCLAUDE / "research" / "throttle_state.json"
REPORT_DIR = TEMUCLAUDE / "research" / "cost_reports"
REPORT_DIR.mkdir(exist_ok=True)

class CostEfficiencyDaemon(DaemonBase):
    def __init__(self):
        super().__init__("cost_efficiency_daemon")

    def run_once(self) -> bool:
        self.logger.info("=== Cost Efficiency cycle started ===")
        throttle = should_throttle()
        credits = fetch_credits()
        burn = get_burn_rate()
        remaining = throttle.get("remaining_credits", 0)
        daily_burn = burn.get("per_day", 0)
        self.logger.info(f"Credits: ${remaining:.2f}, Burn: ${daily_burn:.2f}/day")

        level = self._determine_level(remaining, daily_burn)
        self.logger.info(f"Throttle level: {level}")
        self._apply_throttle(level, throttle)
        roi = compute_roi()
        self._generate_adjustments(roi, level)
        self._save_report(credits, burn, roi, level, throttle)
        return True

    def _determine_level(self, remaining, daily_burn):
        if remaining < 1.0: return "red"
        if remaining < 5.0: return "orange"
        if daily_burn > 2.0: return "yellow"
        return "green"

    def _apply_throttle(self, level, throttle):
        state = {"level": level, "timestamp": datetime.now(timezone.utc).isoformat(),
                 "reason": throttle.get("reason", ""), "actions": []}
        if level == "green": state["actions"] = ["all_active"]
        elif level == "yellow": state["actions"] = ["reduce_research_to_2", "prefer_free_models"]
        elif level == "orange": state["actions"] = ["reduce_research_to_1", "free_models_only", "throttle_marketing"]
        elif level == "red": state["actions"] = ["pause_research", "pause_marketing", "keep_critical_only"]
        with open(THROTTLE_FILE, 'w') as f:
            json.dump(state, f, indent=2)

    def _generate_adjustments(self, roi, level):
        adjustments = {"throttle_level": level, "priority_multipliers": {}, "model_preferences": []}
        if level in ("yellow", "orange", "red"):
            adjustments["model_preferences"] = [":free", "ollama/"]
        if level == "red":
            for d in ["marketing_daemon", "industry_radar_daemon", "swot_daemon", "website_daemon",
                      "research_daemon_1", "research_daemon_2", "research_daemon_3"]:
                adjustments["priority_multipliers"][d] = 0.0
        with open(COST_ADJUSTMENTS_FILE, 'w') as f:
            json.dump(adjustments, f, indent=2)

    def _save_report(self, credits, burn, roi, level, throttle):
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        report = {"timestamp": datetime.now(timezone.utc).isoformat(), "level": level,
                  "credits": credits, "burn": burn, "roi": roi}
        with open(REPORT_DIR / f"cost_{ts}.json", 'w') as f:
            json.dump(report, f, indent=2)
        old = sorted(REPORT_DIR.glob("cost_*.json"), reverse=True)[168:]
        for o in old: o.unlink()

def main():
    daemon = CostEfficiencyDaemon()
    daemon.run(interval=3600)

if __name__ == "__main__":
    main()
