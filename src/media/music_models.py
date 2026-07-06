"""
Temuclaude Music Model Pools

All music generation model configurations with verified pricing (July 2026).
Pricing verified from aimlapi.com individual model pages.
API endpoint: POST /v2/generate/audio (async — submit → poll → retrieve)

Sources:
  - AIML API model pages (aimlapi.com/models/{slug})
  - AIML API docs (docs.aimlapi.com/api-references/music-models/)
  - AIML API /v1/models endpoint (6 music models confirmed)
"""

# =============================================================================
# MUSIC MODEL POOLS
# =============================================================================

# All music models use async pattern: POST /v2/generate/audio → GET /v2/generate/audio
# Sorted by cost ascending for cascading (cheapest first)

# --- Premium Swarm (cascade: cheapest → most expensive) ---
# Used for 10% of requests where highest quality is needed
MUSIC_PREMIUM_POOL = [
    {
        "id": "minimax/music-2.0",
        "cost_per_generation": 0.0315,
        "provider": "aiml",
        "role": "fast, cost-efficient, full songs with vocals — CHEAPEST",
        "strengths": ["fast", "value", "vocals", "instrumentals"],
        "max_duration_seconds": 240,  # 4 minutes
        "supports_lyrics": True,
        "cascade_order": 1,  # generate first (cheapest)
    },
    {
        "id": "minimax/music-1.5",
        "cost_per_generation": 0.15,
        "provider": "aiml",
        "role": "long fully-arranged songs, natural vocals, ethnic instruments",
        "strengths": ["vocals", "ethnic_instruments", "long_duration", "arrangement"],
        "max_duration_seconds": 240,
        "supports_lyrics": True,
        "cascade_order": 2,
    },
    {
        "id": "minimax/music-2.6",
        "cost_per_generation": 0.20,
        "provider": "aiml",
        "role": "frontier — full structured songs, improved vocals, bass, progression",
        "strengths": ["quality", "vocals", "structure", "bass", "progression", "full_song"],
        "max_duration_seconds": 300,  # 5 minutes
        "supports_lyrics": True,
        "cascade_order": 3,
    },
]

# --- Standard Swarm (cascade: cheapest → mid-tier) ---
# Used for 30% of requests
MUSIC_STANDARD_POOL = [
    {
        "id": "minimax/music-2.0",
        "cost_per_generation": 0.0315,
        "provider": "aiml",
        "role": "fast, cost-efficient",
        "strengths": ["fast", "value", "vocals"],
        "max_duration_seconds": 240,
        "supports_lyrics": True,
        "cascade_order": 1,
    },
    {
        "id": "minimax/music-1.5",
        "cost_per_generation": 0.15,
        "provider": "aiml",
        "role": "long songs, ethnic instruments",
        "strengths": ["vocals", "ethnic_instruments", "long_duration"],
        "max_duration_seconds": 240,
        "supports_lyrics": True,
        "cascade_order": 2,
    },
]

# --- Draft Tier (single model, 60% of requests) ---
MUSIC_DRAFT_POOL = [
    {
        "id": "minimax/music-2.0",
        "cost_per_generation": 0.0315,
        "provider": "aiml",
        "role": "cheapest decent quality music generation",
        "strengths": ["fast", "value", "vocals"],
        "max_duration_seconds": 240,
        "supports_lyrics": True,
        "cascade_order": 1,
    },
]

# --- Unique Capability Models (routing, always single model) ---
MUSIC_UNIQUE_POOLS = {
    "song_cover": [
        {
            "id": "minimax/music-cover",
            "cost_per_generation": 0.195,
            "provider": "aiml",
            "role": "ONLY model that transforms existing songs into new styles (cover/remix)",
            "strengths": ["cover", "remix", "style_transfer"],
            "max_duration_seconds": 300,
            "supports_lyrics": False,  # takes source audio, not lyrics
        },
    ],
    "ethnic_instruments": [
        {
            "id": "minimax/music-1.5",
            "cost_per_generation": 0.15,
            "provider": "aiml",
            "role": "excels in diverse cultural and genre contexts with ethnic instruments",
            "strengths": ["ethnic_instruments", "cultural"],
            "max_duration_seconds": 240,
            "supports_lyrics": True,
        },
    ],
    "longest_duration": [
        {
            "id": "minimax/music-2.6",
            "cost_per_generation": 0.20,
            "provider": "aiml",
            "role": "up to 5 minutes — longest duration music generation",
            "strengths": ["long_duration", "full_song"],
            "max_duration_seconds": 300,
            "supports_lyrics": True,
        },
    ],
    "highest_quality": [
        {
            "id": "minimax/music-2.6",
            "cost_per_generation": 0.20,
            "provider": "aiml",
            "role": "frontier quality — improved vocals, bass, structured progression",
            "strengths": ["quality", "vocals", "structure"],
            "max_duration_seconds": 300,
            "supports_lyrics": True,
        },
    ],
    "custom_lyrics_structure": [
        {
            "id": "minimax/music-2.6",
            "cost_per_generation": 0.20,
            "provider": "aiml",
            "role": "supports [Intro], [Verse], [Chorus], [Bridge], [Outro] structure tags",
            "strengths": ["structure", "lyrics", "full_song"],
            "max_duration_seconds": 300,
            "supports_lyrics": True,
        },
    ],
    "eleven_quality": [
        {
            "id": "elevenlabs/eleven_music",
            "cost_per_generation": 0.20,
            "provider": "aiml",
            "role": "high-quality from text prompts — genre, mood, instruments, vocals, tempo",
            "strengths": ["quality", "genre_control", "tempo_control", "vocal_control"],
            "max_duration_seconds": 300,  # 300000ms = 5 min
            "supports_lyrics": True,  # lyrics in prompt
        },
    ],
}

