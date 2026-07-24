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
from typing import Any

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