"""
Timuclaude Phase 5b Test Suite
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


# ============================================================
# TEST 1: OpenRouter Config Exists and is Valid
# ============================================================
def test_openrouter_config() -> bool:
    """Test that OpenRouter config exists and is valid YAML."""
    print("\n=== OPENROUTER CONFIG TESTS ===")
    
    import yaml
    
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "litellm-openrouter.yaml")
    if not os.path.isfile(config_path):
        print(f"  FAIL: litellm-openrouter.yaml missing")
        return False
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    # Check models
    model_names = [m["model_name"] for m in config.get("model_list", [])]
    expected = ["timuclaude", "glm-5.2", "deepseek-v4-pro", "kimi-k2.6", 
                "minimax-m3", "nemotron-3-ultra", "gpt-oss-120b"]
    
    for m in expected:
        if m not in model_names:
            print(f"  FAIL: missing model {m}")
            return False
    
    # Check uses OpenRouter
    for m in config["model_list"]:
        model_str = m["litellm_params"]["model"]
        if "openrouter" not in model_str:
            print(f"  FAIL: {m['model_name']} doesn't use OpenRouter: {model_str}")
            return False
    
    # Check fallbacks
    if "fallbacks" not in config:
        print(f"  FAIL: no fallbacks")
        return False
    
    print(f"  OK: {len(model_names)} models, all OpenRouter, fallbacks present")
    print(f"  1/1 passed")
    return True


# ============================================================
# TEST 2: Ollama Config Still Exists
# ============================================================
def test_ollama_config() -> bool:
    """Test that only OpenRouter config exists (Ollama removed)."""
    print("\n=== CONFIG CLEANUP TESTS ===")
    
    # Ollama config should NOT exist (we shifted to OpenRouter)
    ollama_path = os.path.join(os.path.dirname(__file__), "..", "config", "litellm-ollama.yaml")
    if os.path.isfile(ollama_path):
        print(f"  FAIL: litellm-ollama.yaml should not exist (OpenRouter only)")
        return False
    
    print(f"  OK: no Ollama config (OpenRouter only)")
    print(f"  1/1 passed")
    return True


# ============================================================
# TEST 3: Default Config Auto-Detects Backend
# ============================================================
def test_auto_detect_config() -> bool:
    """Test that default litellm.yaml is OpenRouter config."""
    print("\n=== DEFAULT CONFIG TESTS ===")
    
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "litellm.yaml")
    if not os.path.isfile(config_path):
        print(f"  FAIL: litellm.yaml missing")
        return False
    
    import yaml
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    model_names = [m["model_name"] for m in config.get("model_list", [])]
    expected = ["timuclaude", "glm-5.2", "deepseek-v4-pro", "kimi-k2.6",
                "minimax-m3", "nemotron-3-ultra", "gpt-oss-120b"]
    
    for m in expected:
        if m not in model_names:
            print(f"  FAIL: missing model {m}")
            return False
    
    if "fallbacks" not in config:
        print(f"  FAIL: no fallbacks")
        return False
    
    # Verify it's the OpenRouter config (models use openrouter/ prefix)
    for m in config["model_list"]:
        model_str = m["litellm_params"]["model"]
        if "openrouter" not in model_str:
            print(f"  FAIL: {m['model_name']} doesn't use OpenRouter: {model_str}")
            return False
    
    print(f"  OK: litellm.yaml is OpenRouter config ({len(model_names)} models, all OpenRouter, fallbacks present)")
    print(f"  1/1 passed")
    return True


# ============================================================
# TEST 4: Model IDs Correct
# ============================================================
def test_model_ids() -> bool:
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
            print(f"  FAIL: {name} expected {expected_id}, got {actual}")
            return False
        print(f"  OK: {name} → {actual}")
    
    print(f"  {len(expected_ids)}/{len(expected_ids)} passed")
    return True


# ============================================================
# TEST 5: Free Models Available
# ============================================================
def test_free_models() -> bool:
    """Test that free model IDs are defined."""
    print("\n=== FREE MODELS TESTS ===")
    
    if len(OPENROUTER_FREE_MODELS) < 2:
        print(f"  FAIL: only {len(OPENROUTER_FREE_MODELS)} free models")
        return False
    
    for name, model_id in OPENROUTER_FREE_MODELS.items():
        if ":free" not in model_id:
            print(f"  FAIL: {name} ({model_id}) doesn't end with :free")
            return False
        print(f"  OK: {name} → {model_id}")
    
    print(f"  {len(OPENROUTER_FREE_MODELS)}/{len(OPENROUTER_FREE_MODELS)} passed")
    return True


# ============================================================
# TEST 6: API Base Auto-Detect
# ============================================================
def test_api_base() -> bool:
    """Test that API_BASE is always OpenRouter."""
    print("\n=== API BASE TESTS ===")
    
    # API_BASE should always be OpenRouter (no auto-detect)
    assert API_BASE == OPENROUTER_API_BASE, f"Expected OpenRouter ({OPENROUTER_API_BASE}), got {API_BASE}"
    print(f"  OK: API_BASE always OpenRouter ({API_BASE})")
    
    print(f"  1/1 passed")
    return True


# ============================================================
# TEST 7: .env.example Has OpenRouter Key
# ============================================================
def test_env_example() -> bool:
    """Test that .env.example includes OPENROUTER_API_KEY."""
    print("\n=== ENV EXAMPLE TESTS ===")
    
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env.example")
    with open(env_path) as f:
        content = f.read()
    
    if "OPENROUTER_API_KEY" not in content:
        print(f"  FAIL: .env.example missing OPENROUTER_API_KEY")
        return False
    
    if "TIMUCLAUDE_MASTER_KEY" not in content:
        print(f"  FAIL: .env.example missing TIMUCLAUDE_MASTER_KEY")
        return False
    
    print(f"  OK: .env.example has both OPENROUTER_API_KEY and TIMUCLAUDE_MASTER_KEY")
    print(f"  1/1 passed")
    return True


# ============================================================
# TEST 8: Dockerfile Uses Auto-Detect Config
# ============================================================
def test_dockerfile_config() -> bool:
    """Test that Dockerfile references the correct config."""
    print("\n=== DOCKERFILE CONFIG TESTS ===")
    
    dockerfile_path = os.path.join(os.path.dirname(__file__), "..", "Dockerfile")
    with open(dockerfile_path) as f:
        content = f.read()
    
    if "config/litellm.yaml" not in content:
        print(f"  FAIL: Dockerfile doesn't reference litellm.yaml")
        return False
    
    print(f"  OK: Dockerfile uses config/litellm.yaml (auto-detect)")
    print(f"  1/1 passed")
    return True


# ============================================================
# TEST 9: Landing Page Has Updated Pricing
# ============================================================
def test_landing_pricing() -> bool:
    """Test that landing page has updated pricing ($15, $99, $499)."""
    print("\n=== LANDING PRICING TESTS ===")
    
    page_path = os.path.join(os.path.dirname(__file__), "..", "landing_page.html")
    with open(page_path) as f:
        content = f.read()
    
    for price in ["$15", "$99", "$499"]:
        if price not in content:
            print(f"  FAIL: landing page missing {price}")
            return False
    
    print(f"  OK: landing page has updated pricing ($15, $99, $499)")
    print(f"  1/1 passed")
    return True


# ============================================================
# RUN ALL TESTS
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("TIMUCLAUDE — PHASE 5b TEST SUITE (OpenRouter)")
    print("=" * 60)
    
    results = []
    results.append(("OpenRouter Config", test_openrouter_config()))
    results.append(("Ollama Config", test_ollama_config()))
    results.append(("Auto-Detect Config", test_auto_detect_config()))
    results.append(("Model IDs", test_model_ids()))
    results.append(("Free Models", test_free_models()))
    results.append(("API Base", test_api_base()))
    results.append(("Env Example", test_env_example()))
    results.append(("Dockerfile Config", test_dockerfile_config()))
    results.append(("Landing Pricing", test_landing_pricing()))
    
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