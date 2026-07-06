"""
Temuclaude Phase 5 Test Suite
Tests: Cache, start script, Dockerfile, landing page, fly.toml
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.cache import ResponseCache


# ============================================================
# TEST 1: Cache — Set and Get
# ============================================================
def test_cache_basic():
    """Test basic cache set and get operations."""
    cache = ResponseCache(max_size=100, ttl_seconds=60)

    cache.set("glm-5.2", [{"role": "user", "content": "What is 2+2?"}], "4")
    result = cache.get("glm-5.2", [{"role": "user", "content": "What is 2+2?"}])
    assert result == "4", f"Expected '4', got '{result}'"

    result = cache.get("glm-5.2", [{"role": "user", "content": "What is 3+3?"}])
    assert result is None, f"Expected None, got '{result}'"


# ============================================================
# TEST 2: Cache — TTL Expiration
# ============================================================
def test_cache_ttl():
    """Test that cache entries expire after TTL."""
    cache = ResponseCache(max_size=100, ttl_seconds=1)

    cache.set("model", [{"role": "user", "content": "test"}], "answer")
    result = cache.get("model", [{"role": "user", "content": "test"}])
    assert result == "answer"

    time.sleep(1.5)
    result = cache.get("model", [{"role": "user", "content": "test"}])
    assert result is None, f"Expected None after TTL, got '{result}'"


# ============================================================
# TEST 3: Cache — LRU Eviction
# ============================================================
def test_cache_lru():
    """Test that LRU eviction removes oldest entries when cache is full."""
    cache = ResponseCache(max_size=3, ttl_seconds=60)

    cache.set("m1", [{"q": 1}], "a1")
    cache.set("m2", [{"q": 2}], "a2")
    cache.set("m3", [{"q": 3}], "a3")

    assert cache.get("m1", [{"q": 1}]) == "a1"
    assert cache.get("m2", [{"q": 2}]) == "a2"
    assert cache.get("m3", [{"q": 3}]) == "a3"

    # Add 4th — should evict m1 (oldest)
    cache.set("m4", [{"q": 4}], "a4")
    assert cache.get("m1", [{"q": 1}]) is None, "m1 should be evicted"
    assert cache.get("m4", [{"q": 4}]) == "a4"
    assert cache.get("m2", [{"q": 2}]) == "a2"
    assert cache.get("m3", [{"q": 3}]) == "a3"


# ============================================================
# TEST 4: Cache — Statistics
# ============================================================
def test_cache_stats():
    """Test that cache statistics are tracked correctly."""
    cache = ResponseCache(max_size=100, ttl_seconds=60)

    cache.set("m", [{"q": 1}], "a")
    cache.get("m", [{"q": 1}])  # hit
    cache.get("m", [{"q": 2}])  # miss
    cache.get("m", [{"q": 3}])  # miss

    stats = cache.stats()
    assert stats["exact_hits"] == 1, f"Expected 1 exact hit, got {stats['exact_hits']}"
    assert stats["misses"] == 2, f"Expected 2 misses, got {stats['misses']}"
    assert stats["exact_cache_size"] == 1, f"Expected size 1, got {stats['exact_cache_size']}"
    assert 0 < stats["hit_rate"] < 1, f"Hit rate should be between 0 and 1: {stats['hit_rate']}"

    cache.clear()
    stats = cache.stats()
    assert stats["exact_cache_size"] == 0
    assert stats["exact_hits"] == 0
    assert stats["misses"] == 0


# ============================================================
# TEST 5: start.sh exists and is executable
# ============================================================
def test_start_script():
    """Test that start.sh exists, is executable, and has correct content."""
    start_path = os.path.join(os.path.dirname(__file__), "..", "start.sh")
    assert os.path.isfile(start_path), "start.sh missing"

    with open(start_path) as f:
        content = f.read()

    for item in ["TEMUCLAUDE_MASTER_KEY", "OPENROUTER_API_KEY", "11434",
                 "litellm", "config/litellm.yaml", "4000"]:
        assert item in content, f"start.sh missing '{item}'"

    assert os.access(start_path, os.X_OK), "start.sh not executable"


# ============================================================
# TEST 6: Dockerfile exists and has correct structure
# ============================================================
def test_dockerfile():
    """Test that Dockerfile exists and has correct structure."""
    dockerfile_path = os.path.join(os.path.dirname(__file__), "..", "Dockerfile")
    assert os.path.isfile(dockerfile_path), "Dockerfile missing"

    with open(dockerfile_path) as f:
        content = f.read()

    for item in ["FROM python", "WORKDIR", "requirements.txt", "COPY src",
                 "COPY config", "EXPOSE 4000", "litellm", "HEALTHCHECK"]:
        assert item in content, f"Dockerfile missing '{item}'"


# ============================================================
# TEST 7: fly.toml exists and has correct config
# ============================================================
def test_fly_config():
    """Test that fly.toml exists and has correct configuration."""
    fly_path = os.path.join(os.path.dirname(__file__), "..", "fly.toml")
    assert os.path.isfile(fly_path), "fly.toml missing"

    with open(fly_path) as f:
        content = f.read()

    for item in ["temuclaude", "primary_region", "Dockerfile", "4000", "/health"]:
        assert item in content, f"fly.toml missing '{item}'"


# ============================================================
# TEST 8: Landing page exists and has content
# ============================================================
def test_landing_page():
    """Test that landing_page.html exists and has key content."""
    page_path = os.path.join(os.path.dirname(__file__), "..", "landing_page.html")
    assert os.path.isfile(page_path), "landing_page.html missing"

    with open(page_path) as f:
        content = f.read()

    for item in ["<title>", "Temuclaude", "API", "github.com", "MIT"]:
        assert item in content, f"landing page missing '{item}'"

    assert "benchmark" in content.lower(), "landing page missing 'benchmark'"
    assert "pricing" in content.lower(), "landing page missing 'pricing'"


# ============================================================
# TEST 9: .dockerignore exists
# ============================================================
def test_dockerignore():
    """Test that .dockerignore exists and excludes sensitive files."""
    di_path = os.path.join(os.path.dirname(__file__), "..", ".dockerignore")
    assert os.path.isfile(di_path), ".dockerignore missing"

    with open(di_path) as f:
        content = f.read()

    for pattern in [".git", "__pycache__", ".env", "logs"]:
        assert pattern in content, f".dockerignore missing '{pattern}'"


# ============================================================
# RUN ALL TESTS
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("TEMUCLAUDE — PHASE 5 TEST SUITE")
    print("=" * 60)

    tests = [
        ("Cache Basic", test_cache_basic),
        ("Cache TTL", test_cache_ttl),
        ("Cache LRU", test_cache_lru),
        ("Cache Stats", test_cache_stats),
        ("Start Script", test_start_script),
        ("Dockerfile", test_dockerfile),
        ("Fly Config", test_fly_config),
        ("Landing Page", test_landing_page),
        ("Dockerignore", test_dockerignore),
    ]

    all_passed = True
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS: {name}")
        except Exception as e:
            print(f"  FAIL: {name} — {e}")
            all_passed = False

    print(f"\n{'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    sys.exit(0 if all_passed else 1)