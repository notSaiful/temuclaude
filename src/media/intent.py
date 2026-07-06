"""
Temuclaude Media Intent Classification

Classifies media prompts into task types and determines quality tier.
Adapted from orchestrator.py's classify_task() and determine_tier().

Two functions:
  classify_media_task(prompt) → task type string
  determine_media_tier(prompt, task_type) → tier string ("draft", "standard", "premium")
"""

import re


def classify_media_task(prompt: str) -> str:
    """Classify a media generation prompt into a task type for routing.

    Order matters: check more specific categories first.

    Image task types:
      - vector_svg: vector/SVG output (Recraft only)
      - extreme_ar: extreme aspect ratios (Nano Banana 2 only)
      - realtime_search: real-time web search (Seedream 5.0 Lite only)
      - high_res_4k: 4K resolution request
      - text_in_image: text/typography/poster/logo with text
      - multilingual: Chinese/Japanese/Korean text
      - character: character consistency with references
      - photoreal: photorealistic image request
      - general_image: default

    Video task types:
      - video_dialogue: dialogue/speech/talking
      - video_4k: 4K video request
      - video_long: long duration (>15s)
      - video_multi_input: multiple input references
      - video_i2v: image-to-video
      - video_standard: default video
    """
    prompt_lower = prompt.lower()

    # === VIDEO DETECTION (check first — video prompts may contain image keywords) ===
    video_keywords = [
        "video", "animate", "animation", "motion", "cinematic", "clip",
        "movie", "film", "scene", "sequence", "footage", "render video",
        "moving", "playback", "frame", "fps",
    ]
    is_video = any(kw in prompt_lower for kw in video_keywords)

    # Also check for video-specific verbs
    video_verbs = ["generate video", "create video", "make video", "produce video",
                   "animate this", "animate the", "bring to life", "make it move"]
    if not is_video:
        is_video = any(v in prompt_lower for v in video_verbs)

    if is_video:
        # Video sub-classification

        # Dialogue/speech (check first — Veo 3.1 is the only model with true dialogue)
        if any(k in prompt_lower for k in [
            "dialogue", "speech", "talking", "conversation", "speak", "says",
            "narrator", "voiceover", "voice over", "monologue", "interview",
            "character speaking", "person saying", "lip sync", "lip-sync",
        ]):
            return "video_dialogue"

        # 4K/high resolution video
        if any(k in prompt_lower for k in ["4k video", "4k cinematic", "60fps", "ultra hd video", "uhd video"]):
            return "video_4k"

        # Long duration video
        if any(k in prompt_lower for k in [
            "30 second", "30s video", "20 second", "20s video", "long video",
            "extended video", "full length",
        ]):
            return "video_long"

        # Multi-input video (multiple reference images)
        if any(k in prompt_lower for k in [
            "multiple images", "reference images", "storyboard",
            "multiple references", "9 images", "character sheet",
        ]):
            return "video_multi_input"

        # Image-to-video (has an input image)
        if any(k in prompt_lower for k in [
            "image to video", "from this image", "animate this image",
            "make this image into video", "make this image into a video",
            "turn this image into video", "turn this image into a video",
            "make this photo move", "turn this image into video",
            "using this picture", "based on this image",
            "first frame", "i2v", "this image as video",
            "this picture as video", "animate this photo",
            "bring this image to life", "animate this picture",
        ]):
            return "video_i2v"

        return "video_standard"

    # === IMAGE CLASSIFICATION ===

    # Vector/SVG (Recraft only)
    if any(k in prompt_lower for k in [
        "vector", "svg", "vector graphic", "illustration vector",
        "flat design", "geometric", "icon design", "logo as svg",
    ]):
        return "vector_svg"

    # Extreme aspect ratio (Nano Banana 2 only)
    if any(k in prompt_lower for k in [
        "ultrawide", "panoramic", "panorama", "1:8", "8:1",
        "banner", "billboard", "skyscraper", "tower format",
        "very tall", "very wide", "extreme aspect",
    ]):
        return "extreme_ar"

    # Real-time search (Seedream 5.0 Lite only)
    if any(k in prompt_lower for k in [
        "real-time", "realtime", "current", "news", "today",
        "latest", "up to date", "now showing", "currently",
        "search for", "look up", "what does", "what is happening",
    ]):
        return "realtime_search"

    # 4K resolution request
    if any(k in prompt_lower for k in [
        "4k", "8k", "ultra hd", "uhd", "high resolution",
        "4096", "3840", "maximum resolution", "max resolution",
    ]):
        return "high_res_4k"

    # Multilingual text (check BEFORE text_in_image — multilingual is more specific)
    if any(k in prompt_lower for k in [
        "chinese", "中文", "japanese", "日本語", "korean", "한국어",
        "arabic", "العربية", "hindi", "हिन्दी", "thai", "ไทย",
        "multilingual", "cjk", "double-byte",
    ]):
        return "multilingual"

    # Text in image
    if any(k in prompt_lower for k in [
        "text", "typography", "poster", "sign", "label", "banner text",
        "with text", "says ", "reading ", "written", "caption",
        "menu", "flyer", "brochure", "letterhead", "card with",
        "quote on", "slogan", "tagline", "headline",
    ]):
        return "text_in_image"

    # Character consistency with references
    if any(k in prompt_lower for k in [
        "character", "person", "consistent character", "reference image",
        "same person", "same character", "character sheet",
        "maintain identity", "face consistent", "multiple angles",
    ]):
        return "character"

    # Photorealistic
    if any(k in prompt_lower for k in [
        "photo", "photograph", "realistic", "camera", "studio",
        "photorealistic", "lens", "aperture", "iso", "lighting setup",
        "product shot", "product photo", "headshot", "portrait photo",
        "dslr", "film grain", "depth of field", "bokeh",
    ]):
        return "photoreal"

    return "general_image"


