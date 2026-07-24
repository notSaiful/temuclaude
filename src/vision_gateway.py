"""TemuClaude vision gateway — z.ai GLM-4.6V (understanding) + GLM-OCR (text extraction).

Feature-flagged via TEMUCLAUDE_VISION_ENABLED. The engine's existing text /v1 route is
untouched. This module is consumed by the POST /v1/vision/understand route in api_server.py.

z.ai request/response shapes verified from docs.z.ai on 2026-07-24:
  GLM-4.6V -> POST https://api.z.ai/api/paas/v4/chat/completions  (OpenAI-compatible)
  GLM-OCR  -> POST https://api.z.ai/api/paas/v4/layout_parsing    (custom endpoint)
"""
from __future__ import annotations

import json
import os
from typing import Any, Awaitable, Callable

import aiohttp
from openai import AsyncOpenAI

ZAI_BASE_URL = "https://api.z.ai/api/paas/v4"
DEFAULT_VISION_MODEL = "glm-4.6v"
DEFAULT_OCR_MODEL = "glm-ocr"


def build_chat_messages(image_url: str, prompt: str) -> list[dict]:
    """OpenAI-style multipart messages for a z.ai vision chat call."""
    return [
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": prompt},
            ],
        }
    ]


def _extract_chat_content(resp: Any) -> str:
    """Pull choices[0].message.content from an OpenAI-style response (object or dict)."""
    choices = getattr(resp, "choices", None)
    if choices is None and isinstance(resp, dict):
        choices = resp.get("choices")
    if not choices:
        raise ValueError("z.ai chat response missing choices")
    first = choices[0]
    message = getattr(first, "message", None) if not isinstance(first, dict) else first.get("message")
    content = getattr(message, "content", None) if not isinstance(message, dict) else message.get("content")
    if content is None:
        raise ValueError("z.ai chat response missing message content")
    return content


def _try_json(text: str) -> Any:
    """Parse JSON from a model string, tolerating ```json fences. Return None if not JSON."""
    text = (text or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        pass
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 3:
            candidate = parts[1]
            if candidate[:4].lower() == "json":
                candidate = candidate[4:]
            candidate = candidate.strip()
            try:
                return json.loads(candidate)
            except (ValueError, TypeError):
                pass
    return None


def extract_image_links(resp: dict) -> list[str]:
    """Collect image URLs from a GLM-OCR layout_parsing response."""
    links: list[str] = []
    for url in (resp.get("layout_visualization") or []):
        if isinstance(url, str):
            links.append(url)
    for page in (resp.get("layout_details") or []):
        for item in (page or []):
            if isinstance(item, dict) and item.get("label") == "image":
                content = item.get("content")
                if isinstance(content, str):
                    links.append(content)
    return links


def parse_ocr_response(resp: dict) -> dict:
    """Normalize a GLM-OCR layout_parsing response into a stable contract."""
    return {
        "markdown": resp.get("md_results", "") or "",
        "layout_details": resp.get("layout_details") or [],
        "image_links": extract_image_links(resp),
        "data_info": resp.get("data_info"),
        "raw": resp,
    }


def vision_enabled() -> bool:
    return os.environ.get("TEMUCLAUDE_VISION_ENABLED", "").strip().lower() in ("1", "true", "yes", "on")


class ZaiVisionClient:
    """Calls z.ai for vision understanding (GLM-4.6V) and OCR (GLM-OCR).

    HTTP clients are injectable for testing: pass ``chat_client`` (an object exposing
    ``await chat.completions.create(model=..., messages=...)``) and ``ocr_post`` (an
    ``async (url, payload) -> dict``). ``from_env()`` builds the real clients.
    """

    def __init__(
        self,
        *,
        api_key: str,
        vision_model: str = DEFAULT_VISION_MODEL,
        ocr_model: str = DEFAULT_OCR_MODEL,
        base_url: str = ZAI_BASE_URL,
        chat_client: Any = None,
        ocr_post: Callable[[str, dict], Awaitable[dict]] | None = None,
    ) -> None:
        self.api_key = api_key
        self.vision_model = vision_model
        self.ocr_model = ocr_model
        self.base_url = base_url
        self._chat_client = chat_client
        self._ocr_post = ocr_post or self._aiohttp_ocr_post

    @classmethod
    def from_env(cls) -> "ZaiVisionClient":
        api_key = os.environ.get("ZAI_API_KEY", "").strip()
        vision_model = os.environ.get("TEMUCLAUDE_VISION_MODEL", DEFAULT_VISION_MODEL).strip() or DEFAULT_VISION_MODEL
        chat_client = AsyncOpenAI(base_url=ZAI_BASE_URL, api_key=api_key) if api_key else None
        return cls(api_key=api_key, vision_model=vision_model, chat_client=chat_client)

    async def understand(self, image_url: str, prompt: str) -> dict:
        if self._chat_client is None:
            raise RuntimeError("ZAI_API_KEY not set; vision chat client unavailable")
        messages = build_chat_messages(image_url, prompt)
        try:
            resp = await self._chat_client.chat.completions.create(
                model=self.vision_model, messages=messages, max_tokens=4000
            )
        except Exception as exc:  # surface z.ai errors (e.g. wrong model string) verbatim
            raise RuntimeError(f"z.ai vision chat call failed ({self.vision_model}): {exc}") from exc
        content = _extract_chat_content(resp)
        return {"task": "understand", "model": self.vision_model, "content": content, "parsed": _try_json(content)}

    async def extract_text(self, image_url: str) -> dict:
        payload = {"model": self.ocr_model, "file": image_url}
        resp = await self._ocr_post(f"{self.base_url}/layout_parsing", payload)
        result: dict = {"task": "extract_text", "model": self.ocr_model}
        result.update(parse_ocr_response(resp))
        return result

    async def _aiohttp_ocr_post(self, url: str, payload: dict) -> dict:
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=120)
            ) as r:
                data = await r.json()
                if r.status != 200:
                    raise RuntimeError(f"z.ai OCR error {r.status}: {data}")
                return data
