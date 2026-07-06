"""Tests for vision module."""
import sys
sys.path.insert(0, "/Users/saiful/temuclaude")
from src.vision import (
    _is_url, _is_base64_uri, _normalize_image,
    build_vision_messages, detect_image_in_query
)
import pytest


def test_is_url():
    assert _is_url("https://example.com/image.png") == True
    assert _is_url("http://example.com/img.jpg") == True
    assert _is_url("data:image/png;base64,abc") == False
    assert _is_url("/local/path.png") == False


def test_is_base64_uri():
    assert _is_base64_uri("data:image/png;base64,abc123") == True
    assert _is_base64_uri("https://example.com/image.png") == False


def test_build_vision_messages_url():
    messages = build_vision_messages("https://example.com/img.png", "What is this?")
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    content = messages[0]["content"]
    assert any(part["type"] == "text" for part in content)
    assert any(part["type"] == "image_url" for part in content)


def test_build_vision_messages_base64():
    uri = "data:image/png;base64,iVBORw0KGgo="
    messages = build_vision_messages(uri, "Describe this")
    assert len(messages) == 1
    image_part = [p for p in messages[0]["content"] if p["type"] == "image_url"]
    assert len(image_part) == 1


def test_normalize_image_url():
    result = _normalize_image("https://example.com/img.png")
    assert result == "https://example.com/img.png"


def test_normalize_image_base64():
    uri = "data:image/jpeg;base64,abc123"
    result = _normalize_image(uri)
    assert result == uri


def test_detect_image_in_query():
    text = "What's in this image? https://example.com/photo.png"
    result = detect_image_in_query(text)
    assert result is not None
    assert "photo.png" in result


def test_detect_image_in_query_none():
    text = "Just a regular question"
    assert detect_image_in_query(text) is None


def test_normalize_image_invalid():
    with pytest.raises(ValueError):
        _normalize_image("not_a_valid_input_12345")