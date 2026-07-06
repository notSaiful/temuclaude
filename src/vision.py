"""
Temuclaude Vision Analysis Module
Multimodal image understanding via vision-capable models.

Uses Kimi K2.6 (has vision capability in MODEL_POOL) via Ollama Cloud.
Supports image URLs and base64 data URIs.

Based on:
- GPT-4V system card: visual reasoning via multimodal LLMs
- Kimi K2.6: 1M context, vision support, Ollama Cloud
"""
import asyncio
import base64
import re
import os
from typing import Optional, List
from openai import AsyncOpenAI

from .models import OLLAMA_API_BASE


def _get_api_key() -> str:
    """Get Ollama API key from environment."""
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    key = os.environ.get("OLLAMA_API_KEY", "")
    if not key and os.path.isfile(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("OLLAMA_API_KEY="):
                    key = line.strip().split("=", 1)[1].strip('"').strip("'")
                    break
    return key


def _is_url(image: str) -> bool:
    """Check if the image input is a URL."""
    return image.startswith(("http://", "https://"))


def _is_base64_uri(image: str) -> bool:
    """Check if the image input is a base64 data URI."""
    return image.startswith("data:image/")


def _file_to_base64(path: str) -> str:
    """Convert a local file path to base64 data URI."""
    ext = os.path.splitext(path)[1].lower().lstrip(".")
    if ext not in ("png", "jpeg", "jpg", "gif", "webp"):
        ext = "png"
    if ext == "jpg":
        ext = "jpeg"
    with open(path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/{ext};base64,{data}"


def _normalize_image(image: str) -> str:
    """Normalize image input to URL or base64 data URI."""
    if _is_url(image) or _is_base64_uri(image):
        return image
    if os.path.isfile(image):
        return _file_to_base64(image)
    raise ValueError(f"Invalid image input: must be URL, base64 URI, or file path. Got: {image[:50]}")


def build_vision_messages(image: str, question: str) -> List[dict]:
    """Build OpenAI-compatible messages for vision model.

    Args:
        image: URL, base64 data URI, or local file path
        question: Question about the image

    Returns:
        Messages list with image content
    """
    image_url = _normalize_image(image)

    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": question},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        }
    ]


async def analyze_image(
    image: str,
    question: str,
    model: str = "kimi-k2.6",
    api_key: Optional[str] = None,
) -> str:
    """Analyze an image with a vision-capable model.

    Args:
        image: URL, base64 data URI, or local file path
        question: Question about the image
        model: Model name from MODEL_POOL (must have vision capability)
        api_key: Ollama API key (auto-detected if None)

    Returns:
        Model's response text
    """
    if api_key is None:
        api_key = _get_api_key()

    if not api_key:
        raise RuntimeError("No Ollama API key found. Set OLLAMA_API_KEY in .env or environment.")

    client = AsyncOpenAI(base_url=OLLAMA_API_BASE, api_key=api_key)
    messages = build_vision_messages(image, question)

    # Get the ollama_tag for the model
    from .models import MODEL_POOL
    ollama_tag = MODEL_POOL.get(model, {}).get("ollama_tag", f"{model}:cloud")

    response = await client.chat.completions.create(
        model=ollama_tag,
        messages=messages,
        max_tokens=2000,
    )
    return response.choices[0].message.content


async def describe_image(image: str, model: str = "kimi-k2.6", api_key: Optional[str] = None) -> str:
    """Generate a detailed description of an image."""
    return await analyze_image(
        image,
        "Describe this image in detail. What do you see? Include objects, people, "
        "colors, text, setting, and any notable features.",
        model=model,
        api_key=api_key,
    )


async def extract_text_from_image(image: str, model: str = "kimi-k2.6", api_key: Optional[str] = None) -> str:
    """Extract text from an image (OCR via multimodal model)."""
    return await analyze_image(
        image,
        "Extract all text visible in this image. Return only the extracted text, "
        "preserving formatting and layout as much as possible.",
        model=model,
        api_key=api_key,
    )


async def compare_images(
    images: List[str],
    question: str,
    model: str = "kimi-k2.6",
    api_key: Optional[str] = None,
) -> str:
    """Compare multiple images.

    Args:
        images: List of image URLs, base64 URIs, or file paths
        question: Comparison question
        model: Vision-capable model name
        api_key: Ollama API key

    Returns:
        Comparison result
    """
    if api_key is None:
        api_key = _get_api_key()

    if not api_key:
        raise RuntimeError("No Ollama API key found.")

    client = AsyncOpenAI(base_url=OLLAMA_API_BASE, api_key=api_key)

    content = [{"type": "text", "text": question}]
    for img in images:
        image_url = _normalize_image(img)
        content.append({"type": "image_url", "image_url": {"url": image_url}})

    messages = [{"role": "user", "content": content}]

    from .models import MODEL_POOL
    ollama_tag = MODEL_POOL.get(model, {}).get("ollama_tag", f"{model}:cloud")

    response = await client.chat.completions.create(
        model=ollama_tag,
        messages=messages,
        max_tokens=2000,
    )
    return response.choices[0].message.content


def detect_image_in_query(text: str) -> Optional[str]:
    """Detect if the query references an image.

    Returns the image path/URL if detected, None otherwise.
    """
    # URL pattern
    url_match = re.search(r"https?://\S+\.(?:png|jpg|jpeg|gif|webp|bmp)", text, re.IGNORECASE)
    if url_match:
        return url_match.group(0)

    # File path pattern
    path_match = re.search(r"(/[\w\-/.]+\.(?:png|jpg|jpeg|gif|webp|bmp))", text, re.IGNORECASE)
    if path_match:
        path = path_match.group(1)
        if os.path.isfile(path):
            return path

    return None