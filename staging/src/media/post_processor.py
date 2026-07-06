"""
Temuclaude Media Post-Processor

After the best output is selected by the quality gate, post-processing
improves it further:
  1. Upscale to target resolution (Topaz Sharpen, FLUX SRPO)
  2. Face restoration if faces detected
  3. Generative upscaling for difficult cases

For videos:
  1. (Future) Frame interpolation to 60fps (RIFE/FILM)
  2. (Future) Super-resolution

This is a capability NO single-model platform has. It's another
competitive advantage — we take a good 1024x1024 image and make it 4K quality.
"""

import asyncio
import logging
from typing import Optional

from .providers.base import MediaProviderManager

logger = logging.getLogger(__name__)


class MediaPostProcessor:
    """Post-process generated images and videos for final quality boost."""

    def __init__(self, provider_manager: MediaProviderManager = None):
        self.provider_manager = provider_manager or MediaProviderManager()

    async def should_upscale(self, image_url: str, current_size: str, target_resolution: int) -> bool:
        """Determine if upscaling is needed.

        Upscale if:
          - The target resolution is higher than current
          - The image URL is valid
        """
        if not image_url:
            return False

        # Parse current size (e.g., "1024x1024")
        try:
            w, h = current_size.lower().split("x")
            current_max = max(int(w), int(h))
            return current_max < target_resolution
        except (ValueError, AttributeError):
            # If we can't parse, assume upscaling is beneficial
            return True

    async def upscale_image(
        self,
        image_url: str,
        target_resolution: int = 4096,
        method: str = "sharpen",
    ) -> Optional[str]:
        """Upscale an image to the target resolution.

        Args:
            image_url: URL of the image to upscale
            target_resolution: Target max dimension (e.g., 4096 for 4K)
            method: "sharpen" (Topaz Sharpen), "sharpen_gen" (generative), "flux_srpo" (FLUX SRPO)

        Returns:
            URL of the upscaled image, or original URL if upscaling fails.
        """
        if not image_url:
            return image_url

        # Select the upscaling model
        from .models import IMAGE_POST_PROCESS

        model_key = method if method in IMAGE_POST_PROCESS else "upscale"
        model_config = IMAGE_POST_PROCESS[model_key]
        model_id = model_config["id"]

        try:
            result = await self.provider_manager.generate_image(
                model_id,
                prompt=image_url,  # For upscaling models, the "prompt" is the image URL
                estimated_cost=model_config.get("cost_per_image", 0.0),
            )

            if result and result.get("url"):
                logger.info(f"Upscaled image to {target_resolution}px using {model_id}")
                return result["url"]
            else:
                logger.warning(f"Upscaling failed with {model_id}, returning original")
                return image_url

        except Exception as e:
            logger.warning(f"Upscaling error: {e}")
            return image_url

    async def process_image(
        self,
        image_url: str,
        task_type: str = "general_image",
        current_size: str = "1024x1024",
        target_resolution: int = 4096,
        always_upscale: bool = False,
    ) -> dict:
        """Full post-processing pipeline for an image.

        1. Upscale if target > current (or if always_upscale is True)
        2. (Future) Face restoration if faces detected

        Args:
            image_url: URL of the best image from quality gate
            task_type: Task type (affects which post-processing to apply)
            current_size: Current image size (e.g., "1024x1024")
            target_resolution: Target resolution
            always_upscale: Force upscaling even if current >= target

        Returns:
            Dict with:
              - 'url': Final image URL (upscaled or original)
              - 'upscaled': Whether upscaling was applied
              - 'original_url': The original image URL
              - 'cost': Post-processing cost
        """
        if not image_url:
            return {
                "url": "",
                "upscaled": False,
                "original_url": "",
                "cost": 0.0,
            }

        # Determine if upscaling is needed
        needs_upscale = always_upscale or await self.should_upscale(
            image_url, current_size, target_resolution
        )

        # Skip upscaling for vector/SVG (they're resolution-independent)
        if task_type == "vector_svg":
            needs_upscale = False

        # Skip upscaling for draft tier (cost optimization)
        if task_type == "general_image" and not always_upscale:
            # Only upscale if current resolution is significantly below target
            try:
                w, h = current_size.lower().split("x")
                if max(int(w), int(h)) >= 2048:
                    needs_upscale = False
            except (ValueError, AttributeError):
                pass

        if not needs_upscale:
            return {
                "url": image_url,
                "upscaled": False,
                "original_url": image_url,
                "cost": 0.0,
            }

        # Upscale
        from .models import IMAGE_POST_PROCESS
        upscale_cost = IMAGE_POST_PROCESS.get("upscale", {}).get("cost_per_image", 0.02)

        upscaled_url = await self.upscale_image(
            image_url,
            target_resolution=target_resolution,
            method="sharpen",
        )

        return {
            "url": upscaled_url,
            "upscaled": upscaled_url != image_url,
            "original_url": image_url,
            "cost": upscale_cost if upscaled_url != image_url else 0.0,
            "target_resolution": target_resolution,
        }

    async def process_video(
        self,
        video_url: str,
        task_type: str = "video_standard",
        target_fps: int = 60,
        target_resolution: str = "1080p",
    ) -> dict:
        """Post-process a video.

        Future capabilities (not yet implemented):
          - Frame interpolation to 60fps (RIFE/FILM)
          - Super-resolution upscaling
          - Audio enhancement

        Currently returns the video as-is.

        Args:
            video_url: URL of the best video from quality gate
            task_type: Video task type
            target_fps: Target frame rate
            target_resolution: Target resolution

        Returns:
            Dict with:
              - 'url': Final video URL
              - 'processed': Whether post-processing was applied
              - 'original_url': Original video URL
              - 'cost': Post-processing cost
        """
        # Video post-processing is not yet implemented
        # This is a placeholder for future work

        return {
            "url": video_url,
            "processed": False,
            "original_url": video_url,
            "cost": 0.0,
            "note": "Video post-processing (frame interpolation, super-resolution) is planned for future implementation.",
        }

    async def process(
        self,
        url: str,
        media_type: str = "image",
        task_type: str = "general_image",
        **kwargs,
    ) -> dict:
        """Unified entry point for post-processing.

        Args:
            url: URL of the best output from quality gate
            media_type: "image" or "video"
            task_type: Task type
            **kwargs: Additional parameters (target_resolution, etc.)

        Returns:
            Post-processing result dict.
        """
        if media_type == "video":
            return await self.process_video(url, task_type, **kwargs)
        else:
            return await self.process_image(url, task_type, **kwargs)