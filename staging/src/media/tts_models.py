"""
Temuclaude TTS Model Pools

All TTS model configurations with verified pricing (July 2026).
Pricing verified from aimlapi.com individual model pages.

Sources:
  - AIML API model pages (aimlapi.com/models/{slug})
  - AIML API /v1/models endpoint (26 TTS models confirmed)
  - Hume Octave 2 page (71% preference over ElevenLabs in blind test)
  - MiniMax Speech 2.6 page (studio-grade prosody, instant cloning)
"""

# =============================================================================
# TTS MODEL POOLS
# =============================================================================

# --- Premium Swarm (best-of-3, 10% of requests) ---
# These are the frontier TTS models. Running 3 in parallel and judging
# picks the best output for any given text.
TTS_PREMIUM_POOL = [
    {
        "id": "elevenlabs/v3_alpha",
        "cost_per_1k_chars": 0.234,
        "provider": "aiml",
        "role": "most expressive, voice cloning, conversational AI",
        "strengths": ["expressive", "voice_cloning", "conversational", "multilingual"],
        "languages": 32,
        "latency_ms": 300,
    },
    {
        "id": "hume/octave-2",
        "cost_per_1k_chars": 0.078,
        "provider": "aiml",
        "role": "LLM-powered emotion understanding, 71% preferred over ElevenLabs",
        "strengths": ["emotion", "llm_understanding", "naturalness", "low_latency"],
        "languages": 11,
        "latency_ms": 100,
    },
    {
        "id": "minimax/speech-2.6-hd",
        "cost_per_1k_chars": 0.13,
        "provider": "aiml",
        "role": "studio-grade prosody, breath control, instant cloning",
        "strengths": ["prosody", "voice_cloning", "naturalness", "multi_voice"],
        "languages": 15,
        "latency_ms": 200,
    },
]

# --- Standard Swarm (best-of-3, 30% of requests) ---
TTS_STANDARD_POOL = [
    {
        "id": "elevenlabs/eleven_turbo_v2_5",
        "cost_per_1k_chars": 0.117,
        "provider": "aiml",
        "role": "near real-time, good quality",
        "strengths": ["fast", "quality", "multilingual"],
        "languages": 32,
        "latency_ms": 150,
    },
    {
        "id": "minimax/speech-2.6-turbo",
        "cost_per_1k_chars": 0.078,
        "provider": "aiml",
        "role": "fast, expressive",
        "strengths": ["fast", "expressive", "multi_voice"],
        "languages": 15,
        "latency_ms": 100,
    },
    {
        "id": "microsoft/vibevoice-7b",
        "cost_per_1k_chars": 0.052,
        "provider": "aiml",
        "role": "customizable personas, emotional nuance",
        "strengths": ["customizable", "emotion", "naturalness"],
        "languages": 10,
        "latency_ms": 250,
    },
]

# --- Draft Tier (single model, 60% of requests) ---
TTS_DRAFT_POOL = [
    {
        "id": "alibaba/qwen3-tts-flash",
        "cost_per_1k_chars": 0.013,
        "provider": "aiml",
        "role": "119 languages, ultra-low latency, cheapest decent quality",
        "strengths": ["fast", "multilingual", "value"],
        "languages": 119,
        "latency_ms": 80,
    },
]

# --- Budget Tier (when cost is the priority) ---
TTS_BUDGET_POOL = [
    {
        "id": "openai/gpt-4o-mini-tts",
        "cost_per_1k_chars": 0.00078,
        "provider": "aiml",
        "role": "cheapest overall, emotional intonation",
        "strengths": ["cheap", "emotion", "quality"],
        "languages": 10,
        "latency_ms": 200,
    },
    {
        "id": "openai/tts-1",
        "cost_per_1k_chars": 0.0195,
        "provider": "aiml",
        "role": "reliable, multi-voice",
        "strengths": ["reliable", "multi_voice"],
        "languages": 10,
        "latency_ms": 300,
    },
]

# --- Unique Capability Models (routing, always single model) ---
TTS_UNIQUE_POOLS = {
    "voice_cloning": [
        {
            "id": "elevenlabs/v3_alpha",
            "cost_per_1k_chars": 0.234,
            "provider": "aiml",
            "role": "best voice cloning quality",
            "strengths": ["voice_cloning"],
        },
        {
            "id": "minimax/speech-2.6-hd",
            "cost_per_1k_chars": 0.13,
            "provider": "aiml",
            "role": "instant voice cloning",
            "strengths": ["voice_cloning", "instant"],
        },
    ],
    "ultra_low_latency": [
        {
            "id": "deepgram/aura-2",
            "cost_per_1k_chars": 0.039,
            "provider": "aiml",
            "role": "sub-200ms TTFB, enterprise-grade",
            "strengths": ["low_latency", "enterprise"],
            "latency_ms": 200,
        },
    ],
    "119_languages": [
        {
            "id": "alibaba/qwen3-tts-flash",
            "cost_per_1k_chars": 0.013,
            "provider": "aiml",
            "role": "119 languages — most of any TTS model",
            "strengths": ["multilingual"],
        },
    ],
    "emotion_understanding": [
        {
            "id": "hume/octave-2",
            "cost_per_1k_chars": 0.078,
            "provider": "aiml",
            "role": "LLM-powered emotional understanding — interprets emotional intent",
            "strengths": ["emotion", "llm_understanding"],
        },
    ],
    "microsoft_prosody": [
        {
            "id": "microsoft/mai-voice-2",
            "cost_per_1k_chars": 0.0286,  # $28.60/1M tokens ≈ $0.0286/1k chars
            "provider": "aiml",
            "role": "Microsoft Azure AI Speech, natural prosody, multiple styles",
            "strengths": ["prosody", "naturalness", "multi_style"],
        },
    ],
    "highest_quality": [
        {
            "id": "elevenlabs/eleven_multilingual_v2",
            "cost_per_1k_chars": 0.234,
            "provider": "aiml",
            "role": "premium quality, same voice across languages",
            "strengths": ["quality", "multilingual", "voice_consistency"],
        },
    ],
}

