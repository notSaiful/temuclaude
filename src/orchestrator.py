"""
Timuclaude Core Orchestrator
The main entry point. User sends a query → gets one response.
All orchestration is invisible.

This is the "Fugu equivalent" — Hermes is the orchestrator,
this module encodes the orchestration strategies as code.
"""
import time
import asyncio
import os
import sys
from typing import Optional
from openai import AsyncOpenAI

# Handle both package import (from src.orchestrator) and direct script execution
if __package__:
    from .models import (
        MODEL_POOL,
        CHEAP_MODELS,
        TASK_MODEL_MAP,
        FUSION_PANEL,
        AGGREGATOR_MAP,
        OLLAMA_API_BASE,
        API_BASE,
        _USE_OPENROUTER,
    )
    from .logger import QueryLogger
    from .fusion import fuse, get_panel, get_aggregator
    from .consistency import self_consistency
    from .verifier import verify_with_code
    from .self_qa import self_qa_gate
    from .skills_loader import build_enhanced_system_prompt
    from .adaptive import get_model_for_task
    from .gepa import get_system_prompt
else:
    # When run directly as: python src/orchestrator.py
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.models import (
        MODEL_POOL,
        CHEAP_MODELS,
        TASK_MODEL_MAP,
        FUSION_PANEL,
        AGGREGATOR_MAP,
        OLLAMA_API_BASE,
        API_BASE,
        _USE_OPENROUTER,
    )
    from src.logger import QueryLogger
    from src.fusion import fuse, get_panel, get_aggregator
    from src.consistency import self_consistency
    from src.verifier import verify_with_code
    from src.self_qa import self_qa_gate
    from src.skills_loader import build_enhanced_system_prompt
    from src.adaptive import get_model_for_task
    from src.gepa import get_system_prompt


