"""
Temuclaude Model Pool — Configuration for all Ollama Cloud models
"""

# Model pool configuration
# Each model has a role, strengths, and routing priority

MODEL_POOL = {
    "glm-5.2": {
        "ollama_tag": "glm-5.2:cloud",
        "role": "orchestrator",
        "strengths": ["reasoning", "coding", "knowledge", "agentic"],
        "context_length": 1_000_000,
        "thinking": True,
        "tools": True,
        "cost_tier": "flat",  # Ollama Cloud = flat rate
        "routing_weight": 1.0,
    },
    "deepseek-v4-pro": {
        "ollama_tag": "deepseek-v4-pro:cloud",
        "role": "reasoning_specialist",
        "strengths": ["math", "coding", "reasoning", "science"],
        "context_length": 1_000_000,
        "thinking": True,
        "tools": True,
        "cost_tier": "flat",
        "routing_weight": 0.9,
    },
    "kimi-k2.6": {
        "ollama_tag": "kimi-k2.6:cloud",
        "role": "long_context_specialist",
        "strengths": ["long_context", "vision", "reasoning", "swarm"],
        "context_length": 1_000_000,
        "thinking": True,
        "tools": True,
        "cost_tier": "flat",
        "routing_weight": 0.85,
    },
    "minimax-m3": {
        "ollama_tag": "minimax-m3:cloud",
        "role": "generation_specialist",
        "strengths": ["generation", "vision", "reasoning", "creative"],
        "context_length": 1_000_000,
        "thinking": True,
        "tools": True,
        "cost_tier": "flat",
        "routing_weight": 0.8,
    },
    "nemotron-3-ultra": {
        "ollama_tag": "nemotron-3-ultra:cloud",
        "role": "verifier",
        "strengths": ["verification", "agentic", "evaluation"],
        "context_length": 262_144,
        "thinking": True,
        "tools": True,
        "cost_tier": "flat",
        "routing_weight": 0.7,
    },
    "llama-3.3-70b-instruct": {
        "ollama_tag": "llama3.3:70b",
        "role": "specialist",
        "strengths": ["reasoning", "coding", "knowledge"],
        "context_length": 131_072,
        "thinking": False,
        "tools": True,
        "cost_tier": "cheap",
        "routing_weight": 0.88,
    },
    "gemini-2.0-flash": {
        "ollama_tag": "gemini-2.0-flash:cloud",
        "role": "worker",
        "strengths": ["multimodal", "speed", "knowledge"],
        "context_length": 1_048_576,
        "thinking": False,
        "tools": True,
        "cost_tier": "ultra_cheap",
        "routing_weight": 0.86,
    },
    "mistral-large-2": {
        "ollama_tag": "mistral-large:cloud",
        "role": "specialist",
        "strengths": ["coding", "reasoning", "multilingual"],
        "context_length": 131_072,
        "thinking": False,
        "tools": True,
        "cost_tier": "premium",
        "routing_weight": 0.85,
    },
    "claude-3.5-sonnet": {
        "ollama_tag": "claude-3.5-sonnet:cloud",
        "role": "frontier_fallback",
        "strengths": ["coding", "reasoning", "agentic"],
        "context_length": 200_000,
        "thinking": False,
        "tools": True,
        "cost_tier": "premium",
        "routing_weight": 0.95,
    },
}

# Cheaper models for trivial queries
CHEAP_MODELS = {
    "gpt-oss-120b": {
        "ollama_tag": "gpt-oss:120b-cloud",
        "role": "cheap_router",
        "strengths": ["general", "simple_qa"],
        "cost_tier": "flat",
        "routing_weight": 0.5,
    },
}

# Task type → best model mapping (for routing)
TASK_MODEL_MAP = {
    "math": "deepseek-v4-pro",
    "coding": "deepseek-v4-pro",
    "long_context": "kimi-k2.6",
    "knowledge": "glm-5.2",
    "reasoning": "deepseek-v4-pro",
    "creative": "minimax-m3",
    "agentic": "glm-5.2",
    "verification": "nemotron-3-ultra",
    "vision": "kimi-k2.6",
    "simple": "gpt-oss-120b",
}

