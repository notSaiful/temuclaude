"""
Temuclaude Media Orchestration Module

Full 10-stage pipeline for image and video generation:
  1. Semantic Cache
  2. Intent Classification
  3. Tier Determination (ATTS adaptive)
  4. Prompt Enhancement (GEPA)
  5. Parallel Generation (best-of-N)
  6. Multi-Judge Consensus (3 vision LLMs)
  7. Quality Gate (USVA + Reflexion)
  8. Post-Processing (upscale, face restore)
  9. Memory Bank (learn win rates)
  10. Return

Usage:
    from src.media import MediaOrchestrator

    mo = MediaOrchestrator(call_llm_func=your_llm_caller)
    result = await mo.generate_image("a photorealistic cat")
    result = await mo.generate_video("a cinematic sunset video")
    result = await mo.generate("a video of a dog")  # auto-detect
"""

from .orchestrator import MediaOrchestrator
from .intent import classify_media_task, determine_media_tier, is_video_prompt
from .models import (
    IMAGE_PREMIUM_POOL, IMAGE_STANDARD_POOL, IMAGE_DRAFT_POOL,
    IMAGE_UNIQUE_POOLS, IMAGE_POST_PROCESS,
    VIDEO_PREMIUM_CINEMATIC, VIDEO_PREMIUM_DIALOGUE, VIDEO_STANDARD_POOL,
    VIDEO_DRAFT_POOL, VIDEO_BUDGET_POOL, VIDEO_UNIQUE_POOLS,
    JUDGE_POOL, PROMPT_ENHANCER_MODEL,
    get_image_pool, get_video_pool, get_judge_pool,
    estimate_image_cost, estimate_video_cost,
    QUALITY_THRESHOLDS, MAX_REFINE_ITERATIONS,
)
from .generator import MediaGenerator
from .judge import MediaJudge
from .quality_gate import MediaQualityGate
from .post_processor import MediaPostProcessor
from .memory import MediaMemoryBank, get_memory_bank
from .media_cache import MediaCache, get_media_cache
from .prompt_enhancer import enhance_prompt, enhance_prompts_for_pool
from .providers.base import MediaProviderManager, AIMLProvider, FalProvider
from .cascading_generator import CascadingMediaGenerator

# TTS
from .tts_orchestrator import TTSOrchestrator, TTSGenerator, TTSJudge, TTSQualityGate
from .tts_provider import TTSProvider, TTSProviderManager
from .tts_intent import classify_tts_task, determine_tts_tier, get_default_voice

__all__ = [
    # Main orchestrator
    "MediaOrchestrator",
    # Components
    "MediaGenerator",
    "MediaJudge",
    "MediaQualityGate",
    "MediaPostProcessor",
    "MediaMemoryBank",
    "MediaCache",
    "MediaProviderManager",
    "AIMLProvider",
    "FalProvider",
    # Classification
    "classify_media_task",
    "determine_media_tier",
    "is_video_prompt",
    # Model pools
    "IMAGE_PREMIUM_POOL",
    "IMAGE_STANDARD_POOL",
    "IMAGE_DRAFT_POOL",
    "IMAGE_UNIQUE_POOLS",
    "IMAGE_POST_PROCESS",
    "VIDEO_PREMIUM_CINEMATIC",
    "VIDEO_PREMIUM_DIALOGUE",
    "VIDEO_STANDARD_POOL",
    "VIDEO_DRAFT_POOL",
    "VIDEO_BUDGET_POOL",
    "VIDEO_UNIQUE_POOLS",
    "JUDGE_POOL",
    "PROMPT_ENHANCER_MODEL",
    # Helpers
    "get_image_pool",
    "get_video_pool",
    "get_judge_pool",
    "estimate_image_cost",
    "estimate_video_cost",
    "get_memory_bank",
    "get_media_cache",
    "enhance_prompt",
    "enhance_prompts_for_pool",
    "QUALITY_THRESHOLDS",
    "MAX_REFINE_ITERATIONS",
    # TTS
    "TTSOrchestrator",
    "TTSGenerator",
    "TTSJudge",
    "TTSQualityGate",
    "TTSProvider",
    "TTSProviderManager",
    "classify_tts_task",
    "determine_tts_tier",
    "get_default_voice",
    "CascadingMediaGenerator",
]