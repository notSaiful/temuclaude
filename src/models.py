"""
Timuclaude Model Pool — Configuration for all Ollama Cloud models
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

# OpenRouter model IDs (for production — scales to thousands of concurrent users)
OPENROUTER_MODELS = {
    "glm-5.2": "z-ai/glm-5.2",
    "deepseek-v4-pro": "deepseek/deepseek-v4-pro",
    "kimi-k2.6": "moonshotai/kimi-k2.6",
    "kimi-k2.7-code": "moonshotai/kimi-k2.7-code",
    "minimax-m3": "minimax/minimax-m3",
    "nemotron-3-ultra": "nvidia/nemotron-3-ultra-550b-a55b",
    "gpt-oss-120b": "openai/gpt-oss-120b",
}

# Free models on OpenRouter (no cost, rate limited)
OPENROUTER_FREE_MODELS = {
    "gpt-oss-120b": "openai/gpt-oss-120b:free",
    "nemotron-3-ultra": "nvidia/nemotron-3-ultra-550b-a55b:free",
    "nemotron-3-super": "nvidia/nemotron-3-super-120b-a12b:free",
}

# API base URLs
OLLAMA_API_BASE = "http://localhost:11434"
OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"

# Auto-detect: use OpenRouter if key is set, otherwise Ollama
import os as _os
_USE_OPENROUTER = bool(_os.environ.get("OPENROUTER_API_KEY"))

# Active API base (auto-detect)
API_BASE = OPENROUTER_API_BASE if _USE_OPENROUTER else OLLAMA_API_BASE

# LiteLLM proxy port
LITELLM_PORT = 4000