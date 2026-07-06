"""Tests for evenhandedness module."""
import sys
sys.path.insert(0, "/Users/saiful/temuclaude")
from src.evenhandedness import (
    detect_controversial_topic, is_stereotype_risk,
    build_steel_man_prompt, build_opposing_view_prompt,
    build_balance_prompt, CONTROVERSIAL_TOPICS
)
import asyncio


def test_detect_controversial_topic_yes():
    assert detect_controversial_topic("What about gun control laws?") is not None
    assert detect_controversial_topic("Tell me about abortion") is not None
    assert detect_controversial_topic("What about climate policy?") is not None


def test_detect_controversial_topic_no():
    assert detect_controversial_topic("How to cook pasta?") is None
    assert detect_controversial_topic("What is Python?") is None


def test_is_stereotype_risk_yes():
    assert is_stereotype_risk("All those people are lazy") == True
    assert is_stereotype_risk("Every single one of them is corrupt") == True


def test_is_stereotype_risk_no():
    assert is_stereotype_risk("Some people like coffee") == False
    assert is_stereotype_risk("Many factors contribute to inflation") == False


def test_build_steel_man_prompt():
    messages = build_steel_man_prompt("gun control", "more gun control")
    assert len(messages) == 2
    assert "impartial" in messages[0]["content"].lower()


def test_build_opposing_view_prompt():
    messages = build_opposing_view_prompt("gun control", "Some text about guns")
    assert len(messages) == 2


def test_build_balance_prompt():
    messages = build_balance_prompt("Some text about abortion", "abortion")
    assert len(messages) == 2


def test_controversial_topics_not_empty():
    assert len(CONTROVERSIAL_TOPICS) > 10


def test_balance_response_no_controversial():
    from src.evenhandedness import balance_response
    result = asyncio.run(balance_response("How to cook rice?"))
    assert result == "How to cook rice?"