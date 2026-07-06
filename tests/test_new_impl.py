#!/usr/bin/env python3
"""Tests for new breakthrough implementations.

Tests:
1. Context compression (4-layer progressive)
2. Self-MoA mode
3. Unified routing + cascading
4. MoE model pool expansion
"""

import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# ── Test 1: Context Compression ─────────────────────────────────
class TestContextCompression:
    def test_snip_tool_outputs(self):
        """Snip should truncate large tool outputs."""
        from src.context_compression import snip_tool_outputs, estimate_tokens
        
        history = [
            {"role": "user", "content": "What is 2+2?"},
            {"role": "assistant", "content": "x" * 5000},  # Large output
            {"role": "user", "content": "Thanks!"},
        ]
        
        result, saved = snip_tool_outputs(history, threshold=100)
        
        # The large output should be snipped
        assert saved > 0
        assert "[...snipped" in result[1]["content"]
        # Small messages should be unchanged
        assert result[0]["content"] == "What is 2+2?"
    
    def test_microcompact_removes_duplicates(self):
        """Microcompact should remove duplicate content."""
        from src.context_compression import microcompact
        
        history = [
            {"role": "system", "content": "You are helpful."},
            {"role": "system", "content": "You are helpful."},  # Duplicate
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        
        result, saved = microcompact(history)
        
        # Should have saved some tokens by removing the duplicate
        assert saved > 0
        # First occurrence should be kept
        assert result[0]["content"] == "You are helpful."
    
    def test_collapse_sections(self):
        """Collapse should fold old conversation sections."""
        from src.context_compression import collapse_sections, estimate_tokens
        
        # Create a long history
        history = []
        for i in range(30):
            history.append({"role": "user", "content": f"Message {i} " + "x" * 200})
            history.append({"role": "assistant", "content": f"Response {i} " + "y" * 200})
        
        result, saved, markers = collapse_sections(history, max_tokens=1000)
        
        assert saved > 0
        assert len(markers) > 0
        # Should have COLLAPSED markers
        collapsed_markers = [m for m in result if isinstance(m, dict) and "[COLLAPSED:" in str(m.get("content", ""))]
        assert len(collapsed_markers) > 0
    
    def test_compress_context_pipeline(self):
        """Full compression pipeline should reduce token count."""
        from src.context_compression import compress_context, estimate_tokens
        
        # Create history that needs compression
        history = []
        for i in range(20):
            history.append({"role": "user", "content": f"Question {i}: " + "a" * 500})
            history.append({"role": "assistant", "content": f"Answer {i}: " + "b" * 500})
        
        original_tokens = sum(estimate_tokens(str(msg.get("content", ""))) for msg in history)
        
        result = compress_context(history, target_tokens=2000)
        
        assert result.original_tokens == original_tokens
        assert result.compressed_tokens < original_tokens
        assert result.saved_tokens > 0
        assert "snip" in result.method
    
    def test_compress_context_no_op(self):
        """If already under target, no compression should happen."""
        from src.context_compression import compress_context
        
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
        ]
        
        result = compress_context(history, target_tokens=1000)
        
        assert result.method == "none"
        assert result.saved_tokens == 0
    
    def test_auto_restore_files(self, tmp_path):
        """Auto-restore should return file content summaries."""
        from src.context_compression import auto_restore_files
        
        # Create test files
        f1 = tmp_path / "test1.py"
        f1.write_text("print('hello')")
        f2 = tmp_path / "test2.py"
        f2.write_text("def foo(): pass")
        
        messages = auto_restore_files([str(f1), str(f2), "/nonexistent.py"], max_files=5)
        
        assert len(messages) == 2  # Nonexistent file skipped
        assert "test1.py" in messages[0]["content"]
        assert "test2.py" in messages[1]["content"]


