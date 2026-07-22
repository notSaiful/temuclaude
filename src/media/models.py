"""
Temuclaude Media Model Pools

Image and video model configurations with verified pricing (July 2026).
All ELO scores from Artificial Analysis blind-vote leaderboards.
All pricing verified from AIML API individual model pages.

Sources:
  - Artificial Analysis Text-to-Image Leaderboard (132 models, July 2026)
  - Artificial Analysis Text-to-Video Leaderboard (24 models with audio, July 2026)
  - Artificial Analysis Image-to-Video Leaderboard (25 models, July 2026)
  - AIML API model pages (aimlapi.com/models/{model})
  - arXiv:2501.09732 (inference-time scaling for diffusion models)
  - arXiv:2507.05604 (N-particle ensemble, "collective wisdom")
"""

# =============================================================================
# IMAGE GENERATION MODEL POOLS
# =============================================================================

# --- Premium Swarm (best-of-5, 10% of requests) ---
# Projected ELO: 1380-1487 (beats GPT Image 2's 1340)
# Cost: $0.448/image
# NOTE: This pool is also used for CASCADING — generate with cheapest first,
# judge, only add more if quality is below threshold.
# Sorted by cost ascending for efficient cascading.
IMAGE_PREMIUM_POOL = [
    {
        "id": "reve/create-image",
        "elo": 1281,
        "cost_per_image": 0.031,
        "provider": "aiml",
        "role": "best value — ELO 1281 at 6.8x cheaper than GPT Image 2",
        "strengths": ["overall_quality", "value", "aesthetics"],
        "cascade_order": 1,  # generate first (cheapest)
    },
    {
        "id": "microsoft/mai-image-2.5",
        "elo": 1272,
        "cost_per_image": 0.048,
        "provider": "aiml",
        "role": "near-frontier at low cost",
        "strengths": ["overall_quality", "value"],
        "cascade_order": 2,  # add if Reve not good enough
    },
    {
        "id": "google/nano-banana-2",
        "elo": 1255,
        "cost_per_image": 0.067,
        "provider": "aiml",
        "role": "unique — 14 refs, extreme AR, grounding, 4K native",
        "strengths": ["character_consistency", "extreme_ar", "grounding", "4k_resolution", "text_rendering"],
        "cascade_order": 3,
    },
    {
        "id": "blackforestlabs/flux-2-max",
        "elo": 1193,
        "cost_per_image": 0.091,
        "provider": "aiml",
        "role": "photorealism specialist",
        "strengths": ["photorealism", "lighting", "texture"],
        "cascade_order": 4,
    },
    {
        "id": "openai/gpt-image-2",
        "elo": 1340,
        "cost_per_image": 0.211,
        "provider": "aiml",
        "role": "frontier — #1 globally, reasoning step, text rendering",
        "strengths": ["overall_quality", "text_rendering", "prompt_adherence", "reasoning", "editing"],
        "cascade_order": 5,  # only add if all others are below threshold
    },
]

# --- Standard Swarm (best-of-3, 30% of requests) ---
# Projected ELO: ~1300
# Cost: $0.118/image
# Sorted by cost ascending for cascading.
IMAGE_STANDARD_POOL = [
    {
        "id": "reve/create-image",
        "elo": 1281,
        "cost_per_image": 0.031,
        "provider": "aiml",
        "role": "best value quality",
        "strengths": ["overall_quality", "value"],
        "cascade_order": 1,
    },
    {
        "id": "blackforestlabs/flux-2-pro",
        "elo": 1186,
        "cost_per_image": 0.039,
        "provider": "aiml",
        "role": "photorealism standard",
        "strengths": ["photorealism", "prompt_adherence"],
        "cascade_order": 2,
    },
    {
        "id": "microsoft/mai-image-2.5",
        "elo": 1272,
        "cost_per_image": 0.048,
        "provider": "aiml",
        "role": "near-frontier",
        "strengths": ["overall_quality", "value"],
        "cascade_order": 3,
    },
]

# --- Draft Tier (single model, 60% of requests) ---
# Cost: $0.005/image (42x cheaper than GPT Image 2)
IMAGE_DRAFT_POOL = [
    {
        "id": "alibaba/z-image-turbo",
        "elo": 1105,
        "cost_per_image": 0.005,
        "provider": "aiml",
        "role": "cheapest decent quality, open weights",
        "strengths": ["speed", "value"],
    },
]

