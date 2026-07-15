"""
Temuclaude Phase 5b Test Suite
Tests: OpenRouter config, auto-detect backend, model IDs, pricing
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models import (
    OPENROUTER_MODELS, OPENROUTER_FREE_MODELS,
    OLLAMA_API_BASE, OPENROUTER_API_BASE, API_BASE,
    MODEL_POOL, TASK_MODEL_MAP,
)


def _fail(message):
    print(f"  FAIL: {message}")
    raise AssertionError(message)


def _run_manual_test(test_func):
    try:
        test_func()
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False


# ============================================================
# TEST 1: OpenRouter Config Exists and is Valid
# ============================================================
def test_openrouter_config():
    """Test that OpenRouter config exists and is valid YAML."""
    print("\n=== OPENROUTER CONFIG TESTS ===")
    
    import yaml
    
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "litellm-openrouter.yaml")
    if not os.path.isfile(config_path):
        _fail("litellm-openrouter.yaml missing")
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Check models
    model_names = [m["model_name"] for m in config.get("model_list", [])]
    expected = ["temuclaude", "glm-5.2", "deepseek-v4-pro", "kimi-k2.6", 
                "minimax-m3", "nemotron-3-ultra", "gpt-oss-120b"]
    
    for m in expected:
        if m not in model_names:
            _fail(f"missing model {m}")
    
    # Check uses OpenRouter
    for m in config["model_list"]:
        model_str = m["litellm_params"]["model"]
        if "openrouter" not in model_str:
            _fail(f"{m['model_name']} doesn't use OpenRouter: {model_str}")
    
    # Check fallbacks
    if "fallbacks" not in config:
        _fail("no fallbacks")
    
    print(f"  OK: {len(model_names)} models, all OpenRouter, fallbacks present")
    print(f"  1/1 passed")


# ============================================================
# TEST 2: Ollama Config Still Exists
# ============================================================
def test_ollama_config():
    """Test that only OpenRouter config exists (Ollama removed)."""
    print("\n=== CONFIG CLEANUP TESTS ===")
    
    # Ollama config should NOT exist (we shifted to OpenRouter)
    ollama_path = os.path.join(os.path.dirname(__file__), "..", "config", "litellm-ollama.yaml")
    if os.path.isfile(ollama_path):
        _fail("litellm-ollama.yaml should not exist (OpenRouter only)")
    
    print(f"  OK: no Ollama config (OpenRouter only)")
    print(f"  1/1 passed")


# ============================================================
# TEST 3: Default Config Auto-Detects Backend
# ============================================================
def test_auto_detect_config():
    """Test that default litellm.yaml is OpenRouter config."""
    print("\n=== DEFAULT CONFIG TESTS ===")
    
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "litellm.yaml")
    if not os.path.isfile(config_path):
        _fail("litellm.yaml missing")
    
    import yaml
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    model_names = [m["model_name"] for m in config.get("model_list", [])]
    expected = ["temuclaude", "glm-5.2", "deepseek-v4-pro", "kimi-k2.6",
                "minimax-m3", "nemotron-3-ultra", "gpt-oss-120b"]
    
    for m in expected:
        if m not in model_names:
            _fail(f"missing model {m}")
    
    if "fallbacks" not in config:
        _fail("no fallbacks")
    
    # Verify it's the OpenRouter config (models use openrouter/ prefix)
    for m in config["model_list"]:
        model_str = m["litellm_params"]["model"]
        if "openrouter" not in model_str:
            _fail(f"{m['model_name']} doesn't use OpenRouter: {model_str}")
    
    print(f"  OK: litellm.yaml is OpenRouter config ({len(model_names)} models, all OpenRouter, fallbacks present)")
    print(f"  1/1 passed")


# ============================================================
# TEST 4: Model IDs Correct
# ============================================================
def test_model_ids():
    """Test that OpenRouter model IDs are correct."""
    print("\n=== MODEL ID TESTS ===")
    
    expected_ids = {
        "glm-5.2": "z-ai/glm-5.2",
        "deepseek-v4-pro": "deepseek/deepseek-v4-pro",
        "kimi-k2.6": "moonshotai/kimi-k2.6",
        "minimax-m3": "minimax/minimax-m3",
        "nemotron-3-ultra": "nvidia/nemotron-3-ultra-550b-a55b",
        "gpt-oss-120b": "openai/gpt-oss-120b",
    }
    
    for name, expected_id in expected_ids.items():
        actual = OPENROUTER_MODELS.get(name)
        if actual != expected_id:
            _fail(f"{name} expected {expected_id}, got {actual}")
        print(f"  OK: {name} → {actual}")
    
    print(f"  {len(expected_ids)}/{len(expected_ids)} passed")


# ============================================================
# TEST 5: Low-cost Models Available
# ============================================================
def test_free_models():
    """Test that current low-cost model IDs are defined."""
    print("\n=== LOW-COST MODEL TESTS ===")
    
    if len(OPENROUTER_FREE_MODELS) < 2:
        _fail(f"only {len(OPENROUTER_FREE_MODELS)} low-cost models")
    
    for name, model_id in OPENROUTER_FREE_MODELS.items():
        if model_id.endswith(":free"):
            _fail(f"{name} still uses removed provider alias {model_id}")
        print(f"  OK: {name} → {model_id}")
    
    print(f"  {len(OPENROUTER_FREE_MODELS)}/{len(OPENROUTER_FREE_MODELS)} passed")


# ============================================================
# TEST 6: API Base Auto-Detect
# ============================================================
def test_api_base():
    """Test that API_BASE is set correctly based on OPENROUTER_API_KEY."""
    print("\n=== API BASE TESTS ===")
    
    # API_BASE should be OpenRouter if key is set, Ollama if not
    if "OPENROUTER_API_KEY" in os.environ:
        assert API_BASE == OPENROUTER_API_BASE, f"Expected OpenRouter, got {API_BASE}"
        print(f"  OK: OPENROUTER_API_KEY set → OpenRouter ({API_BASE})")
    else:
        assert API_BASE == OLLAMA_API_BASE, f"Expected Ollama, got {API_BASE}"
        print(f"  OK: no OPENROUTER_API_KEY → Ollama ({API_BASE})")
    
    print(f"  1/1 passed")


# ============================================================
# TEST 7: .env.example Has OpenRouter Key
# ============================================================
def test_env_example():
    """Test that .env.example includes OPENROUTER_API_KEY."""
    print("\n=== ENV EXAMPLE TESTS ===")
    
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env.example")
    with open(env_path) as f:
        content = f.read()
    
    if "OPENROUTER_API_KEY" not in content:
        _fail(".env.example missing OPENROUTER_API_KEY")
    
    if "TEMUCLAUDE_MASTER_KEY" not in content:
        _fail(".env.example missing TEMUCLAUDE_MASTER_KEY")
    
    print(f"  OK: .env.example has both OPENROUTER_API_KEY and TEMUCLAUDE_MASTER_KEY")
    print(f"  1/1 passed")


# ============================================================
# TEST 8: Dockerfile Uses Auto-Detect Config
# ============================================================
def test_dockerfile_config():
    """Test that Dockerfile references the correct config."""
    print("\n=== DOCKERFILE CONFIG TESTS ===")
    
    dockerfile_path = os.path.join(os.path.dirname(__file__), "..", "Dockerfile")
    with open(dockerfile_path) as f:
        content = f.read()
    
    if "config/litellm.yaml" not in content:
        _fail("Dockerfile doesn't reference litellm.yaml")
    
    print(f"  OK: Dockerfile uses config/litellm.yaml (auto-detect)")
    print(f"  1/1 passed")


# ============================================================
# TEST 9: Landing Page Has Updated Pricing
# ============================================================
def test_landing_pricing():
    """Test that landing page has updated pricing ($15, $99, $499)."""
    print("\n=== LANDING PRICING TESTS ===")
    
    page_path = os.path.join(os.path.dirname(__file__), "..", "landing_page.html")
    with open(page_path) as f:
        content = f.read()
    
    for price in ["$15", "$99", "$499"]:
        if price not in content:
            _fail(f"landing page missing {price}")
    
    print(f"  OK: landing page has updated pricing ($15, $99, $499)")
    print(f"  1/1 passed")


# ============================================================
# RUN ALL TESTS
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("TEMUCLAUDE — PHASE 5b TEST SUITE (OpenRouter)")
    print("=" * 60)
    
    results = []
    results.append(("OpenRouter Config", _run_manual_test(test_openrouter_config)))
    results.append(("Ollama Config", _run_manual_test(test_ollama_config)))
    results.append(("Auto-Detect Config", _run_manual_test(test_auto_detect_config)))
    results.append(("Model IDs", _run_manual_test(test_model_ids)))
    results.append(("Free Models", _run_manual_test(test_free_models)))
    results.append(("API Base", _run_manual_test(test_api_base)))
    results.append(("Env Example", _run_manual_test(test_env_example)))
    results.append(("Dockerfile Config", _run_manual_test(test_dockerfile_config)))
    results.append(("Landing Pricing", _run_manual_test(test_landing_pricing)))
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_passed = False
    
    print(f"\n{'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    sys.exit(0 if all_passed else 1)
