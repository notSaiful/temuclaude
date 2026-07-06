#!/usr/bin/env python3
"""Ollama API Client — free or near-free inference for the swarm."""

import json, os, time
from urllib.request import urlopen, Request

OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY", "")
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")

def fetch_models():
    try:
        url = f"{OLLAMA_BASE_URL}/api/tags"
        headers = {"Accept": "application/json"}
        if OLLAMA_API_KEY:
            headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"
        req = Request(url, headers=headers)
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [m.get("name", "") for m in data.get("models", [])]
    except Exception:
        return []

def call_model(model, prompt, max_tokens=1000):
    try:
        url = f"{OLLAMA_BASE_URL}/api/chat"
        data = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
            "stream": False, "options": {"num_predict": max_tokens, "temperature": 0.0}}).encode()
        headers = {"Content-Type": "application/json"}
        if OLLAMA_API_KEY:
            headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"
        req = Request(url, data=data, headers=headers)
        start = time.time()
        with urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            response_text = result.get("message", {}).get("content", "")
            return {"response": response_text, "latency": time.time() - start,
                "prompt_tokens": len(prompt) // 4, "completion_tokens": len(response_text) // 4,
                "cost_usd": 0.0, "provider": "ollama", "error": None}
    except Exception as e:
        return {"response": "", "latency": 0, "cost_usd": 0, "error": str(e)}

def is_available():
    if OLLAMA_API_KEY:
        return True
    try:
        urlopen(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return True
    except Exception:
        return False

if __name__ == "__main__":
    print(f"Available: {is_available()}")
    print(f"Models: {fetch_models()[:10]}")
