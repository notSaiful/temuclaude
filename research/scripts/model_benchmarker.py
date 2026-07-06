#!/usr/bin/env python3
"""Model Benchmarker — evaluates a candidate model on benchmark prompts."""

import json, os, sys, time
from pathlib import Path
from datetime import datetime, timezone
from urllib.request import urlopen, Request

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
if not OPENROUTER_API_KEY:
    env_file = Path(os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude") + "/.env")
    if env_file.exists():
        for line in env_file.read_text().split("\n"):
            if line.startswith("OPENROUTER_API_KEY"):
                OPENROUTER_API_KEY = line.split("=", 1)[1].strip().strip("'\"")
                break

BENCHMARK_PROMPTS = [
    {"id": "mmlu_1", "prompt": "What is the capital of Australia? Answer with just the city name.", "expected_contains": "Canberra", "max_tokens": 50},
    {"id": "hle_1", "prompt": "If all roses are flowers, and some flowers fade quickly, can we conclude that some roses fade quickly? Answer yes or no with explanation.", "expected_contains": "no", "max_tokens": 100},
    {"id": "math_1", "prompt": "What is 17 * 23? Answer with just the number.", "expected_contains": "391", "max_tokens": 20},
    {"id": "code_1", "prompt": "Write a Python function that reverses a string. Only output the code.", "expected_contains": "def reverse", "max_tokens": 200},
    {"id": "instruction_1", "prompt": "List 3 fruits. Format as: 1. fruit1 2. fruit2 3. fruit3", "expected_contains": "1.", "max_tokens": 50},
]

def call_model(model_id, prompt, max_tokens=100):
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        data = json.dumps({"model": model_id, "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens, "temperature": 0.0}).encode()
        req = Request(url, data=data, headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"})
        start = time.time()
        with urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return {"response": result.get("choices", [{}])[0].get("message", {}).get("content", ""),
                    "latency": time.time() - start, "error": None}
    except Exception as e:
        return {"response": "", "latency": 0, "error": str(e)}

def benchmark_model(model_id):
    results = []
    pass_count = 0
    total_latency = 0
    for bp in BENCHMARK_PROMPTS:
        r = call_model(model_id, bp["prompt"], bp.get("max_tokens", 100))
        if r["error"]:
            results.append({"id": bp["id"], "passed": False, "error": r["error"]})
            continue
        passed = bp["expected_contains"].lower() in r["response"].lower()
        results.append({"id": bp["id"], "passed": passed, "latency": r["latency"]})
        if passed: pass_count += 1
        total_latency += r["latency"]
        time.sleep(1)
    return {"model_id": model_id, "pass_rate": pass_count / len(BENCHMARK_PROMPTS),
            "pass_count": pass_count, "avg_latency": total_latency / len(BENCHMARK_PROMPTS) if BENCHMARK_PROMPTS else 0,
            "results": results, "timestamp": datetime.now(timezone.utc).isoformat()}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python model_benchmarker.py <model_id>")
        sys.exit(1)
    print(json.dumps(benchmark_model(sys.argv[1]), indent=2))
