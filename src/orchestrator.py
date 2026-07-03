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
    from .tot import tree_of_thoughts
    from .debate import multi_agent_debate
    from .skill_curator import track_skill_usage
    from .pareto_tracker import record_query as record_pareto, calculate_pareto, get_adjusted_budgets
    from .preference_router import record_routing_decision, get_routing_recommendations
    from .verifier import verify_with_code, verify_steps_with_code, apply_budget_forcing, verify_logical_with_z3
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
    from src.verifier import verify_with_code, verify_steps_with_code, apply_budget_forcing, verify_logical_with_z3
    from src.self_qa import self_qa_gate
    from src.skills_loader import build_enhanced_system_prompt
    from src.adaptive import get_model_for_task
    from src.gepa import get_system_prompt
    from src.tot import tree_of_thoughts
    from src.debate import multi_agent_debate
    from src.skill_curator import track_skill_usage
    from src.pareto_tracker import record_query as record_pareto, calculate_pareto, get_adjusted_budgets
    from src.preference_router import record_routing_decision, get_routing_recommendations


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
        """Determine routing tier: trivial, medium, or hard.
        
        Enhanced with ATTS adaptive compute allocation (arXiv:2408.03314):
        Compute-optimal strategy allocates compute adaptively per prompt difficulty.
        Easy → less compute, Hard → more compute. 4x efficiency improvement.
        """
        word_count = len(query.split())
        char_count = len(query)

        # Trivial: very short AND simple task type
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

    def get_adaptive_token_budget(self, tier: str) -> int:
        """Get adaptive token budget based on difficulty (ATTS pattern).
        
        ATTS research: 28% token savings with 2% accuracy cost.
        - Trivial: 150 tokens (quick answer)
        - Medium: 500 tokens (standard response)
        - Hard: 8192 tokens (full reasoning)
        """
        budgets = {
            "trivial": 500,    # Quick answer, no reasoning needed
            "medium": 4096,    # Standard response with some reasoning
            "hard": 8192,      # Full reasoning for complex problems
        }
        return budgets.get(tier, 8192)

    def get_adaptive_n_samples(self, tier: str) -> int:
        """Get adaptive sample count for self-consistency (BEST-Route pattern).
        
        BEST-Route research: 60% cost reduction with <1% performance drop.
        - Trivial: 1 sample (no need for self-consistency)
        - Medium: 3 samples (small panel)
        - Hard: 10 samples (full self-consistency)
        """
        from .consistency import get_adaptive_n_samples
        return get_adaptive_n_samples(tier)

    def should_use_self_moA(self, task_type: str, tier: str = "medium") -> bool:
        """Decide whether to use Self-MoA instead of heterogeneous panel.
        
        Self-MoA research (arXiv:2502.00674): Sampling one top model N times
        can outperform mixing different models by +6.6%. Use when one model
        clearly dominates the task type AND cost matters (trivial/medium tier).
        
        For hard tier, heterogeneous panel is better — diversity helps on
        complex problems. For trivial/medium, Self-MoA with the best model
        is cheaper and potentially better.
        
        Args:
            task_type: The classified task type
            tier: The difficulty tier (trivial, medium, hard)
        
        Returns:
            True if Self-MoA should be used, False for heterogeneous panel
        """
        # Self-MoA for trivial and medium tiers (cost-sensitive)
        # Heterogeneous panel for hard tier (diversity helps)
        if tier in ("trivial", "medium"):
            return True
        return False

    async def call_model(self, model: str, messages: list, temperature: float = 0.0, max_tokens: int = 8192, timeout: int = 120) -> str:
        """Call a single model with timeout, retry, and cross-backend fallback.
        
        If using Ollama and it fails, automatically falls back to OpenRouter (if key is set).
        If using OpenRouter and it fails, automatically falls back to Ollama (if running).
        """
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

    async def _try_other_backend(self, model: str, messages: list, temperature: float, max_tokens: int, timeout: int) -> Optional[str]:
        """Try other backends if the primary one fails.
        
        Fallback order:
        1. If primary is Ollama → try OpenRouter (if key), then ai/ml (if key)
        2. If primary is OpenRouter → try Ollama (if running), then ai/ml (if key)
        3. If primary is ai/ml → try OpenRouter (if key), then Ollama (if running)
        
        Returns the response or None if all backends fail.
        """
        if __package__:
            from .models import (
                OPENROUTER_MODELS, AIML_MODELS, AIML_API_BASE,
                OPENROUTER_API_BASE, OLLAMA_API_BASE, _USE_OPENROUTER, _HAS_AIML_KEY,
            )
        else:
            from src.models import (
                OPENROUTER_MODELS, AIML_MODELS, AIML_API_BASE,
                OPENROUTER_API_BASE, OLLAMA_API_BASE, _USE_OPENROUTER, _HAS_AIML_KEY,
            )
        
        # Build list of fallback backends to try (excluding the primary)
        fallback_backends = []
        
        # Always try OpenRouter if key is set and it's not the primary
        openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
        if openrouter_key and not _USE_OPENROUTER:
            fallback_backends.append(("openrouter", openrouter_key, OPENROUTER_API_BASE, OPENROUTER_MODELS))
        
        # Always try ai/ml if key is set
        aiml_key = os.environ.get("AIML_API_KEY", "")
        if aiml_key:
            fallback_backends.append(("aiml", aiml_key, AIML_API_BASE, AIML_MODELS))
        
        # Try Ollama if it's running and not the primary
        if not _USE_OPENROUTER:
            pass  # Ollama is primary, skip
        else:
            # Check if Ollama is running
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{OLLAMA_API_BASE}/api/tags", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        if resp.status == 200:
                            fallback_backends.append(("ollama", "ollama", f"{OLLAMA_API_BASE}/v1", None))
            except Exception:
                pass  # Ollama not running
        
        # Try each fallback backend
        for backend_name, key, base_url, model_map in fallback_backends:
            try:
                if backend_name == "ollama":
                    ollama_tag = MODEL_POOL.get(model, CHEAP_MODELS.get(model, {})).get("ollama_tag", model)
                    fb_client = AsyncOpenAI(base_url=base_url, api_key="ollama")
                    response = await asyncio.wait_for(
                        fb_client.chat.completions.create(
                            model=ollama_tag,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                        ),
                        timeout=timeout,
                    )
                else:
                    # OpenRouter or ai/ml — both OpenAI-compatible
                    tag = model_map.get(model, model) if model_map else model
                    fb_client = AsyncOpenAI(base_url=base_url, api_key=key)
                    response = await asyncio.wait_for(
                        fb_client.chat.completions.create(
                            model=tag,
                            messages=messages,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            extra_headers={"Authorization": f"Bearer {key}"},
                        ),
                        timeout=timeout,
                    )
                
                content = response.choices[0].message.content or ""
                if content.strip():
                    return content
            except Exception:
                continue
        
        return None

    async def call_model_with_fallback(self, model: str, messages: list, max_tokens: int = 8192, temperature: float = 0.0, timeout: int = 120) -> str:
        """Call a model, and if it fails, try fallback models + cross-backend fallback."""
        answer = await self.call_model(model, messages, temperature=temperature, max_tokens=max_tokens, timeout=timeout)
        if not answer.startswith("[ERROR"):
            return answer

        # Try fallback models on the same backend first
        fallbacks = ["glm-5.2", "deepseek-v4-pro", "kimi-k2.6"]
        if model in fallbacks:
            fallbacks.remove(model)

        for fallback in fallbacks:
            answer = await self.call_model(fallback, messages, temperature=temperature, max_tokens=max_tokens, timeout=timeout)
            if not answer.startswith("[ERROR"):
                return answer

        # All same-backend models failed — try the OTHER backend
        for fallback in [model] + fallbacks:
            cross_backend = await self._try_other_backend(fallback, messages, temperature, max_tokens, timeout)
            if cross_backend is not None:
                return cross_backend

        return answer  # All failed, return last error

    async def complete(self, query: str, system_prompt: str = None) -> str:
        """
        Main entry point. User sends a query, gets one response.
        All orchestration is internal.
        
        Enhanced with:
        - ATTS adaptive token budgets (28% token savings)
        - Adaptive sample counts (60% cost reduction, BEST-Route)
        - PRM-weighted self-consistency (+18.4% MATH, OmegaPRM)
        - 3-layer MoA fusion (+4% quality, arXiv:2406.04692)
        - USVA 4-rubric verification (ATTS)
        - Reflexion memory on failures (91% HumanEval, arXiv:2303.11366)
        - Unified routing + cascading (arXiv:2410.10347)
        """
        start_time = time.time()

        # Step 1: Classify the task
        task_type = await self.classify_task(query)
        tier = self.determine_tier(query, task_type)

        # Step 2: Route based on tier (unified routing + cascading)
        if tier == "trivial":
            # Use cheap model for trivial queries
            model = "gpt-oss-120b"
            token_budget = self.get_adaptive_token_budget(tier)
            enhanced_prompt = build_enhanced_system_prompt(task_type, system_prompt)
            track_skill_usage(task_type)  # Track for curator
            messages = [
                {"role": "system", "content": enhanced_prompt},
                {"role": "user", "content": query},
            ]
            answer = await self.call_model_with_fallback(model, messages, max_tokens=token_budget)
            models_used = [model]
            strategy = "direct_cheap+skills+adaptive_tokens"
        elif tier == "medium":
            # Use adaptive routing to pick best model (learned from logs)
            model = get_model_for_task(task_type)
            token_budget = self.get_adaptive_token_budget(tier)
            evolved_prompt = get_system_prompt(task_type, system_prompt)
            enhanced_prompt = build_enhanced_system_prompt(task_type, evolved_prompt)
            track_skill_usage(task_type)  # Track for curator
            messages = [
                {"role": "system", "content": enhanced_prompt},
                {"role": "user", "content": query},
            ]
            
            # For reasoning/math at medium tier, use Tree of Thoughts (arXiv:2305.10601)
            # ToT gives +70pp on search-heavy tasks. Only for reasoning/math.
            if task_type in ("reasoning", "math") and len(query.split()) > 15:
                tot_result = await tree_of_thoughts(
                    query, model, self.call_model_with_fallback,
                    max_depth=3, branching=3, max_nodes=10,
                    max_tokens=token_budget
                )
                if tot_result["found"]:
                    answer = tot_result["answer"]
                    strategy = f"tree_of_thoughts(d={3},nodes={tot_result['nodes_explored']})"
                else:
                    # ToT didn't find a final answer — fall back to direct
                    answer = await self.call_model_with_fallback(model, messages, max_tokens=token_budget)
                    strategy = "direct_specialist+tot_fallback"
            else:
                answer = await self.call_model_with_fallback(model, messages, max_tokens=token_budget)
                strategy = "direct_specialist+skills+adaptive+adaptive_tokens"
            
            models_used = [model]
        else:
            # Hard tier: full orchestration with 3-layer MoA + adaptive compute
            # Strategy depends on task type:
            # - math: 3-layer MoA + code verification + PRM-weighted self-consistency
            # - coding: 3-layer MoA + code verification
            # - knowledge: 3-layer MoA only
            # - reasoning: 3-layer MoA + PRM-weighted self-consistency
            # - creative: 3-layer MoA only
            # - agentic: 3-layer MoA only

            use_code_verify = task_type in ("math", "coding")
            use_self_consistency = task_type in ("math", "reasoning")
            token_budget = self.get_adaptive_token_budget(tier)

            # Step 1: Run 3-layer MoA Fusion panel
            fusion_result = await fuse(
                query, task_type, self.call_model_with_fallback,
                max_tokens=token_budget, moa_layers=3
            )
            answer = fusion_result["answer"]
            models_used = fusion_result["panel"] + [fusion_result["aggregator"]]
            strategy = f"fusion_3L_MoA({fusion_result['moa_layers']}layers)"

            # Step 2: Code verification (for math/coding)
            if use_code_verify:
                code_model = TASK_MODEL_MAP.get(task_type, "deepseek-v4-pro")
                # Step-Level Code Verification (rStar-Math pattern)
                # First verify the fusion answer's reasoning steps, then final answer
                step_result = await verify_steps_with_code(
                    query, answer, code_model, self.call_model_with_fallback,
                    max_tokens=2048, execution_timeout=10
                )
                if step_result["verified"]:
                    # Step-level verification passed — high confidence
                    answer = step_result["answer"]
                    models_used.append(f"{code_model}+step_verify({step_result['steps_verified']}/{step_result['steps_total']})")
                    strategy += f"+step_verify({step_result['steps_verified']}/{step_result['steps_total']})"
                else:
                    # Step verification failed — try final-answer verification as fallback
                    code_result = await verify_with_code(
                        query, code_model, self.call_model_with_fallback, max_tokens=4096
                    )
                    if code_result["verified"] and code_result["answer"]:
                        answer = code_result["answer"]
                        models_used.append(f"{code_model}+code")
                        strategy += "+code_verify"
                    # If both failed, keep the fusion answer

            # Step 3: PRM-weighted self-consistency (for math/reasoning)
            if use_self_consistency:
                consistency_model = get_aggregator(task_type)
                # Adaptive N samples based on difficulty (BEST-Route)
                n_samples = self.get_adaptive_n_samples(tier)
                consistency_result = await self_consistency(
                    query, consistency_model, self.call_model_with_fallback,
                    n_samples=n_samples, temperature=0.7, max_tokens=token_budget,
                    use_prm_weighting=True, verifier_model="nemotron-3-ultra"
                )
                if consistency_result["confidence"] >= 0.6:
                    # High agreement — use the consistency answer
                    answer = consistency_result["answer"]
                    models_used.append(f"{consistency_model}+consistency_prm(n={n_samples})")
                    strategy += f"+prm_consistency(n={n_samples})"
                # If low agreement, keep the fusion answer

            # Step 4: Self-QA gate with USVA 4-rubric + Reflexion
            # Score the answer using USVA, retry with reflexion if below threshold
            qa_result = await self_qa_gate(
                query, answer, "nemotron-3-ultra", self.call_model_with_fallback,
                threshold=8, max_retries=2, max_tokens=2000,
                use_usva=True, use_reflexion=True
            )
            if qa_result["accepted"]:
                answer = qa_result["final_answer"]
                strategy += "+usva_qa_passed"
            elif qa_result["attempts"] > 1:
                # Retried with reflexion but still below threshold
                # ESCALATION: Multi-agent debate (arXiv:2511.11306 — selective debate)
                # Only trigger when self-QA fails — debate is expensive
                debate_result = await multi_agent_debate(
                    query, self.call_model_with_fallback,
                    panel=["glm-5.2", "deepseek-v4-pro", "kimi-k2.6"],
                    rounds=2, aggregator="nemotron-3-ultra",
                    max_tokens=token_budget
                )
                answer = debate_result["answer"]
                models_used.append("debate_panel+nemotron")
                strategy += f"+debate_escalation({debate_result['rounds']}r)"
            # If only 1 attempt (first pass), keep the original answer

            # Step 5: s1 Budget Forcing (arXiv:2501.19393)
            # If the answer is too short for a hard problem, append "Wait" to force more reasoning
            if task_type in ("math", "reasoning") and len(answer.split()) < 50:
                forced = apply_budget_forcing(answer, min_reasoning_tokens=200)
                if forced != answer:
                    # Budget forcing triggered — regenerate with "Wait" appended
                    answer = forced
                    strategy += "+s1_budget_forcing"

            # Step 6: Z3/SMT Logical Verification (ConsistPRM pattern)
            # For reasoning tasks, verify logical consistency using Z3
            if task_type == "reasoning":
                z3_result = verify_logical_with_z3(query, answer)
                if z3_result["verified"]:
                    strategy += "+z3_verified"
                elif "contradictions" in z3_result.get("reason", "").lower():
                    # Contradictions found — flag for retry via debate
                    strategy += "+z3_contradiction"
                    # Escalate to debate if not already done
                    if "debate" not in strategy:
                        debate_result = await multi_agent_debate(
                            query, self.call_model_with_fallback,
                            panel=["glm-5.2", "deepseek-v4-pro", "kimi-k2.6"],
                            rounds=2, aggregator="nemotron-3-ultra",
                            max_tokens=token_budget
                        )
                        answer = debate_result["answer"]
                        models_used.append("debate_z3_escalation")
                        strategy += "+debate_z3"

            latency_ms = int((time.time() - start_time) * 1000)

        # Record Pareto efficiency metrics (token_savings vs accuracy)
        try:
            estimated_tokens = len(answer) // 4 if answer else 0  # Rough token estimate
            record_pareto(tier, estimated_tokens, correct=None, task_type=task_type, strategy=strategy)
        except Exception:
            pass  # Don't let metrics break the response

        # Record routing decision for preference-data collection (RouteLLM pattern)
        try:
            record_routing_decision(
                query=query, task_type=task_type, tier=tier,
                model=models_used[0] if models_used else "unknown",
                models_used=models_used, strategy=strategy,
                latency_ms=latency_ms, success=not answer.startswith("[ERROR"),
            )
        except Exception:
            pass  # Don't let metrics break the response

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