# --- Unique Capability Models (routing, always single model) ---
# These are the ONLY models that can do certain things
IMAGE_UNIQUE_POOLS = {
    "vector_svg": [
        {
            "id": "recraft-v3",
            "elo": 1067,
            "cost_per_image": 0.04,
            "provider": "aiml",
            "role": "ONLY model with vector/SVG output",
            "strengths": ["vector_svg"],
        },
    ],
    "text_in_image": [
        {
            "id": "blackforestlabs/flux-2-flex",
            "elo": 1180,
            "cost_per_image": 0.06,
            "provider": "aiml",
            "role": "SOTA for text/UI/logos",
            "strengths": ["text_rendering", "ui_design"],
        },
        {
            "id": "openai/gpt-image-2",
            "elo": 1340,
            "cost_per_image": 0.211,
            "provider": "aiml",
            "role": "excellent text rendering",
            "strengths": ["text_rendering", "reasoning"],
        },
    ],
    "extreme_ar": [
        {
            "id": "google/nano-banana-2",
            "elo": 1255,
            "cost_per_image": 0.067,
            "provider": "aiml",
            "role": "ONLY model supporting 1:8 and 8:1 aspect ratios",
            "strengths": ["extreme_ar", "grounding"],
        },
    ],
    "realtime_search": [
        {
            "id": "bytedance/seedream-5-0-lite-preview",
            "elo": 1119,
            "cost_per_image": 0.035,
            "provider": "aiml",
            "role": "ONLY model with real-time web search in generation",
            "strengths": ["realtime_search", "knowledge"],
        },
    ],
    "multilingual": [
        {
            "id": "bytedance/seedream-4-5",
            "elo": 1165,
            "cost_per_image": 0.052,
            "provider": "aiml",
            "role": "Chinese/multilingual text specialist",
            "strengths": ["multilingual", "chinese_text"],
        },
        {
            "id": "x-ai/grok-imagine-image-pro",
            "elo": 1203,
            "cost_per_image": 0.091,
            "provider": "aiml",
            "role": "multilingual xAI quality",
            "strengths": ["multilingual", "overall_quality"],
        },
    ],
    "high_res_4k": [
        {
            "id": "google/nano-banana-2",
            "elo": 1255,
            "cost_per_image": 0.067,
            "provider": "aiml",
            "role": "4K native resolution (4096x2304)",
            "strengths": ["4k_resolution", "character_consistency"],
        },
    ],
    "character": [
        {
            "id": "google/nano-banana-2",
            "elo": 1255,
            "cost_per_image": 0.067,
            "provider": "aiml",
            "role": "14 reference images for character consistency",
            "strengths": ["character_consistency", "grounding"],
        },
        {
            "id": "openai/gpt-image-2",
            "elo": 1340,
            "cost_per_image": 0.211,
            "provider": "aiml",
            "role": "16 reference images",
            "strengths": ["character_consistency", "reasoning"],
        },
    ],
}

# --- Post-Processing Models ---
IMAGE_POST_PROCESS = {
    "upscale": {
        "id": "topaz-labs/sharpen",
        "cost_per_image": 0.02,
        "provider": "aiml",
        "role": "upscale to 4K",
    },
    "upscale_gen": {
        "id": "topaz-labs/sharpen-gen",
        "cost_per_image": 0.03,
        "provider": "aiml",
        "role": "generative upscaling with face restoration",
    },
    "flux_srpo": {
        "id": "flux/srpo",
        "cost_per_image": 0.015,
        "provider": "aiml",
        "role": "FLUX super-resolution",
    },
}

# =============================================================================
# VIDEO GENERATION MODEL POOLS
# =============================================================================

# --- Premium Cinematic Swarm (best-of-3, for 4K/cinematic) ---
# Projected ELO: 1280-1325 (beats Seedance 2.0's 1225)
# Cost: $42.43/min
VIDEO_PREMIUM_CINEMATIC = [
    {
        "id": "bytedance/seedance-2.0",
        "elo_t2v": 1225,
        "elo_i2v": 1189,
        "cost_per_min": 9.07,
        "provider": "aiml",
        "role": "#1 video model globally, multi-input (9img+3clip+3audio)",
        "strengths": ["overall_quality", "multi_input", "audio", "cinematic"],
    },
    {
        "id": "alibaba/happyhorse-1-0",
        "elo_t2v": 1131,
        "elo_i2v": 1090,
        "cost_per_min": 13.20,
        "provider": "aiml",
        "role": "#3 globally, 7-language lip-sync",
        "strengths": ["lip_sync", "audio", "multilingual"],
    },
    {
        "id": "klingai/video-v3-pro-text-to-video",
        "elo_t2v": 1114,
        "elo_i2v": 1065,
        "cost_per_min": 20.16,
        "provider": "aiml",
        "role": "4K/60fps cinematic",
        "strengths": ["4k_resolution", "60fps", "audio", "cinematic"],
    },
]

