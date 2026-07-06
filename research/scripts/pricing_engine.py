#!/usr/bin/env python3
"""
Pricing Engine — dynamic pricing based on verified competitor prices (July 2026).

All competitor prices verified by scraping official pricing pages on July 7, 2026.
See PRICING-RESEARCH-REPORT.md for full source citations.

Target: 78% gross margin (above AI industry average of 50-60% per BVP/a16z/ICONIQ).
Ummah Fund: 25% of profit to verified Muslim charities.
"""

# --- Verified competitor pricing (per 1M tokens, USD) ---
# Sources: official pricing pages scraped Jul 7, 2026
COMPETITOR_PRICING = {
    # Frontier (verified from platform.claude.com, openai.com, ai.google.dev, docs.x.ai)
    "claude_fable_5":        {"input": 10.00, "output": 50.00, "source": "platform.claude.com"},
    "claude_mythos_5":       {"input": 10.00, "output": 50.00, "source": "platform.claude.com"},
    "claude_opus_4.8":       {"input": 5.00,  "output": 25.00, "source": "platform.claude.com"},
    "gpt_5.5":               {"input": 5.00,  "output": 30.00, "source": "openai.com/api/pricing"},
    "gpt_5.4":               {"input": 2.50,  "output": 15.00, "source": "openai.com/api/pricing"},
    "claude_sonnet_5":       {"input": 3.00,  "output": 15.00, "source": "platform.claude.com"},
    "claude_sonnet_5_intro": {"input": 2.00,  "output": 10.00, "source": "platform.claude.com (through Aug 31 2026)"},
    "gemini_3.1_pro":        {"input": 0.00,  "output": 12.00, "source": "ai.google.dev/gemini-api/docs/pricing"},
    "gemini_3.5_flash":      {"input": 0.00,  "output": 9.00,  "source": "ai.google.dev/gemini-api/docs/pricing"},
    "grok_4.3":              {"input": 1.25,  "output": 2.50,  "source": "docs.x.ai/developers/models"},
    "perplexity_sonar_pro":  {"input": 3.00,  "output": 15.00, "source": "docs.perplexity.ai"},

    # Mid-tier (verified from docs.z.ai, mistral.ai, pricepertoken.com)
    "glm_5.2":               {"input": 1.40,  "output": 4.40,  "source": "docs.z.ai/guides/overview/pricing"},
    "glm_4.7":               {"input": 0.60,  "output": 2.20,  "source": "docs.z.ai/guides/overview/pricing"},
    "mistral_large":         {"input": 2.00,  "output": 6.00,  "source": "mistral.ai/pricing"},
    "mistral_medium_3.5":    {"input": 1.50,  "output": 4.50,  "source": "mistral.ai/pricing"},
    "kimi_k2.6":             {"input": 0.55,  "output": 2.20,  "source": "pricepertoken.com/moonshotai-kimi-k2"},
    "qwen3_max":             {"input": 0.78,  "output": 3.90,  "source": "pricepertoken.com/qwen3-max"},

    # Ultra-cheap (verified from api-docs.deepseek.com, docs.z.ai)
    "deepseek_v4_flash":     {"input": 0.14,  "output": 0.28,  "source": "api-docs.deepseek.com/quick_start/pricing"},
    "deepseek_v4_pro":       {"input": 0.435, "output": 0.87,  "source": "api-docs.deepseek.com/quick_start/pricing"},
    "glm_4.7_flashx":        {"input": 0.07,  "output": 0.40,  "source": "docs.z.ai/guides/overview/pricing"},
    "glm_4_32b":             {"input": 0.10,  "output": 0.10,  "source": "docs.z.ai/guides/overview/pricing"},
    "qwen3_235b_a22b":       {"input": 0.09,  "output": 0.10,  "source": "pricepertoken.com"},

    # FREE (verified from docs.z.ai, openrouter.ai)
    "glm_4.7_flash":         {"input": 0.00,  "output": 0.00,  "source": "docs.z.ai (FREE)"},
    "glm_4.5_flash":         {"input": 0.00,  "output": 0.00,  "source": "docs.z.ai (FREE)"},
    "gpt_oss_120b_free":     {"input": 0.00,  "output": 0.00,  "source": "openrouter.ai (FREE)"},
    "nemotron_3_ultra_free": {"input": 0.00,  "output": 0.00,  "source": "openrouter.ai (FREE)"},
}