# Fusion panel configuration
FUSION_PANEL = ["glm-5.2", "deepseek-v4-pro", "kimi-k2.6", "minimax-m3", "nemotron-3-ultra"]

# Dynamic aggregator selection
AGGREGATOR_MAP = {
    "math": "deepseek-v4-pro",
    "coding": "deepseek-v4-pro",
    "knowledge": "glm-5.2",
    "reasoning": "deepseek-v4-pro",
    "creative": "minimax-m3",
    "agentic": "glm-5.2",
    "default": "glm-5.2",
}

# OpenRouter model IDs (production backend — scales to thousands of concurrent users)
# 8-model pool — deep researched July 4, 2026
OPENROUTER_MODELS = {
    "glm-5.2": "z-ai/glm-5.2",                          # IQ 51 — orchestrator
    "deepseek-v4-pro": "deepseek/deepseek-v4-pro",      # IQ 44 — hard reasoning
    "hy3-preview": "tencent/hy3-preview",                # cheapest — trivial router (60% of queries)
    "mimo-v2.5": "xiaomi/mimo-v2.5",                     # IQ 40 — multimodal (image+video)
    "gemini-3-flash": "google/gemini-3-flash-preview",  # IQ 50 — #1 Legal, #2 Health
    "minimax-m3": "minimax/minimax-m3",                  # IQ 44 — vision + creative
    "claude-sonnet-5": "anthropic/claude-sonnet-5",     # IQ 53 — frontier fallback (hardest 2%)
    "nemotron-3-ultra": "nvidia/nemotron-3-ultra-550b-a55b",  # IQ 38 — verifier
    "kimi-k2.6": "moonshotai/kimi-k2.6",                # legacy — kept for compatibility
    "kimi-k2.7-code": "moonshotai/kimi-k2.7-code",      # legacy — kept for compatibility
    "gpt-oss-120b": "openai/gpt-oss-120b",              # legacy — kept for compatibility
    # v3 Hybrid pool models
    "llama-3.3-70b-instruct": "meta-llama/llama-3.3-70b-instruct",
    "gemini-2.0-flash": "google/gemini-2.0-flash",
    "mistral-large-2": "mistralai/mistral-large-2",
    "claude-3.5-sonnet": "anthropic/claude-3.5-sonnet",
    # Ultra-cheap MoE models for shepherding workers and medium tier
    "deepseek-v4-flash": "deepseek/deepseek-v4-flash",  # $0.09/$0.18/M — shepherd worker
    "qwen3-235b-moe": "qwen/qwen3-235b-a22b-2507",      # $0.09/$0.10/M — MoE reasoning
    "qwen3-next-80b-moe": "qwen/qwen3-next-80b-a3b-instruct",  # $0.09/$0.78/M — MoE general
    "gemma-4-26b-moe": "google/gemma-4-26b-a4b-it",     # $0.06/$0.30/M — MoE knowledge
}

# Free models on OpenRouter (no cost, rate limited)
# These are used for the trivial tier — 60% of queries at $0 cost
OPENROUTER_FREE_MODELS = {
    "gpt-oss-120b": "openai/gpt-oss-120b:free",
    "nemotron-3-ultra": "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nemotron-3-super": "nvidia/nemotron-3-super-120b-a12b:free",
}

# Free model fallback order for trivial tier
# Try each in order until one succeeds (rate limits may block some)
FREE_MODEL_CHAIN = [
    "openai/gpt-oss-120b:free",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
]

