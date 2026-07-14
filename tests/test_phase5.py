"""
Temuclaude Phase 5 Test Suite
Tests: Cache, start script, Dockerfile, landing page, fly.toml
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.cache import ResponseCache


def test_cache_basic():
    cache = ResponseCache(max_size=100, ttl_seconds=60)
    cache.set("glm-5.2", [{"role": "user", "content": "What is 2+2?"}], "4")
    result = cache.get("glm-5.2", [{"role": "user", "content": "What is 2+2?"}])
    assert result == "4"
    result = cache.get("glm-5.2", [{"role": "user", "content": "What is 3+3?"}])
    assert result is None


def test_cache_ttl():
    cache = ResponseCache(max_size=100, ttl_seconds=1)
    cache.set("model", [{"role": "user", "content": "test"}], "answer")
    result = cache.get("model", [{"role": "user", "content": "test"}])
    assert result == "answer"
    time.sleep(1.5)
    result = cache.get("model", [{"role": "user", "content": "test"}])
    assert result is None


def test_cache_lru():
    cache = ResponseCache(max_size=3, ttl_seconds=60)
    cache.set("m1", [{"q": 1}], "a1")
    cache.set("m2", [{"q": 2}], "a2")
    cache.set("m3", [{"q": 3}], "a3")
    assert cache.get("m1", [{"q": 1}]) == "a1"
    assert cache.get("m2", [{"q": 2}]) == "a2"
    assert cache.get("m3", [{"q": 3}]) == "a3"
    cache.set("m4", [{"q": 4}], "a4")
    assert cache.get("m1", [{"q": 1}]) is None
    assert cache.get("m4", [{"q": 4}]) == "a4"


def test_cache_stats():
    cache = ResponseCache(max_size=100, ttl_seconds=60)
    cache.set("m", [{"q": 1}], "a")
    cache.get("m", [{"q": 1}])
    cache.get("m", [{"q": 2}])
    cache.get("m", [{"q": 3}])
    stats = cache.stats()
    assert stats["exact_hits"] == 1
    assert stats["misses"] == 2
    assert stats["exact_cache_size"] == 1
    cache.clear()
    stats = cache.stats()
    assert stats["exact_cache_size"] == 0
    assert stats["exact_hits"] == 0
    assert stats["misses"] == 0


def test_start_script():
    start_path = os.path.join(os.path.dirname(__file__), "..", "start.sh")
    assert os.path.isfile(start_path), "start.sh missing"
    with open(start_path) as f:
        content = f.read()
    for item in ["TEMUCLAUDE_API_KEY", "uvicorn", "api_server:app", "PORT"]:
        assert item in content, f"start.sh missing '{item}'"
    assert os.access(start_path, os.X_OK), "start.sh not executable"


def test_dockerfile():
    dockerfile_path = os.path.join(os.path.dirname(__file__), "..", "Dockerfile")
    assert os.path.isfile(dockerfile_path), "Dockerfile missing"
    with open(dockerfile_path) as f:
        content = f.read()
    for item in ["FROM python", "WORKDIR", "requirements.txt", "src ./src",
                 "config ./config", "EXPOSE 8080", "HEALTHCHECK", "USER app"]:
        assert item in content, f"Dockerfile missing '{item}'"


def test_fly_config():
    fly_path = os.path.join(os.path.dirname(__file__), "..", "fly.toml")
    assert os.path.isfile(fly_path), "fly.toml missing"
    with open(fly_path) as f:
        content = f.read()
    # Accept both timuclaude and temuclaude (project name evolved)
    assert "timuclaude" in content.lower() or "temuclaude" in content.lower(), "fly.toml missing app name"
    for item in ["primary_region", "Dockerfile", "8080", "/health"]:
        assert item in content, f"fly.toml missing '{item}'"


def test_landing_page():
    page_path = os.path.join(os.path.dirname(__file__), "..", "landing_page.html")
    assert os.path.isfile(page_path), "landing_page.html missing"
    with open(page_path) as f:
        content = f.read()
    for item in ["<title>", "API", "github.com", "MIT"]:
        assert item in content, f"landing page missing '{item}'"
    assert "benchmark" in content.lower(), "landing page missing 'benchmark'"
    assert "pricing" in content.lower(), "landing page missing 'pricing'"


def test_dockerignore():
    di_path = os.path.join(os.path.dirname(__file__), "..", ".dockerignore")
    assert os.path.isfile(di_path), ".dockerignore missing"
    with open(di_path) as f:
        content = f.read()
    for pattern in [".git", "__pycache__", ".env", "logs"]:
        assert pattern in content, f".dockerignore missing '{pattern}'"


if __name__ == "__main__":
    tests = [
        ("Cache Basic", test_cache_basic), ("Cache TTL", test_cache_ttl),
        ("Cache LRU", test_cache_lru), ("Cache Stats", test_cache_stats),
        ("Start Script", test_start_script), ("Dockerfile", test_dockerfile),
        ("Fly Config", test_fly_config), ("Landing Page", test_landing_page),
        ("Dockerignore", test_dockerignore),
    ]
    all_passed = True
    for name, fn in tests:
        try:
            fn(); print(f"  PASS: {name}")
        except Exception as e:
            print(f"  FAIL: {name} — {e}"); all_passed = False
    print(f"\n{'ALL PASSED' if all_passed else 'FAILED'}")
    sys.exit(0 if all_passed else 1)
