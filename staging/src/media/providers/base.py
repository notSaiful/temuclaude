"""
Temuclaude Media Provider Abstraction

Multi-provider failover for image and video generation:
  AIML API (primary) → fal.ai (secondary) → OpenRouter (tertiary)

Each provider implements the same interface:
  - generate_image(model_id, prompt, **kwargs) → image_url or None
  - generate_video(model_id, prompt, **kwargs) → video_url or None
  - is_available() → bool

The MediaProviderManager tries providers in order and returns the first success.
"""

import os
import logging

logger = logging.getLogger(__name__)


class MediaProvider:
    """Base class for media generation providers."""

    def is_available(self) -> bool:
        raise NotImplementedError

    async def generate_image(self, model_id: str, prompt: str, **kwargs) -> dict | None:
        """Generate an image. Returns dict with 'url', 'model', 'cost' or None on failure."""
        raise NotImplementedError

    async def generate_video(self, model_id: str, prompt: str, **kwargs) -> dict | None:
        """Generate a video. Returns dict with 'url', 'model', 'cost', 'generation_id' or None."""
        raise NotImplementedError

    async def get_video_status(self, generation_id: str) -> dict | None:
        """Check status of an async video generation. Returns dict with 'status', 'url' or None."""
        raise NotImplementedError


class AIMLProvider(MediaProvider):
    """AIML API provider — 739 models including all major image and video models.

    API docs: https://docs.aimlapi.com/api-references/image-models
    Image endpoint: POST https://api.aimlapi.com/v1/images/generations/
    Video endpoint: POST https://api.aimlapi.com/v2/generate/video/{provider}/generation
    """

    BASE_URL = "https://api.aimlapi.com/v1"
    VIDEO_BASE_URL = "https://api.aimlapi.com/v2/generate/video"

    def __init__(self):
        self.api_key = os.environ.get("AIML_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def generate_image(self, model_id: str, prompt: str, **kwargs) -> dict | None:
        """Generate an image via AIML API.

        Args:
            model_id: AIML API model ID (e.g., "openai/gpt-image-2", "reve/create-image")
            prompt: Text prompt for image generation
            **kwargs: size, n, negative_prompt, etc.

        Returns:
            dict with 'url', 'model', 'cost' on success, None on failure.
        """
        import aiohttp

        url = f"{self.BASE_URL}/images/generations/"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model_id,
            "prompt": prompt,
        }
        # Add optional parameters
        if "size" in kwargs:
            payload["size"] = kwargs["size"]
        if "n" in kwargs:
            payload["n"] = kwargs["n"]
        if "negative_prompt" in kwargs:
            payload["negative_prompt"] = kwargs["negative_prompt"]
        if "seed" in kwargs:
            payload["seed"] = kwargs["seed"]
        if "num_inference_steps" in kwargs:
            payload["num_inference_steps"] = kwargs["num_inference_steps"]
        if "guidance_scale" in kwargs:
            payload["guidance_scale"] = kwargs["guidance_scale"]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=180)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.warning(f"AIML API image generation failed: {resp.status} — {error_text[:200]}")
                        return None

                    data = await resp.json()

                    # Extract image URL from response
                    # AIML API returns images in data[].url or data[].b64_json
                    images = data.get("data", data.get("images", []))
                    if not images:
                        logger.warning(f"AIML API returned no images for {model_id}")
                        return None

                    image_data = images[0]
                    image_url = image_data.get("url", "")
                    if not image_url and image_data.get("b64_json"):
                        # Some models return base64 — we'd need to save and host it
                        # For now, return the base64 as a data URL
                        image_url = f"data:image/png;base64,{image_data['b64_json']}"

                    if not image_url:
                        logger.warning(f"AIML API returned no URL for {model_id}")
                        return None

                    return {
                        "url": image_url,
                        "model": model_id,
                        "provider": "aiml",
                        "cost": kwargs.get("estimated_cost", 0.0),
                    }

        except Exception as e:
            logger.warning(f"AIML API image generation error for {model_id}: {e}")
            return None

    async def generate_video(self, model_id: str, prompt: str, **kwargs) -> dict | None:
        """Generate a video via AIML API.

        Video generation is ASYNC: submit → get generation_id → poll for result.

        Args:
            model_id: AIML API video model ID (e.g., "bytedance/seedance-2.0")
            prompt: Text prompt for video generation
            **kwargs: first_frame_image, duration, resolution, etc.

        Returns:
            dict with 'generation_id', 'model', 'provider' on success, None on failure.
            The video URL is NOT returned here — call get_video_status() to retrieve it.
        """
        import aiohttp

        # Determine the video provider path from model_id
        # AIML API uses URLs like /v2/generate/video/{provider}/generation
        # Provider is extracted from model_id prefix (e.g., "bytedance" → "bytedance")
        provider = model_id.split("/")[0] if "/" in model_id else "minimax"

        url = f"{self.VIDEO_BASE_URL}/{provider}/generation"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model_id,
            "prompt": prompt,
        }
        # Add optional parameters
        if "first_frame_image" in kwargs:
            payload["first_frame_image"] = kwargs["first_frame_image"]
        if "duration" in kwargs:
            payload["duration"] = kwargs["duration"]
        if "resolution" in kwargs:
            payload["resolution"] = kwargs["resolution"]
        if "aspect_ratio" in kwargs:
            payload["aspect_ratio"] = kwargs["aspect_ratio"]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=180)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.warning(f"AIML API video generation failed: {resp.status} — {error_text[:200]}")
                        return None

                    data = await resp.json()
                    generation_id = data.get("generation_id", data.get("id", ""))

                    if not generation_id:
                        logger.warning(f"AIML API returned no generation_id for {model_id}")
                        return None

                    return {
                        "generation_id": str(generation_id),
                        "model": model_id,
                        "provider": "aiml",
                        "provider_path": provider,
                        "cost": kwargs.get("estimated_cost", 0.0),
                    }

        except Exception as e:
            logger.warning(f"AIML API video generation error for {model_id}: {e}")
            return None

    async def get_video_status(self, generation_id: str, provider_path: str = "minimax") -> dict | None:
        """Check the status of an async video generation.

        Returns:
            dict with 'status' ('processing', 'completed', 'failed'),
            'url' (video URL if completed), or None on error.
        """
        import aiohttp

        url = f"{self.VIDEO_BASE_URL}/{provider_path}/generation"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        params = {"generation_id": generation_id}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, params=params, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status != 200:
                        return None

                    data = await resp.json()
                    status = data.get("status", "processing")

                    result = {"status": status}

                    if status == "completed":
                        video_data = data.get("video", data.get("output", {}))
                        if isinstance(video_data, dict):
                            result["url"] = video_data.get("url", "")
                        elif isinstance(video_data, list) and video_data:
                            result["url"] = video_data[0].get("url", "") if isinstance(video_data[0], dict) else str(video_data[0])
                        elif isinstance(video_data, str):
                            result["url"] = video_data

                    return result

        except Exception as e:
            logger.warning(f"AIML API video status check error: {e}")
            return None