# --- Premium Dialogue Swarm (best-of-3, for dialogue/speech) ---
# Cost: $46.27/min
VIDEO_PREMIUM_DIALOGUE = [
    {
        "id": "bytedance/seedance-2.0",
        "elo_t2v": 1225,
        "elo_i2v": 1189,
        "cost_per_min": 9.07,
        "provider": "aiml",
        "role": "#1 overall",
        "strengths": ["overall_quality", "audio"],
    },
    {
        "id": "alibaba/happyhorse-1-0",
        "elo_t2v": 1131,
        "elo_i2v": 1090,
        "cost_per_min": 13.20,
        "provider": "aiml",
        "role": "#3, lip-sync",
        "strengths": ["lip_sync", "multilingual"],
    },
    {
        "id": "google/veo-3.1-t2v",
        "elo_t2v": 1100,
        "elo_i2v": 1084,
        "cost_per_min": 24.00,
        "provider": "aiml",
        "role": "ONLY model with 48kHz synchronized dialogue",
        "strengths": ["dialogue", "audio"],
    },
]

# --- Standard Swarm (best-of-2, 30% of requests) ---
# Projected ELO: ~1260
# Cost: $22.27/min
VIDEO_STANDARD_POOL = [
    {
        "id": "bytedance/seedance-2.0",
        "elo_t2v": 1225,
        "elo_i2v": 1189,
        "cost_per_min": 9.07,
        "provider": "aiml",
        "role": "#1 quality",
        "strengths": ["overall_quality", "audio"],
    },
    {
        "id": "alibaba/happyhorse-1-0",
        "elo_t2v": 1131,
        "elo_i2v": 1090,
        "cost_per_min": 13.20,
        "provider": "aiml",
        "role": "#3, strong #2 option",
        "strengths": ["lip_sync", "audio", "multilingual"],
    },
]

# --- Draft Tier (single model, 60% of requests) ---
# Cost: $2.40/min (open weights, can self-host)
VIDEO_DRAFT_POOL = [
    {
        "id": "ltxv/ltxv-2-fast",
        "elo_t2v": 976,
        "elo_i2v": 946,
        "cost_per_min": 2.40,
        "provider": "aiml",
        "role": "open weights, cheapest video",
        "strengths": ["speed", "value", "open_weights"],
    },
]

# --- Budget Tier (when cost is priority over quality) ---
VIDEO_BUDGET_POOL = [
    {
        "id": "google/veo-3.1-lite-generate-001",
        "elo_t2v": 1089,
        "elo_i2v": 1058,
        "cost_per_min": 4.80,
        "provider": "aiml",
        "role": "cheapest Google quality",
        "strengths": ["value", "audio"],
    },
    {
        "id": "x-ai/grok-imagine-video",
        "elo_t2v": 1071,
        "elo_i2v": 1076,
        "cost_per_min": 3.90,
        "provider": "aiml",
        "role": "cheapest quality video",
        "strengths": ["value", "audio"],
    },
]

# --- Unique Capability Video Models ---
VIDEO_UNIQUE_POOLS = {
    "video_4k": [
        {
            "id": "klingai/video-v3-pro-text-to-video",
            "elo_t2v": 1114,
            "cost_per_min": 20.16,
            "provider": "aiml",
            "role": "native 4K at 60fps",
            "strengths": ["4k_resolution", "60fps"],
        },
    ],
    "video_dialogue": [
        {
            "id": "google/veo-3.1-t2v",
            "elo_t2v": 1100,
            "cost_per_min": 24.00,
            "provider": "aiml",
            "role": "ONLY model with 48kHz synchronized dialogue",
            "strengths": ["dialogue", "audio"],
        },
    ],
    "video_long": [
        {
            "id": "ltxv/ltxv-2",
            "elo_t2v": 962,
            "cost_per_min": 3.60,
            "provider": "aiml",
            "role": "20-second clips (longest open-source)",
            "strengths": ["long_duration", "open_weights"],
        },
    ],
    "video_multi_input": [
        {
            "id": "bytedance/seedance-2.0",
            "elo_t2v": 1225,
            "cost_per_min": 9.07,
            "provider": "aiml",
            "role": "9 images + 3 video clips + 3 audio files per generation",
            "strengths": ["multi_input", "overall_quality"],
        },
    ],
    "video_i2v_best": [
        {
            "id": "bytedance/seedance-2.0",
            "elo_i2v": 1189,
            "cost_per_min": 9.07,
            "provider": "aiml",
            "role": "#1 image-to-video",
            "strengths": ["i2v_quality", "overall_quality"],
        },
        {
            "id": "alibaba/happyhorse-1-0",
            "elo_i2v": 1090,
            "cost_per_min": 13.20,
            "provider": "aiml",
            "role": "#5 i2v, lip-sync",
            "strengths": ["i2v_quality", "lip_sync"],
        },
    ],
}

