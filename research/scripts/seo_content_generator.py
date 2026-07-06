#!/usr/bin/env python3
"""
SEO Content Generator — auto-generates blog posts and comparison pages.
Uses Ollama free models.
"""

import json, os, sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ollama_client import call_model

CONTENT_DIR = Path(os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude") + "/website/content/blog")

COMPETITORS = ["OpenAI GPT-5.6", "Anthropic Claude 4", "Google Gemini 3.5", "OpenRouter", "vLLM"]
TUTORIAL_TOPICS = ["route requests across multiple LLMs", "reduce LLM costs by 50x",
    "build a self-improving AI system", "orchestrate model fusion"]

def generate_comparison_page(competitor):
    prompt = f"""Write a detailed SEO comparison page: "Temuclaude vs {competitor}".
    Include: feature comparison, pricing, benchmarks, pros and cons.
    Format as Markdown. 800 words. Meta description included."""
    result = call_model("glm-5.2:cloud", prompt, max_tokens=2000)
    return result.get("response", "")

def generate_tutorial(topic):
    prompt = f"""Write a technical tutorial: "How to {topic} with Temuclaude".
    Include code examples and step-by-step instructions. Markdown. 600 words."""
    result = call_model("glm-5.2:cloud", prompt, max_tokens=2000)
    return result.get("response", "")

def generate_all_content():
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    generated = []
    for comp in COMPETITORS:
        slug = comp.lower().replace(" ", "-").replace(".", "")
        fp = CONTENT_DIR / f"temuclaude-vs-{slug}.md"
        if not fp.exists():
            content = generate_comparison_page(comp)
            if content:
                fp.write_text(content)
                generated.append(str(fp))
    for topic in TUTORIAL_TOPICS:
        slug = topic.lower().replace(" ", "-")
        fp = CONTENT_DIR / f"how-to-{slug}.md"
        if not fp.exists():
            content = generate_tutorial(topic)
            if content:
                fp.write_text(content)
                generated.append(str(fp))
    return generated
