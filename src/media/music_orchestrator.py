"""
Temuclaude Music Generator, Judge, Quality Gate, and Orchestrator

Full 10-stage pipeline for music generation:
  1. Cache
  2. Intent classification
  3. Tier determination
  4. Prompt enhancement (GEPA)
  5. Parallel generation (best-of-N music models)
  6. Multi-judge consensus (score musicality, prompt adherence, audio quality)
  7. Quality gate (Reflexion loop)
  8. Post-processing (format normalization, loudness normalization)
  9. Memory bank
  10. Return

Usage:
    from src.media.music_orchestrator import MusicOrchestrator
    music = MusicOrchestrator(call_llm_func=orchestrator.call_model_with_fallback)
    result = await music.generate("upbeat electronic dance track with female vocals")
    print(result["url"])  # best audio URL
"""

import asyncio
import json
import logging
import time
import re
from typing import Optional, Callable, Awaitable

from .music_models import (
    MUSIC_PREMIUM_POOL, MUSIC_STANDARD_POOL, MUSIC_DRAFT_POOL,
    MUSIC_UNIQUE_POOLS, MUSIC_JUDGE_POOL, MUSIC_PROMPT_ENHANCER_MODEL,
    get_music_pool, get_music_judge_pool, get_music_prompt_enhancer,
    estimate_music_cost, MUSIC_QUALITY_THRESHOLDS, MUSIC_MAX_REFINE_ITERATIONS,
    MUSIC_CACHE_TTL_SECONDS, MUSIC_CASCADE_STOP_THRESHOLDS,
    MUSIC_JUDGE_COUNT_BY_TIER, MUSIC_API_ENDPOINT,
)
from .music_provider import MusicProviderManager
from .music_intent import classify_music_task, determine_music_tier, get_default_music_params
from .memory import get_memory_bank
from .media_cache import get_media_cache

logger = logging.getLogger(__name__)


# =============================================================================
# MUSIC GENERATOR — Parallel best-of-N music generation
# =============================================================================

