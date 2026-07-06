"""
Temuclaude Music Intent Classification

Classifies music generation prompts into task types and determines quality tier.
"""

import re


def classify_music_task(prompt: str, lyrics: str = "") -> str:
    """Classify a music generation request into a task type for routing.

    Args:
        prompt: The music description/style prompt
        lyrics: Optional lyrics text

    Returns:
        Task type string for routing
    """
    combined = f"{prompt} {lyrics}".lower()

    # Song cover/remix — transforming an existing song
    if any(k in combined for k in [
        "cover", "remix", "reinterpret", "transform this song",
        "change the style of", "different genre version",
        "cover version", "remake", "rearrange this",
    ]):
        return "song_cover"

    # Ethnic instruments — cultural/diverse music
    if any(k in combined for k in [
        "ethnic", "traditional", "cultural", "folk",
        "sitar", "tabla", "erhu", "koto", "djembe", "didgeridoo",
        "bagpipes", "bouzouki", "oud", "saz", "charango",
        "indian classical", "chinese traditional", "japanese traditional",
        "african drums", "celtic", "flamenco",
    ]):
        return "ethnic_instruments"

    # Longest duration — 5+ minute request
    if any(k in combined for k in [
        "5 minute", "5 min", "300 second", "long song",
        "full length song", "extended", "full track",
    ]):
        return "longest_duration"

    # Custom lyrics with structure tags
    if any(k in combined for k in [
        "[intro]", "[verse]", "[chorus]", "[bridge]", "[outro]",
        "song structure", "structured lyrics",
    ]):
        return "custom_lyrics_structure"

    # Highest quality — explicit quality request
    if any(k in combined for k in [
        "highest quality", "best quality", "premium", "studio quality",
        "professional", "broadcast quality", "master quality",
    ]):
        return "highest_quality"

    # Eleven quality — specific request for ElevenLabs
    if any(k in combined for k in [
        "elevenlabs", "eleven music", "high quality from text",
    ]):
        return "eleven_quality"

    # Background music
    if any(k in combined for k in [
        "background music", "bgm", "ambient", "background track",
        "underscore", "atmospheric", "ambient bed",
    ]):
        return "background_music"

    # Jingle
    if any(k in combined for k in [
        "jingle", "ad music", "commercial music", "short jingle",
        "brand sound", "logo sound",
    ]):
        return "jingle"

    # Soundtrack
    if any(k in combined for k in [
        "soundtrack", "film score", "movie score", "game music",
        "cinematic music", "orchestral score",
    ]):
        return "soundtrack"

    # Podcast intro
    if any(k in combined for k in [
        "podcast", "intro music", "outro music", "theme song",
        "show intro", "podcast theme",
    ]):
        return "podcast_intro"

    return "general_music"


def determine_music_tier(prompt: str, task_type: str, explicit_tier: str = None) -> str:
    """Determine quality tier for music generation.

    Tiers:
      - draft: single cheap model ($0.0315/gen, 60% of requests)
      - standard: cascade 2 models ($0.06 avg, 30% of requests)
      - premium: cascade 3-4 models ($0.10 avg, 10% of requests)
    """
    if explicit_tier and explicit_tier in ("draft", "standard", "premium"):
        return explicit_tier

    # Unique capability tasks always use their specific model
    unique_tasks = {
        "song_cover", "ethnic_instruments", "longest_duration",
        "highest_quality", "custom_lyrics_structure", "eleven_quality",
    }
    if task_type in unique_tasks:
        return "premium"

    # Short prompt → draft
    if len(prompt) <= 50 and task_type == "general_music":
        return "draft"

    # Premium for high-value content
    if task_type in ("soundtrack", "highest_quality") and len(prompt) > 100:
        return "premium"

    return "standard"


def get_default_music_params(task_type: str) -> dict:
    """Get default music generation parameters for a task type."""
    params_map = {
        "general_music": {"duration_ms": 30000, "format": "mp3", "sample_rate": 44100, "bitrate": 256000},
        "song_cover": {"duration_ms": 180000, "format": "mp3", "sample_rate": 44100, "bitrate": 256000},
        "ethnic_instruments": {"duration_ms": 120000, "format": "mp3", "sample_rate": 44100, "bitrate": 256000},
        "longest_duration": {"duration_ms": 300000, "format": "mp3", "sample_rate": 44100, "bitrate": 256000},
        "highest_quality": {"duration_ms": 180000, "format": "wav", "sample_rate": 44100, "bitrate": 256000},
        "custom_lyrics_structure": {"duration_ms": 180000, "format": "mp3", "sample_rate": 44100, "bitrate": 256000},
        "eleven_quality": {"duration_ms": 180000, "format": "mp3", "sample_rate": 44100, "bitrate": 256000},
        "background_music": {"duration_ms": 120000, "format": "mp3", "sample_rate": 44100, "bitrate": 128000},
        "jingle": {"duration_ms": 30000, "format": "mp3", "sample_rate": 44100, "bitrate": 128000},
        "soundtrack": {"duration_ms": 180000, "format": "wav", "sample_rate": 44100, "bitrate": 256000},
        "podcast_intro": {"duration_ms": 30000, "format": "mp3", "sample_rate": 44100, "bitrate": 128000},
    }
    return params_map.get(task_type, {"duration_ms": 30000, "format": "mp3", "sample_rate": 44100, "bitrate": 256000})