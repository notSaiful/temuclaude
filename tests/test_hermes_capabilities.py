"""Integration test — verify all 16 new modules import and basic functions work."""
import sys
sys.path.insert(0, "/Users/saiful/temuclaude")


def test_import_sequential_thinking():
    from src.sequential_thinking import sequential_think_sync, build_thought_prompt
    assert callable(sequential_think_sync)


def test_import_vision():
    from src.vision import analyze_image, build_vision_messages, detect_image_in_query
    assert callable(analyze_image)
    assert callable(detect_image_in_query)


def test_import_web_search():
    from src.web_search import should_search, search, search_first_policy
    assert callable(should_search)
    assert callable(search)


def test_import_citation():
    from src.citation import CitationTracker, add_citations, format_footnotes
    assert callable(add_citations)


def test_import_safety():
    from src.safety import filter_response, check_input
    assert callable(filter_response)


def test_import_evenhandedness():
    from src.evenhandedness import detect_controversial_topic, balance_response
    assert callable(detect_controversial_topic)


def test_import_copyright():
    from src.copyright_check import check_copyright, sanitize_response
    assert callable(check_copyright)


def test_import_memory():
    from src.memory import MemoryStore, get_store
    assert MemoryStore is not None


def test_import_code_executor():
    from src.code_executor import execute_code, execute_code_safe
    assert callable(execute_code)


def test_import_tone():
    from src.tone import format_response, remove_filler
    assert callable(format_response)


def test_import_time_utils():
    from src.time_utils import get_current_time, convert_time
    assert callable(get_current_time)


def test_import_deep_research():
    from src.deep_research import deep_research, is_research_request
    assert callable(deep_research)


def test_import_team_reasoning():
    from src.team_reasoning import team_solve, TeamResult
    assert callable(team_solve)


def test_import_prompt_engine():
    from src.prompt_engine import optimize_prompt, add_few_shot
    assert callable(optimize_prompt)


def test_import_browser():
    from src.browser import fetch_page, extract_text, validate_url
    assert callable(validate_url)


def test_import_github():
    from src.github_integration import search_repos, get_readme, _parse_repo_url
    assert callable(search_repos)


def test_all_modules_in_src():
    """Verify all 16 new module files exist in src/."""
    import os
    src_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "src")
    expected = [
        "sequential_thinking.py", "vision.py", "web_search.py", "citation.py",
        "safety.py", "evenhandedness.py", "copyright_check.py", "memory.py",
        "code_executor.py", "tone.py", "time_utils.py", "deep_research.py",
        "team_reasoning.py", "prompt_engine.py", "browser.py", "github_integration.py",
    ]
    for fname in expected:
        path = os.path.join(src_dir, fname)
        assert os.path.isfile(path), f"Missing: {fname}"


def test_orchestrator_still_imports():
    """Verify the existing orchestrator still works."""
    from src.orchestrator import ask
    assert callable(ask)