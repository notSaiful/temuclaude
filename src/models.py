"""
Temuclaude Model Pool — Configuration for all Ollama Cloud models
"""

# Model pool configuration
# Each model has a role, strengths, and routing priority

MODEL_POOL = {
    "glm-5.2": {
        "ollama_tag": "glm-5.2:cloud",
        "role": "orchestrator",
        "strengths": ["planning", "project_software_engineering", "long_horizon_agentic", "synthesis"],
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
        "role": "ui_ux_coding_specialist",
        "strengths": ["coding", "ui_ux_generation", "multimodal", "multi_agent_orchestration"],
        "context_length": 262_144,
        "thinking": True,
        "tools": True,
        "cost_tier": "flat",
        "routing_weight": 0.85,
    },
    "minimax-m3": {
        "ollama_tag": "minimax-m3:cloud",
        "role": "multimodal_long_context_specialist",
        "strengths": ["image_video_understanding", "long_context", "creative", "agentic"],
        "context_length": 1_000_000,
        "thinking": True,
        "tools": True,
        "cost_tier": "flat",
        "routing_weight": 0.8,
    },
    "nemotron-3-ultra": {
        "ollama_tag": "nemotron-3-ultra:cloud",
        "role": "verifier",
        "strengths": ["verification", "reasoning", "agentic", "long_context", "high_stakes_rag"],
        "context_length": 1_000_000,
        "thinking": True,
        "tools": True,
        "cost_tier": "flat",
        "routing_weight": 0.7,
    },
    # Premium routes are capability-specific and must never become implicit
    # defaults.  `get_runtime_model()` below resolves them to a proven open
    # route unless the matching direct-provider credential is configured.
    "gemini-3.5-flash": {
        "ollama_tag": "gemini-3.5-flash",
        "role": "premium_multimodal",
        "strengths": ["multimodal", "ui_control", "tools", "long_context"],
        "context_length": 1_000_000,
        "thinking": True,
        "tools": True,
        "cost_tier": "premium",
        "routing_weight": 0.0,
    },
    "gpt-5.6-luna": {
        "ollama_tag": "gpt-5.6-luna",
        "role": "fast_gpt_worker",
        "strengths": ["high_volume", "tool_use", "long_context", "independent_proposal"],
        "context_length": 1_000_000,
        "thinking": True,
        "tools": True,
        "cost_tier": "premium",
        "routing_weight": 0.0,
    },
    "gpt-5.6-sol": {
        "ollama_tag": "gpt-5.6-sol",
        "role": "frontier_adjudicator",
        "strengths": ["complex_reasoning", "coding", "professional_work", "adjudication"],
        "context_length": 1_050_000,
        "thinking": True,
        "tools": True,
        "cost_tier": "frontier",
        "routing_weight": 0.0,
    },
    "grok-4.5": {
        "ollama_tag": "grok-4.5",
        "role": "coding_agent_escalation",
        "strengths": ["coding", "agentic", "repair", "knowledge"],
        "context_length": 1_000_000,
        "thinking": True,
        "tools": True,
        "cost_tier": "premium",
        "routing_weight": 0.0,
    },
    "gpt-5.6-terra": {
        "ollama_tag": "gpt-5.6-terra",
        "role": "emergency_fallback",
        "strengths": ["reasoning", "coding", "knowledge", "agentic"],
        "context_length": 1_000_000,
        "thinking": True,
        "tools": True,
        "cost_tier": "emergency",
        "routing_weight": 0.0,
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
        "ollama_tag": "gemini-2.5-flash:cloud",
        "role": "worker",
        "strengths": ["multimodal", "speed", "knowledge"],
        "context_length": 1_048_576,
        "thinking": False,
        "tools": True,
        "cost_tier": "ultra_cheap",
        "routing_weight": 0.86,
    },
    "mistral-large-2": {
        "ollama_tag": "mistral-large-3:cloud",
        "role": "specialist",
        "strengths": ["coding", "reasoning", "multilingual"],
        "context_length": 262_144,
        "thinking": False,
        "tools": True,
        "cost_tier": "premium",
        "routing_weight": 0.85,
    },
    "claude-3.5-sonnet": {
        "ollama_tag": "claude-sonnet-4.6:cloud",
        "role": "frontier_fallback",
        "strengths": ["coding", "reasoning", "agentic"],
        "context_length": 1_000_000,
        "thinking": False,
        "tools": True,
        "cost_tier": "premium",
        "routing_weight": 0.95,
    },
    "gemini-2.5-flash": {
        "ollama_tag": "gemini-2.5-flash:cloud",
        "role": "worker",
        "strengths": ["multimodal", "speed", "knowledge"],
        "context_length": 1_048_576,
        "thinking": False,
        "tools": True,
        "cost_tier": "ultra_cheap",
        "routing_weight": 0.86,
    },
    "mistral-large-3": {
        "ollama_tag": "mistral-large-3:cloud",
        "role": "specialist",
        "strengths": ["coding", "reasoning", "multilingual"],
        "context_length": 262_144,
        "thinking": False,
        "tools": True,
        "cost_tier": "premium",
        "routing_weight": 0.85,
    },
    "claude-sonnet-4.6": {
        "ollama_tag": "claude-sonnet-4.6:cloud",
        "role": "frontier_fallback",
        "strengths": ["coding", "reasoning", "agentic"],
        "context_length": 1_000_000,
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
    "long_context": "minimax-m3",
    "knowledge": "glm-5.2",
    "reasoning": "deepseek-v4-pro",
    "creative": "minimax-m3",
    "agentic": "glm-5.2",
    "verification": "nemotron-3-ultra",
    "vision": "gemini-3.5-flash",
    "ui_ux": "kimi-k2.6",
    "simple": "deepseek-v4-flash",
}

# Pro uses every configured frontier and specialist role for complex work.
# Unconfigured direct-provider models resolve to strong in-pool routes and are
# deduplicated by the fusion panel. Lite and explicit savings modes stay bounded.
FUSION_PANEL = [
    "glm-5.2",
    "deepseek-v4-pro",
    "kimi-k2.6",
    "minimax-m3",
    "gemini-3.5-flash",
    "gpt-5.6-luna",
    "gpt-5.6-sol",
    "grok-4.5",
    "nemotron-3-ultra",
]

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
    "claude-sonnet-5": "anthropic/claude-sonnet-4.6",   # legacy alias -> Sonnet 4.6
    "nemotron-3-ultra": "nvidia/nemotron-3-ultra-550b-a55b",  # IQ 38 — verifier
    "kimi-k2.6": "moonshotai/kimi-k2.6",                # legacy — kept for compatibility
    "kimi-k2.7-code": "moonshotai/kimi-k2.7-code",      # legacy — kept for compatibility
    "gpt-oss-120b": "openai/gpt-oss-120b",              # legacy — kept for compatibility
    # v3 Hybrid pool models
    "llama-3.3-70b-instruct": "meta-llama/llama-3.3-70b-instruct",
    "gemini-2.0-flash": "google/gemini-2.5-flash",
    "mistral-large-2": "mistralai/mistral-large-2512",
    "claude-3.5-sonnet": "anthropic/claude-sonnet-4.6",
    "gemini-2.5-flash": "google/gemini-2.5-flash",
    "mistral-large-3": "mistralai/mistral-large-2512",
    "claude-sonnet-4.6": "anthropic/claude-sonnet-4.6",
    # Ultra-cheap MoE models for shepherding workers and medium tier
    "deepseek-v4-flash": "deepseek/deepseek-v4-flash",  # $0.09/$0.18/M — shepherd worker
    # Direct-provider routes. These IDs are deliberately also registered here
    # for observability, but `get_runtime_model` prevents unconfigured direct
    # providers from being selected as a normal route.
    "gemini-3.5-flash": "google/gemini-3.5-flash",
    "gpt-5.6-luna": "openai/gpt-5.6-luna",
    "gpt-5.6-sol": "openai/gpt-5.6-sol",
    "grok-4.5": "x-ai/grok-4.5",
    "gpt-5.6-terra": "openai/gpt-5.6-terra",
    "qwen3-235b-moe": "qwen/qwen3-235b-a22b-2507",      # $0.09/$0.10/M — MoE reasoning
    "qwen3-235b-thinking": "qwen/qwen3-235b-a22b-thinking-2507",
    "qwen3.7-plus": "qwen/qwen3.7-plus",
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

# Provider/runtime fallback order. Preferred model IDs above remain unchanged;
# these are only attempted when a preferred provider/model fails at runtime.
OPENROUTER_MODEL_FALLBACKS = {
    "deepseek-v4-flash": ["deepseek-v4-pro", "glm-5.2"],
    "qwen3-235b-thinking": ["deepseek-v4-flash"],
    "qwen3.7-plus": ["deepseek-v4-flash"],
    "gemini-3.5-flash": ["minimax-m3", "glm-5.2", "deepseek-v4-pro"],
    "gpt-5.6-luna": ["glm-5.2", "deepseek-v4-pro"],
    "gpt-5.6-sol": ["grok-4.5", "deepseek-v4-pro", "glm-5.2"],
    "grok-4.5": ["gpt-5.6-sol", "deepseek-v4-pro", "glm-5.2"],
    "gpt-5.6-terra": ["gpt-5.6-sol", "grok-4.5", "deepseek-v4-pro", "glm-5.2"],
    "gemini-2.0-flash": ["gemini-3-flash", "glm-5.2"],
    "gemini-2.5-flash": ["gemini-3-flash", "glm-5.2"],
    "mistral-large-2": ["minimax-m3", "deepseek-v4-pro"],
    "mistral-large-3": ["minimax-m3", "deepseek-v4-pro"],
    "claude-3.5-sonnet": ["glm-5.2", "deepseek-v4-pro"],
    "claude-sonnet-4.6": ["glm-5.2", "deepseek-v4-pro"],
    "nemotron-3-ultra": ["nemotron-3-super", "gpt-oss-120b", "glm-5.2"],
    "llama-3.3-70b-instruct": ["hy3-preview", "gpt-oss-120b"],
    "kimi-k2.6": ["glm-5.2", "deepseek-v4-pro"],
}

# Updated stack: ten active roles plus a disabled emergency fallback. Pro
# selects the strongest available role set for the task; Lite and explicit
# savings profiles own cost-bounded routing.
UPDATED_MODEL_STACK = {
    "deepseek-v4-flash": "high-volume worker",
    "deepseek-v4-pro": "reasoning, math, and technical analysis",
    "glm-5.2": "planning, orchestration, and synthesis",
    "kimi-k2.6": "coding-driven UI/UX and multi-agent implementation",
    "minimax-m3": "multimodal, creative, product, and long-context review",
    "gemini-3.5-flash": "premium multimodal and tool use",
    "gpt-5.6-luna": "fast GPT-family proposal and tool work",
    "gpt-5.6-sol": "frontier reasoning, coding, and adjudication",
    "grok-4.5": "hard coding-agent escalation",
    "nemotron-3-ultra": "independent verification",
}

# Direct providers use OpenAI-compatible endpoints. A direct route is selected
# only when the relevant credential exists. Terra has a second opt-in flag so a
# preview/emergency model cannot become an accidental production default.
DIRECT_MODEL_PROVIDERS = {
    "gemini-3.5-flash": {
        "env": "GOOGLE_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-3.5-flash",
    },
    "gpt-5.6-luna": {
        "env": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-5.6-luna",
    },
    "gpt-5.6-sol": {
        "env": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-5.6-sol",
    },
    "grok-4.5": {
        "env": "XAI_API_KEY",
        "base_url": "https://api.x.ai/v1",
        "model": "grok-4.5",
    },
    "gpt-5.6-terra": {
        "env": "OPENAI_API_KEY",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-5.6-terra",
        "enable_env": "TEMUCLAUDE_ENABLE_TERRA_FALLBACK",
    },
}


def _env_truthy(value: str) -> bool:
    return value.lower() in {"1", "true", "yes", "on"}


def get_direct_model_provider(model: str, environ=None):
    """Return direct-provider metadata only when the route is explicitly ready."""
    import os

    environ = os.environ if environ is None else environ
    config = DIRECT_MODEL_PROVIDERS.get(model)
    if not config or not environ.get(config["env"]):
        return None
    enable_env = config.get("enable_env")
    if enable_env and not _env_truthy(environ.get(enable_env, "")):
        return None
    return config


def get_runtime_model(model: str, environ=None, _seen=None) -> str:
    """Resolve a model to one whose provider is configured.

    This keeps premium additions safe: missing API access degrades to a proven
    in-pool route rather than issuing an invalid provider request or silently
    charging an unexpected model.
    """
    import os

    environ = os.environ if environ is None else environ

    # Frontier aliases are valid OpenRouter routes too. A configured
    # OpenRouter key makes them available even if the corresponding native
    # provider credential is absent; call_model still prefers an explicitly
    # configured direct provider before selecting OpenRouter.
    if (
        model not in DIRECT_MODEL_PROVIDERS
        or get_direct_model_provider(model, environ)
        or (environ.get("OPENROUTER_API_KEY") and model in OPENROUTER_MODELS)
    ):
        return model

    seen = set() if _seen is None else _seen
    if model in seen:
        return "glm-5.2"
    seen.add(model)
    for fallback in OPENROUTER_MODEL_FALLBACKS.get(model, ["glm-5.2", "deepseek-v4-pro"]):
        resolved = get_runtime_model(fallback, environ, seen)
        if resolved:
            return resolved
    return "glm-5.2"

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
GROQ_API_BASE = "https://api.groq.com/openai/v1"
DEEPINFRA_API_BASE = "https://api.deepinfra.com/v1/openai"

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

AIML_MODEL_FALLBACKS = {
    "glm-5.2": ["glm-5.2"],
    "deepseek-v4-pro": ["deepseek-v4-pro"],
    "deepseek-v4-flash": ["deepseek-v4-flash"],
    "minimax-m3": ["minimax-m3"],
    "gpt-oss-120b": ["gpt-oss-120b"],
    "nemotron-3-ultra": ["nemotron-3-nano", "gpt-oss-120b"],
    "gemini-2.0-flash": ["glm-5.2", "deepseek-v4-pro"],
    "gemini-2.5-flash": ["glm-5.2", "deepseek-v4-pro"],
    "mistral-large-2": ["minimax-m3", "deepseek-v4-pro"],
    "mistral-large-3": ["minimax-m3", "deepseek-v4-pro"],
    "claude-3.5-sonnet": ["glm-5.2", "deepseek-v4-pro"],
    "claude-sonnet-4.6": ["glm-5.2", "deepseek-v4-pro"],
    "gemini-3-flash": ["glm-5.2"],
    "claude-sonnet-5": ["glm-5.2", "deepseek-v4-pro"],
}

GROQ_MODELS = {
    "llama-3.3-70b-instruct": "llama-3.3-70b-versatile",
    "gpt-oss-120b": "openai/gpt-oss-120b",
}

GROQ_MODEL_FALLBACKS = {
    "llama-3.3-70b-instruct": ["llama-3.3-70b-instruct"],
    "gpt-oss-120b": ["gpt-oss-120b"],
    "gemini-2.0-flash": ["gpt-oss-120b", "llama-3.3-70b-instruct"],
    "gemini-2.5-flash": ["gpt-oss-120b", "llama-3.3-70b-instruct"],
    "mistral-large-2": ["gpt-oss-120b", "llama-3.3-70b-instruct"],
    "mistral-large-3": ["gpt-oss-120b", "llama-3.3-70b-instruct"],
    "claude-3.5-sonnet": ["gpt-oss-120b", "llama-3.3-70b-instruct"],
    "claude-sonnet-4.6": ["gpt-oss-120b", "llama-3.3-70b-instruct"],
    "nemotron-3-ultra": ["gpt-oss-120b", "llama-3.3-70b-instruct"],
    "nemotron-3-super": ["gpt-oss-120b", "llama-3.3-70b-instruct"],
}

DEEPINFRA_MODELS = {
    "llama-3.3-70b-instruct": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "deepseek-v3": "deepseek-ai/DeepSeek-V3",
}

DEEPINFRA_MODEL_FALLBACKS = {
    "llama-3.3-70b-instruct": ["llama-3.3-70b-instruct"],
    "gemini-2.0-flash": ["llama-3.3-70b-instruct", "deepseek-v3"],
    "gemini-2.5-flash": ["llama-3.3-70b-instruct", "deepseek-v3"],
    "mistral-large-2": ["llama-3.3-70b-instruct", "deepseek-v3"],
    "mistral-large-3": ["llama-3.3-70b-instruct", "deepseek-v3"],
    "claude-3.5-sonnet": ["llama-3.3-70b-instruct", "deepseek-v3"],
    "claude-sonnet-4.6": ["llama-3.3-70b-instruct", "deepseek-v3"],
    "nemotron-3-ultra": ["llama-3.3-70b-instruct"],
    "nemotron-3-super": ["llama-3.3-70b-instruct"],
    "gpt-oss-120b": ["llama-3.3-70b-instruct"],
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
_AIML_FALLBACK_ENABLED = _os.environ.get("AIML_FALLBACK_ENABLED", "").lower() in {"1", "true", "yes", "on"}
_HAS_AIML_KEY = bool(_os.environ.get("AIML_API_KEY")) and _AIML_FALLBACK_ENABLED
_GROQ_FALLBACK_ENABLED = _os.environ.get("GROQ_FALLBACK_ENABLED", "").lower() in {"1", "true", "yes", "on"}
_HAS_GROQ_KEY = bool(_os.environ.get("GROQ_API_KEY")) and _GROQ_FALLBACK_ENABLED
_DEEPINFRA_FALLBACK_ENABLED = _os.environ.get("DEEPINFRA_FALLBACK_ENABLED", "").lower() in {"1", "true", "yes", "on"}
_HAS_DEEPINFRA_KEY = bool(_os.environ.get("DEEPINFRA_API_KEY")) and _DEEPINFRA_FALLBACK_ENABLED

# Active API base (auto-detect: OpenRouter if key set, else Ollama)
API_BASE = OPENROUTER_API_BASE if _USE_OPENROUTER else OLLAMA_API_BASE

# LiteLLM proxy port
LITELLM_PORT = 4000
