#!/usr/bin/env python3
"""
Ummah Fund — automatic profit routing to verified Muslim charities.
25% of profit goes here. Transparent, public ledger.
"""

import json, os
from pathlib import Path
from datetime import datetime, timezone

FUND_FILE = Path(os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude") + "/research/ummah_fund.json")

ALLOCATION = {
    "palestine_food_relief": 40,
    "muslim_community_kitchens": 20,
    "orphan_feeding": 15,
    "muslim_medical_clinics": 15,
    "islamic_schools": 10,
}
PROFIT_TO_UMMAH_PCT = 25

def compute_fund_allocation(revenue, costs):
    profit = revenue - costs
    fund_amount = profit * (PROFIT_TO_UMMAH_PCT / 100)
    if fund_amount <= 0:
        return {"profit": profit, "fund_total": 0, "allocations": {}, "note": "No profit yet"}
    allocations = {cause: fund_amount * (pct / 100) for cause, pct in ALLOCATION.items()}
    return {"revenue": revenue, "costs": costs, "profit": profit, "fund_total": fund_amount,
            "profit_to_ummah_pct": PROFIT_TO_UMMAH_PCT, "allocations": allocations,
            "timestamp": datetime.now(timezone.utc).isoformat()}

def update_fund_ledger(allocation):
    ledger = []
    if FUND_FILE.exists():
        ledger = json.loads(FUND_FILE.read_text())
    ledger.append(allocation)
    with open(FUND_FILE, 'w') as f:
        json.dump(ledger, f, indent=2)

def get_fund_summary():
    if not FUND_FILE.exists():
        return {"total_distributed": 0, "entries": 0}
    ledger = json.loads(FUND_FILE.read_text())
    total = sum(e.get("fund_total", 0) for e in ledger)
    return {"total_distributed": total, "entries": len(ledger),
            "last": ledger[-1] if ledger else None, "allocation_breakdown": ALLOCATION}
