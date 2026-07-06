"""Tests for deep_research module."""
import sys
import asyncio
sys.path.insert(0, "/Users/saiful/temuclaude")
from src.deep_research import (
    count_words, parse_outline, research_plan,
    research_section, is_research_request, deep_research
)


def test_count_words():
    assert count_words("hello world") == 2
    assert count_words("") == 0
    assert count_words("one two three four") == 4


def test_parse_outline():
    raw = "1. Introduction\n   - Background\n   - Context\n2. Current State\n   - Latest"
    sections = parse_outline(raw)
    assert len(sections) >= 1
    assert "Introduction" in sections[0]["title"]


def test_parse_outline_markdown():
    raw = "## Background\n- History\n- Definitions\n## Analysis\n- Methods"
    sections = parse_outline(raw)
    assert len(sections) >= 2


def test_research_plan_fallback():
    result = asyncio.run(research_plan("AI safety", model_fn=None))
    assert len(result) >= 5
    assert "title" in result[0]


def test_research_section_fallback():
    section = {"title": "Background", "subsections": ["History", "Context"]}
    result = asyncio.run(research_section(section, "AI safety", model_fn=None))
    assert "Background" in result


def test_is_research_request_yes():
    assert is_research_request("Do a deep research on AI safety") == True
    assert is_research_request("Write a comprehensive report on climate change") == True


def test_is_research_request_no():
    assert is_research_request("What is 2+2?") == False
    assert is_research_request("Write a hello world function") == False


def test_deep_research_fallback():
    result = asyncio.run(deep_research("AI safety", model_fn=None, min_words=100))
    assert "report" in result
    assert "word_count" in result
    assert result["sections"] >= 5