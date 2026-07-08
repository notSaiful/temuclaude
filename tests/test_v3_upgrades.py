"""
Tests for TemuClaude v3 upgrades:
- Hybrid Model Pool Config
- MCTS Reasoning Tree Search
- Generator-Discriminator Self-Play Loop
- Implicit Thought Tags parsing/stripping
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from src.models import MODEL_POOL, OPENROUTER_MODELS
from src.reasoning_tree import ReasoningNode, MCTSReasoningSearch
from src.orchestrator import Temuclaude


def test_hybrid_model_pool_config():
    """Verify that new models are defined in the pool and mapped correctly."""
    assert "llama-3.3-70b-instruct" in MODEL_POOL
    assert "gemini-2.0-flash" in MODEL_POOL
    assert "mistral-large-2" in MODEL_POOL
    assert "claude-3.5-sonnet" in MODEL_POOL

    assert MODEL_POOL["llama-3.3-70b-instruct"]["role"] == "specialist"
    assert MODEL_POOL["gemini-2.0-flash"]["role"] == "worker"
    assert MODEL_POOL["mistral-large-2"]["role"] == "specialist"
    assert MODEL_POOL["claude-3.5-sonnet"]["role"] == "frontier_fallback"

    assert OPENROUTER_MODELS["llama-3.3-70b-instruct"] == "meta-llama/llama-3.3-70b-instruct"
    assert OPENROUTER_MODELS["gemini-2.0-flash"] == "google/gemini-2.0-flash"
    assert OPENROUTER_MODELS["mistral-large-2"] == "mistralai/mistral-large-2"
    assert OPENROUTER_MODELS["claude-3.5-sonnet"] == "anthropic/claude-3.5-sonnet"


@pytest.mark.asyncio
async def test_mcts_reasoning_search():
    """Test step-level search tree execution using mock callbacks."""
    async def mock_model_call(model, messages, tokens):
        # Return a simple next step based on the prompt content
        user_msg = messages[-1]["content"]
        if "Determine if the next reasoning step is correct" in user_msg:
            return "9"  # PRM score 0.9
        elif "Is the final answer correct?" in user_msg:
            return "YES"  # ORM result YES
        elif "Complete the remaining steps" in user_msg:
            return "Therefore, the answer is 42."
        else:
            return "Next logical reasoning step."

    searcher = MCTSReasoningSearch(
        call_model_func=mock_model_call,
        prm_model="gemini-2.0-flash",
        policy_model="deepseek-v4-pro",
        branch_factor=2,
        max_depth=2,
        iterations=2
    )

    res = await searcher.search("What is the meaning of life?", initial_thought="Thinking.")
    assert "path" in res
    assert "confidence" in res
    assert len(res["path"]) > 0
    assert res["confidence"] > 0.0


@pytest.mark.asyncio
async def test_generator_discriminator_loop():
    """Verify that the generator-discriminator self-play loop corrects flaws correctly."""
    tc = Temuclaude()
    
    # Mock call_model_with_fallback to simulate flaws and corrections
    async def mock_call(model, messages, max_tokens=None, **kwargs):
        content = messages[-1]["content"]
        if "Analyze the draft solution above" in content:
            if "flawed solution" in content:
                return "The logic contains an arithmetic slip on Step 2."
            return "NO_ISSUES"
        elif "Correct the draft solution according to the critique" in content:
            return "Repaired solution without arithmetic slip."
        return "Standard response."

    with patch.object(tc, 'call_model_with_fallback', new=mock_call):
        # Case 1: No flaws detected
        ans1 = await tc.generator_discriminator_loop("What is 12x12?", "The solution is 144.")
        assert ans1 == "The solution is 144."

        # Case 2: Flaws corrected
        ans2 = await tc.generator_discriminator_loop("What is 13x17?", "flawed solution: 13x17 is 211.")
        assert ans2 == "Repaired solution without arithmetic slip."


@pytest.mark.asyncio
async def test_thought_tags_injection_and_stripping():
    """Verify that thought tags are appended to system prompts and stripped from final answers."""
    tc = Temuclaude()

    # Verify formatting tag injection in call_model
    async def mock_completions_create(*args, **kwargs):
        # Capture the messages sent to the mock OpenAI client
        messages = kwargs.get("messages", [])
        # Find the system message content
        sys_content = next((msg["content"] for msg in messages if msg["role"] == "system"), "")
        
        mock_response = AsyncMock()
        mock_choice = AsyncMock()
        if "CRITICAL" in sys_content:
            mock_choice.message.content = "<thought>Thinking about 2+2.</thought>The answer is 4."
        else:
            mock_choice.message.content = "The answer is 4."
        mock_response.choices = [mock_choice]
        return mock_response

    tc.client.chat.completions.create = mock_completions_create

    # 1. Check call_model appends directives and returns tags
    messages = [{"role": "system", "content": "You are a math helper."}, {"role": "user", "content": "2+2"}]
    res = await tc.call_model("deepseek-v4-pro", messages)
    assert "<thought>" in res
    assert "The answer is 4." in res

    # 2. Check complete strips tags before returning to user
    with patch.object(tc, 'classify_task', return_value="math"), \
         patch.object(tc, 'determine_tier', return_value="trivial"), \
         patch.object(tc, 'project_multimodal_inputs', side_effect=lambda x: x):
        
        # Override call_model_with_fallback to return tagged result
        async def mock_call_fallback(model, messages, max_tokens=None, **kwargs):
            return "<thought>Thinking about 2+2.</thought>The answer is 4."
        
        with patch.object(tc, 'call_model_with_fallback', new=mock_call_fallback):
            final_ans = await tc.complete("2+2", budget_profile="balanced")
            # The final returned answer should have the <thought> block stripped
            assert "<thought>" not in final_ans
            assert "The answer is 4." in final_ans
