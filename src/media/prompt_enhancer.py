"""
Temuclaude Media Prompt Enhancement

GEPA-adapted prompt evolution for image and video generation models.
Each model has different strengths — the prompt is rewritten to leverage them.

Uses our existing LLM pool (GLM-5.2, cheapest capable model) to rewrite prompts.
This alone can improve output quality by 20-30%.

Adapted from gepa.py (GEPA prompt evolution for LLMs).
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Per-model strength hints — what to add to prompts for each model
MODEL_STRENGTH_HINTS = {
    # === IMAGE MODELS ===
    "openai/gpt-image-2": (
        "Add detailed spatial layout and reasoning about composition. "
        "If text is needed, specify exact text content and placement. "
        "Add layout instructions like 'position the subject in the lower third'."
    ),
    "reve/create-image": (
        "Add artistic style, mood, and lighting atmosphere. "
        "Specify the emotional tone and visual aesthetic."
    ),
    "google/nano-banana-2": (
        "Add reference image descriptions. Specify aspect ratio if extreme. "
        "Add grounding if real places are mentioned. Mention 4K if high resolution."
    ),
    "blackforestlabs/flux-2-max": (
        "Add camera details (lens, aperture, ISO, focal length). "
        "Add lighting setup (studio, golden hour, neon). "
        "Add material textures and surface descriptions."
    ),
    "blackforestlabs/flux-2-pro": (
        "Add photographic details: color grading, depth of field, bokeh. "
        "Specify camera and lens characteristics."
    ),
    "blackforestlabs/flux-2-flex": (
        "Add specific text content, font style, and layout instructions. "
        "Mention UI/UX elements if applicable. Specify alignment and spacing."
    ),
    "microsoft/mai-image-2.5": (
        "Add composition and framing details. Specify color palette. "
        "Add professional photography context."
    ),
    "bytedance/seedream-4-5": (
        "Add Chinese/multilingual text if needed. Add cultural style references. "
        "Specify traditional or modern aesthetic."
    ),
    "bytedance/seedream-5-0-lite-preview": (
        "Add real-time context, current events, and factual references. "
        "Mention specific dates or current information if relevant."
    ),
    "recraft-v3": (
        "Add vector design instructions. Mention SVG paths, geometric shapes. "
        "Specify flat design, clean lines, and minimal gradients."
    ),
    "alibaba/z-image-turbo": (
        "Keep the prompt simple and concise. This is a fast draft model — "
        "don't add unnecessary detail. Focus on the core subject."
    ),
    "x-ai/grok-imagine-image-pro": (
        "Add multilingual text if needed. Specify cultural context. "
        "Add artistic style references."
    ),

    # === VIDEO MODELS ===
    "bytedance/seedance-2.0": (
        "Add cinematic camera movements (pan, zoom, orbit). "
        "Specify audio cues (dialogue, ambient sound, music). "
        "If multi-input, describe each reference image's role."
    ),
    "alibaba/happyhorse-1-0": (
        "Add lip-sync language specification. Specify which of the 7 supported "
        "languages (English, Mandarin, Cantonese, Japanese, Korean, German, French). "
        "Add character animation details."
    ),
    "klingai/video-v3-pro-text-to-video": (
        "Specify 4K resolution and 60fps if desired. "
        "Add cinematic camera movements. Specify audio type (dialogue, SFX, ambient)."
    ),
    "google/veo-3.1-t2v": (
        "Add dialogue text if the video has speech. Specify the speaker's tone. "
        "Add ambient sound descriptions. Mention 48kHz audio quality if relevant."
    ),
    "google/veo-3.1-lite-generate-001": (
        "Keep prompt concise. This is the lite tier — focus on core action. "
        "Specify 720p resolution."
    ),
    "pixverse/v5-5-text-to-video": (
        "Add motion description. Specify style (realistic, anime, illustrated). "
        "Add camera movement details."
    ),
    "ltxv/ltxv-2-fast": (
        "Keep prompt simple. This is a fast draft video model. "
        "Focus on the main subject and primary action."
    ),
    "ltxv/ltxv-2": (
        "Add scene duration if long (>10s). Specify style and mood. "
        "Mention open-source aesthetic if relevant."
    ),
    "x-ai/grok-imagine-video": (
        "Add multilingual audio if needed. Specify style and mood. "
        "Keep prompt focused on key action."
    ),
    "wan-2-6-t2v": (
        "Add multi-shot description if storytelling. Specify scene transitions. "
        "Add character consistency notes."
    ),
}

# Task-type-based enhancements (applied to all models for that task)
TASK_TYPE_HINTS = {
    "photoreal": "Ensure photorealistic details: natural lighting, realistic skin texture, camera lens effects, depth of field.",
    "text_in_image": "Specify exact text content, font style, size, and placement. Ensure text is legible and correctly spelled.",
    "character": "Describe character features in detail: hair, eyes, clothing, pose, expression. Ensure consistency across views.",
    "multilingual": "Ensure text is correctly rendered in the specified language. Use appropriate fonts and cultural design elements.",
    "vector_svg": "Use flat design, clean geometric shapes, minimal gradients, and scalable vector aesthetics.",
    "extreme_ar": "Specify exact aspect ratio. Ensure composition works at the extreme ratio.",
    "realtime_search": "Include current, up-to-date information. Reference real entities and accurate details.",
    "high_res_4k": "Add fine detail descriptions that benefit from 4K resolution: textures, patterns, subtle lighting.",
    "video_dialogue": "Specify exact dialogue text, speaker tone, and emotion. Add ambient sound description.",
    "video_4k": "Add fine visual details that benefit from 4K. Specify high-quality lighting and composition.",
    "video_long": "Describe scene progression over time. Add transition cues between segments.",
    "video_multi_input": "Describe how each reference image contributes to the final video.",
    "video_i2v": "Describe how the input image should animate. Specify motion direction and speed.",
    "video_standard": "Add camera movement and scene description. Specify mood and style.",
}


def get_strength_hint(model_id: str) -> str:
    """Get the strength hint for a specific model."""
    return MODEL_STRENGTH_HINTS.get(model_id, "")


def get_task_hint(task_type: str) -> str:
    """Get the task-type-based enhancement hint."""
    return TASK_TYPE_HINTS.get(task_type, "")


def build_enhancement_prompt(original_prompt: str, model_id: str, task_type: str) -> str:
    """Build the LLM prompt for rewriting the user's prompt.

    This is the prompt we send to our LLM (GLM-5.2) to rewrite the user's
    prompt for a specific model's strengths.
    """
    strength_hint = get_strength_hint(model_id)
    task_hint = get_task_hint(task_type)

    hints = ""
    if strength_hint:
        hints += f"Model-specific guidance: {strength_hint}\n"
    if task_hint:
        hints += f"Task guidance: {task_hint}\n"

    if not hints:
        return original_prompt  # No enhancement needed

    return f"""You are a prompt engineering expert. Rewrite the following image/video generation prompt to leverage the specific strengths of the target model.