# --- TemuClaude's own cost structure ---
# 60% of queries → free models ($0), 30% → ultra-cheap ($0.05-0.14/MTok), 10% → premium ($1-3/MTok)
# Weighted blended cost: ~$0.05/MTok
BLENDED_COST_PER_MTOK = 0.05

# --- Targets ---
TARGET_GROSS_MARGIN = 0.78   # 78% — above industry avg 50-60%
UMMAH_FUND_PCT = 0.25        # 25% of profit to Ummah Fund

# --- TemuClaude API pricing (recommended Jul 7, 2026) ---
# Position: between ultra-cheap ($0.14) and mid-tier ($1.40)
# 10-25x cheaper than frontier, 3-8x cheaper than mid-tier
# 3-4x more than ultra-cheap (justified by orchestration quality)
TEMUCLAUDE_PRICING = {
    "input_per_mtok":  0.50,
    "output_per_mtok": 2.00,
    "cached_input_per_mtok": 0.05,   # 90% cache discount (industry standard)
}

# --- Subscription tiers (4-tier model) ---
SUBSCRIPTION_TIERS = {
    "free": {
        "price_usd": 0,
        "price_inr_paise": 0,
        "queries_per_day": 100,
        "queries_per_month": 3000,
        "api_access": False,
        "models": "free models only",
        "rate_limit_per_min": 20,
        "support": "Community",
    },
    "developer": {
        "price_usd": 15,
        "price_inr_paise": 1250,   # ~₹1,040
        "queries_per_month": 50000,
        "api_access": True,
        "models": "all models, full orchestration",
        "rate_limit_per_min": 100,
        "support": "Email (48h)",
    },
    "pro": {
        "price_usd": 49,
        "price_inr_paise": 4100,   # ~₹3,410
        "queries_per_month": 500000,
        "api_access": True,
        "models": "priority routing, faster latency",
        "rate_limit_per_min": 1000,
        "support": "Email (24h) + Dashboard",
    },
    "enterprise": {
        "price_usd": 499,
        "price_inr_paise": 41500,  # ~₹34,500
        "queries_per_month": -1,   # unlimited
        "api_access": True,
        "models": "SSO, SLA 99.9%, dedicated routing, custom models",
        "rate_limit_per_min": 10000,
        "support": "Dedicated + Slack + SLA",
    },
}

# --- Dynamic pricing discounts ---
VOLUME_DISCOUNTS = {
    "10M_tokens/month": 0.20,    # 20% off
    "annual_commit_50K": 0.30,   # 30% off for >$50K/year commits
    "off_peak_batch": 0.50,      # 50% off for async/batch
    "educational_islamic": 0.50, # 50% off for Islamic schools/madrasas
    "ummah_partner": 1.00,       # 100% off (free) for verified Muslim charities
}

# --- Ummah Fund allocation ---
UMMAH_FUND_ALLOCATION = {
    "palestine_food_relief": 40,
    "muslim_community_kitchens": 20,
    "orphan_feeding": 15,
    "muslim_medical_clinics": 15,
    "islamic_schools": 10,
}


def compute_gross_margin(price_per_mtok, cost_per_mtok=BLENDED_COST_PER_MTOK):
    """Compute gross margin percentage."""
    if price_per_mtok <= 0:
        return 0
    return (1 - cost_per_mtok / price_per_mtok) * 100


def compute_net_margin_after_ummah(price_per_mtok, cost_per_mtok=BLENDED_COST_PER_MTOK):
    """Compute net margin after 25% Ummah Fund allocation."""
    gross_margin = 1 - cost_per_mtok / price_per_mtok
    profit_after_ummah = gross_margin * (1 - UMMAH_FUND_PCT)
    return profit_after_ummah * 100


