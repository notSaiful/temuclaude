#!/usr/bin/env python3
"""
Cost Tracker — reads real spending from OpenRouter API and Ollama.
Outputs: research/cost_data.json (consumed by sync_daemon → Vercel API)
"""

import json
import os
import time
from pathlib import Path
from datetime import datetime
from urllib.request import urlopen, Request

RESEARCH_DIR = Path(os.environ.get("RESEARCH_DIR", "/Users/saiful/temuclaude/research"))
OUTPUT_FILE = RESEARCH_DIR / "cost_data.json"

# OpenRouter API
OR_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OR_BASE = "https://openrouter.ai/api/v1"


def _api_get(url, headers=None):
    try:
        req = Request(url, headers=headers or {})
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}


def fetch_openrouter_cost():
    """Get real spending data from OpenRouter."""
    if not OR_KEY:
        return {"available": False, "error": "No OPENROUTER_API_KEY set"}

    headers = {"Authorization": f"Bearer {OR_KEY}"}

    # Get credits
    credits = _api_get(f"{OR_BASE}/credits", headers)
    # Get key info (usage breakdown)
    key_info = _api_get(f"{OR_BASE}/key", headers)

    data = {"available": True, "source": "openrouter"}

    if "data" in credits:
        c = credits["data"]
        data["totalCredits"] = c.get("total_credits", 0)
        data["totalUsage"] = c.get("total_usage", 0)

    if "data" in key_info:
        k = key_info["data"]
        data["usageTotal"] = k.get("usage", 0)
        data["usageDaily"] = k.get("usage_daily", 0)
        data["usageWeekly"] = k.get("usage_weekly", 0)
        data["usageMonthly"] = k.get("usage_monthly", 0)
        data["isFreeTier"] = k.get("is_free_tier", True)
        data["limit"] = k.get("limit")
        data["limitRemaining"] = k.get("limit_remaining")
        data["expiresAt"] = k.get("expires_at")

        # Calculate burn rate per day from weekly usage
        weekly = k.get("usage_weekly", 0)
        data["burnRatePerDay"] = round(weekly / 7, 4) if weekly else 0

        # Throttle level based on free tier and usage
        if k.get("is_free_tier", True):
            # Free tier: $0 budget, everything is free
            data["throttleLevel"] = "green"
            data["remainingCredits"] = 0
            data["budgetStatus"] = "free_tier"
        else:
            total = data.get("totalCredits", 0)
            used = data.get("totalUsage", 0)
            remaining = total - used
            data["remainingCredits"] = round(remaining, 4)

            if remaining < 1:
                data["throttleLevel"] = "red"
            elif remaining < 5:
                data["throttleLevel"] = "orange"
            elif remaining < 10:
                data["throttleLevel"] = "yellow"
            else:
                data["throttleLevel"] = "green"

            data["budgetStatus"] = "paid"

    return data


def fetch_cost_data():
    """Aggregate cost data from all providers."""
    or_data = fetch_openrouter_cost()

    output = {
        "timestamp": datetime.now().isoformat(),
        "openrouter": or_data,
        # Summary for the UI
        "summary": {
            "remainingCredits": or_data.get("remainingCredits", 0),
            "burnRatePerDay": or_data.get("burnRatePerDay", 0),
            "throttleLevel": or_data.get("throttleLevel", "green"),
            "totalSpent24h": or_data.get("usageDaily", 0),
            "totalSpentMonthly": or_data.get("usageMonthly", 0),
            "isFreeTier": or_data.get("isFreeTier", True),
            "budgetStatus": or_data.get("budgetStatus", "unknown"),
        },
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(output, indent=2, default=str))
    print(f"Cost data written → {OUTPUT_FILE}")
    return output


if __name__ == "__main__":
    fetch_cost_data()