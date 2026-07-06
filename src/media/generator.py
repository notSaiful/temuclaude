"""
Temuclaude Media Parallel Generator

Runs N image/video models in parallel (best-of-N) and returns all outputs.
Adapted from fusion.py's panel generation pattern.

For images: all models generate simultaneously, return list of image URLs.
For videos: all models submit simultaneously, return list of generation IDs
           (video URLs are retrieved later via async polling).
"""

import asyncio
import logging
from typing import Optional

from .providers.base import MediaProviderManager
from .models import (
    get_image_pool,
    get_video_pool,
    estimate_image_cost,
    estimate_video_cost,
)
from .prompt_enhancer import enhance_prompts_for_pool

logger = logging.getLogger(__name__)


class MediaGenerator:
    """Parallel best-of-N media generation.

    For images:
      1. Get the model pool for the tier/task type
      2. Enhance prompts for each model (GEPA)
      3. Generate with all models in parallel
      4. Return list of successful outputs

    For videos:
      1. Get the model pool
      2. Enhance prompts
      3. Submit to all models in parallel (async — get generation IDs)
      4. Poll all for completion
      5. Return list of successful video URLs
    """

    def __init__(self, provider_manager: MediaProviderManager = None, call_llm_func=None):
        self.provider_manager = provider_manager or MediaProviderManager()
        self.call_llm_func = call_llm_func  # for prompt enhancement

    async def generate_images(
        self,
        prompt: str,
        tier: str = "standard",
        task_type: str = "general_image",
        size: str = "1024x1024",
        explicit_tier: str = None,
    ) -> dict:
        """Generate images using best-of-N parallel models.

        Args:
            prompt: User's image generation prompt
            tier: Quality tier ("draft", "standard", "premium")
            task_type: Classified task type
            size: Image size (e.g., "1024x1024", "1920x1080")
            explicit_tier: If set, overrides tier

        Returns:
            Dict with:
              - 'outputs': List of {model, url, enhanced_prompt, score?}
              - 'models_used': List of model IDs that were attempted
              - 'successful_models': List of model IDs that produced output
              - 'failed_models': List of model IDs that failed
              - 'estimated_cost': Total cost of this generation
              - 'tier': Tier used
              - 'task_type': Task type
              - 'enhanced_prompts': Dict of model_id → enhanced prompt
        """
        start_time = asyncio.get_event_loop().time()

        # Get the model pool for this tier and task type
        model_pool = get_image_pool(tier, task_type)
        if not model_pool:
            return {
                "outputs": [],
                "models_used": [],
                "successful_models": [],
                "failed_models": [],
                "estimated_cost": 0.0,
                "tier": tier,
                "task_type": task_type,
                "enhanced_prompts": {},
                "error": "No models available for this tier/task type",
            }

        models_used = [m["id"] for m in model_pool]
        estimated_cost = estimate_image_cost(model_pool)

        # Enhance prompts for each model (GEPA prompt evolution)
        enhanced_prompts = await enhance_prompts_for_pool(
            prompt, model_pool, task_type, self.call_llm_func
        )

        # Generate with all models in parallel
        tasks = []
        for model_config in model_pool:
            model_id = model_config["id"]
            enhanced_prompt = enhanced_prompts.get(model_id, prompt)

            # Build kwargs for this model
            kwargs = {
                "size": size,
                "estimated_cost": model_config.get("cost_per_image", 0.0),
            }

            # Add seed for diversity if best-of-N
            if len(model_pool) > 1:
                # Use different seeds for each model to get diverse outputs
                # This is the N-particle approach from arXiv:2507.05604
                kwargs["seed"] = hash(model_id) % 2**32  # deterministic per model

            tasks.append(
                self.provider_manager.generate_image(model_id, enhanced_prompt, **kwargs)
            )

        # Run all in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        outputs = []
        successful_models = []
        failed_models = []

        for i, result in enumerate(results):
            model_id = model_pool[i]["id"]
            if isinstance(result, Exception):
                logger.warning(f"Image generation failed for {model_id}: {result}")
                failed_models.append(model_id)
            elif result and result.get("url"):
                outputs.append({
                    "model": model_id,
                    "url": result["url"],
                    "enhanced_prompt": enhanced_prompts.get(model_id, prompt),
                    "provider": result.get("provider", "unknown"),
                })
                successful_models.append(model_id)
            else:
                failed_models.append(model_id)

        elapsed = asyncio.get_event_loop().time() - start_time

        return {
            "outputs": outputs,
            "models_used": models_used,
            "successful_models": successful_models,
            "failed_models": failed_models,
            "estimated_cost": estimated_cost,
            "tier": tier,
            "task_type": task_type,
            "enhanced_prompts": enhanced_prompts,
            "elapsed_seconds": round(elapsed, 2),
            "size": size,
        }

    async def generate_videos(
        self,
        prompt: str,
        tier: str = "standard",
        task_type: str = "video_standard",
        duration_seconds: int = 5,
        resolution: str = "1080p",
        first_frame_image: str = None,
        explicit_tier: str = None,
    ) -> dict:
        """Generate videos using best-of-N parallel models.

        Video generation is ASYNC:
          1. Submit to all models in parallel → get generation IDs
          2. Poll all generation IDs in parallel → get video URLs

        Args:
            prompt: User's video generation prompt
            tier: Quality tier
            task_type: Classified task type
            duration_seconds: Video duration
            resolution: Video resolution
            first_frame_image: URL of first frame (for image-to-video)

        Returns:
            Dict with:
              - 'outputs': List of {model, url, generation_id}
              - 'models_used': List of model IDs attempted
              - 'successful_models': List that produced video
              - 'failed_models': List that failed
              - 'estimated_cost': Total cost
              - 'tier': Tier used
              - 'task_type': Task type
              - 'enhanced_prompts': Dict of model_id → enhanced prompt
        """
        start_time = asyncio.get_event_loop().time()

        # Get the model pool
        model_pool = get_video_pool(tier, task_type)
        if not model_pool:
            return {
                "outputs": [],
                "models_used": [],
                "successful_models": [],
                "failed_models": [],
                "estimated_cost": 0.0,
                "tier": tier,
                "task_type": task_type,
                "enhanced_prompts": {},
                "error": "No models available for this tier/task type",
            }

        models_used = [m["id"] for m in model_pool]
        estimated_cost = estimate_video_cost(model_pool, duration_seconds)

        # Enhance prompts for each model
        enhanced_prompts = await enhance_prompts_for_pool(
            prompt, model_pool, task_type, self.call_llm_func
        )

        # Submit to all models in parallel (get generation IDs)
        submit_tasks = []
        for model_config in model_pool:
            model_id = model_config["id"]
            enhanced_prompt = enhanced_prompts.get(model_id, prompt)

            kwargs = {
                "duration": duration_seconds,
                "resolution": resolution,
                "estimated_cost": model_config.get("cost_per_min", 0.0) * (duration_seconds / 60.0),
            }
            if first_frame_image:
                kwargs["first_frame_image"] = first_frame_image

            submit_tasks.append(
                self.provider_manager.generate_video(model_id, enhanced_prompt, **kwargs)
            )

        submit_results = await asyncio.gather(*submit_tasks, return_exceptions=True)

        # Process submission results — collect generation IDs
        pending_generations = []
        failed_models = []

        for i, result in enumerate(submit_results):
            model_id = model_pool[i]["id"]
            if isinstance(result, Exception):
                logger.warning(f"Video submission failed for {model_id}: {result}")
                failed_models.append(model_id)
            elif result and result.get("generation_id"):
                pending_generations.append({
                    "model": model_id,
                    "generation_id": result["generation_id"],
                    "provider": result.get("provider", "aiml"),
                    "provider_path": result.get("provider_path", "minimax"),
                })
            else:
                failed_models.append(model_id)

        # Poll all pending generations in parallel
        poll_tasks = []
        for gen in pending_generations:
            poll_tasks.append(
                self.provider_manager.poll_video(
                    gen["generation_id"],
                    gen["provider"],
                    gen["provider_path"],
                    max_wait=300,
                    poll_interval=5,
                )
            )

        poll_results = await asyncio.gather(*poll_tasks, return_exceptions=True)

        # Collect final video URLs
        outputs = []
        successful_models = []

        for i, result in enumerate(poll_results):
            model_id = pending_generations[i]["model"]
            if isinstance(result, Exception):
                logger.warning(f"Video polling failed for {model_id}: {result}")
                failed_models.append(model_id)
            elif result and result.get("url"):
                outputs.append({
                    "model": model_id,
                    "url": result["url"],
                    "generation_id": pending_generations[i]["generation_id"],
                    "enhanced_prompt": enhanced_prompts.get(model_id, prompt),
                })
                successful_models.append(model_id)
            else:
                failed_models.append(model_id)

        elapsed = asyncio.get_event_loop().time() - start_time

        return {
            "outputs": outputs,
            "models_used": models_used,
            "successful_models": successful_models,
            "failed_models": failed_models,
            "estimated_cost": estimated_cost,
            "tier": tier,
            "task_type": task_type,
            "enhanced_prompts": enhanced_prompts,
            "elapsed_seconds": round(elapsed, 2),
            "duration_seconds": duration_seconds,
            "resolution": resolution,
        }

    async def generate(
        self,
        prompt: str,
        tier: str = "standard",
        task_type: str = "general_image",
        media_type: str = "image",
        **kwargs,
    ) -> dict:
        """Unified entry point for both image and video generation.

        Args:
            prompt: User's prompt
            tier: Quality tier
            task_type: Classified task type
            media_type: "image" or "video"
            **kwargs: Additional parameters (size, duration, etc.)

        Returns:
            Generation result dict
        """
        if media_type == "video":
            return await self.generate_videos(prompt, tier, task_type, **kwargs)
        else:
            return await self.generate_images(prompt, tier, task_type, **kwargs)