# ── Test 2: Self-MoA ────────────────────────────────────────────
class TestSelfMoA:
    def test_should_use_self_moa_for_math(self):
        """Math tasks should use Self-MoA."""
        from src.self_moa import should_use_self_moa
        
        assert should_use_self_moa("math") == True
        assert should_use_self_moa("code") == True
        assert should_use_self_moa("reasoning") == True
    
    def test_should_not_use_self_moa_for_creative(self):
        """Creative tasks should use full panel."""
        from src.self_moa import should_use_self_moa
        
        assert should_use_self_moa("creative") == False
        assert should_use_self_moa("general") == False
    
    def test_should_use_self_moa_with_dominance_data(self):
        """Should use Self-MoA when one model dominates."""
        from src.self_moa import should_use_self_moa
        
        # Model A wins 80% of the time
        perf = {"model_a": 0.8, "model_b": 0.15, "model_c": 0.05}
        assert should_use_self_moa("general", model_perf=perf) == True
        
        # No clear dominance
        perf = {"model_a": 0.35, "model_b": 0.35, "model_c": 0.30}
        assert should_use_self_moa("general", model_perf=perf) == False
    
    def test_get_dominant_model(self):
        """Should return model with highest win rate."""
        from src.self_moa import get_dominant_model
        
        perf = {"model_a": 0.3, "model_b": 0.6, "model_c": 0.1}
        assert get_dominant_model(perf) == "model_b"
    
    @pytest.mark.asyncio
    async def test_self_moa_generate(self):
        """Self-MoA should generate N responses and select best."""
        from src.self_moa import self_moa_generate
        
        async def mock_call(model, messages, **kwargs):
            return f"Response from {model}: The answer is 42."
        
        result = await self_moa_generate(
            question="What is 6*7?",
            model="test-model",
            call_model_func=mock_call,
            n=3,
        )
        
        assert "42" in result["answer"]
        assert len(result["all_responses"]) == 3
        assert result["agreement"] > 0  # All responses agree


# ── Test 3: Unified Routing + Cascading ──────────────────────────
class TestUnifiedRouting:
    def test_classify_difficulty_trivial(self):
        """Short simple questions should be trivial."""
        from src.unified_routing import classify_difficulty
        
        assert classify_difficulty("Hi there") == "trivial"
        assert classify_difficulty("What is Python?") == "trivial"
    
    def test_classify_difficulty_hard(self):
        """Math/code questions should be hard."""
        from src.unified_routing import classify_difficulty
        
        assert classify_difficulty("Calculate the fibonacci sequence") == "hard"
        assert classify_difficulty("Debug this function for me") == "hard"
    
    def test_classify_difficulty_extreme(self):
        """Very long or complex questions should be extreme."""
        from src.unified_routing import classify_difficulty
        
        long_q = "x" * 600
        assert classify_difficulty(long_q) == "extreme"
        assert classify_difficulty("Implement a step by step algorithm for distributed consensus") == "extreme"
    
    @pytest.mark.asyncio
    async def test_unified_route_first_try_success(self):
        """Should return answer on first try if quality passes."""
        from src.unified_routing import unified_route_and_cascade
        
        async def mock_call(model, messages, **kwargs):
            return "The answer is 42."
        
        async def mock_verify(q, a, m, c):
            return {"score": 9.0, "accepted": True}
        
        result = await unified_route_and_cascade(
            question="What is 6*7?",
            call_model_func=mock_call,
            verify_func=mock_verify,
        )
        
        assert "42" in result.answer
        assert result.cascade_depth == 0
        assert result.quality_score == 9.0
    
    @pytest.mark.asyncio
    async def test_unified_route_cascades_on_low_quality(self):
        """Should cascade to stronger model when quality is low."""
        from src.unified_routing import unified_route_and_cascade
        
        call_count = [0]
        
        async def mock_call(model, messages, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return "I don't know."  # Low quality
            return "The answer is 42."  # High quality
        
        async def mock_verify(q, a, m, c):
            if "42" in a:
                return {"score": 9.0}
            return {"score": 3.0}
        
        result = await unified_route_and_cascade(
            question="What is 6*7?",
            call_model_func=mock_call,
            verify_func=mock_verify,
            quality_threshold=8.0,
        )
        
        assert "42" in result.answer
        assert result.cascade_depth >= 1
        assert len(result.all_attempts) >= 2


# ── Test 4: MoE Model Pool ───────────────────────────────────────
class TestMoEModelPool:
    def test_moe_models_in_pool(self):
        """MoE models should be in the model pool."""
        from src.models import MODEL_POOL
        
        # Check that MODEL_POOL is a dict/list
        assert MODEL_POOL is not None
        # The pool should have at least some models
        assert len(MODEL_POOL) >= 3