"""Layer 2 — adaptive Pro routing (2026-07-17).

Before Layer 2, `budget_profile='max_quality'` forced `tier='hard'` for every Pro
request, so even "What is the capital of France?" ran the full gauntlet (MCTS,
9-model MoA panel, 10-sample self-consistency, QA gate, Z3). After Layer 2,
`determine_tier()` (already computed at orchestrator.py:1112) is honoured for
`max_quality`: trivial/medium Pro queries take the fast tier-dispatch path and
only genuinely hard Pro queries run the gauntlet. `balanced` stays always-hard.

The signal we assert is structural: the hard gauntlet calls `fuse()` (the MoA
panel); the trivial/medium fast paths do not. We spy on `fuse` and assert it is
never entered for trivial/medium Pro queries. The gauntlet may crash on mocked
inputs under the OLD code — that's fine, the spy still records that `fuse` was
called, which is exactly the pre-Layer-2 behavior we're replacing.
"""
import pytest

import src.orchestrator as orch_mod
from src.orchestrator import Temuclaude


class _NoopCache:
    def get(self, *a, **k):
        return None

    def set(self, *a, **k):
        return None


def _wire_fast_path_mocks(monkeypatch, tc, determine_tier_value):
    """Mock everything that could make a real network call or hit the cache/IO,
    so the test is hermetic. Leaves `fuse` to be spied separately by the caller."""
    async def _classify(q):
        return "knowledge"

    async def _noop_projection(q):
        return q

    monkeypatch.setattr(tc, "classify_task", _classify)
    monkeypatch.setattr(tc, "determine_tier", lambda q, t: determine_tier_value)
    monkeypatch.setattr(tc, "project_multimodal_inputs", _noop_projection)
    monkeypatch.setattr(tc, "trigger_professional_skills", lambda q, sp: sp)
    monkeypatch.setattr(orch_mod, "get_cache", lambda: _NoopCache())
    monkeypatch.setattr(tc.logger, "log", lambda **kw: None)


def _spy_fuse(monkeypatch):
    """Replace orchestrator.fuse with a spy. Returns the fuse_called flag dict."""
    fuse_called = {"v": False}
    original_fuse = orch_mod.fuse

    async def spy_fuse(*args, **kwargs):
        fuse_called["v"] = True
        return {"answer": "Gauntlet synthesis answer."}

    monkeypatch.setattr(orch_mod, "fuse", spy_fuse)
    # Restore is handled by monkeypatch teardown; no manual finally needed.
    return fuse_called


@pytest.mark.asyncio
async def test_max_quality_trivial_pro_takes_fast_path(monkeypatch):
    """max_quality + trivial tier -> single-model fast path, NOT the hard gauntlet."""
    tc = Temuclaude()
    _wire_fast_path_mocks(monkeypatch, tc, "trivial")

    calls = []

    async def fake_call(model, messages, **kw):
        calls.append(model)
        return "The capital of France is Paris."

    monkeypatch.setattr(tc, "call_model_with_fallback", fake_call)
    fuse_called = _spy_fuse(monkeypatch)

    result = None
    try:
        result = await tc.complete(
            "What is the capital of France?", budget_profile="max_quality"
        )
    except Exception:
        pass  # gauntlet may crash on mocked inputs under OLD code; signal is fuse_called

    assert fuse_called["v"] is False, "trivial Pro must NOT enter the hard gauntlet (fuse)"
    assert result is not None, "trivial fast path should return without raising"
    assert "Paris" in result
    assert calls == ["deepseek-v4-flash"], f"expected single trivial-path call, got {calls}"


@pytest.mark.asyncio
async def test_max_quality_medium_pro_takes_fast_path(monkeypatch):
    """max_quality + medium tier -> medium fast path, NOT the hard gauntlet."""
    tc = Temuclaude()
    _wire_fast_path_mocks(monkeypatch, tc, "medium")

    async def fake_call(model, messages, **kw):
        return "Photosynthesis converts light energy into chemical energy."

    monkeypatch.setattr(tc, "call_model_with_fallback", fake_call)
    fuse_called = _spy_fuse(monkeypatch)

    try:
        await tc.complete(
            "Explain how photosynthesis works in plants.", budget_profile="max_quality"
        )
    except Exception:
        pass  # medium-branch QA gate may choke on mocked judge output; signal is fuse_called

    assert fuse_called["v"] is False, "medium Pro must NOT enter the hard gauntlet (fuse)"


@pytest.mark.asyncio
async def test_balanced_trivial_pro_still_forces_hard_gauntlet(monkeypatch):
    """balanced is the always-hard compatibility alias: even a trivial query must
    enter the gauntlet (fuse), so callers can't silently receive a cheap draft."""
    tc = Temuclaude()
    _wire_fast_path_mocks(monkeypatch, tc, "trivial")

    async def fake_call(model, messages, **kw):
        return "stubbed gauntlet step"

    monkeypatch.setattr(tc, "call_model_with_fallback", fake_call)
    fuse_called = _spy_fuse(monkeypatch)

    try:
        await tc.complete("hi", budget_profile="balanced")
    except Exception:
        pass  # gauntlet may crash on mocked inputs; signal is fuse_called

    assert fuse_called["v"] is True, "balanced must force the hard gauntlet even for trivial queries"