class MusicGenerator:
    """Run N music models in parallel and return all audio outputs."""

    def __init__(self, provider_manager: MusicProviderManager = None):
        self.provider_manager = provider_manager or MusicProviderManager()

    async def generate_music(
        self,
        prompt: str,
        tier: str = "standard",
        task_type: str = "general_music",
        lyrics: str = "",
        duration_ms: int = None,
        format: str = "mp3",
        explicit_tier: str = None,
    ) -> dict:
        """Generate music using best-of-N parallel models.

        Args:
            prompt: Music description/style prompt
            tier: Quality tier ("draft", "standard", "premium")
            task_type: Classified task type for routing
            lyrics: Optional lyrics text
            duration_ms: Duration in milliseconds (None = use default for task type)
            format: Audio format ("mp3", "wav")
            explicit_tier: Override tier

        Returns:
            Dict with outputs, models_used, cost, etc.
        """
        start_time = asyncio.get_event_loop().time()

        model_pool = get_music_pool(tier, task_type)
        if not model_pool:
            return {
                "outputs": [],
                "models_used": [],
                "successful_models": [],
                "failed_models": [],
                "estimated_cost": 0.0,
                "tier": tier,
                "task_type": task_type,
                "error": "No music models available for this tier/task type",
            }

        models_used = [m["id"] for m in model_pool]
        estimated_cost = estimate_music_cost(model_pool)

        # Get default params for task type if not specified
        if duration_ms is None:
            params = get_default_music_params(task_type)
            duration_ms = params.get("duration_ms", 30000)
            if format == "mp3" and params.get("format"):
                format = params["format"]

        # Generate with all models in parallel
        tasks = []
        for model_config in model_pool:
            model_id = model_config["id"]
            kwargs = {
                "lyrics": lyrics if model_config.get("supports_lyrics", True) else "",
                "duration_ms": min(duration_ms, model_config.get("max_duration_seconds", 240) * 1000),
                "format": format,
                "estimated_cost": model_config.get("cost_per_generation", 0.0),
            }
            # Add model-specific params
            if "tags" in model_config:
                kwargs["tags"] = model_config["tags"]

            tasks.append(
                self.provider_manager.generate_music(model_id, prompt, **kwargs)
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        outputs = []
        successful_models = []
        failed_models = []

        for i, result in enumerate(results):
            model_id = model_pool[i]["id"]
            if isinstance(result, Exception):
                logger.warning(f"Music generation failed for {model_id}: {result}")
                failed_models.append(model_id)
            elif result and result.get("url"):
                outputs.append({
                    "model": model_id,
                    "url": result["url"],
                    "format": format,
                    "duration_ms": duration_ms,
                })
                successful_models.append(model_id)
            else:
                failed_models.append(model_id)

        elapsed = asyncio.get_event_loop().time() - start_time

        return {
            "outputs": outputs,
            "models_used": models_used,
            "successful_models": successful_models,
            "failed_models": failed_models,
            "estimated_cost": estimated_cost,
            "tier": tier,
            "task_type": task_type,
            "elapsed_seconds": round(elapsed, 2),
            "duration_ms": duration_ms,
            "format": format,
        }


# =============================================================================
# MUSIC JUDGE — Multi-judge consensus on music quality
# =============================================================================

def build_music_judge_prompt(prompt: str, lyrics: str, task_type: str, audio_url: str, model_name: str) -> list:
    """Build the LLM prompt for judging music output.

    The judge scores based on text analysis (prompt adherence, genre match, structure)
    and audio metadata. For premium tier with audio-capable judges (Gemini), the judge
    can actually listen to the generated music.
    """
    system_prompt = """You are an expert music quality judge. You evaluate AI-generated music on 5 dimensions, scoring each from 1 to 10.

Scoring rubric:
- musicality (1-10): Is it musically coherent with good melody, harmony, and rhythm? 10 = professional quality, 1 = discordant/random.
- prompt_adherence (1-10): Does it match the requested genre, mood, and style? 10 = perfect match, 1 = completely wrong.
- vocal_quality (1-10): If vocals are present, are they natural and well-mixed? 10 = studio quality, 1 = robotic/distorted. (If instrumental, score 7.)
- audio_quality (1-10): Is the production quality good? No artifacts, proper mixing, good dynamics? 10 = pristine, 1 = noisy/distorted.
- structure (1-10): Does it have a coherent song structure (intro, verse, chorus, etc.)? 10 = well-structured, 1 = formless.

Return ONLY a JSON object with the 5 scores. No explanation.
Example: {"musicality": 8, "prompt_adherence": 7, "vocal_quality": 8, "audio_quality": 9, "structure": 7}"""

    user_prompt = f"""Original prompt: {prompt[:500]}
Lyrics: {lyrics[:300] if lyrics else "(no lyrics provided)"}
Task type: {task_type}
Audio URL (generated by {model_name}): {audio_url}

Score this music on the 5 dimensions. Return ONLY the JSON object."""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def calculate_music_overall_score(scores: dict) -> float:
    """Calculate overall music score from dimension scores."""
    weights = {
        "musicality": 0.30,
        "prompt_adherence": 0.25,
        "vocal_quality": 0.15,
        "audio_quality": 0.20,
        "structure": 0.10,
    }
    total_weight = sum(weights.values())
    weighted_sum = sum(scores.get(dim, 5.0) * weight for dim, weight in weights.items())
    return weighted_sum / total_weight


class MusicJudge:
    """Multi-judge consensus for music evaluation."""

    def __init__(self, call_llm_func=None):
        self.call_llm_func = call_llm_func
        self.judges = get_music_judge_pool()

    async def judge_output(
        self,
        prompt: str,
        lyrics: str,
        task_type: str,
        output: dict,
    ) -> dict:
        """Judge a single music output with ALL judges."""
        model_name = output.get("model", "unknown")
        audio_url = output.get("url", "")

        if not audio_url:
            return {
                "model": model_name,
                "url": "",
                "judge_scores": [],
                "consensus_score": 0.0,
            }

        if not self.call_llm_func:
            # Fallback: neutral scores
            scores = {dim: 5.0 for dim in
                      ["musicality", "prompt_adherence", "vocal_quality", "audio_quality", "structure"]}
            scores["overall"] = 5.0
            scores["judge"] = "fallback"
            scores["weight"] = 1.0
            return {
                "model": model_name,
                "url": audio_url,
                "judge_scores": [scores],
                "consensus_score": 5.0,
            }

        # Run all judges in parallel
        tasks = []
        for judge in self.judges:
            messages = build_music_judge_prompt(prompt, lyrics, task_type, audio_url, model_name)
            tasks.append(self._judge_single(judge, messages))

        judge_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        judge_scores = []
        for i, result in enumerate(judge_results):
            if isinstance(result, Exception):
                logger.warning(f"Judge {self.judges[i]['id']} raised: {result}")
                judge_scores.append({
                    "judge": self.judges[i]["id"],
                    "overall": 5.0,
                    "weight": self.judges[i].get("weight", 1.0),
                    "error": str(result),
                })
            else:
                judge_scores.append(result)

        # Weighted consensus
        total_weight = 0.0
        weighted_sum = 0.0
        for js in judge_scores:
            weight = js.get("weight", 1.0)
            weighted_sum += js.get("overall", 5.0) * weight
            total_weight += weight

        consensus_score = weighted_sum / total_weight if total_weight > 0 else 5.0

        return {
            "model": model_name,
            "url": audio_url,
            "judge_scores": judge_scores,
            "consensus_score": round(consensus_score, 2),
        }

    async def _judge_single(self, judge: dict, messages: list) -> dict:
        """Judge with a single judge model."""
        try:
            response = await self.call_llm_func(
                judge.get("openrouter_id", judge["id"]),
                messages,
                max_tokens=300,
                temperature=0.0,
            )

            # Parse JSON scores
            scores = self._parse_scores(response)
            scores["overall"] = calculate_music_overall_score(scores)
            scores["judge"] = judge["id"]
            scores["weight"] = judge.get("weight", 1.0)
            return scores

        except Exception as e:
            logger.warning(f"Judge {judge['id']} failed: {e}")
            scores = {dim: 5.0 for dim in
                      ["musicality", "prompt_adherence", "vocal_quality", "audio_quality", "structure"]}
            scores["overall"] = 5.0
            scores["judge"] = judge["id"]
            scores["weight"] = judge.get("weight", 1.0)
            scores["error"] = str(e)
            return scores

    def _parse_scores(self, response: str) -> dict:
        """Parse judge response into scores."""
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                scores = json.loads(json_str)
                for dim in ["musicality", "prompt_adherence", "vocal_quality", "audio_quality", "structure"]:
                    if dim not in scores:
                        scores[dim] = 5.0
                    else:
                        scores[dim] = max(1, min(10, float(scores[dim])))
                return scores
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback: regex
        scores = {}
        for dim in ["musicality", "prompt_adherence", "vocal_quality", "audio_quality", "structure"]:
            pattern = rf"{dim}['\"]?\s*[:=]\s*['\"]?(\d+(?:\.\d+)?)"
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                try:
                    scores[dim] = max(1, min(10, float(match.group(1))))
                except ValueError:
                    scores[dim] = 5.0
            else:
                scores[dim] = 5.0
        return scores

    async def judge_all(
        self,
        prompt: str,
        lyrics: str,
        task_type: str,
        outputs: list,
    ) -> dict:
        """Judge all music outputs and determine the winner."""
        if not outputs:
            return {
                "judged_outputs": [],
                "winner": None,
                "best_score": 0.0,
                "all_scores": {},
            }

        tasks = [self.judge_output(prompt, lyrics, task_type, output) for output in outputs]
        judged = await asyncio.gather(*tasks, return_exceptions=True)

        judged_outputs = []
        for i, result in enumerate(judged):
            if isinstance(result, Exception):
                judged_outputs.append({
                    "model": outputs[i].get("model", "unknown"),
                    "url": outputs[i].get("url", ""),
                    "judge_scores": [],
                    "consensus_score": 0.0,
                    "error": str(result),
                })
            else:
                judged_outputs.append(result)

        judged_outputs.sort(key=lambda x: x.get("consensus_score", 0.0), reverse=True)

        all_scores = {jo["model"]: jo.get("consensus_score", 0.0) for jo in judged_outputs}
        winner = judged_outputs[0] if judged_outputs else None
        best_score = winner.get("consensus_score", 0.0) if winner else 0.0

        return {
            "judged_outputs": judged_outputs,
            "winner": winner,
            "best_score": best_score,
            "all_scores": all_scores,
        }


# =============================================================================
# MUSIC QUALITY GATE — Reflexion loop
# =============================================================================

class MusicQualityGate:
    """Quality gate with Reflexion for music."""

    def __init__(self, generator: MusicGenerator = None, judge: MusicJudge = None, call_llm_func=None):
        self.generator = generator or MusicGenerator()
        self.judge = judge or MusicJudge(call_llm_func=call_llm_func)
        self.call_llm_func = call_llm_func

    def get_threshold(self, task_type: str) -> float:
        return MUSIC_QUALITY_THRESHOLDS.get(task_type, 7.0)

    async def evaluate_and_refine(
        self,
        prompt: str,
        lyrics: str,
        tier: str,
        task_type: str,
        generation_result: dict,
        duration_ms: int = 30000,
        format: str = "mp3",
        iteration: int = 0,
        max_iterations: int = None,
        **gen_kwargs,
    ) -> dict:
        """Evaluate music generation and refine if below threshold."""
        if max_iterations is None:
            max_iterations = MUSIC_MAX_REFINE_ITERATIONS

        threshold = self.get_threshold(task_type)
        outputs = generation_result.get("outputs", [])

        # Draft tier: no judge, just return the single output
        judge_count = MUSIC_JUDGE_COUNT_BY_TIER.get(tier, 1)
        if judge_count == 0:
            # Draft — return first output without judging
            winner = outputs[0] if outputs else None
            best_score = 6.0  # Assume "good enough" for draft
            judge_result = {"winner": winner, "best_score": best_score, "all_scores": {}}
        else:
            # Judge all outputs
            judge_result = await self.judge.judge_all(prompt, lyrics, task_type, outputs)

        best_score = judge_result.get("best_score", 0.0)
        winner = judge_result.get("winner")

        iteration_record = {
            "iteration": iteration,
            "tier": tier,
            "models_used": generation_result.get("models_used", []),
            "successful_models": generation_result.get("successful_models", []),
            "failed_models": generation_result.get("failed_models", []),
            "estimated_cost": generation_result.get("estimated_cost", 0.0),
            "best_score": best_score,
            "all_scores": judge_result.get("all_scores", {}),
            "winner": winner,
        }

        if best_score >= threshold or iteration >= max_iterations:
            return {
                "final_output": winner,
                "final_score": best_score,
                "iterations": iteration + 1,
                "passed_gate": best_score >= threshold,
                "threshold": threshold,
                "history": [iteration_record],
                "total_cost": generation_result.get("estimated_cost", 0.0),
            }

        # Below threshold — refine with enhanced prompt
        logger.info(f"Music quality gate: score {best_score:.1f} < {threshold:.1f}, refining...")

        # Enhance prompt for retry (add more detail based on what went wrong)
        enhanced_prompt = prompt
        if self.call_llm_func:
            try:
                critique_messages = [
                    {"role": "system", "content": "You are a music production expert. Improve the given music prompt to get better results. Return ONLY the improved prompt, nothing else."},
                    {"role": "user", "content": f"Original prompt: {prompt}\nScore: {best_score:.1f}/10\nTask: {task_type}\n\nRewrite this prompt to be more specific about genre, mood, instruments, tempo, and structure. Max 200 words."},
                ]
                enhanced_prompt = await self.call_llm_func(
                    "z-ai/glm-5.2", critique_messages, max_tokens=200, temperature=0.7,
                )
                if enhanced_prompt:
                    enhanced_prompt = enhanced_prompt.strip()
            except Exception as e:
                logger.warning(f"Prompt enhancement failed: {e}")

        new_generation = await self.generator.generate_music(
            prompt=enhanced_prompt or prompt,
            tier=tier,
            task_type=task_type,
            lyrics=lyrics,
            duration_ms=duration_ms,
            format=format,
        )

        next_result = await self.evaluate_and_refine(
            enhanced_prompt or prompt, lyrics, tier, task_type, new_generation,
            duration_ms, format, iteration + 1, max_iterations, **gen_kwargs,
        )

        next_result["history"] = [iteration_record] + next_result.get("history", [])
        next_result["total_cost"] = (
            generation_result.get("estimated_cost", 0.0)
            + next_result.get("total_cost", 0.0)
        )

        return next_result

    async def run(
        self,
        prompt: str,
        tier: str = "standard",
        task_type: str = "general_music",
        lyrics: str = "",
        duration_ms: int = 30000,
        format: str = "mp3",
        **gen_kwargs,
    ) -> dict:
        """Full quality gate pipeline."""
        generation = await self.generator.generate_music(
            prompt=prompt, tier=tier, task_type=task_type,
            lyrics=lyrics, duration_ms=duration_ms, format=format,
        )
        return await self.evaluate_and_refine(
            prompt, lyrics, tier, task_type, generation,
            duration_ms, format, **gen_kwargs,
        )


# =============================================================================
# MUSIC ORCHESTRATOR — Full 10-stage pipeline
# =============================================================================

class MusicOrchestrator:
    """Full 10-stage music generation pipeline.

    Usage:
        music = MusicOrchestrator(call_llm_func=orchestrator.call_model_with_fallback)
        result = await music.generate("upbeat electronic dance track", quality_tier="standard")
        print(result["url"])  # best audio URL
    """

    def __init__(self, call_llm_func: Callable[..., Awaitable[str]] = None):
        self.call_llm_func = call_llm_func
        self.generator = MusicGenerator()
        self.judge = MusicJudge(call_llm_func=call_llm_func)
        self.quality_gate = MusicQualityGate(
            generator=self.generator, judge=self.judge, call_llm_func=call_llm_func,
        )
        self.memory = get_memory_bank()
        self.cache = get_media_cache()

    async def generate(
        self,
        prompt: str,
        quality_tier: str = "auto",
        lyrics: str = "",
        duration_ms: int = None,
        format: str = "mp3",
    ) -> dict:
        """Generate music through the full pipeline.

        Args:
            prompt: Music description/style prompt
            quality_tier: "draft", "standard", "premium", or "auto"
            lyrics: Optional lyrics text
            duration_ms: Duration in milliseconds (None = auto from task type)
            format: Audio format ("mp3", "wav")

        Returns:
            Dict with url, score, model, cost, etc.
        """
        start_time = time.time()

        # Stage 1: Cache (use task_type="auto" for get — it matches set which uses the classified task_type
        # because the cache key includes task_type in the hash. We need to check with the final task_type.
        # So we classify first, then check cache.
        explicit_tier = quality_tier if quality_tier != "auto" else None

        # Stage 2: Intent classification (moved before cache check so we can use task_type in cache key)
        task_type = classify_music_task(prompt, lyrics)

        # Stage 3: Tier determination
        if quality_tier == "auto":
            tier = determine_music_tier(prompt, task_type, explicit_tier)
        else:
            tier = quality_tier

        cache_key = f"{prompt}|{lyrics[:100]}|{duration_ms}|{format}"
        cached = self.cache.get_generation_result(
            cache_key, tier, task_type, "audio", format,
        )
        if cached:
            logger.info("Music cache HIT")
            self.memory.record_generation(
                task_type=cached.get("task_type", "general_music"),
                models_used=[], winner="", scores={}, cache_hit=True,
            )
            cached["cache_hit"] = True
            cached["elapsed_seconds"] = round(time.time() - start_time, 2)
            return cached

        # Get default duration if not specified
        if duration_ms is None:
            params = get_default_music_params(task_type)
            duration_ms = params.get("duration_ms", 30000)
            if format == "mp3" and params.get("format"):
                format = params["format"]

        logger.info(f"Music pipeline: task={task_type}, tier={tier}, duration={duration_ms}ms, prompt={prompt[:50]}...")

        # Stage 4-7: Generate → Judge → Quality Gate
        gate_result = await self.quality_gate.run(
            prompt=prompt,
            tier=tier,
            task_type=task_type,
            lyrics=lyrics,
            duration_ms=duration_ms,
            format=format,
        )

        final_output = gate_result.get("final_output")
        final_score = gate_result.get("final_score", 0.0)
        iterations = gate_result.get("iterations", 1)
        passed_gate = gate_result.get("passed_gate", False)
        total_cost = gate_result.get("total_cost", 0.0)
        history = gate_result.get("history", [])

        final_url = final_output.get("url", "") if final_output else ""
        winning_model = final_output.get("model", "") if final_output else ""

        # Stage 8: Post-processing (placeholder — loudness normalization could be added)
        # Music post-processing would involve ffmpeg for loudness normalization,
        # format conversion, trimming, etc. For now, the URL is used as-is.

        # Stage 9: Memory bank
        if history:
            latest = history[-1]
            self.memory.record_generation(
                task_type=task_type,
                models_used=latest.get("models_used", []),
                winner=winning_model,
                scores=latest.get("all_scores", {}),
                cost=total_cost,
                iterations=iterations,
            )

        # Stage 10: Return
        elapsed = time.time() - start_time

        result = {
            "url": final_url,
            "score": final_score,
            "model": winning_model,
            "models_used": history[-1].get("models_used", []) if history else [],
            "successful_models": history[-1].get("successful_models", []) if history else [],
            "tier": tier,
            "task_type": task_type,
            "iterations": iterations,
            "passed_gate": passed_gate,
            "cost": round(total_cost, 4),
            "cache_hit": False,
            "duration_ms": duration_ms,
            "format": format,
            "has_lyrics": bool(lyrics),
            "elapsed_seconds": round(elapsed, 2),
            "history": history,
        }

        # Cache the result
        self.cache.set_generation_result(
            cache_key, quality_tier, task_type, result,
            media_type="audio", size=format,
        )

        logger.info(
            f"Music pipeline complete: score={final_score:.1f}, model={winning_model}, "
            f"iterations={iterations}, cost=${total_cost:.4f}, elapsed={elapsed:.1f}s"
        )

        return result

    def get_stats(self) -> dict:
        """Get pipeline statistics."""
        return {
            "cache": self.cache.stats(),
            "memory": self.memory.get_summary(),
        }