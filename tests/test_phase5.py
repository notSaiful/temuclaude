"""
Timuclaude Phase 5 Test Suite
Tests: Cache, start script, Dockerfile, landing page, fly.toml
"""
import sys
import os
import time
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.cache import ResponseCache


# ============================================================
# TEST 1: Cache — Set and Get
# ============================================================
def test_cache_basic() -> bool:
    """Test basic cache set and get operations."""
    print("\n=== CACHE BASIC TESTS ===")
    
    cache = ResponseCache(max_size=100, ttl_seconds=60)
    
    # Set a value
    cache.set("glm-5.2", [{"role": "user", "content": "What is 2+2?"}], "4")
    
    # Get it back
    result = cache.get("glm-5.2", [{"role": "user", "content": "What is 2+2?"}])
    assert result == "4", f"Expected '4', got '{result}'"
    print(f"  OK: set and get — value = '{result}'")
    
    # Get a non-existent key
    result = cache.get("glm-5.2", [{"role": "user", "content": "What is 3+3?"}])
    assert result is None, f"Expected None, got '{result}'"
    print(f"  OK: miss for non-existent key")
    
    print(f"  2/2 passed")
    return True


# ============================================================
# TEST 2: Cache — TTL Expiration
# ============================================================
def test_cache_ttl() -> bool:
    """Test that cache entries expire after TTL."""
    print("\n=== CACHE TTL TESTS ===")
    
    cache = ResponseCache(max_size=100, ttl_seconds=1)  # 1 second TTL
    
    # Set a value
    cache.set("model", [{"role": "user", "content": "test"}], "answer")
    
    # Get immediately — should be cached
    result = cache.get("model", [{"role": "user", "content": "test"}])
    assert result == "answer", f"Expected 'answer', got '{result}'"
    print(f"  OK: value cached before TTL")
    
    # Wait for TTL to expire
    time.sleep(1.5)
    
    # Get after expiry — should be None
    result = cache.get("model", [{"role": "user", "content": "test"}])
    assert result is None, f"Expected None after TTL, got '{result}'"
    print(f"  OK: value expired after TTL")
    
    print(f"  2/2 passed")
    return True


# ============================================================
# TEST 3: Cache — LRU Eviction
# ============================================================
def test_cache_lru() -> bool:
    """Test that LRU eviction removes oldest entries when cache is full."""
    print("\n=== CACHE LRU TESTS ===")
    
    cache = ResponseCache(max_size=3, ttl_seconds=60)
    
    # Fill cache with 3 entries
    cache.set("m1", [{"q": 1}], "a1")
    cache.set("m2", [{"q": 2}], "a2")
    cache.set("m3", [{"q": 3}], "a3")
    
    # All should be present
    assert cache.get("m1", [{"q": 1}]) == "a1"
    assert cache.get("m2", [{"q": 2}]) == "a2"
    assert cache.get("m3", [{"q": 3}]) == "a3"
    print(f"  OK: 3 entries cached")
    
    # Add 4th entry — should evict oldest (m1)
    cache.set("m4", [{"q": 4}], "a4")
    
    # m1 should be evicted
    assert cache.get("m1", [{"q": 1}]) is None, "m1 should be evicted"
    print(f"  OK: oldest entry evicted (m1)")
    
    # m4 should be present
    assert cache.get("m4", [{"q": 4}]) == "a4"
    print(f"  OK: new entry cached (m4)")
    
    # m2 and m3 should still be present
    assert cache.get("m2", [{"q": 2}]) == "a2"
    assert cache.get("m3", [{"q": 3}]) == "a3"
    print(f"  OK: remaining entries intact (m2, m3)")
    
    print(f"  4/4 passed")
    return True


# ============================================================
# TEST 4: Cache — Statistics
# ============================================================
def test_cache_stats() -> bool:
    """Test that cache statistics are tracked correctly."""
    print("\n=== CACHE STATS TESTS ===")
    
    cache = ResponseCache(max_size=100, ttl_seconds=60)
    
    # 2 misses, 1 hit
    cache.set("m", [{"q": 1}], "a")
    cache.get("m", [{"q": 1}])  # hit
    cache.get("m", [{"q": 2}])  # miss
    cache.get("m", [{"q": 3}])  # miss
    
    stats = cache.stats()
    assert stats["hits"] == 1, f"Expected 1 hit, got {stats['hits']}"
    assert stats["misses"] == 2, f"Expected 2 misses, got {stats['misses']}"
    assert stats["size"] == 1, f"Expected size 1, got {stats['size']}"
    assert 0 < stats["hit_rate"] < 1, f"Hit rate should be between 0 and 1: {stats['hit_rate']}"
    print(f"  OK: hits={stats['hits']}, misses={stats['misses']}, hit_rate={stats['hit_rate']:.1%}")
    
    # Clear
    cache.clear()
    stats = cache.stats()
    assert stats["size"] == 0
    assert stats["hits"] == 0
    assert stats["misses"] == 0
    print(f"  OK: clear resets stats")
    
    print(f"  2/2 passed")
    return True


