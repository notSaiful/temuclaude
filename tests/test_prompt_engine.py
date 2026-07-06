"""Tests for prompt_engine module."""
import sys
import asyncio
sys.path.insert(0, "/Users/saiful/temuclaude")
from src.prompt_engine import (
    optimize_prompt, add_few_shot, add_chain_of_thought,
    add_self_consistency, modular_prompt, add_role, add_structured_output,
    optimize_prompt_with_llm, a_b_test
)


def test_optimize_prompt():
    prompt = "Answer the user's question."
    result = optimize_prompt(prompt)
    assert "You are" in result  # Should add role


def test_optimize_prompt_already_has_role():
    prompt = "You are a helpful assistant. Answer questions."
    result = optimize_prompt(prompt)
    assert "You are" in result


def test_add_few_shot():
    prompt = "Answer questions."
    examples = [{"input": "What is 2+2?", "output": "4"}]
    result = add_few_shot(prompt, examples)
    assert "Example 1" in result
    assert "2+2" in result


def test_add_few_shot_empty():
    result = add_few_shot("prompt", [])
    assert result == "prompt"


def test_add_chain_of_thought():
    result = add_chain_of_thought("Answer questions.")
    assert "step" in result.lower()
    assert "reasoning" in result.lower()


def test_add_self_consistency():
    result = add_self_consistency("Answer questions.", n=5)
    assert "5" in result
    assert "independent" in result.lower()


def test_modular_prompt():
    sections = {"role": "You are an expert.", "rules": "Be concise.", "format": "Use prose."}
    result = modular_prompt(sections)
    assert "Role" in result
    assert "Rules" in result
    assert "Format" in result


def test_add_role():
    result = add_role("Answer questions.", "an expert")
    assert "You are an expert" in result


def test_add_role_already_has():
    result = add_role("You are a helper. Answer.", "an expert")
    assert result.startswith("You are a helper")


def test_add_structured_output():
    result = add_structured_output("Answer.", "JSON format")
    assert "Output format" in result
    assert "JSON" in result


def test_optimize_prompt_with_llm_fallback():
    result = asyncio.run(optimize_prompt_with_llm("Answer.", model_fn=None))
    assert "You are" in result


def test_a_b_test_fallback():
    result = asyncio.run(a_b_test("prompt A", "prompt B step by step", [], model_fn=None))
    assert "recommendation" in result