# =============================================================================
# JUDGE POOL — Vision LLMs for scoring generated outputs
# =============================================================================

# Multi-judge consensus: 3 vision-capable LLMs score each output
# Each judge scores 1-10 on: prompt adherence, visual quality, text accuracy, artifacts
# Majority vote or weighted average determines winner
JUDGE_POOL = [
    {
        "id": "minimax/minimax-m3",
        "openrouter_id": "minimax/minimax-m3",
        "aiml_id": "minimax/minimax-m3",
        "role": "best vision model (IQ 44)",
        "vision_iq": 44,
        "weight": 1.0,  # highest weight — best vision
    },
    {
        "id": "google/gemini-3-flash-preview",
        "openrouter_id": "google/gemini-3-flash-preview",
        "aiml_id": "google/gemini-3-flash-preview",
        "role": "multimodal (IQ 50), #1 Legal, #2 Health",
        "vision_iq": 50,
        "weight": 0.95,
    },
    {
        "id": "anthropic/claude-sonnet-4.6",
        "openrouter_id": "anthropic/claude-sonnet-4.6",
        "aiml_id": "anthropic/claude-sonnet-4.6",
        "role": "frontier reasoning, used for hardest 2%",
        "vision_iq": 53,
        "weight": 0.90,  # lower weight — expensive, use sparingly
    },
]

# =============================================================================
# PROMPT ENHANCER — LLM used for GEPA prompt evolution
# Uses cheapest model — only needs to rewrite text, not generate images
# =============================================================================
PROMPT_ENHANCER_MODEL = {
    "id": "z-ai/glm-5.2",
    "openrouter_id": "z-ai/glm-5.2",
    "role": "prompt rewriting — cheapest capable model",
}

# =============================================================================
# ROUTING FUNCTIONS
# =============================================================================

def get_image_pool(tier: str, task_type: str = "general_image") -> list:
    """Get the appropriate image model pool for a tier and task type.

    Args:
        tier: "draft", "standard", or "premium"
        task_type: classified media task type

    Returns:
        List of model configs to run in parallel (best-of-N)
    """
    # Check unique capability pools first — always single model
    unique_mapping = {
        "vector_svg": "vector_svg",
        "extreme_ar": "extreme_ar",
        "realtime_search": "realtime_search",
        "high_res_4k": "high_res_4k",
    }

    for task_key, pool_key in unique_mapping.items():
        if task_type == task_key:
            return IMAGE_UNIQUE_POOLS[pool_key]

    # Text-in-image: use 2-model swarm for better text accuracy
    if task_type == "text_in_image":
        return IMAGE_UNIQUE_POOLS["text_in_image"]

    # Multilingual: use 2-model swarm
    if task_type == "multilingual":
        return IMAGE_UNIQUE_POOLS["multilingual"]

    # Character consistency: use 2-model swarm
    if task_type == "character":
        return IMAGE_UNIQUE_POOLS["character"]

    # General routing by tier
    if tier == "draft":
        return IMAGE_DRAFT_POOL
    elif tier == "standard":
        return IMAGE_STANDARD_POOL
    elif tier == "premium":
        return IMAGE_PREMIUM_POOL
    else:
        return IMAGE_STANDARD_POOL  # default