# ============================================================
# TEST 5: start.sh exists and is executable
# ============================================================
def test_start_script() -> bool:
    """Test that start.sh exists, is executable, and has correct content."""
    print("\n=== START SCRIPT TESTS ===")
    
    start_path = os.path.join(os.path.dirname(__file__), "..", "start.sh")
    
    if not os.path.isfile(start_path):
        print(f"  FAIL: start.sh missing")
        return False
    
    with open(start_path) as f:
        content = f.read()
    
    # Check key elements (auto-detect, both backends)
    checks = {
        "TIMUCLAUDE_MASTER_KEY": "TIMUCLAUDE_MASTER_KEY" in content,
        "OPENROUTER_API_KEY": "OPENROUTER_API_KEY" in content,
        "Ollama check": "11434" in content,
        "litellm": "litellm" in content,
        "config/litellm.yaml": "config/litellm.yaml" in content,
        "port 4000": "4000" in content,
    }
    
    for name, ok in checks.items():
        if not ok:
            print(f"  FAIL: start.sh missing '{name}'")
            return False
    
    # Check executable
    if not os.access(start_path, os.X_OK):
        print(f"  FAIL: start.sh not executable")
        return False
    
    print(f"  OK: start.sh exists, executable, has all elements")
    print(f"  1/1 passed")
    return True


# ============================================================
# TEST 6: Dockerfile exists and has correct structure
# ============================================================
def test_dockerfile() -> bool:
    """Test that Dockerfile exists and has correct structure."""
    print("\n=== DOCKERFILE TESTS ===")
    
    dockerfile_path = os.path.join(os.path.dirname(__file__), "..", "Dockerfile")
    
    if not os.path.isfile(dockerfile_path):
        print(f"  FAIL: Dockerfile missing")
        return False
    
    with open(dockerfile_path) as f:
        content = f.read()
    
    checks = {
        "FROM python": "FROM python" in content,
        "WORKDIR": "WORKDIR" in content,
        "requirements.txt": "requirements.txt" in content,
        "COPY src": "COPY src" in content,
        "COPY config": "COPY config" in content,
        "EXPOSE 4000": "EXPOSE 4000" in content,
        "CMD litellm": "litellm" in content,
        "HEALTHCHECK": "HEALTHCHECK" in content,
    }
    
    for name, ok in checks.items():
        if not ok:
            print(f"  FAIL: Dockerfile missing '{name}'")
            return False
    
    print(f"  OK: Dockerfile has all required elements")
    print(f"  1/1 passed")
    return True


# ============================================================
# TEST 7: fly.toml exists and has correct config
# ============================================================
def test_fly_config() -> bool:
    """Test that fly.toml exists and has correct configuration."""
    print("\n=== FLY.TOML TESTS ===")
    
    fly_path = os.path.join(os.path.dirname(__file__), "..", "fly.toml")
    
    if not os.path.isfile(fly_path):
        print(f"  FAIL: fly.toml missing")
        return False
    
    with open(fly_path) as f:
        content = f.read()
    
    checks = {
        "app name": "timuclaude" in content,
        "region": "primary_region" in content,
        "dockerfile": "Dockerfile" in content or "dockerfile" in content,
        "port 4000": "4000" in content,
        "health check": "/health" in content,
    }
    
    for name, ok in checks.items():
        if not ok:
            print(f"  FAIL: fly.toml missing '{name}'")
            return False
    
    print(f"  OK: fly.toml has app name, region, Dockerfile, port, health check")
    print(f"  1/1 passed")
    return True


# ============================================================
# TEST 8: Landing page exists and has content
# ============================================================
def test_landing_page() -> bool:
    """Test that landing_page.html exists and has key content."""
    print("\n=== LANDING PAGE TESTS ===")
    
    page_path = os.path.join(os.path.dirname(__file__), "..", "landing_page.html")
    
    if not os.path.isfile(page_path):
        print(f"  FAIL: landing_page.html missing")
        return False
    
    with open(page_path) as f:
        content = f.read()
    
    checks = {
        "title": "<title>" in content,
        "Timuclaude": "Timuclaude" in content,
        "benchmark": "benchmark" in content.lower() or "Benchmark" in content,
        "pricing": "pricing" in content.lower() or "Pricing" in content,
        "API": "API" in content,
        "GitHub link": "github.com" in content,
        "MIT license": "MIT" in content,
    }
    
    for name, ok in checks.items():
        if not ok:
            print(f"  FAIL: landing page missing '{name}'")
            return False
    
    print(f"  OK: landing page has title, benchmarks, pricing, API, GitHub, license")
    print(f"  1/1 passed")
    return True


# ============================================================
# TEST 9: .dockerignore exists
# ============================================================
def test_dockerignore() -> bool:
    """Test that .dockerignore exists and excludes sensitive files."""
    print("\n=== DOCKERIGNORE TESTS ===")
    
    di_path = os.path.join(os.path.dirname(__file__), "..", ".dockerignore")
    
    if not os.path.isfile(di_path):
        print(f"  FAIL: .dockerignore missing")
        return False
    
    with open(di_path) as f:
        content = f.read()
    
    for pattern in [".git", "__pycache__", ".env", "logs"]:
        if pattern not in content:
            print(f"  FAIL: .dockerignore missing '{pattern}'")
            return False
    
    print(f"  OK: .dockerignore excludes .git, pycache, .env, logs")
    print(f"  1/1 passed")
    return True


# ============================================================
# RUN ALL TESTS
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("TIMUCLAUDE — PHASE 5 TEST SUITE")
    print("=" * 60)
    
    results = []
    results.append(("Cache Basic", test_cache_basic()))
    results.append(("Cache TTL", test_cache_ttl()))
    results.append(("Cache LRU", test_cache_lru()))
    results.append(("Cache Stats", test_cache_stats()))
    results.append(("Start Script", test_start_script()))
    results.append(("Dockerfile", test_dockerfile()))
    results.append(("Fly Config", test_fly_config()))
    results.append(("Landing Page", test_landing_page()))
    results.append(("Dockerignore", test_dockerignore()))
    
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