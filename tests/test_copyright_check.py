"""Tests for copyright_check module."""
import sys
sys.path.insert(0, "/Users/saiful/temuclaude")
from src.copyright_check import (
    find_quotes, find_quotes_fixed, check_quote_length, check_quote_count,
    check_lyrics, check_poems, check_copyright, sanitize_response
)


def test_find_quotes():
    text = 'He said "hello world" and left'
    quotes = find_quotes(text)
    assert len(quotes) == 1
    assert quotes[0] == "hello world"


def test_find_quotes_fixed():
    text = "He said 'test quote' and left"
    quotes = find_quotes_fixed(text)
    assert len(quotes) >= 1


def test_check_quote_length_ok():
    text = 'He said "short quote" today'
    ok, violations = check_quote_length(text)
    assert ok == True
    assert len(violations) == 0


def test_check_quote_length_violation():
    long_quote = "This is a very long quote that exceeds fifteen words and should be flagged as a copyright violation by the system"
    text = f'He said "{long_quote}" today'
    ok, violations = check_quote_length(text)
    assert ok == False
    assert len(violations) == 1


def test_check_quote_count_ok():
    text = "Just one quote: \"hello\""
    ok, count = check_quote_count(text)
    assert ok == True


def test_check_lyrics_detected():
    text = "Verse 1:\nLa la la la\nyeah yeah yeah\nna na na na"
    assert check_lyrics(text) == True


def test_check_lyrics_not_detected():
    text = "This is a normal paragraph about technology."
    assert check_lyrics(text) == False


def test_check_poems_haiku():
    text = "Cherry blossoms fall\nFloating on the gentle stream\nSpring is here again"
    assert check_poems(text) == True


def test_check_poems_not_detected():
    text = "This is a regular paragraph about programming."
    assert check_poems(text) == False


def test_check_copyright_clean():
    text = "This is a normal response with no quotes or lyrics."
    ok, violations = check_copyright(text)
    assert ok == True


def test_check_copyright_long_quote():
    long_quote = "This is a very long quote that definitely exceeds the fifteen word limit for sure"
    text = f'"{long_quote}"'
    ok, violations = check_copyright(text)
    assert ok == False


def test_sanitize_response_long_quote():
    long_quote = " ".join(["word"] * 20)
    text = f'"{long_quote}"'
    result = sanitize_response(text)
    assert len(result.split()) < 20