class FalProvider(MediaProvider):
    """fal.ai provider — best for open-weights FLUX.2 models.

    fal.ai hosts FLUX.2 dev, dev-turbo, klein-9B at lower cost than AIML API.
    Used as secondary provider for open-weights models.
    """

    BASE_URL = "https://fal.run"

    def __init__(self):
        self.api_key = os.environ.get("FAL_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def generate_image(self, model_id: str, prompt: str, **kwargs) -> dict | None:
        """Generate an image via fal.ai.

        Args:
            model_id: fal.ai model ID (e.g., "fal-ai/flux/schnell")
            prompt: Text prompt
            **kwargs: image_size, num_inference_steps, etc.

        Returns:
            dict with 'url', 'model', 'cost' on success, None on failure.
        """
        import aiohttp

        url = f"{self.BASE_URL}/{model_id}"
        headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "prompt": prompt,
        }
        if "image_size" in kwargs:
            payload["image_size"] = kwargs["image_size"]
        elif "size" in kwargs:
            payload["image_size"] = kwargs["size"]
        if "num_inference_steps" in kwargs:
            payload["num_inference_steps"] = kwargs["num_inference_steps"]
        if "seed" in kwargs:
            payload["seed"] = kwargs["seed"]
        if "negative_prompt" in kwargs:
            payload["negative_prompt"] = kwargs["negative_prompt"]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=180)
                ) as resp:
                    if resp.status != 200:
                        return None

                    data = await resp.json()
                    images = data.get("images", [])
                    if not images:
                        return None

                    image_url = images[0].get("url", "") if isinstance(images[0], dict) else str(images[0])

                    if not image_url:
                        return None

                    return {
                        "url": image_url,
                        "model": model_id,
                        "provider": "fal",
                        "cost": kwargs.get("estimated_cost", 0.0),
                    }

        except Exception as e:
            logger.warning(f"fal.ai image generation error for {model_id}: {e}")
            return None

    async def generate_video(self, model_id: str, prompt: str, **kwargs) -> dict | None:
        """fal.ai video generation (async, similar to AIML API)."""
        # fal.ai uses a queue-based system — submit to /queue/submit, poll /queue/status
        import aiohttp

        url = f"https://queue.fal.run/{model_id}/submit"
        headers = {
            "Authorization": f"Key {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "prompt": prompt,
        }
        if "image_url" in kwargs:
            payload["image_url"] = kwargs["image_url"]
        if "duration" in kwargs:
            payload["duration"] = kwargs["duration"]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
                    request_id = data.get("request_id", "")
                    if not request_id:
                        return None
                    return {
                        "generation_id": request_id,
                        "model": model_id,
                        "provider": "fal",
                        "provider_path": "fal",
                        "cost": kwargs.get("estimated_cost", 0.0),
                    }
        except Exception as e:
            logger.warning(f"fal.ai video generation error: {e}")
            return None

    async def get_video_status(self, generation_id: str, provider_path: str = "fal") -> dict | None:
        """Poll fal.ai queue for video status."""
        import aiohttp

        url = f"https://queue.fal.run/fal-ai/{generation_id}/status"
        headers = {"Authorization": f"Key {self.api_key}"}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()
                    status_raw = data.get("status", "IN_QUEUE")
                    # Map fal.ai status to our format
                    if status_raw == "COMPLETED":
                        result_url = f"https://queue.fal.run/fal-ai/{generation_id}"
                        async with session.get(
                            result_url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)
                        ) as resp2:
                            result_data = await resp2.json()
                            video_data = result_data.get("video", {})
                            video_url = video_data.get("url", "") if isinstance(video_data, dict) else ""
                            return {"status": "completed", "url": video_url}
                    elif status_raw in ("IN_QUEUE", "IN_PROGRESS"):
                        return {"status": "processing"}
                    else:
                        return {"status": "failed"}
        except Exception as e:
            logger.warning(f"fal.ai video status check error: {e}")
            return None