def get_competitor_comparison():
    """Return TemuClaude vs all competitors with discount percentages."""
    tc_in = TEMUCLAUDE_PRICING["input_per_mtok"]
    tc_out = TEMUCLAUDE_PRICING["output_per_mtok"]
    comparisons = []
    for name, prices in COMPETITOR_PRICING.items():
        comp_blended = (prices["input"] + prices["output"]) / 2
        tc_blended = (tc_in + tc_out) / 2
        if comp_blended > 0:
            discount = (1 - tc_blended / comp_blended) * 100
        else:
            discount = 0
        comparisons.append({
            "competitor": name,
            "competitor_input": prices["input"],
            "competitor_output": prices["output"],
            "temuclaude_input": tc_in,
            "temuclaude_output": tc_out,
            "temuclaude_discount_pct": round(discount, 1),
            "source": prices["source"],
        })
    return comparisons


def compute_ummah_fund(revenue, costs):
    """Compute Ummah Fund allocation from revenue and costs."""
    profit = revenue - costs
    if profit <= 0:
        return {"profit": profit, "fund_total": 0, "allocations": {}, "note": "No profit yet"}
    fund_amount = profit * UMMAH_FUND_PCT
    allocations = {cause: fund_amount * (pct / 100) for cause, pct in UMMAH_FUND_ALLOCATION.items()}
    return {
        "revenue": revenue,
        "costs": costs,
        "profit": profit,
        "fund_total": fund_amount,
        "profit_to_ummah_pct": UMMAH_FUND_PCT * 100,
        "allocations": allocations,
    }


def get_tier_pricing():
    """Return complete pricing structure for all tiers."""
    return {
        "api": TEMUCLAUDE_PRICING,
        "subscriptions": SUBSCRIPTION_TIERS,
        "gross_margin_pct": compute_gross_margin(TEMUCLAUDE_PRICING["input_per_mtok"]),
        "net_margin_after_ummah_pct": compute_net_margin_after_ummah(TEMUCLAUDE_PRICING["input_per_mtok"]),
        "volume_discounts": VOLUME_DISCOUNTS,
        "ummah_fund_allocation": UMMAH_FUND_ALLOCATION,
    }


def get_revenue_projection(years=5):
    """Project revenue and Ummah Fund contributions over years."""
    # Based on OpenRouter trajectory ($19M→$50M in 15 months) with higher margins
    projections = [
        {"year": 1, "users": 10000,   "api_rev": 500000,    "sub_rev": 2000000,   "ent_rev": 500000,    "total_arr": 3000000},
        {"year": 2, "users": 100000,  "api_rev": 5000000,   "sub_rev": 15000000,  "ent_rev": 5000000,   "total_arr": 25000000},
        {"year": 3, "users": 500000,  "api_rev": 30000000,  "sub_rev": 50000000,  "ent_rev": 30000000,  "total_arr": 110000000},
        {"year": 4, "users": 2000000, "api_rev": 150000000, "sub_rev": 150000000, "ent_rev": 100000000, "total_arr": 400000000},
        {"year": 5, "users": 5000000, "api_rev": 500000000, "sub_rev": 300000000, "ent_rev": 250000000, "total_arr": 1050000000},
    ]
    for p in projections[:years]:
        profit = p["total_arr"] * 0.50  # ~50% net margin
        fund = profit * UMMAH_FUND_PCT
        p["estimated_profit"] = profit
        p["ummah_fund"] = fund
        p["ummah_allocations"] = {cause: fund * (pct / 100) for cause, pct in UMMAH_FUND_ALLOCATION.items()}
    return projections[:years]


if __name__ == "__main__":
    pricing = get_tier_pricing()
    print(f"TemuClaude API Pricing:")
    print(f"  Input:  ${TEMUCLAUDE_PRICING['input_per_mtok']}/MTok")
    print(f"  Output: ${TEMUCLAUDE_PRICING['output_per_mtok']}/MTok")
    print(f"  Cached: ${TEMUCLAUDE_PRICING['cached_input_per_mtok']}/MTok")
    print(f"  Gross margin: {pricing['gross_margin_pct']:.1f}%")
    print(f"  Net margin after Ummah: {pricing['net_margin_after_ummah_pct']:.1f}%")
    print()
    print(f"Subscription tiers:")
    for tier, info in SUBSCRIPTION_TIERS.items():
        price_str = f"${info['price_usd']}/mo" if info['price_usd'] > 0 else "Free"
        queries = f"{info['queries_per_month']:,}/mo" if info.get('queries_per_month', 0) > 0 else "unlimited"
        print(f"  {tier}: {price_str} — {queries}")