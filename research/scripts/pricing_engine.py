#!/usr/bin/env python3
"""Pricing Engine — dynamic pricing based on competitor + cost."""

COMPETITOR_PRICING = {"openai_gpt4": 0.03, "anthropic_claude": 0.015, "openrouter_avg": 0.005}

def compute_optimal_pricing(our_cost_per_1k, competitor_price):
    undercut = competitor_price * 0.50
    min_margin = our_cost_per_1k / 0.30
    optimal = max(undercut, min_margin)
    return {"price_per_1k_tokens": optimal, "our_cost": our_cost_per_1k,
            "margin_pct": (1 - our_cost_per_1k / optimal) * 100 if optimal > 0 else 0,
            "competitor_price": competitor_price, "discount_vs_competitor": (1 - optimal / competitor_price) * 100}

def get_tier_pricing(our_cost):
    return {"free": {"price": 0, "limit": "100 req/day"}, "pro": {"price": 9, "limit": "10k req/month"},
            "enterprise": {"price": 99, "limit": "unlimited"},
            "api": compute_optimal_pricing(our_cost, COMPETITOR_PRICING["openai_gpt4"])}
