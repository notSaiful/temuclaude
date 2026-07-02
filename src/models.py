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

# Ollama API base
OLLAMA_API_BASE = "http://localhost:11434"

# LiteLLM proxy port
LITELLM_PORT = 4000