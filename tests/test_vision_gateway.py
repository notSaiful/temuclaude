"""Tests for the TemuClaude vision gateway (z.ai GLM-4.6V + GLM-OCR).

No live network calls. HTTP clients are injected fakes. Tests follow the repo's
asyncio.run + sync test_* wrapper pattern (see tests/test_media_pipeline.py).
"""
import asyncio
import os
import sys
import types

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.vision_gateway import (
    build_chat_messages, _extract_chat_content, _try_json,
    extract_image_links, parse_ocr_response, vision_enabled,
)


# ---- pure helpers ----

def test_build_chat_messages_uses_multipart_image_url():
    msgs = build_chat_messages("https://x/y.png", "describe the panels")
    assert msgs[0]["role"] == "user"
    parts = msgs[0]["content"]
    assert parts[0] == {"type": "image_url", "image_url": {"url": "https://x/y.png"}}
    assert parts[1] == {"type": "text", "text": "describe the panels"}


def test_extract_chat_content_from_object():
    resp = types.SimpleNamespace(choices=[types.SimpleNamespace(message=types.SimpleNamespace(content="hello"))])
    assert _extract_chat_content(resp) == "hello"


def test_extract_chat_content_from_dict():
    resp = {"choices": [{"message": {"content": "hi"}}]}
    assert _extract_chat_content(resp) == "hi"


def test_extract_chat_content_missing_raises():
    with pytest.raises(ValueError):
        _extract_chat_content({"choices": []})


def test_try_json_parses_plain_fenced_and_rejects_garbage():
    assert _try_json('{"a": 1}') == {"a": 1}
    assert _try_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert _try_json('```\n[1, 2]\n```') == [1, 2]
    assert _try_json("not json") is None
    assert _try_json("") is None


def test_extract_image_links_collects_visualization_and_image_labels():
    resp = {
        "layout_visualization": ["https://x/viz.png"],
        "layout_details": [[
            {"label": "text", "content": "hi"},
            {"label": "image", "content": "https://x/img.png"},
        ]],
    }
    assert extract_image_links(resp) == ["https://x/viz.png", "https://x/img.png"]


def test_parse_ocr_response_contract():
    resp = {"md_results": "# title", "layout_details": [[]], "data_info": {"num_pages": 1}}
    out = parse_ocr_response(resp)
    assert out["markdown"] == "# title"
    assert out["layout_details"] == [[]]
    assert out["image_links"] == []
    assert out["data_info"] == {"num_pages": 1}
    assert out["raw"] == resp


def test_vision_enabled_reads_flag(monkeypatch):
    monkeypatch.setenv("TEMUCLAUDE_VISION_ENABLED", "true")
    assert vision_enabled() is True
    monkeypatch.setenv("TEMUCLAUDE_VISION_ENABLED", "0")
    assert vision_enabled() is False
    monkeypatch.delenv("TEMUCLAUDE_VISION_ENABLED", raising=False)
    assert vision_enabled() is False