# =============================================================================
# JUDGE POOL — same as image/video, but with audio scoring prompts
# =============================================================================
# Reuse the same 3 judges from the media module
# They can score TTS based on text analysis + audio metadata
# For premium tier, Gemini 3 Flash can actually listen to audio

TTS_JUDGE_POOL = [
    {
        "id": "google/gemini-3-flash-preview",
        "openrouter_id": "google/gemini-3-flash-preview",
        "role": "audio understanding — can listen to generated speech",
        "weight": 1.0,
    },
    {
        "id": "minimax/minimax-m3",
        "openrouter_id": "minimax/minimax-m3",
        "role": "text analysis — scores pronunciation, pacing, text rendering",
        "weight": 0.9,
    },
    {
        "id": "z-ai/glm-5.2",
        "openrouter_id": "z-ai/glm-5.2",
        "role": "text analysis — cheap judge for draft tier",
        "weight": 0.8,
    },
]

# =============================================================================
# PROMPT ENHANCER — LLM for TTS prompt rewriting
# =============================================================================
TTS_PROMPT_ENHANCER_MODEL = {
    "id": "z-ai/glm-5.2",
    "openrouter_id": "z-ai/glm-5.2",
    "role": "prompt rewriting for TTS — adds voice/style/emotion guidance",
}

# =============================================================================
# ROUTING FUNCTIONS
# =============================================================================

def get_tts_pool(tier: str, task_type: str = "general_tts") -> list:
    """Get the appropriate TTS model pool for a tier and task type.

    Args:
        tier: "draft", "budget", "standard", or "premium"
        task_type: Classified TTS task type

    Returns:
        List of model configs to run in parallel (best-of-N)
    """
    # Unique capability routing
    unique_mapping = {
        "voice_cloning": "voice_cloning",
        "ultra_low_latency": "ultra_low_latency",
        "119_languages": "119_languages",
        "emotion_understanding": "emotion_understanding",
        "microsoft_prosody": "microsoft_prosody",
        "highest_quality": "highest_quality",
    }

    for task_key, pool_key in unique_mapping.items():
        if task_type == task_key:
            return TTS_UNIQUE_POOLS[pool_key]

    # General routing by tier
    if tier == "draft":
        return TTS_DRAFT_POOL
    elif tier == "budget":
        return TTS_BUDGET_POOL[:1]  # single cheapest
    elif tier == "standard":
        return TTS_STANDARD_POOL
    elif tier == "premium":
        return TTS_PREMIUM_POOL
    else:
        return TTS_STANDARD_POOL  # default


def get_tts_judge_pool() -> list:
    """Get the list of judge models for TTS multi-judge consensus."""
    return TTS_JUDGE_POOL


def get_tts_prompt_enhancer() -> dict:
    """Get the model used for TTS prompt enhancement."""
    return TTS_PROMPT_ENHANCER_MODEL


# =============================================================================
# COST ESTIMATION
# =============================================================================

def estimate_tts_cost(pool: list, text_length: int = 1000) -> float:
    """Estimate total cost of running all models in a pool for given text length.

    Args:
        pool: List of model configs
        text_length: Character count of the text to synthesize

    Returns:
        Total cost in USD
    """
    k_chars = text_length / 1000.0
    return sum(m.get("cost_per_1k_chars", 0.0) * k_chars for m in pool)


# =============================================================================
# TIER CONFIGURATION
# =============================================================================

# Quality thresholds for TTS quality gate
TTS_QUALITY_THRESHOLDS = {
    "general_tts": 7.0,
    "emotion_understanding": 8.0,
    "voice_cloning": 8.0,
    "ultra_low_latency": 6.5,
    "119_languages": 7.0,
    "microsoft_prosody": 7.5,
    "highest_quality": 8.0,
    "narration": 7.5,
    "dialogue": 8.0,
    "audiobook": 8.0,
    "commercial": 8.0,
    "gaming": 7.0,
}

# Maximum iterations for the Reflexion loop
TTS_MAX_REFINE_ITERATIONS = 2  # TTS is faster to regenerate than images

# Cache TTL for TTS results (1 hour)
TTS_CACHE_TTL_SECONDS = 3600

# Available voices per model (for routing)
# These are the standard OpenAI voices — many AIML models support these or their own
COMMON_VOICES = ["alloy", "ash", "ballad", "coral", "echo", "fable", "nova", "onyx", "sage", "shimmer", "verse"]