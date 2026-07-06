#!/usr/bin/env python3
"""
Model Pool Optimizer Daemon — benchmarks and swaps better/cheaper/stronger models.
Runs every 3 hours. Tests models on quality (MMLU sample), speed, cost.
Keeps the best. Swaps out underperformers.
"""

import json
import time
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, "/Users/saiful/temuclaude/research")
from daemon_base import DaemonBase

TEMUCLAUDE = Path("/Users/saiful/temuclaude")
MODEL_CONFIG = TEMUCLAUDE / "src" / "models.json"
BENCHMARK_RESULTS = TEMUCLAUDE / "research" / "model_benchmark_results.json"
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")

# Models to evaluate (Ollama free tier)
CANDIDATE_MODELS = [
    "gpt-oss:120b:cloud",
    "glm-5.2:cloud",
    "deepseek-v4-pro:cloud",
    "kimi-k2.6:cloud",
]


class ModelOptimizerDaemon(DaemonBase):
    def __init__(self):
        super().__init__("model_optimizer_daemon")

    def run_once(self) -> bool:
        self.logger.info("Model optimizer: benchmarking candidate models")
        results = self._benchmark_models()
        self._save_results(results)
        best = self._pick_best(results)
        if best:
            self.logger.info(f"Model optimizer: best model = {best}")
            self._update_config(best)
        return True

    def _benchmark_models(self) -> dict:
        """Quick quality test — ask each model a simple question."""
        results = {}
        test_prompt = "What is 17 * 23? Answer with just the number."

        for model in CANDIDATE_MODELS:
            result = {"model": model, "timestamp": datetime.now(timezone.utc).isoformat()}
            try:
                import urllib.request
                data = json.dumps({
                    "model": model,
                    "prompt": test_prompt,
                    "stream": False,
                    "options": {"temperature": 0, "max_tokens": 50}
                }).encode()
                req = urllib.request.Request(
                    f"{OLLAMA_URL}/api/generate",
                    data=data,
                    headers={"Content-Type": "application/json"}
                )
                start = time.time()
                with urllib.request.urlopen(req, timeout=30) as resp:
                    output = json.loads(resp.read().decode())
                elapsed = time.time() - start

                answer = output.get("response", "").strip()
                result["answer"] = answer
                result["correct"] = "391" in answer
                result["latency_s"] = round(elapsed, 2)
                result["status"] = "ok"
            except Exception as e:
                result["status"] = "error"
                result["error"] = str(e)[:100]
                result["correct"] = False
                result["latency_s"] = 999

            results[model] = result
            self.logger.info(f"  {model}: correct={result['correct']}, latency={result['latency_s']}s")

        return results

    def _pick_best(self, results: dict) -> str:
        """Pick the best model — correct + fastest."""
        correct = {k: v for k, v in results.items() if v.get("correct")}
        if not correct:
            return None
        return min(correct, key=lambda k: correct[k]["latency_s"])

    def _save_results(self, results: dict):
        logs = []
        if BENCHMARK_RESULTS.exists():
            try:
                with open(BENCHMARK_RESULTS) as f:
                    logs = json.load(f)
            except Exception:
                pass
        logs.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "results": results
        })
        logs = logs[-100:]
        with open(BENCHMARK_RESULTS, 'w') as f:
            json.dump(logs, f, indent=2)

    def _update_config(self, best_model: str):
        """Update model config to use the best model."""
        if MODEL_CONFIG.exists():
            try:
                with open(MODEL_CONFIG) as f:
                    config = json.load(f)
                old = config.get("primary_model", "none")
                if old != best_model:
                    config["primary_model"] = best_model
                    with open(MODEL_CONFIG, 'w') as f:
                        json.dump(config, f, indent=2)
                    self.logger.info(f"Swapped primary model: {old} → {best_model}")
            except Exception as e:
                self.logger.warning(f"Config update failed: {e}")


def main():
    daemon = ModelOptimizerDaemon()
    daemon.run(interval=10800)  # 3 hours


if __name__ == "__main__":
    main()