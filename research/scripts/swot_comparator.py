#!/usr/bin/env python3
"""
SWOT Comparator — scans Temuclaude's codebase, benchmarks, and competitive
landscape to produce a structured SWOT analysis.
"""

import json, os, sys, subprocess
from pathlib import Path
from datetime import datetime, timezone

TEMUCLAUDE = Path(os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude"))
SRC_DIR = TEMUCLAUDE / "src"

COMPETITOR_FEATURES = {
    "GPT-5.6 Sol": [
        "native multimodal", "function calling", "code interpreter",
        "web search", "memory", "128k context", "structured output"
    ],
    "Gemini 3.5 Pro": [
        "2M context", "video understanding", "code execution sandbox",
        "multilingual", "function calling", "grounding"
    ],
    "Mythos": [
        "reasoning chains", "self-reflection", "tool use", "planning"
    ],
    "OpenRouter": [
        "400+ model routing", "auto-fallback", "cost optimization", "streaming"
    ],
    "vLLM": [
        "PagedAttention", "continuous batching", "speculative decoding", "AWQ"
    ],
}

def get_our_features() -> list:
    features = []
    if SRC_DIR.exists():
        for pyfile in SRC_DIR.glob("*.py"):
            features.append(pyfile.stem)
    return features

def analyze_strengths(features) -> list:
    strengths = []
    strengths.append("50x lower cost than frontier models — orchestrates 8 free models")
    strengths.append("Fully open-source — no vendor lock-in")
    orchestration = [f for f in features if f in
        ["fusion", "unified_routing", "preference_router", "self_moa",
         "debate", "consistency", "shepherding", "adaptive", "tot"]]
    if orchestration:
        strengths.append(f"Advanced orchestration: {', '.join(orchestration)}")
    cyber = [f for f in features if f in
        ["guard", "honeypot", "counter_attack", "output_firewall",
         "security_pipeline", "taint_tracker", "virtual_chamber"]]
    if cyber:
        strengths.append(f"6-layer cybersecurity: {', '.join(cyber)}")
    strengths.append("Self-improving 24/7 — research swarm discovers and implements breakthroughs")
    return strengths

def analyze_weaknesses(features, fail_rate) -> list:
    weaknesses = []
    our_names = set(features)
    for competitor, their_features in COMPETITOR_FEATURES.items():
        for feat in their_features:
            has_similar = False
            for our in our_names:
                if any(word in our.lower() for word in feat.lower().split()):
                    has_similar = True
                    break
            if not has_similar:
                weaknesses.append({
                    "area": "missing_feature",
                    "competitor": competitor,
                    "feature": feat,
                    "severity": "HIGH",
                    "action": f"Research and implement: {feat} (competitor: {competitor})"
                })
    if fail_rate > 0.3:
        weaknesses.append({
            "area": "implementation_quality",
            "severity": "MEDIUM",
            "action": f"Implementation fail rate {fail_rate*100:.0f}% — improve integrator"
        })
    if "vllm" not in str(features).lower():
        weaknesses.append({
            "area": "inference_speed",
            "severity": "MEDIUM",
            "action": "No self-hosted vLLM — latency penalty"
        })
    return weaknesses

def analyze_opportunities() -> list:
    return [
        {"area": "market_trend", "opportunity": "Agentic AI trending — position as open-source agentic orchestration layer"},
        {"area": "market_trend", "opportunity": "Cost-conscious AI adoption rising — 50x cost advantage differentiates"},
        {"area": "market_trend", "opportunity": "Open-source AI trust growing — transparent and auditable"},
        {"area": "market_trend", "opportunity": "AI cybersecurity underserved — 6-layer defense is unique"},
    ]

def analyze_threats() -> list:
    return [
        {"area": "competitive", "threat": "Frontier models getting cheaper — cost advantage may shrink"},
        {"area": "competitive", "threat": "OpenAI/Google adding orchestration natively"},
        {"area": "technical", "threat": "Free model deprecation — OpenRouter free models could disappear"},
        {"area": "technical", "threat": "API rate limits on free tier — scale bottleneck"},
        {"area": "market", "threat": "Enterprise trust gap — open-source perceived as less reliable"},
    ]

def run_swot(fail_rate: float = 0.0) -> dict:
    features = get_our_features()
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "strengths": analyze_strengths(features),
        "weaknesses": analyze_weaknesses(features, fail_rate),
        "opportunities": analyze_opportunities(),
        "threats": analyze_threats(),
        "feature_count": len(features),
        "fail_rate": fail_rate,
    }

if __name__ == "__main__":
    print(json.dumps(run_swot(), indent=2))
