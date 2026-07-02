"""
Timuclaude Core Orchestrator
The main entry point. User sends a query → gets one response.
All orchestration is invisible.

This is the "Fugu equivalent" — Hermes is the orchestrator,
this module encodes the orchestration strategies as code.
"""
import time
import asyncio
from typing import Optional
from openai import AsyncOpenAI

from .models import (
    MODEL_POOL,
    CHEAP_MODELS,
    TASK_MODEL_MAP,
    FUSION_PANEL,
    AGGREGATOR_MAP,
    OLLAMA_API_BASE,
)
from .logger import QueryLogger


class Timuclaude:
    """
    Timuclaude — one model, one endpoint, one response.
    All orchestration is internal and invisible to the user.
    """

    def __init__(self):
        self.client = AsyncOpenAI(base_url=f"{OLLAMA_API_BASE}/v1", api_key="ollama")
        self.logger = QueryLogger()

    async def classify_task(self, query: str) -> str:
        """Classify the query into a task type for routing."""
        # Keyword-based classification (Phase 2 will use a model for this)
        # Order matters: check more specific categories first
        query_lower = query.lower()
        import re

        # Math: arithmetic expressions like "2+2" or "15*12"
        if re.search(r'\d+\s*[+\-*/^]\s*\d+', query):
            return "math"
        # Math: math terms
        if any(kw in query_lower for kw in [
            "calculate", "solve", "equation", "prove", "integral", "derivative",
            "matrix", "theorem", "algebra", "geometry", "probability", "statistics",
            "sum", "product", "factor", "prime", " polynomial", "function of x",
            "limit", "series", "differential", "vector", "tensor", "topology"
        ]):
            return "math"

        # Creative: writing/generation tasks (check early, before coding)
        if any(kw in query_lower for kw in [
            "write a poem", "write a story", "write a short story",
            "write an essay", "write a blog", "write a script",
            "compose", "screenplay", "generate a", "create a story",
            "write a song", "write a letter",
        ]):
            return "creative"

        # Knowledge: factual questions (check before coding to avoid false positives)
        if any(kw in query_lower for kw in [
            "what is the capital", "what is the capital of", "who is", "when did",
            "where is", "history of", "define ", "definition of", "meaning of",
            "what is the largest", "what is the smallest", "what is the tallest",
        ]):
            return "knowledge"
        # Generic "what is" that's NOT about code/math
        if query_lower.startswith("what is ") and not any(kw in query_lower for kw in ["api", "function", "code", "algorithm"]):
            return "knowledge"

        # Reasoning: analytical questions
        if any(kw in query_lower for kw in [
            "compare", "analyze", "evaluate", "why does", "why is",
            "how does", "explain the mechanism", "trade-off", "tradeoff",
            "consequence", "implication", "difference between",
        ]):
            return "reasoning"

        # Agentic: deployment/setup tasks (check before coding — "deploy react" is agentic not coding)
        if any(kw in query_lower for kw in [
            "deploy", "setup", "install ", "configure", "run ", "execute",
            "build a", "automate", "pipeline", "workflow",
        ]):
            return "agentic"

        # Coding: programming tasks
        if any(kw in query_lower for kw in [
            "code", "function", "debug", "python", "javascript", "java ",
            "react", "typescript", "rust", "golang", "sql", "algorithm",
            "compile", "error:", "bug", "docker", "kubernetes",
            "api endpoint", "rest api", "graphql api",
        ]):
            return "coding"

        return "knowledge"  # default

    def determine_tier(self, query: str, task_type: str) -> str:
        """Determine routing tier: trivial, medium, or hard."""
        word_count = len(query.split())
        char_count = len(query)

        # Trivial: very short AND simple task type
        # Only knowledge and simple tasks qualify as trivial
        # Math (even short) requires computation = medium minimum
        # Coding (even short) requires generation = medium minimum
        if word_count <= 8 and char_count <= 50 and task_type in ("knowledge", "simple"):
            return "trivial"

        # Hard: long, complex queries
        if word_count > 100:
            return "hard"
        if char_count > 500:
            return "hard"
        if task_type in ("math", "reasoning") and word_count > 30:
            return "hard"
        if task_type == "coding" and word_count > 25:
            return "hard"
        if "fix" in query.lower() and ("code" in query.lower() or "error" in query.lower() or "bug" in query.lower()):
            return "hard"

        return "medium"

    async def call_model(self, model: str, messages: list, temperature: float = 0.0, max_tokens: int = 8192) -> str:
        """Call a single Ollama Cloud model. Minimum max_tokens=200 for thinking models."""
        # Thinking models use internal tokens for reasoning — don't cap too low
        if max_tokens < 200:
            max_tokens = 200

        ollama_tag = MODEL_POOL.get(model, CHEAP_MODELS.get(model, {})).get("ollama_tag", model)
        try:
            response = await self.client.chat.completions.create(
                model=ollama_tag,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[ERROR: {model} failed: {e}]"

    async def direct_response(self, model: str, messages: list, max_tokens: int = 8192) -> str:
        """Get a direct response from a single model."""
        return await self.call_model(model, messages, max_tokens=max_tokens)

    async def complete(self, query: str, system_prompt: str = None) -> str:
        """
        Main entry point. User sends a query, gets one response.
        All orchestration is internal.
        """
        start_time = time.time()

        # Step 1: Classify the task
        task_type = await self.classify_task(query)
        tier = self.determine_tier(query, task_type)

        # Step 2: Route based on tier
        if tier == "trivial":
            # Use cheap model for trivial queries
            model = "gpt-oss-120b"
            messages = [
                {"role": "system", "content": system_prompt or "You are Timuclaude, a helpful AI assistant."},
                {"role": "user", "content": query},
            ]
            answer = await self.direct_response(model, messages, max_tokens=500)
            models_used = [model]
            strategy = "direct_cheap"
        elif tier == "medium":
            # Use best model for the task type
            model = TASK_MODEL_MAP.get(task_type, "glm-5.2")
            messages = [
                {"role": "system", "content": system_prompt or "You are Timuclaude, a helpful AI assistant. Provide thorough, accurate answers."},
                {"role": "user", "content": query},
            ]
            answer = await self.direct_response(model, messages, max_tokens=8192)
            models_used = [model]
            strategy = "direct_specialist"
        else:
            # Hard tier: Phase 2 will implement Fusion here
            # For now, use the best model with max thinking
            model = TASK_MODEL_MAP.get(task_type, "glm-5.2")
            messages = [
                {"role": "system", "content": system_prompt or "You are Timuclaude, a helpful AI assistant. Think carefully and provide thorough, accurate answers."},
                {"role": "user", "content": query},
            ]
            answer = await self.direct_response(model, messages, max_tokens=8192)
            models_used = [model]
            strategy = "direct_specialist_max_thinking"

        latency_ms = int((time.time() - start_time) * 1000)

        # Log the query
        self.logger.log(
            user_query=query,
            task_type=task_type,
            routing_tier=tier,
            models_used=models_used,
            strategy=strategy,
            final_answer=answer,
            latency_ms=latency_ms,
            success=not answer.startswith("[ERROR"),
        )

        return answer


# Synchronous wrapper for easy testing
def ask(query: str, system_prompt: str = None) -> str:
    """Simple function to ask Timuclaude a question."""
    tc = Timuclaude()
    return asyncio.run(tc.complete(query, system_prompt))