"""Tests for sequential_thinking module."""
import sys
sys.path.insert(0, "/Users/saiful/temuclaude")
from src.sequential_thinking import (
    build_thought_prompt, parse_thought, evaluate_thought,
    sequential_think_sync, DEFAULT_MAX_STEPS
)


def test_build_thought_prompt():
    messages = build_thought_prompt("What is 2+2?", [], 1)
    assert len(messages) == 2
    assert "system" in messages[0]["role"]
    assert "What is 2+2" in messages[1]["content"]


def test_build_thought_prompt_with_thoughts():
    thoughts = [{"step": 1, "content": "First step", "status": "active"}]
    messages = build_thought_prompt("What is 2+2?", thoughts, 2)
    assert "[Step 1]" in messages[1]["content"]
    assert "Generate step 2" in messages[1]["content"]


def test_parse_thought_normal():
    t = parse_thought("The answer is 4.", 1)
    assert t["step"] == 1
    assert t["is_final"] == False
    assert t["status"] == "active"


def test_parse_thought_final():
    t = parse_thought("FINAL ANSWER: 42", 3)
    assert t["is_final"] == True
    assert t["content"] == "42"
    assert t["status"] == "final"


def test_parse_thought_revision():
    t = parse_thought("REVISE step 1: Actually, the answer is 5", 2)
    assert t["status"] == "revised"
    assert t["revision_of"] == 1


def test_parse_thought_branch():
    t = parse_thought("BRANCH from step 2: Alternative approach", 4)
    assert t["status"] == "branched"
    assert t["branch_from"] == 2


def test_evaluate_thought_good():
    t = {"content": "Because we know that 2 plus 2 equals 4, therefore the answer is 4."}
    score = evaluate_thought(t, "What is 2+2?")
    assert score > 0.5


def test_evaluate_thought_empty():
    t = {"content": ""}
    score = evaluate_thought(t, "test")
    assert score == 0.0


def test_sequential_think_sync():
    def mock_fn(messages):
        return "FINAL ANSWER: 4"
    result = sequential_think_sync("What is 2+2?", model_fn=mock_fn, max_steps=5)
    assert result["steps_used"] == 1
    assert result["final_answer"] == "4"


def test_sequential_think_max_steps():
    def mock_fn(messages):
        return "Thinking step..."
    result = sequential_think_sync("test", model_fn=mock_fn, max_steps=3)
    assert result["steps_used"] == 3