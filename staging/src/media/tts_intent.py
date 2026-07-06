"""
Temuclaude TTS Intent Classification

Classifies TTS prompts into task types and determines quality tier.
Adapted from media/intent.py for voice generation.
"""

import re


def classify_tts_task(text: str, prompt: str = "") -> str:
    """Classify a TTS request into a task type for routing.

    Args:
        text: The text to be converted to speech
        prompt: Optional additional instructions (voice, emotion, style, etc.)

    Returns:
        Task type string for routing
    """
    combined = f"{text} {prompt}".lower()

    # Voice cloning request
    if any(k in combined for k in [
        "clone", "voice cloning", "clone this voice", "voice match",
        "replicate voice", "copy voice", "voice sample",
    ]):
        return "voice_cloning"

    # Emotion understanding — text has emotional content that needs interpretation
    if any(k in combined for k in [
        "emotion", "emotional", "expressive", "feeling", "sentiment",
        "angry", "sad", "happy", "excited", "fearful", "surprised",
        "whisper", "shout", "cry", "laugh", "sigh",
        "dramatic", "theatrical", "passionate", "tender",
    ]):
        return "emotion_understanding"

    # Ultra-low latency — real-time application
    if any(k in combined for k in [
        "real-time", "realtime", "low latency", "ultra fast", "instant",
        "live", "streaming", "interactive", "conversational ai",
        "voice agent", "ivr", "callbot", "chatbot voice",
    ]):
        return "ultra_low_latency"

    # 119 languages — rare language request
    if any(k in combined for k in [
        "119 languages", "rare language", "obscure language",
        "swahili", "tamil", "telugu", "bengali", "urdu", "punjabi",
        "amharic", "yoruba", "igbo", "zulu", "xhosa",
        "kazakh", "uzbek", "mongolian", "tibetan", "burmese",
    ]):
        return "119_languages"

    # Microsoft prosody — specific request for natural prosody
    if any(k in combined for k in [
        "prosody", "natural prosody", "microsoft", "azure", "mai-voice",
    ]):
        return "microsoft_prosody"

    # Audiobook (check before highest_quality — "audiobook" would otherwise match "book")
    if any(k in combined for k in [
        "audiobook", "audio book", "long form", "long-form",
        "chapter", "novel", "book narration",
    ]):
        return "audiobook"

    # Commercial (check before highest_quality — "commercial" would match there)
    if any(k in combined for k in [
        "commercial", "advertisement", "ad copy", "marketing",
        "promo", "trailer", "announcement",
    ]):
        return "commercial"

    # Gaming (check before dialogue — "game character" would match there)
    if any(k in combined for k in [
        "gaming", "npc voice", "game character", "game npc",
    ]):
        return "gaming"

    # Highest quality — explicit quality request (generic, checked after specific types)
    if any(k in combined for k in [
        "highest quality", "best quality", "premium", "studio quality",
        "professional", "broadcast",
    ]):
        return "highest_quality"

    # Narration
    if any(k in combined for k in [
        "narrat", "story", "article", "blog", "news reader",
        "documentary", "voiceover", "voice over",
    ]):
        return "narration"

    # Dialogue
    if any(k in combined for k in [
        "dialogue", "conversation", "character voice",
        "roleplay", "drama",
    ]):
        return "dialogue"

    return "general_tts"


def determine_tts_tier(text: str, task_type: str, explicit_tier: str = None) -> str:
    """Determine quality tier for TTS generation.

    Tiers:
      - draft: single cheap model (60% of requests, $0.013/1k chars)
      - budget: single cheapest model (for cost-sensitive requests)
      - standard: best-of-3 models (30% of requests, $0.247/1k chars)
      - premium: best-of-3 frontier models (10% of requests, $0.442/1k chars)

    Args:
        text: Text to synthesize
        task_type: Classified task type
        explicit_tier: If user explicitly requests a tier

    Returns:
        Tier string
    """
    if explicit_tier and explicit_tier in ("draft", "budget", "standard", "premium"):
        return explicit_tier

    char_count = len(text)

    # Unique capability tasks always use their specific model
    unique_tasks = {
        "voice_cloning", "ultra_low_latency", "119_languages",
        "emotion_understanding", "microsoft_prosody", "highest_quality",
    }
    if task_type in unique_tasks:
        return "premium"

    # Very short text → draft (quick, cheap)
    if char_count <= 100 and task_type == "general_tts":
        return "draft"

    # Long text (audiobook, narration) → standard (good quality, reasonable cost)
    if char_count > 2000:
        return "standard"

    # Premium for high-value content types
    if task_type in ("audiobook", "commercial", "dialogue") and char_count > 200:
        return "premium"

    # Default to standard
    return "standard"


def get_default_voice(task_type: str) -> str:
    """Get a default voice for a task type.

    Different voices work better for different content types.
    """
    voice_map = {
        "general_tts": "alloy",
        "narration": "onyx",
        "dialogue": "coral",
        "audiobook": "fable",
        "commercial": "nova",
        "gaming": "shimmer",
        "emotion_understanding": "coral",
        "voice_cloning": "alloy",  # will be overridden by clone reference
        "ultra_low_latency": "alloy",
        "119_languages": "alloy",
        "microsoft_prosody": "alloy",
        "highest_quality": "coral",
    }
    return voice_map.get(task_type, "alloy")