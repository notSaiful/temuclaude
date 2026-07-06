#!/usr/bin/env python3
"""Prompt Evolver — evolutionary prompt optimization."""

import json, os
from pathlib import Path
from datetime import datetime, timezone
from ollama_client import call_model
from model_benchmarker import BENCHMARK_PROMPTS

PROMPT_STORE = Path(os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude") + "/research/evolved_prompts.json")

def evaluate_prompt(prompt, task_type):
    pass_count = 0
    for bp in BENCHMARK_PROMPTS[:3]:
        full = prompt + "\n\n" + bp["prompt"]
        result = call_model("glm-5.2:cloud", full, max_tokens=bp.get("max_tokens", 100))
        if bp["expected_contains"].lower() in result.get("response", "").lower():
            pass_count += 1
    return pass_count / 3

def generate_mutations(prompt, n=3):
    mutations = []
    for _ in range(n):
        mutation_prompt = f"Improve this prompt for better accuracy:\n\nOriginal: {prompt}\n\nImproved:"
        result = call_model("glm-5.2:cloud", mutation_prompt, max_tokens=500)
        if result.get("response"):
            mutations.append(result["response"].strip())
    return mutations

def evolve_prompt(current_prompt, task_type, generations=3):
    best_prompt = current_prompt
    best_score = evaluate_prompt(best_prompt, task_type)
    for gen in range(generations):
        for mutation in generate_mutations(best_prompt, n=2):
            score = evaluate_prompt(mutation, task_type)
            if score > best_score * 1.02:
                best_prompt = mutation
                best_score = score
    return {"prompt": best_prompt, "score": best_score, "generations": generations}
