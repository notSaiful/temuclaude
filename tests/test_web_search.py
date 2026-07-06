"""Tests for web_search module."""
import sys
sys.path.insert(0, "/Users/saiful/temuclaude")
from src.web_search import (
    should_search, format_search_query, search_first_policy
)


def test_should_search_yes():
    assert should_search("What is the latest version of Python?") == True
    assert should_search("What is the current price of Bitcoin?") == True
    assert should_search("Who is the president of France?") == True


def test_should_search_no():
    assert should_search("What is 2+2?") == False
    assert should_search("Define photosynthesis") == False
    assert should_search("How does a CPU work?") == False
    assert should_search("Explain the theory of relativity") == False


def test_format_search_query():
    result = format_search_query("What is the latest version of Python?")
    assert "what is" not in result.lower()
    assert "version of Python" in result


def test_format_search_query_strips_punctuation():
    result = format_search_query("Who is the current president?")
    assert not result.endswith("?")
    assert not result.endswith(".")


def test_search_first_policy_no_search():
    result = should_search("Solve x^2 + 2x + 1 = 0")
    assert result == False


def test_search_first_policy_search():
    result = should_search("What is the latest news today?")
    assert result == True