class MediaProviderManager:
    """Multi-provider failover manager.

    Tries providers in order: AIML API → fal.ai → (OpenRouter as last resort).
    Returns the first successful result.
    """

    def __init__(self):
        self.providers = [
            AIMLProvider(),
            FalProvider(),
        ]

    def get_available_providers(self) -> list:
        """Return list of available providers."""
        return [p for p in self.providers if p.is_available()]

    async def generate_image(self, model_id: str, prompt: str, **kwargs) -> dict | None:
        """Try each available provider until one succeeds.

        Returns dict with 'url', 'model', 'provider', 'cost' on success, None on failure.
        """
        for provider in self.providers:
            if not provider.is_available():
                continue
            result = await provider.generate_image(model_id, prompt, **kwargs)
            if result:
                return result
        logger.warning(f"All providers failed for image generation: {model_id}")
        return None

    async def generate_video(self, model_id: str, prompt: str, **kwargs) -> dict | None:
        """Try each available provider for video generation."""
        for provider in self.providers:
            if not provider.is_available():
                continue
            result = await provider.generate_video(model_id, prompt, **kwargs)
            if result:
                return result
        logger.warning(f"All providers failed for video generation: {model_id}")
        return None

    async def poll_video(self, generation_id: str, provider: str, provider_path: str = "minimax",
                         max_wait: int = 300, poll_interval: int = 5) -> dict | None:
        """Poll for video completion. Returns dict with 'url' when ready, None on timeout/failure."""
        import time

        # Find the right provider for polling
        poll_provider = None
        for p in self.providers:
            if p.__class__.__name__.lower().startswith(provider[:3]) and p.is_available():
                poll_provider = p
                break

        if not poll_provider:
            # Default to AIML
            poll_provider = self.providers[0]

        start = time.time()
        while time.time() - start < max_wait:
            status = await poll_provider.get_video_status(generation_id, provider_path)
            if not status:
                await asyncio_sleep(poll_interval)
                continue

            if status.get("status") == "completed":
                return {"url": status.get("url", ""), "status": "completed"}
            elif status.get("status") == "failed":
                logger.warning(f"Video generation failed: {generation_id}")
                return None

            await asyncio_sleep(poll_interval)

        logger.warning(f"Video generation timed out after {max_wait}s: {generation_id}")
        return None


async def asyncio_sleep(seconds: float):
    """Wrapper for asyncio.sleep — avoids importing asyncio at module level."""
    import asyncio
    await asyncio.sleep(seconds)