# Ultra-cheap MoE models for medium tier (3-5x compute savings vs dense models)
# MoE = Mixture of Experts: activates only a fraction of parameters per token
ULTRA_CHEAP_MODELS = {
    "qwen3-235b-moe": {
        "ollama_tag": "qwen3-235b-a22b-2507",
        "openrouter_id": "qwen/qwen3-235b-a22b-2507",
        "role": "moe_reasoning",
        "strengths": ["reasoning", "math", "coding"],
        "active_params": "22B of 235B",
        "context_length": 262_144,
        "cost_tier": "ultra_cheap",
        "input_cost_per_m": 0.09,  # $0.09/M input
        "output_cost_per_m": 0.10,  # $0.10/M output
        "routing_weight": 0.85,
    },
    "qwen3-next-80b-moe": {
        "ollama_tag": "qwen3-next-80b-a3b-instruct",
        "openrouter_id": "qwen/qwen3-next-80b-a3b-instruct",
        "role": "moe_general",
        "strengths": ["general", "reasoning", "coding"],
        "active_params": "3B of 80B",
        "context_length": 262_144,
        "cost_tier": "ultra_cheap",
        "input_cost_per_m": 0.09,
        "output_cost_per_m": 0.78,
        "routing_weight": 0.80,
    },
    "gemma-4-26b-moe": {
        "ollama_tag": "gemma-4-26b-a4b-it",
        "openrouter_id": "google/gemma-4-26b-a4b-it",
        "role": "moe_knowledge",
        "strengths": ["knowledge", "reasoning"],
        "active_params": "4B of 26B",
        "context_length": 262_144,
        "cost_tier": "ultra_cheap",
        "input_cost_per_m": 0.06,
        "output_cost_per_m": 0.30,
        "routing_weight": 0.75,
    },
    "deepseek-v4-flash": {
        "ollama_tag": "deepseek-v4-flash:cloud",
        "openrouter_id": "deepseek/deepseek-v4-flash",
        "role": "fast_reasoning",
        "strengths": ["reasoning", "math", "coding", "fast"],
        "context_length": 1_000_000,
        "cost_tier": "ultra_cheap",
        "input_cost_per_m": 0.09,
        "output_cost_per_m": 0.18,
        "routing_weight": 0.88,
    },
}

# API base URLs
OLLAMA_API_BASE = "http://localhost:11434"
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
AIML_API_BASE = "https://api.aimlapi.com/v1"

# ai/ml model IDs (fallback backend — same OpenAI-compatible API format)
# EVALUATED July 6, 2026: kept ONLY verified models that add efficiency or
# unique capability. All unverified-IQ models REMOVED for zero quality risk.
# See AIML-MODEL-RESEARCH.md for full analysis.
AIML_MODELS = {
    # === VERIFIED models — cheaper output on AIML than OpenRouter ===
    # These provide real efficiency wins when AIML is used as fallback.
    "glm-5.2": "zhipu/glm-5.2",                    # AIML output $1.82 vs OR $3.00
    "deepseek-v4-pro": "deepseek/deepseek-v4-pro", # AIML output $0.565 vs OR $0.87
    "deepseek-v4-flash": "deepseek/deepseek-v4-flash",  # same price, redundancy
    "minimax-m3": "minimax/minimax-m3",            # AIML output $0.39 vs OR $1.20
    "gpt-oss-120b": "openai/gpt-oss-120b",         # same model, redundancy

    # === VERIFIED cheap fallback — unique to AIML ===
    "nemotron-3-nano": "nvidia/nemotron-3-nano-30b-a3b",  # $0.065/M, MMLU 57.9 verified

    # === UNIQUE capability — search-augmented (new effectiveness) ===
    "sonar-pro": "perplexity/sonar-pro",           # built-in web search for time-sensitive queries
}

# Auto-detect: use OpenRouter if key is set, otherwise Ollama
import os as _os
try:
    from dotenv import load_dotenv
    # Load .env from project root
    load_dotenv(_os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), ".env"))
except ImportError:
    pass

_USE_OPENROUTER = bool(_os.environ.get("OPENROUTER_API_KEY"))
_HAS_AIML_KEY = bool(_os.environ.get("AIML_API_KEY"))

# Active API base (auto-detect: OpenRouter if key set, else Ollama)
API_BASE = OPENROUTER_API_BASE if _USE_OPENROUTER else OLLAMA_API_BASE

# LiteLLM proxy port
LITELLM_PORT = 4000