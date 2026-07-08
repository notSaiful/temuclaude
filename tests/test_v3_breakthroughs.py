import pytest
import asyncio
from src.reasoning_tree import MCTSReasoningSearch, ReasoningNode, PRMVerdict
from src.ui_ux.loop_engine import LoopEngine
from src.orchestrator import Temuclaude

def test_marrp_cosine_similarity():
    """Verify that the cosine similarity calculator (MARRP) yields mathematically correct scores."""
    search = MCTSReasoningSearch(call_model_func=None)
    
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    assert search._calculate_cosine_similarity(vec1, vec2) == pytest.approx(1.0)
    
    vec3 = [0.0, 1.0, 0.0]
    assert search._calculate_cosine_similarity(vec1, vec3) == pytest.approx(0.0)
    
    vec4 = [-1.0, 0.0, 0.0]
    assert search._calculate_cosine_similarity(vec1, vec4) == pytest.approx(-1.0)

def test_cgarh_autocomplete():
    """Verify that CGARH correctly balances mismatched brackets, braces, and quotes."""
    tc = Temuclaude()
    
    # 1. Unclosed braces
    unclosed_braces = "function test() {\n  return 123;"
    assert tc._compiler_guided_autocomplete(unclosed_braces) == "function test() {\n  return 123;\n}"
    
    # 2. Unclosed brackets and parenthesis
    unclosed_mix = "const arr = [1, 2, (3"
    assert tc._compiler_guided_autocomplete(unclosed_mix) == "const arr = [1, 2, (3)]"
    
    # 3. Unclosed quotes
    unclosed_quote = "const str = 'hello"
    assert tc._compiler_guided_autocomplete(unclosed_quote) == "const str = 'hello'"
    
    # 4. Correct code block wrapper updates
    wrapped_unclosed = "Here is the code:\n```javascript\nfunction run() {\n  console.log('hi');\n```"
    assert "}" in tc._compiler_guided_autocomplete(wrapped_unclosed)

def test_aprh_extraction_and_hydration():
    """Verify that APRH component extraction and hydration behaves surgically on source files."""
    engine = LoopEngine()
    
    sample_js_code = (
        "import React from 'react';\n\n"
        "class Header extends React.Component {\n"
        "  render() {\n"
        "    return <h1>Title</h1>;\n"
        "  }\n"
        "}\n\n"
        "function Navigation() {\n"
        "  return <nav>Links</nav>;\n"
        "}\n\n"
        "class App extends React.Component {\n"
        "  render() {\n"
        "    return <div>Main</div>;\n"
        "  }\n"
        "}"
    )
    
    # Extract Class
    header_block = engine._extract_component(sample_js_code, "Header")
    assert header_block is not None
    assert "class Header" in header_block
    assert "Title" in header_block
    assert "Navigation" not in header_block
    
    # Extract Function
    nav_block = engine._extract_component(sample_js_code, "Navigation")
    assert nav_block is not None
    assert "function Navigation" in nav_block
    assert "Links" in nav_block
    assert "Header" not in nav_block
    
    # Hydrate (Replace)
    refined_nav = (
        "function Navigation() {\n"
        "  return <nav>Home | About</nav>;\n"
        "}"
    )
    hydrated = engine._hydrate_component(sample_js_code, "Navigation", refined_nav)
    assert "Home | About" in hydrated
    assert "Links" not in hydrated
    assert "class Header" in hydrated  # Maintained unchanged

@pytest.mark.asyncio
async def test_dprm_p2p_consensus():
    """Verify that the peer-to-peer reward model uses consensus and escalates on split votes."""
    calls = []
    
    # Mock model call function that returns specific scores
    async def mock_call(model, messages, max_tokens):
        calls.append((model, messages))
        if "llama" in model:
            return "8"
        if "mistral" in model:
            return "8"
        if "glm" in model:
            return "2"  # split vote!
        # primary model fallback
        return "10"
        
    search = MCTSReasoningSearch(call_model_func=mock_call, prm_model="primary-prm")
    
    # Test low consensus variance escalation
    score = await search._score_step(query="2+2", context="init", step="let x = 4")
    
    # Confirm primary model fallback was invoked due to low consensus
    assert any(c[0] == "primary-prm" for c in calls)
    assert score == pytest.approx(1.0) # primary model returned 10 -> 1.0


def test_structured_prm_verdict_parser():
    search = MCTSReasoningSearch(call_model_func=None)

    verdict = search._parse_prm_verdict("score=7; label=logic_gap", source="test")
    assert isinstance(verdict, PRMVerdict)
    assert verdict.score == pytest.approx(0.7)
    assert verdict.label == "logic_gap"
    assert verdict.needs_escalation is True
    assert verdict.source == "test"

    correct = search._parse_prm_verdict("score=9; label=correct", source="test")
    assert correct.score == pytest.approx(0.9)
    assert correct.label == "correct"
    assert correct.confidence >= 0.85
    assert correct.needs_escalation is False


@pytest.mark.asyncio
async def test_structured_prm_peer_consensus_label():
    async def mock_call(model, messages, max_tokens):
        return "9"

    search = MCTSReasoningSearch(call_model_func=mock_call, prm_model="primary-prm")
    verdict = await search._score_step_structured(query="2+2", context="init", step="2+2=4")

    assert verdict.score == pytest.approx(0.9)
    assert verdict.label == "correct"
    assert verdict.confidence >= 0.9
    assert verdict.needs_escalation is False
    assert verdict.source == "peer_consensus"


@pytest.mark.asyncio
async def test_structured_prm_primary_escalation_label():
    calls = []

    async def mock_call(model, messages, max_tokens):
        calls.append(model)
        if model == "primary-prm":
            return "score=4; label=unsupported"
        if "llama" in model:
            return "9"
        if "mistral" in model:
            return "1"
        return "9"

    search = MCTSReasoningSearch(call_model_func=mock_call, prm_model="primary-prm")
    verdict = await search._score_step_structured(query="2+2", context="init", step="2+2=5")

    assert "primary-prm" in calls
    assert verdict.score == pytest.approx(0.4)
    assert verdict.label == "unsupported"
    assert verdict.needs_escalation is True
    assert verdict.source == "primary_after_peer_disagreement"
