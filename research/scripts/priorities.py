"""
Timuclaude Research Swarm — Priority Configuration
Defines research priority levels and token allocation.

PRIORITY SYSTEM (based on marginal value of research):
  RANK 1 (40% tokens): Maximum research — things we DON'T know
  RANK 2 (25% tokens): High research — competitive intelligence, monitoring
  RANK 3 (20% tokens): Medium research — scan for new developments
  RANK 4 (10% tokens): Low research — headline scan only
  RANK 5 ( 0% tokens): Zero research — already saturated

Each research area has a priority level and search frequency.
"""

RESEARCH_PRIORITIES = {
    # RANK 1 — MAXIMUM RESEARCH (40% of tokens)
    # Things we don't know yet, high marginal value
    "new_papers_repos": {
        "rank": 1,
        "weight": 10,
        "description": "Unknown unknowns — new papers/repos with techniques we haven't seen",
        "search_frequency": "every 6h",
        "deep_read": True,
        "token_budget": "high",
    },
    "marketing_strategy": {
        "rank": 1,
        "weight": 10,
        "description": "Completely new area — how to get users, attention, community",
        "search_frequency": "2x daily",
        "deep_read": True,
        "token_budget": "high",
    },
    "mcts_implementation": {
        "rank": 1,
        "weight": 9,
        "description": "THE breakthrough for small models beating large ones — need implementation details",
        "search_frequency": "daily",
        "deep_read": True,
        "token_budget": "high",
    },
    "prm_training": {
        "rank": 1,
        "weight": 9,
        "description": "How to auto-generate PRM training data without human labels",
        "search_frequency": "daily",
        "deep_read": True,
        "token_budget": "high",
    },
    "dspy_integration": {
        "rank": 1,
        "weight": 8,
        "description": "How to integrate DSPy/MIPROv2 for self-improving prompt optimization",
        "search_frequency": "daily",
        "deep_read": True,
        "token_budget": "high",
    },

    # RANK 2 — HIGH RESEARCH (25% of tokens)
    # Competitive intelligence, monitoring, model pool
    "frontier_model_docs": {
        "rank": 2,
        "weight": 7,
        "description": "What GPT-5.6, Gemini 3.5, Claude 4.6 are doing — scan, deep-read on changes",
        "search_frequency": "2x daily",
        "deep_read": False,  # Scan only, deep-read on new releases
        "token_budget": "medium",
    },
    "benchmark_results": {
        "rank": 2,
        "weight": 7,
        "description": "Track HLE, GDPval, SciCode, MATH, SWE-bench scores",
        "search_frequency": "daily",
        "deep_read": False,  # Scan leaderboards, deep-read on significant changes
        "token_budget": "medium",
    },
    "new_model_releases": {
        "rank": 2,
        "weight": 6,
        "description": "New open-weight models for the pool — scan, deep-read on strong candidates",
        "search_frequency": "daily",
        "deep_read": False,
        "token_budget": "medium",
    },
    "cost_optimization": {
        "rank": 2,
        "weight": 6,
        "description": "Protect the 50x cost advantage — new routing, caching, early exit techniques",
        "search_frequency": "daily",
        "deep_read": False,
        "token_budget": "medium",
    },
    "routing_optimization": {
        "rank": 2,
        "weight": 6,
        "description": "Improve model selection — RouteLLM, BEST-Route, preference-data routing",
        "search_frequency": "daily",
        "deep_read": False,
        "token_budget": "medium",
    },

    # RANK 3 — MEDIUM RESEARCH (20% of tokens)
    # Have most info, scan for new developments
    "fusion_patterns": {
        "rank": 3,
        "weight": 4,
        "description": "New MoA variants, fusion improvements — scan titles only",
        "search_frequency": "daily",
        "deep_read": False,
        "token_budget": "low",
    },
    "multi_agent_debate": {
        "rank": 3,
        "weight": 4,
        "description": "Debate optimization, collective delusion prevention — scan only",
        "search_frequency": "daily",
        "deep_read": False,
        "token_budget": "low",
    },
    "self_verification": {
        "rank": 3,
        "weight": 4,
        "description": "Step-level verification, code execution — scan only",
        "search_frequency": "daily",
        "deep_read": False,
        "token_budget": "low",
    },
    "best_of_n_sampling": {
        "rank": 3,
        "weight": 3,
        "description": "Sampling improvements, adaptive N — scan only",
        "search_frequency": "daily",
        "deep_read": False,
        "token_budget": "low",
    },
    "tool_augmented_reasoning": {
        "rank": 3,
        "weight": 3,
        "description": "Toolformer, code interpreter — scan only",
        "search_frequency": "daily",
        "deep_read": False,
        "token_budget": "low",
    },
    "self_improving_systems": {
        "rank": 3,
        "weight": 3,
        "description": "Auto-improvement patterns — scan only",
        "search_frequency": "daily",
        "deep_read": False,
        "token_budget": "low",
    },
    "hermes_improvements": {
        "rank": 3,
        "weight": 3,
        "description": "Hermes features, config, MCP — scan only",
        "search_frequency": "daily",
        "deep_read": False,
        "token_budget": "low",
    },
    "skill_discovery": {
        "rank": 3,
        "weight": 3,
        "description": "Useful skills for timuclaude — scan only",
        "search_frequency": "weekly",
        "deep_read": False,
        "token_budget": "low",
    },

    # RANK 4 — LOW RESEARCH (10% of tokens)
    # Well-covered or low signal, headline scan only
    "cot_variants": {
        "rank": 4,
        "weight": 2,
        "description": "ToT, GoT implemented — scan titles only",
        "search_frequency": "weekly",
        "deep_read": False,
        "token_budget": "minimal",
    },
    "speculative_decoding": {
        "rank": 4,
        "weight": 2,
        "description": "Needs self-hosting — track for future",
        "search_frequency": "weekly",
        "deep_read": False,
        "token_budget": "minimal",
    },
    "model_merging": {
        "rank": 4,
        "weight": 2,
        "description": "Needs self-hosting — track for future",
        "search_frequency": "weekly",
        "deep_read": False,
        "token_budget": "minimal",
    },
    "ai_agent_architecture": {
        "rank": 4,
        "weight": 2,
        "description": "Not urgent for timuclaude — scan only",
        "search_frequency": "weekly",
        "deep_read": False,
        "token_budget": "minimal",
    },
    "social_media": {
        "rank": 4,
        "weight": 1,
        "description": "HN, Reddit, Twitter — very low signal",
        "search_frequency": "weekly",
        "deep_read": False,
        "token_budget": "minimal",
    },

    # RANK 5 — ZERO RESEARCH (0% of tokens)
    # Already saturated, 2500+ lines of research done
    "management_science": {"rank": 5, "weight": 0, "description": "DONE — 850 lines"},
    "planning_theory": {"rank": 5, "weight": 0, "description": "DONE — 239 lines"},
    "quality_control": {"rank": 5, "weight": 0, "description": "DONE — 610 lines"},
    "coding_agent_architecture": {"rank": 5, "weight": 0, "description": "DONE — 267 lines"},
    "military_planning": {"rank": 5, "weight": 0, "description": "DONE"},
    "self_managing_systems": {"rank": 5, "weight": 0, "description": "DONE"},
    "meta_cognition": {"rank": 5, "weight": 0, "description": "DONE"},
}


def get_rank_1_topics():
    """Get all RANK 1 research topics — maximum priority."""
    return {k: v for k, v in RESEARCH_PRIORITIES.items() if v["rank"] == 1}

def get_rank_2_topics():
    """Get all RANK 2 research topics — high priority."""
    return {k: v for k, v in RESEARCH_PRIORITIES.items() if v["rank"] == 2}

def get_rank_3_topics():
    """Get all RANK 3 research topics — medium priority."""
    return {k: v for k, v in RESEARCH_PRIORITIES.items() if v["rank"] == 3}

def get_research_weight(topic: str) -> int:
    """Get the research weight for a topic (higher = more important)."""
    topic_data = RESEARCH_PRIORITIES.get(topic, {})
    return topic_data.get("weight", 0)

def should_deep_read(topic: str) -> bool:
    """Should this topic be deep-read or just scanned?"""
    topic_data = RESEARCH_PRIORITIES.get(topic, {})
    return topic_data.get("deep_read", False)

def get_token_budget(topic: str) -> str:
    """Get the token budget level for a topic."""
    topic_data = RESEARCH_PRIORITIES.get(topic, {})
    return topic_data.get("token_budget", "minimal")