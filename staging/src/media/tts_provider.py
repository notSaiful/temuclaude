"""
Temuclaude TTS Provider

Calls the AIML API TTS endpoint: POST /v1/tts
Returns audio URL for the generated speech.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TTSProvider:
    """AIML API TTS provider.

    All 26 TTS models on AIML API use the same endpoint:
      POST https://api.aimlapi.com/v1/tts
      Body: {"model": "model_id", "text": "...", "voice": "...", "response_format": "mp3"}
      Response: {"audio": {"url": "https://..."}}

    So we only need one provider class.
    """

    BASE_URL = "https://api.aimlapi.com/v1"
    TTS_ENDPOINT = f"{BASE_URL}/tts"

    def __init__(self):
        self.api_key = os.environ.get("AIML_API_KEY", "")

    def is_available(self) -> bool:
        return bool(self.api_key)

    async def generate_speech(
        self,
        model_id: str,
        text: str,
        voice: str = "alloy",
        response_format: str = "mp3",
        speed: float = 1.0,
        **kwargs,
    ) -> Optional[dict]:
        """Generate speech from text via AIML API TTS endpoint.

        Args:
            model_id: TTS model ID (e.g., "openai/tts-1", "elevenlabs/v3_alpha")
            text: Text to convert to speech (max 4096 chars)
            voice: Voice name (e.g., "alloy", "coral", "nova")
            response_format: Audio format ("mp3", "opus", "aac", "flac", "wav", "pcm")
            speed: Speech speed (0.25 to 4.0, default 1.0)
            **kwargs: Additional model-specific parameters

        Returns:
            Dict with:
              - 'url': Audio URL
              - 'model': Model ID
              - 'provider': 'aiml'
              - 'cost': Estimated cost
            Or None on failure.
        """
        if not self.is_available():
            logger.warning("AIML API key not set — TTS generation unavailable")
            return None

        import aiohttp

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Truncate text to max length
        if len(text) > 4096:
            text = text[:4096]
            logger.warning(f"Text truncated to 4096 chars for {model_id}")

        payload = {
            "model": model_id,
            "text": text,
            "voice": voice,
            "response_format": response_format,
            "speed": speed,
        }

        # Add optional parameters
        if "style" in kwargs:
            payload["style"] = kwargs["style"]

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.TTS_ENDPOINT,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.warning(
                            f"TTS generation failed for {model_id}: {resp.status} — {error_text[:200]}"
                        )
                        return None

                    data = await resp.json()

                    # Extract audio URL
                    audio_data = data.get("audio", {})
                    audio_url = ""
                    if isinstance(audio_data, dict):
                        audio_url = audio_data.get("url", "")
                    elif isinstance(audio_data, str):
                        audio_url = audio_data

                    if not audio_url:
                        logger.warning(f"TTS returned no audio URL for {model_id}")
                        return None

                    # Extract cost info if available
                    meta = data.get("meta", {})
                    usage = meta.get("usage", {}) if isinstance(meta, dict) else {}
                    usd_spent = usage.get("usd_spent", 0.0) if isinstance(usage, dict) else 0.0

                    return {
                        "url": audio_url,
                        "model": model_id,
                        "provider": "aiml",
                        "cost": usd_spent or kwargs.get("estimated_cost", 0.0),
                        "voice": voice,
                        "format": response_format,
                    }

        except Exception as e:
            logger.warning(f"TTS generation error for {model_id}: {e}")
            return None


class TTSProviderManager:
    """Multi-provider failover for TTS.

    Currently only AIML API (all TTS models are there).
    OpenRouter has gpt-audio but it's not a standard TTS endpoint.
    """

    def __init__(self):
        self.providers = [TTSProvider()]

    def get_available_providers(self) -> list:
        return [p for p in self.providers if p.is_available()]

    async def generate_speech(self, model_id: str, text: str, **kwargs) -> Optional[dict]:
        """Try each available provider until one succeeds."""
        for provider in self.providers:
            if not provider.is_available():
                continue
            result = await provider.generate_speech(model_id, text, **kwargs)
            if result:
                return result
        logger.warning(f"All TTS providers failed for: {model_id}")
        return None