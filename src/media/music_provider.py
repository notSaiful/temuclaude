"""
Temuclaude Music Provider

Calls the AIML API music generation endpoint.
Music generation is ASYNC: POST to submit → GET to poll → retrieve audio URL.

API endpoint: POST https://api.aimlapi.com/v2/generate/audio
Poll: GET https://api.aimlapi.com/v2/generate/audio/{generation_id}
"""

import os
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class MusicProvider:
    """AIML API music generation provider.

    All music models on AIML API use the async pattern:
      POST /v2/generate/audio → returns generation_id
      GET /v2/generate/audio/{id} → returns status + audio URL when done

    Models: minimax/music-2.0, minimax/music-1.5, minimax/music-2.6,
            minimax/music-cover, elevenlabs/eleven_music
    """

    BASE_URL = "https://api.aimlapi.com/v2"
    SUBMIT_ENDPOINT = f"{BASE_URL}/generate/audio"
    POLL_ENDPOINT = f"{BASE_URL}/generate/audio"  # + /{generation_id}

    def __init__(self):
        self.api_key = os.environ.get("AIML_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def generate_music(
        self,
        model_id: str,
        prompt: str,
        lyrics: str = "",
        duration_ms: int = 30000,
        format: str = "mp3",
        sample_rate: int = 44100,
        **kwargs,
    ) -> Optional[dict]:
        """Generate music via AIML API (async submit → poll → retrieve).

        Args:
            model_id: Music model ID (e.g., "minimax/music-2.0")
            prompt: Music description/style prompt
            lyrics: Optional lyrics text
            duration_ms: Duration in milliseconds
            format: Audio format ("mp3", "wav")
            sample_rate: Sample rate
            **kwargs: Additional model-specific parameters

        Returns:
            Dict with 'url', 'model', 'provider', 'cost' on success, None on failure.
        """
        if not self.is_available():
            logger.warning("AIML API key not set — music generation unavailable")
            return None

        import aiohttp

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model_id,
            "prompt": prompt,
        }

        # Add optional parameters
        if lyrics:
            payload["lyrics"] = lyrics
        if duration_ms:
            payload["duration_ms"] = duration_ms
        if format:
            payload["format"] = format
        if sample_rate:
            payload["sample_rate"] = sample_rate

        # Pass through any additional kwargs
        for key in ("title", "tags", "negative_tags", "audio_url", "reference_audio_url"):
            if key in kwargs:
                payload[key] = kwargs[key]

        try:
            # Step 1: Submit generation request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.SUBMIT_ENDPOINT,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.warning(
                            f"Music submit failed for {model_id}: {resp.status} — {error_text[:200]}"
                        )
                        return None

                    data = await resp.json()
                    generation_id = data.get("generation_id", data.get("id", ""))

                    if not generation_id:
                        # Some models return the result directly (sync mode)
                        audio_url = self._extract_audio_url(data)
                        if audio_url:
                            return {
                                "url": audio_url,
                                "model": model_id,
                                "provider": "aiml",
                                "cost": data.get("meta", {}).get("usage", {}).get("usd_spent", 0.0)
                                        if isinstance(data.get("meta"), dict) else 0.0,
                            }
                        logger.warning(f"Music submit returned no generation_id for {model_id}")
                        return None

            # Step 2: Poll for result
            result = await self._poll_music_status(generation_id, model_id, headers)
            return result

        except asyncio.TimeoutError:
            logger.warning(f"Music generation timed out for {model_id}")
            return None
        except Exception as e:
            logger.warning(f"Music generation error for {model_id}: {e}")
            return None

    async def _poll_music_status(
        self,
        generation_id: str,
        model_id: str,
        headers: dict,
        max_wait: int = 300,
        poll_interval: int = 5,
    ) -> Optional[dict]:
        """Poll the AIML API for music generation completion.

        Args:
            generation_id: The generation ID from submit
            model_id: Model ID for logging
            headers: Auth headers
            max_wait: Maximum wait time in seconds (default 5 min)
            poll_interval: Polling interval in seconds

        Returns:
            Dict with audio URL on success, None on failure/timeout.
        """
        import aiohttp

        poll_url = f"{self.POLL_ENDPOINT}/{generation_id}"
        elapsed = 0

        async with aiohttp.ClientSession() as session:
            while elapsed < max_wait:
                try:
                    async with session.get(
                        poll_url,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30),
                    ) as resp:
                        if resp.status != 200:
                            logger.warning(f"Music poll failed: {resp.status}")
                            await asyncio.sleep(poll_interval)
                            elapsed += poll_interval
                            continue

                        data = await resp.json()

                        # Check status
                        status = data.get("status", "").lower()

                        if status in ("completed", "succeeded", "success", "done"):
                            audio_url = self._extract_audio_url(data)
                            if audio_url:
                                cost = (
                                    data.get("meta", {}).get("usage", {}).get("usd_spent", 0.0)
                                    if isinstance(data.get("meta"), dict)
                                    else 0.0
                                )
                                return {
                                    "url": audio_url,
                                    "model": model_id,
                                    "provider": "aiml",
                                    "generation_id": generation_id,
                                    "cost": cost,
                                }
                            logger.warning(f"Music completed but no audio URL for {model_id}")
                            return None

                        elif status in ("failed", "error", "cancelled"):
                            error_msg = data.get("error", data.get("message", "unknown"))
                            logger.warning(f"Music generation failed for {model_id}: {error_msg}")
                            return None

                        # Still processing — wait and retry
                        await asyncio.sleep(poll_interval)
                        elapsed += poll_interval

                except Exception as e:
                    logger.warning(f"Music poll error: {e}")
                    await asyncio.sleep(poll_interval)
                    elapsed += poll_interval

        logger.warning(f"Music generation timed out after {max_wait}s for {model_id}")
        return None

    def _extract_audio_url(self, data: dict) -> str:
        """Extract audio URL from API response."""
        # Try common response shapes
        audio = data.get("audio", {})
        if isinstance(audio, dict):
            url = audio.get("url", "")
            if url:
                return url
        elif isinstance(audio, str):
            return audio

        # Try alternative fields
        for key in ("url", "audio_url", "output_url", "download_url", "result"):
            val = data.get(key, "")
            if val and isinstance(val, str):
                return val

        # Try outputs list
        outputs = data.get("outputs", [])
        if isinstance(outputs, list) and outputs:
            first = outputs[0]
            if isinstance(first, dict):
                return first.get("url", "")
            elif isinstance(first, str):
                return first

        return ""


class MusicProviderManager:
    """Multi-provider failover for music generation.

    Currently only AIML API (all music models are there).
    Can be extended to add Suno, Udio direct APIs in the future.
    """

    def __init__(self):
        self.providers = [MusicProvider()]

    def get_available_providers(self) -> list:
        return [p for p in self.providers if p.is_available()]

    async def generate_music(self, model_id: str, prompt: str, **kwargs) -> Optional[dict]:
        """Try each available provider until one succeeds."""
        for provider in self.providers:
            if not provider.is_available():
                continue
            result = await provider.generate_music(model_id, prompt, **kwargs)
            if result:
                return result
        logger.warning(f"All music providers failed for: {model_id}")
        return None