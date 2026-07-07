#!/usr/bin/env python3
"""
Revenue Daemon — tracks income, optimizes pricing, routes profits to Ummah fund.
"""

import json, time, os, sys
from pathlib import Path

sys.path.insert(0, os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"))
sys.path.insert(0, os.path.join(os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"), "scripts"))

from daemon_base import DaemonBase
from pricing_engine import get_tier_pricing
from ummah_fund import compute_fund_allocation, update_fund_ledger, get_fund_summary
from unlimited_memory import remember

class RevenueDaemon(DaemonBase):
    def __init__(self):
        super().__init__("revenue_daemon")

    def run_once(self) -> bool:
        revenue = self._compute_revenue()
        costs = self._compute_costs()
        pricing = get_tier_pricing()
        allocation = compute_fund_allocation(revenue, costs)
        if allocation.get("fund_total", 0) > 0:
            update_fund_ledger(allocation)
            self.logger.info(f"Ummah fund: ${allocation['fund_total']:.2f} allocated")
        remember("revenue", "revenue_daemon",
                 f"Revenue: ${revenue:.2f}, Ummah: ${allocation.get('fund_total', 0):.2f}",
                 {"revenue": revenue, "costs": costs, **allocation})
        fund = get_fund_summary()
        self.logger.info(f"Total Ummah distributed: ${fund['total_distributed']:.2f}")
        return True

    def _compute_revenue(self):
        return 0.0  # Integrate with billing when available

    def _compute_costs(self):
        try:
            from usage_tracker import compute_summary
            return compute_summary().get("total_spent", 0)
        except Exception:
            return 0.0

def main():
    daemon = RevenueDaemon()
    daemon.run(interval=3600)

if __name__ == "__main__":
    main()