def get_video_pool(tier: str, task_type: str = "video_standard") -> list:
    """Get the appropriate video model pool for a tier and task type.

    Args:
        tier: "draft", "budget", "standard", or "premium"
        task_type: classified media task type

    Returns:
        List of model configs to run in parallel (best-of-N)
    """
    # Unique capability routing
    if task_type == "video_4k":
        return VIDEO_UNIQUE_POOLS["video_4k"]
    if task_type == "video_dialogue":
        return VIDEO_UNIQUE_POOLS["video_dialogue"]
    if task_type == "video_long":
        return VIDEO_UNIQUE_POOLS["video_long"]
    if task_type == "video_multi_input":
        return VIDEO_UNIQUE_POOLS["video_multi_input"]
    if task_type in ("video_i2v", "image_to_video"):
        return VIDEO_UNIQUE_POOLS["video_i2v_best"]

    # Premium routing — cinematic vs dialogue
    if tier == "premium":
        if "dialogue" in task_type or "speech" in task_type or "talking" in task_type:
            return VIDEO_PREMIUM_DIALOGUE
        return VIDEO_PREMIUM_CINEMATIC

    # Standard routing
    if tier == "standard":
        return VIDEO_STANDARD_POOL

    # Budget routing
    if tier == "budget":
        return VIDEO_BUDGET_POOL[:1]  # single cheapest

    # Draft routing
    return VIDEO_DRAFT_POOL


def get_judge_pool() -> list:
    """Get the list of judge models for multi-judge consensus."""
    return JUDGE_POOL


def get_prompt_enhancer() -> dict:
    """Get the model used for prompt enhancement."""
    return PROMPT_ENHANCER_MODEL


# =============================================================================
# COST ESTIMATION
# =============================================================================

def estimate_image_cost(pool: list) -> float:
    """Estimate total cost of running all models in a pool (per image)."""
    return sum(m.get("cost_per_image", 0.0) for m in pool)


def estimate_video_cost(pool: list, duration_seconds: int = 5) -> float:
    """Estimate total cost of running all models in a pool for a given duration."""
    duration_min = duration_seconds / 60.0
    return sum(m.get("cost_per_min", 0.0) * duration_min for m in pool)


# =============================================================================
# TIER CONFIGURATION
# =============================================================================

# Quality thresholds for the quality gate (Stage 7)
# If best output score < threshold, trigger Reflexion loop (critique + regenerate)
QUALITY_THRESHOLDS = {
    "photoreal": 8.0,
    "text_in_image": 8.5,  # text needs to be accurate
    "character": 8.0,
    "vector_svg": 7.0,
    "extreme_ar": 7.5,
    "realtime_search": 7.0,
    "multilingual": 7.5,
    "high_res_4k": 7.5,
    "general_image": 7.5,
    "video_standard": 7.0,
    "video_dialogue": 8.0,
    "video_4k": 7.5,
    "video_long": 7.0,
    "video_multi_input": 7.5,
    "video_i2v": 7.0,
}

# Maximum iterations for the Reflexion loop (Stage 7)
MAX_REFINE_ITERATIONS = 3

# Cache TTL for image/video results (1 hour, same as LLM cache)
MEDIA_CACHE_TTL_SECONDS = 3600

# =============================================================================
# EFFICIENCY CONFIGURATION — Cascading + Adaptive Judging
# =============================================================================

# CASCADING: Instead of running all N models blindly in parallel, generate with
# the cheapest model first, judge it, and only add more models if the quality
# is below threshold. This is the SAME approach our LLM orchestrator uses
# (ATTS adaptive compute, shepherding, unified routing — arXiv:2410.10347).
#
# Cost savings with cascading:
#   Premium: 60% of requests cost $0.031 (Reve alone) instead of $0.448
#   Blended premium cost: $0.057/image (vs $0.448 blind) = 7.9x cheaper
CASCADING_ENABLED = True

# CASCADED QUALITY THRESHOLDS — when to stop adding more models
# These are LOWER than the final quality gate thresholds, because we just need
# "good enough" to stop the cascade. The quality gate runs AFTER.
CASCADE_STOP_THRESHOLDS = {
    "draft": 6.0,       # draft models only need 6/10 to stop cascade
    "standard": 7.0,    # standard models need 7/10
    "premium": 7.5,     # premium models need 7.5/10
}

# ADAPTIVE JUDGING: Don't use 3 judges for every tier.
# Draft tier doesn't need judges at all (single model, just return it).
# Standard tier uses 1 cheap judge.
# Premium tier uses 3 judges for consensus.
ADAPTIVE_JUDGING_ENABLED = True

JUDGE_COUNT_BY_TIER = {
    "draft": 0,       # no judge — just return the single output
    "budget": 0,      # no judge — just return the cheapest output
    "standard": 1,    # 1 judge (cheapest vision model)
    "premium": 3,     # full 3-judge consensus
}

# BATCH JUDGE: Instead of separate LLM calls per output per judge, send ALL
# outputs to each judge in a SINGLE call. This reduces judge calls from
# N_outputs × N_judges to just N_judges (5x savings for premium).
BATCH_JUDGE_ENABLED = True