class Timuclaude:
    """
    Timuclaude — one model, one endpoint, one response.
    All orchestration is internal and invisible to the user.
    """

    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            base_url=f"{API_BASE}/v1" if "localhost" in API_BASE else API_BASE,
            api_key=os.environ.get("OPENROUTER_API_KEY", "ollama") if _USE_OPENROUTER else "ollama",
        )
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

    async def call_model(self, model: str, messages: list, temperature: float = 0.0, max_tokens: int = 8192, timeout: int = 120) -> str:
        """Call a single model with timeout and retry. Auto-detects Ollama or OpenRouter."""
        # Thinking models use internal tokens for reasoning — don't cap too low
        if max_tokens < 200:
            max_tokens = 200

        # Determine which backend and model ID to use
        if __package__:
            from .models import OPENROUTER_MODELS, _USE_OPENROUTER
        else:
            from src.models import OPENROUTER_MODELS, _USE_OPENROUTER
        
        if _USE_OPENROUTER:
            # OpenRouter: use provider/model format
            ollama_tag = OPENROUTER_MODELS.get(model, model)
            api_key = os.environ.get("OPENROUTER_API_KEY", "")
        else:
            # Ollama: use :cloud suffix
            ollama_tag = MODEL_POOL.get(model, CHEAP_MODELS.get(model, {})).get("ollama_tag", model)
            api_key = "ollama"
        
        for attempt in range(2):  # 1 retry max
            try:
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=ollama_tag,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        extra_headers={"Authorization": f"Bearer {api_key}"} if _USE_OPENROUTER and api_key else None,
                    ),
                    timeout=timeout,
                )
                content = response.choices[0].message.content or ""
                if content.strip():
                    return content
                # Empty response — retry with higher max_tokens
                max_tokens = max(max_tokens * 2, 500)
            except asyncio.TimeoutError:
                if attempt < 1:
                    await asyncio.sleep(0.5)
                    continue
                return f"[ERROR: {model} timed out after {timeout}s]"
            except Exception as e:
                if attempt < 1:
                    await asyncio.sleep(0.5)
                    continue
                return f"[ERROR: {model} failed: {e}]"

        return f"[ERROR: {model} returned empty response after 3 attempts]"

    async def call_model_with_fallback(self, model: str, messages: list, max_tokens: int = 8192, temperature: float = 0.0, timeout: int = 120) -> str:
        """Call a model, and if it fails, try fallback models."""
        answer = await self.call_model(model, messages, temperature=temperature, max_tokens=max_tokens, timeout=timeout)
        if not answer.startswith("[ERROR"):
            return answer

        # Try fallback models based on task type
        fallbacks = ["glm-5.2", "deepseek-v4-pro", "kimi-k2.6"]
        if model in fallbacks:
            fallbacks.remove(model)

        for fallback in fallbacks:
            answer = await self.call_model(fallback, messages, temperature=temperature, max_tokens=max_tokens, timeout=timeout)
            if not answer.startswith("[ERROR"):
                return answer

        return answer  # All failed, return last error

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
        # Phase 3: Use adaptive routing + skill-enhanced prompts + evolved prompts
        if tier == "trivial":
            # Use cheap model for trivial queries
            model = "gpt-oss-120b"
            enhanced_prompt = build_enhanced_system_prompt(task_type, system_prompt)
            messages = [
                {"role": "system", "content": enhanced_prompt},
                {"role": "user", "content": query},
            ]
            answer = await self.call_model_with_fallback(model, messages, max_tokens=500)
            models_used = [model]
            strategy = "direct_cheap+skills"
        elif tier == "medium":
            # Use adaptive routing to pick best model (learned from logs)
            model = get_model_for_task(task_type)
            evolved_prompt = get_system_prompt(task_type, system_prompt)
            enhanced_prompt = build_enhanced_system_prompt(task_type, evolved_prompt)
            messages = [
                {"role": "system", "content": enhanced_prompt},
                {"role": "user", "content": query},
            ]
            answer = await self.call_model_with_fallback(model, messages, max_tokens=8192)
            models_used = [model]
            strategy = "direct_specialist+skills+adaptive"
        else:
            # Hard tier: full orchestration
            # Strategy depends on task type:
            # - math: Fusion + code verification + self-consistency
            # - coding: Fusion + code verification
            # - knowledge: Fusion only
            # - reasoning: Fusion + self-consistency
            # - creative: Fusion only
            # - agentic: Fusion only

            use_code_verify = task_type in ("math", "coding")
            use_self_consistency = task_type in ("math", "reasoning")

            # Step 1: Run Fusion panel
            fusion_result = await fuse(
                query, task_type, self.call_model_with_fallback, max_tokens=8192
            )
            answer = fusion_result["answer"]
            models_used = fusion_result["panel"] + [fusion_result["aggregator"]]
            strategy = "fusion"

            # Step 2: Code verification (for math/coding)
            if use_code_verify:
                code_model = TASK_MODEL_MAP.get(task_type, "deepseek-v4-pro")
                code_result = await verify_with_code(
                    query, code_model, self.call_model_with_fallback, max_tokens=4096
                )
                if code_result["verified"] and code_result["answer"]:
                    # Code execution succeeded — use verified answer
                    answer = code_result["answer"]
                    models_used.append(f"{code_model}+code")
                    strategy += "+code_verify"
                # If code failed, keep the fusion answer

            # Step 3: Self-consistency (for math/reasoning)
            if use_self_consistency:
                consistency_model = get_aggregator(task_type)
                # N=10 for speed (N=20 for benchmarks). Configurable in future.
                consistency_result = await self_consistency(
                    query, consistency_model, self.call_model_with_fallback,
                    n_samples=10, temperature=0.7, max_tokens=8192
                )
                if consistency_result["confidence"] >= 0.6:
                    # High agreement — use the consistency answer
                    answer = consistency_result["answer"]
                    models_used.append(f"{consistency_model}+consistency")
                    strategy += "+consistency"
                # If low agreement, keep the fusion answer

            # Step 4: Self-QA gate (Phase 3)
            # Score the answer, retry if below threshold
            qa_result = await self_qa_gate(
                query, answer, "nemotron-3-ultra", self.call_model_with_fallback,
                threshold=8, max_retries=2, max_tokens=2000
            )
            if qa_result["accepted"]:
                answer = qa_result["final_answer"]
                strategy += "+self_qa_passed"
            elif qa_result["attempts"] > 1:
                # Retried but still below threshold — use best attempt
                answer = qa_result["final_answer"]
                strategy += f"+self_qa_retry({qa_result['attempts']})"
            # If only 1 attempt (first pass), keep the original answer

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


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m src.orchestrator 'Your question here'")
        print("   or: python src/orchestrator.py 'Your question here'")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    print(f"Question: {query}")
    print(f"Answer: {ask(query)}")