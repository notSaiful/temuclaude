"""Tests for tone module."""
import sys
sys.path.insert(0, "/Users/saiful/temuclaude")
from src.tone import (
    remove_filler, simplify_wordy, bullets_to_prose,
    enforce_conciseness, count_questions, check_one_question,
    format_response
)


def test_remove_filler():
    text = "Certainly! The answer is 42."
    result = remove_filler(text)
    assert "Certainly" not in result
    assert "42" in result


def test_remove_filler_multiple():
    text = "Absolutely! Great! Let me help you with that. The answer is 42."
    result = remove_filler(text)
    assert "Absolutely" not in result
    assert "Great" not in result


def test_simplify_wordy():
    text = "In order to run the code, you need Python."
    result = simplify_wordy(text)
    assert "In order to" not in result
    assert "run" in result.lower()


def test_simplify_wordy_due_to():
    text = "Due to the fact that Python is installed, it works."
    result = simplify_wordy(text)
    assert "Due to the fact" not in result
    assert "because" in result.lower()


def test_bullets_to_prose():
    text = "Items:\n- apple\n- banana\n- cherry"
    result = bullets_to_prose(text)
    # Short bullet lists should be converted to prose
    assert "- " not in result or "apple" in result


def test_enforce_conciseness():
    text = "Certainly! In order to explain, due to the fact that Python is great, it works well."
    result = enforce_conciseness(text)
    assert "Certainly" not in result
    assert "In order to" not in result


def test_count_questions():
    assert count_questions("What is this? How does it work?") == 2
    assert count_questions("This is a statement.") == 0


def test_check_one_question_ok():
    ok, count = check_one_question("What is Python?")
    assert ok == True
    assert count == 1


def test_check_one_question_violation():
    ok, count = check_one_question("What is this? How does it work? Why?")
    assert ok == False
    assert count == 3


def test_format_response_professional():
    text = "Certainly! The answer is here:\n- item 1\n- item 2\n- item 3"
    result = format_response(text, style="professional")
    assert "Certainly" not in result