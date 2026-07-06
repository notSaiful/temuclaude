#!/usr/bin/env python3
"""
Usage Tracker — monitors credit consumption, per-daemon budgets, ROI.
"""

import json, os, time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request

TEMUCLAUDE = Path(os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude"))
LEDGER_FILE = TEMUCLAUDE / "research" / "cost_ledger.json"
SUMMARY_FILE = TEMUCLAUDE / "research" / "cost_summary.json"
CREDITS_FILE = TEMUCLAUDE / "research" / "credits_state.json"
BUDGET_FILE = TEMUCLAUDE / "research" / "daemon_budgets.json"

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
if not OPENROUTER_API_KEY:
    env_file = TEMUCLAUDE / ".env"
    if env_file.exists():
        for line in env_file.read_text().split("\n"):
            if line.startswith("OPENROUTER_API_KEY"):
                OPENROUTER_API_KEY = line.split("=", 1)[1].strip().strip("'\"")
                break

CREDIT_ALERT_THRESHOLD = 5.0
CREDIT_CRITICAL_THRESHOLD = 1.0
DAILY_BURN_LIMIT = 2.0

DAEMON_CREDIT_BUDGETS = {
    "scout_daemon": 0.00, "distiller_daemon": 0.00,
    "research_daemon_1": 0.15, "research_daemon_2": 0.15, "research_daemon_3": 0.15,
    "integrator_daemon": 0.30, "coordinator_daemon": 0.00,
    "cyber_daemon": 0.15, "efficiency_daemon": 0.15, "media_daemon": 0.10,
    "marketing_daemon": 0.05, "feedback_daemon": 0.00,
    "meta_auditor_daemon": 0.20, "swot_daemon": 0.10, "website_daemon": 0.00,
    "industry_radar_daemon": 0.05, "model_optimizer_daemon": 0.20,
    "cost_efficiency_daemon": 0.00, "revenue_daemon": 0.00, "growth_daemon": 0.05,
    "competitive_dominance_daemon": 0.20, "self_expansion_daemon": 0.00,
    "super_intelligence_daemon": 0.15,
}

def fetch_credits():
    try:
        req = Request("https://openrouter.ai/api/v1/key", headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}"})
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {"total_credits": data.get("data", {}).get("total_credits", 0),
                    "total_usage": data.get("data", {}).get("total_usage", 0),
                    "timestamp": datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}

def load_ledger():
    if LEDGER_FILE.exists():
        with open(LEDGER_FILE) as f:
            return json.load(f)
    return []

def save_ledger(entries):
    if len(entries) > 10000:
        entries = entries[-10000:]
    with open(LEDGER_FILE, 'w') as f:
        json.dump(entries, f, indent=2)

def log_usage(model, prompt_tokens, completion_tokens, cost_usd, daemon, task_type, result):
    if model.startswith("ollama/"):
        cost_usd = 0.0
    entry = {"timestamp": datetime.now(timezone.utc).isoformat(), "model": model,
             "prompt_tokens": prompt_tokens, "completion_tokens": completion_tokens,
             "total_tokens": prompt_tokens + completion_tokens, "cost_usd": cost_usd,
             "daemon": daemon, "task_type": task_type, "result": result}
    ledger = load_ledger()
    ledger.append(entry)
    save_ledger(ledger)

def compute_summary():
    ledger = load_ledger()
    if not ledger:
        return {}
    summary = {"timestamp": datetime.now(timezone.utc).isoformat(), "total_spent": 0, "total_tokens": 0, "by_daemon": {}}
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent = [e for e in ledger if e["timestamp"] >= cutoff.isoformat()]
    for entry in recent:
        summary["total_spent"] += entry["cost_usd"]
        summary["total_tokens"] += entry["total_tokens"]
        d = entry["daemon"]
        if d not in summary["by_daemon"]:
            summary["by_daemon"][d] = {"count": 0, "cost": 0, "tokens": 0}
        summary["by_daemon"][d]["count"] += 1
        summary["by_daemon"][d]["cost"] += entry["cost_usd"]
        summary["by_daemon"][d]["tokens"] += entry["total_tokens"]
    with open(SUMMARY_FILE, 'w') as f:
        json.dump(summary, f, indent=2)
    return summary

def get_burn_rate():
    ledger = load_ledger()
    now = datetime.now(timezone.utc)
    day_cost = sum(e["cost_usd"] for e in ledger if e["timestamp"] >= (now - timedelta(hours=24)).isoformat())
    return {"per_day": day_cost}

def should_throttle():
    credits = fetch_credits()
    burn = get_burn_rate()
    remaining = credits.get("total_credits", 0) - credits.get("total_usage", 0)
    throttle = {"should_throttle": False, "reason": "", "remaining_credits": remaining, "burn_rate_per_day": burn["per_day"]}
    if remaining < CREDIT_CRITICAL_THRESHOLD:
        throttle["should_throttle"] = True
        throttle["reason"] = f"CRITICAL: Only ${remaining:.2f} credits remaining"
    elif burn["per_day"] > DAILY_BURN_LIMIT:
        throttle["should_throttle"] = True
        throttle["reason"] = f"Daily burn ${burn['per_day']:.2f} exceeds limit ${DAILY_BURN_LIMIT}"
    elif remaining < CREDIT_ALERT_THRESHOLD:
        throttle["reason"] = f"WARNING: Only ${remaining:.2f} credits remaining"
    with open(CREDITS_FILE, 'w') as f:
        json.dump({**credits, **throttle}, f, indent=2)
    return throttle

# Budget allocator
def load_budgets():
    if BUDGET_FILE.exists():
        with open(BUDGET_FILE) as f:
            return json.load(f)
    return {}

def save_budgets(budgets):
    with open(BUDGET_FILE, 'w') as f:
        json.dump(budgets, f, indent=2)

def reset_budgets():
    budgets = {d: {"allowance": a, "spent": 0.0, "remaining": a} for d, a in DAEMON_CREDIT_BUDGETS.items()}
    save_budgets(budgets)

def check_budget(daemon_name):
    budgets = load_budgets()
    remaining = budgets.get(daemon_name, {}).get("remaining", 0)
    return {"can_spend": remaining > 0, "remaining": remaining}

def spend_credits(daemon_name, amount, model, prompt_tokens, completion_tokens, task_type, result):
    log_usage(model, prompt_tokens, completion_tokens, amount, daemon_name, task_type, result)
    budgets = load_budgets()
    if daemon_name in budgets:
        budgets[daemon_name]["spent"] += amount
        budgets[daemon_name]["remaining"] = max(0, budgets[daemon_name]["allowance"] - budgets[daemon_name]["spent"])
        save_budgets(budgets)
    return {"budget_exhausted": budgets.get(daemon_name, {}).get("remaining", 0) <= 0}

if __name__ == "__main__":
    print(f"Credits: {json.dumps(fetch_credits(), indent=2)}")
    print(f"Burn: {get_burn_rate()}")
    print(f"Throttle: {json.dumps(should_throttle(), indent=2)}")