# =============================================================================
# JUDGE POOL — same vision/audio LLMs for scoring music
# =============================================================================
MUSIC_JUDGE_POOL = [
    {
        "id": "google/gemini-3-flash-preview",
        "openrouter_id": "google/gemini-3-flash-preview",
        "role": "audio understanding — can listen to generated music",
        "weight": 1.0,
    },
    {
        "id": "minimax/minimax-m3",
        "openrouter_id": "minimax/minimax-m3",
        "role": "text analysis — scores prompt adherence, lyrics structure",
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
# PROMPT ENHANCER
# =============================================================================
MUSIC_PROMPT_ENHANCER_MODEL = {
    "id": "z-ai/glm-5.2",
    "openrouter_id": "z-ai/glm-5.2",
    "role": "prompt rewriting for music — adds genre/mood/instrument guidance",
}

# =============================================================================
# ROUTING FUNCTIONS
# =============================================================================

def get_music_pool(tier: str, task_type: str = "general_music") -> list:
    """Get the appropriate music model pool for a tier and task type."""
    unique_mapping = {
        "song_cover": "song_cover",
        "ethnic_instruments": "ethnic_instruments",
        "longest_duration": "longest_duration",
        "highest_quality": "highest_quality",
        "custom_lyrics_structure": "custom_lyrics_structure",
        "eleven_quality": "eleven_quality",
    }

    for task_key, pool_key in unique_mapping.items():
        if task_type == task_key:
            return MUSIC_UNIQUE_POOLS[pool_key]

    if tier == "draft":
        return MUSIC_DRAFT_POOL
    elif tier == "standard":
        return MUSIC_STANDARD_POOL
    elif tier == "premium":
        return MUSIC_PREMIUM_POOL
    else:
        return MUSIC_STANDARD_POOL


def get_music_judge_pool() -> list:
    return MUSIC_JUDGE_POOL


def get_music_prompt_enhancer() -> dict:
    return MUSIC_PROMPT_ENHANCER_MODEL


# =============================================================================
# COST ESTIMATION
# =============================================================================

def estimate_music_cost(pool: list) -> float:
    """Estimate total cost of running all models in a pool."""
    return sum(m.get("cost_per_generation", 0.0) for m in pool)


# =============================================================================
# TIER CONFIGURATION
# =============================================================================

MUSIC_QUALITY_THRESHOLDS = {
    "general_music": 7.0,
    "song_cover": 7.5,
    "ethnic_instruments": 7.0,
    "longest_duration": 7.0,
    "highest_quality": 8.0,
    "custom_lyrics_structure": 7.5,
    "eleven_quality": 8.0,
    "background_music": 6.5,
    "jingle": 7.0,
    "soundtrack": 7.5,
    "podcast_intro": 7.0,
}

MUSIC_MAX_REFINE_ITERATIONS = 2  # music is expensive to regenerate

MUSIC_CACHE_TTL_SECONDS = 3600  # 1 hour

# Cascade stop thresholds (lower than final quality gate — just need "good enough")
MUSIC_CASCADE_STOP_THRESHOLDS = {
    "draft": 6.0,
    "standard": 7.0,
    "premium": 7.5,
}

# Adaptive judging
MUSIC_JUDGE_COUNT_BY_TIER = {
    "draft": 0,      # no judge — just return the single output
    "standard": 1,   # 1 judge
    "premium": 3,    # full 3-judge consensus
}

# API endpoint
MUSIC_API_ENDPOINT = "https://api.aimlapi.com/v2/generate/audio"