def determine_media_tier(prompt: str, task_type: str, explicit_tier: str = None) -> str:
    """Determine quality tier for media generation.

    Uses ATTS adaptive compute allocation (arXiv:2408.03314):
    Easy → less compute, Hard → more compute.

    Tiers:
      - draft: single cheap model (60% of requests, $0.005/image)
      - standard: best-of-3 models (30% of requests, $0.118/image)
      - premium: best-of-5 models (10% of requests, $0.448/image)

    For video:
      - draft: single cheap model ($2.40/min)
      - budget: single cheap quality model ($3.90-4.80/min)
      - standard: best-of-2 ($22.27/min)
      - premium: best-of-3 ($42-46/min)

    Args:
        prompt: User's media prompt
        task_type: Classified task type from classify_media_task()
        explicit_tier: If user explicitly requests a tier, use that

    Returns:
        Tier string: "draft", "standard", "premium", or "budget"
    """
    # If user explicitly requests a tier, honor it
    if explicit_tier and explicit_tier in ("draft", "standard", "premium", "budget"):
        return explicit_tier

    word_count = len(prompt.split())
    char_count = len(prompt)

    # Unique capability tasks always use their specific model (not tiered)
    unique_tasks = {
        "vector_svg", "extreme_ar", "realtime_search", "high_res_4k",
        "video_dialogue", "video_4k", "video_long", "video_multi_input",
    }
    if task_type in unique_tasks:
        return "premium"  # unique models are in the premium/unique pool

    # Video tasks
    if task_type.startswith("video_"):
        # Trivial video: short prompt, simple task
        if word_count <= 10 and task_type == "video_standard":
            return "draft"

        # Complex video: long prompt or specific requirements
        if word_count > 50:
            return "premium"
        if char_count > 300:
            return "premium"

        # Medium video
        return "standard"

    # Image tasks
    # Trivial: very short, simple prompts
    if word_count <= 8 and char_count <= 50 and task_type in ("general_image", "photoreal"):
        return "draft"

    # Premium: complex prompts with specific requirements
    if word_count > 50:
        return "premium"
    if char_count > 300:
        return "premium"
    if any(k in prompt.lower() for k in [
        "complex", "detailed", "multiple subjects", "specific", "exact",
        "precise", "professional", "commercial", "high quality", "best quality",
        "intricate", "elaborate", "comprehensive",
    ]):
        return "premium"

    # Text in image: needs higher tier for accurate text
    if task_type == "text_in_image" and word_count > 15:
        return "premium"

    # Character consistency: needs higher tier
    if task_type == "character" and word_count > 20:
        return "premium"

    # Standard: default
    return "standard"


def is_video_prompt(prompt: str) -> bool:
    """Quick check if a prompt is for video generation (not image)."""
    task_type = classify_media_task(prompt)
    return task_type.startswith("video_")


# Test helper
if __name__ == "__main__":
    test_prompts = [
        ("a cat", "general_image", "draft"),
        ("a photorealistic product photo of headphones on white background studio lighting", "photoreal", "standard"),
        ("generate a video of a sunset", "video_standard", "standard"),
        ("create a video with dialogue where a man says hello", "video_dialogue", "premium"),
        ("vector svg logo for a tech company", "vector_svg", "premium"),
        ("ultrawide panoramic cityscape", "extreme_ar", "premium"),
        ("a poster that says 'Hello World' in bold text", "text_in_image", "standard"),
        ("a Chinese poster with 中文 text", "multilingual", "standard"),
        ("a 4K video at 60fps of a waterfall", "video_4k", "premium"),
        ("make this image into a video", "video_i2v", "standard"),
        ("animate this image into a cinematic video", "video_i2v", "standard"),
    ]

    for prompt, expected_type, expected_tier in test_prompts:
        task = classify_media_task(prompt)
        tier = determine_media_tier(prompt, task)
        type_ok = "✓" if task == expected_type else "✗"
        tier_ok = "✓" if tier == expected_tier else "✗"
        print(f"  {type_ok} type={task:20s} tier={tier:10s} — {prompt[:50]}")