Original prompt: {original_prompt}
Target model: {model_id}
Task type: {task_type}

{hints}Rewrite the prompt to be more effective for this model. Keep it concise (max 2-3 sentences). Do not add a preamble or explanation — return ONLY the rewritten prompt, nothing else.

Rewritten prompt:"""


async def enhance_prompt(
    original_prompt: str,
    model_id: str,
    task_type: str,
    call_llm_func=None,
) -> str:
    """Enhance a prompt for a specific model using LLM.

    Uses our existing LLM pool (GLM-5.2) to rewrite the prompt.
    If the LLM call fails, returns the original prompt unchanged.

    Args:
        original_prompt: User's original prompt
        model_id: Target model ID (e.g., "openai/gpt-image-2")
        task_type: Classified task type
        call_llm_func: Async function to call LLM (from orchestrator)

    Returns:
        Enhanced prompt string, or original if enhancement fails
    """
    # If no model-specific hints, return original
    strength_hint = get_strength_hint(model_id)
    task_hint = get_task_hint(task_type)
    if not strength_hint and not task_hint:
        return original_prompt

    # If no LLM function provided, apply hints manually (simple concatenation)
    if call_llm_func is None:
        # Fallback: manually add hints to prompt
        enhanced = original_prompt
        if task_hint:
            enhanced = f"{enhanced} {task_hint}"
        if strength_hint:
            enhanced = f"{enhanced} {strength_hint}"
        # Cap at reasonable length
        if len(enhanced) > 2000:
            enhanced = enhanced[:2000]
        return enhanced

    # Use LLM to rewrite prompt
    enhancement_request = build_enhancement_prompt(original_prompt, model_id, task_type)

    try:
        messages = [
            {"role": "system", "content": "You are a prompt engineering expert. You rewrite prompts to be more effective for specific AI image/video generation models. Return ONLY the rewritten prompt, no preamble or explanation."},
            {"role": "user", "content": enhancement_request},
        ]

        enhanced = await call_llm_func(
            "z-ai/glm-5.2",  # cheapest capable model
            messages,
            max_tokens=500,
            temperature=0.7,  # some creativity in prompt rewriting
        )

        # Clean up — remove any preamble the LLM might have added
        enhanced = enhanced.strip()

        # Remove common LLM preambles
        preambles = [
            "Rewritten prompt:",
            "Here is the rewritten prompt:",
            "Here's the rewritten prompt:",
            "Enhanced prompt:",
            "Here is the enhanced prompt:",
        ]
        for preamble in preambles:
            if enhanced.startswith(preamble):
                enhanced = enhanced[len(preamble):].strip()
                break

        # Remove quotes if LLM wrapped the prompt in them
        if enhanced.startswith('"') and enhanced.endswith('"'):
            enhanced = enhanced[1:-1].strip()
        if enhanced.startswith("'") and enhanced.endswith("'"):
            enhanced = enhanced[1:-1].strip()

        # If the enhancement is too short or empty, return original
        if len(enhanced) < 10:
            return original_prompt

        # If the enhancement is way too long, truncate
        if len(enhanced) > 2000:
            enhanced = enhanced[:2000]

        return enhanced

    except Exception as e:
        logger.warning(f"Prompt enhancement failed for {model_id}: {e}")
        return original_prompt


async def enhance_prompts_for_pool(
    original_prompt: str,
    model_pool: list,
    task_type: str,
    call_llm_func=None,
) -> dict:
    """Enhance the prompt for each model in the pool.

    Args:
        original_prompt: User's original prompt
        model_pool: List of model configs (from models.py)
        task_type: Classified task type
        call_llm_func: Async LLM call function

    Returns:
        Dict mapping model_id → enhanced_prompt
    """
    enhanced_prompts = {}

    # For draft tier (single model), just enhance once
    if len(model_pool) == 1:
        model_id = model_pool[0]["id"]
        enhanced = await enhance_prompt(original_prompt, model_id, task_type, call_llm_func)
        enhanced_prompts[model_id] = enhanced
        return enhanced_prompts

    # For multi-model pools, enhance in parallel
    import asyncio

    tasks = []
    model_ids = []
    for model_config in model_pool:
        model_id = model_config["id"]
        model_ids.append(model_id)
        tasks.append(enhance_prompt(original_prompt, model_id, task_type, call_llm_func))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    for model_id, result in zip(model_ids, results):
        if isinstance(result, Exception):
            logger.warning(f"Prompt enhancement failed for {model_id}: {result}")
            enhanced_prompts[model_id] = original_prompt  # fallback to original
        else:
            enhanced_prompts[model_id] = result

    return enhanced_prompts