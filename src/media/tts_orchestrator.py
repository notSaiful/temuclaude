"""
Temuclaude TTS Generator, Judge, Quality Gate, and Orchestrator

Full 10-stage pipeline for TTS generation:
  1. Cache
  2. Intent classification
  3. Tier determination
  4. Prompt/voice enhancement
  5. Parallel generation (best-of-N TTS models)
  6. Multi-judge consensus (score naturalness, emotion, clarity)
  7. Quality gate (Reflexion loop)
  8. Post-processing (format conversion placeholder)
  9. Memory bank
  10. Return
"""

import asyncio
import json
import logging
import time
import re
from typing import Optional, Callable, Awaitable

from .tts_models import (
    TTS_PREMIUM_POOL, TTS_STANDARD_POOL, TTS_DRAFT_POOL, TTS_BUDGET_POOL,
    TTS_UNIQUE_POOLS, TTS_JUDGE_POOL, TTS_PROMPT_ENHANCER_MODEL,
    get_tts_pool, get_tts_judge_pool, get_tts_prompt_enhancer,
    estimate_tts_cost, TTS_QUALITY_THRESHOLDS, TTS_MAX_REFINE_ITERATIONS,
    TTS_CACHE_TTL_SECONDS, COMMON_VOICES,
)
from .tts_provider import TTSProviderManager
from .tts_intent import classify_tts_task, determine_tts_tier, get_default_voice
from .memory import get_memory_bank
from .media_cache import get_media_cache

logger = logging.getLogger(__name__)


# =============================================================================
# TTS GENERATOR — Parallel best-of-N TTS generation
# =============================================================================

class TTSGenerator:
    """Run N TTS models in parallel and return all audio outputs."""

    def __init__(self, provider_manager: TTSProviderManager = None):
        self.provider_manager = provider_manager or TTSProviderManager()

    async def generate_speech(
        self,
        text: str,
        tier: str = "standard",
        task_type: str = "general_tts",
        voice: str = None,
        response_format: str = "mp3",
        speed: float = 1.0,
        explicit_tier: str = None,
    ) -> dict:
        """Generate speech using best-of-N parallel TTS models.

        Args:
            text: Text to convert to speech
            tier: Quality tier
            task_type: Classified task type
            voice: Voice name (if None, uses default for task type)
            response_format: Audio format
            speed: Speech speed
            explicit_tier: Override tier

        Returns:
            Dict with outputs, models_used, cost, etc.
        """
        start_time = asyncio.get_event_loop().time()

        model_pool = get_tts_pool(tier, task_type)
        if not model_pool:
            return {
                "outputs": [],
                "models_used": [],
                "successful_models": [],
                "failed_models": [],
                "estimated_cost": 0.0,
                "tier": tier,
                "task_type": task_type,
                "error": "No TTS models available for this tier/task type",
            }

        models_used = [m["id"] for m in model_pool]
        estimated_cost = estimate_tts_cost(model_pool, len(text))

        # Use default voice if not specified
        if voice is None:
            voice = get_default_voice(task_type)

        # Generate with all models in parallel
        tasks = []
        for model_config in model_pool:
            model_id = model_config["id"]
            kwargs = {
                "voice": voice,
                "response_format": response_format,
                "speed": speed,
                "estimated_cost": model_config.get("cost_per_1k_chars", 0.0) * (len(text) / 1000.0),
            }
            tasks.append(
                self.provider_manager.generate_speech(model_id, text, **kwargs)
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        outputs = []
        successful_models = []
        failed_models = []

        for i, result in enumerate(results):
            model_id = model_pool[i]["id"]
            if isinstance(result, Exception):
                logger.warning(f"TTS generation failed for {model_id}: {result}")
                failed_models.append(model_id)
            elif result and result.get("url"):
                outputs.append({
                    "model": model_id,
                    "url": result["url"],
                    "voice": voice,
                    "format": response_format,
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
            "voice": voice,
            "text_length": len(text),
        }


# =============================================================================
# TTS JUDGE — Multi-judge consensus on speech quality
# =============================================================================

def build_tts_judge_prompt(text: str, task_type: str, audio_url: str, model_name: str) -> list:
    """Build the LLM prompt for judging TTS output.

    The judge scores based on text analysis (pronunciation, pacing) and
    audio metadata. For premium tier with audio-capable judges, the judge
    can actually listen to the audio.
    """
    system_prompt = """You are an expert TTS (text-to-speech) quality judge. You evaluate AI-generated speech on 5 dimensions, scoring each from 1 to 10.

Scoring rubric:
- naturalness (1-10): Does it sound human? 10 = indistinguishable from human speech, 1 = robotic.
- emotion (1-10): Does it convey appropriate emotion for the text? 10 = perfectly matched, 1 = flat/wrong.
- clarity (1-10): Is the speech clear and intelligible? 10 = crystal clear, 1 = mumbled/unclear.
- pronunciation (1-10): Are all words pronounced correctly? 10 = perfect, 1 = many errors.
- pacing (1-10): Is the speed and rhythm appropriate? 10 = perfect pacing, 1 = too fast/slow/irregular.

Return ONLY a JSON object with the 5 scores. No explanation.
Example: {"naturalness": 8, "emotion": 7, "clarity": 9, "pronunciation": 8, "pacing": 8}"""

    user_prompt = f"""Original text: {text[:500]}
Task type: {task_type}
Audio URL (generated by {model_name}): {audio_url}

Score this speech on the 5 dimensions. Return ONLY the JSON object."""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def calculate_tts_overall_score(scores: dict) -> float:
    """Calculate overall TTS score from dimension scores."""
    weights = {
        "naturalness": 0.30,
        "emotion": 0.20,
        "clarity": 0.20,
        "pronunciation": 0.15,
        "pacing": 0.15,
    }
    total_weight = sum(weights.values())
    weighted_sum = sum(scores.get(dim, 5.0) * weight for dim, weight in weights.items())
    return weighted_sum / total_weight


class TTSJudge:
    """Multi-judge consensus for TTS evaluation."""

    def __init__(self, call_llm_func=None):
        self.call_llm_func = call_llm_func
        self.judges = TTS_JUDGE_POOL

    async def judge_output(
        self,
        text: str,
        task_type: str,
        output: dict,
    ) -> dict:
        """Judge a single TTS output with ALL judges."""
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
            scores = {dim: 5.0 for dim in ["naturalness", "emotion", "clarity", "pronunciation", "pacing"]}
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
            messages = build_tts_judge_prompt(text, task_type, audio_url, model_name)
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
            scores["overall"] = calculate_tts_overall_score(scores)
            scores["judge"] = judge["id"]
            scores["weight"] = judge.get("weight", 1.0)
            return scores

        except Exception as e:
            logger.warning(f"Judge {judge['id']} failed: {e}")
            scores = {dim: 5.0 for dim in ["naturalness", "emotion", "clarity", "pronunciation", "pacing"]}
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
                for dim in ["naturalness", "emotion", "clarity", "pronunciation", "pacing"]:
                    if dim not in scores:
                        scores[dim] = 5.0
                    else:
                        scores[dim] = max(1, min(10, float(scores[dim])))
                return scores
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback: regex
        scores = {}
        for dim in ["naturalness", "emotion", "clarity", "pronunciation", "pacing"]:
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
        text: str,
        task_type: str,
        outputs: list,
    ) -> dict:
        """Judge all TTS outputs and determine the winner."""
        if not outputs:
            return {
                "judged_outputs": [],
                "winner": None,
                "best_score": 0.0,
                "all_scores": {},
            }

        tasks = [self.judge_output(text, task_type, output) for output in outputs]
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
# TTS QUALITY GATE — Reflexion loop
# =============================================================================

class TTSQualityGate:
    """Quality gate with Reflexion for TTS."""

    def __init__(self, generator: TTSGenerator = None, judge: TTSJudge = None, call_llm_func=None):
        self.generator = generator or TTSGenerator()
        self.judge = judge or TTSJudge(call_llm_func=call_llm_func)
        self.call_llm_func = call_llm_func

    def get_threshold(self, task_type: str) -> float:
        return TTS_QUALITY_THRESHOLDS.get(task_type, 7.0)

    async def evaluate_and_refine(
        self,
        text: str,
        tier: str,
        task_type: str,
        generation_result: dict,
        voice: str = None,
        iteration: int = 0,
        max_iterations: int = None,
        **gen_kwargs,
    ) -> dict:
        """Evaluate TTS generation and refine if below threshold."""
        if max_iterations is None:
            max_iterations = TTS_MAX_REFINE_ITERATIONS

        threshold = self.get_threshold(task_type)
        outputs = generation_result.get("outputs", [])

        # Judge all outputs
        judge_result = await self.judge.judge_all(text, task_type, outputs)
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

        # Below threshold — refine (for TTS, we try different voices or speeds)
        logger.info(f"TTS quality gate: score {best_score:.1f} < {threshold:.1f}, refining...")

        # Try with a different voice on retry
        if voice is None:
            voice = get_default_voice(task_type)

        # Cycle through voices for diversity
        voice_idx = (iteration + 1) % len(COMMON_VOICES)
        new_voice = COMMON_VOICES[voice_idx]

        new_generation = await self.generator.generate_speech(
            text=text,
            tier=tier,
            task_type=task_type,
            voice=new_voice,
            **gen_kwargs,
        )

        next_result = await self.evaluate_and_refine(
            text, tier, task_type, new_generation, new_voice,
            iteration + 1, max_iterations, **gen_kwargs,
        )

        next_result["history"] = [iteration_record] + next_result.get("history", [])
        next_result["total_cost"] = (
            generation_result.get("estimated_cost", 0.0)
            + next_result.get("total_cost", 0.0)
        )

        return next_result

    async def run(
        self,
        text: str,
        tier: str = "standard",
        task_type: str = "general_tts",
        voice: str = None,
        **gen_kwargs,
    ) -> dict:
        """Full quality gate pipeline."""
        generation = await self.generator.generate_speech(
            text=text, tier=tier, task_type=task_type, voice=voice, **gen_kwargs,
        )
        return await self.evaluate_and_refine(
            text, tier, task_type, generation, voice, **gen_kwargs,
        )


# =============================================================================
# TTS ORCHESTRATOR — Full 10-stage pipeline
# =============================================================================

class TTSOrchestrator:
    """Full 10-stage TTS generation pipeline.

    Usage:
        tts = TTSOrchestrator(call_llm_func=orchestrator.call_model_with_fallback)
        result = await tts.generate("Hello world", quality_tier="standard")
        print(result["url"])  # best audio URL
    """

    def __init__(self, call_llm_func: Callable[..., Awaitable[str]] = None):
        self.call_llm_func = call_llm_func
        self.generator = TTSGenerator()
        self.judge = TTSJudge(call_llm_func=call_llm_func)
        self.quality_gate = TTSQualityGate(
            generator=self.generator, judge=self.judge, call_llm_func=call_llm_func,
        )
        self.memory = get_memory_bank()
        self.cache = get_media_cache()

    async def generate(
        self,
        text: str,
        quality_tier: str = "auto",
        voice: str = None,
        response_format: str = "mp3",
        speed: float = 1.0,
        prompt: str = "",
    ) -> dict:
        """Generate speech through the full pipeline.

        Args:
            text: Text to convert to speech
            quality_tier: "draft", "budget", "standard", "premium", or "auto"
            voice: Voice name (None = auto-select)
            response_format: Audio format
            speed: Speech speed
            prompt: Additional instructions

        Returns:
            Dict with url, score, model, cost, etc.
        """
        start_time = time.time()

        # Stage 1: Cache
        explicit_tier = quality_tier if quality_tier != "auto" else None
        cache_key_text = f"{text}|{quality_tier}|{voice}|{response_format}|{speed}"
        cached = self.cache.get_generation_result(
            cache_key_text, quality_tier, "tts", "audio", response_format,
        )
        if cached:
            logger.info("TTS cache HIT")
            self.memory.record_generation(
                task_type=cached.get("task_type", "general_tts"),
                models_used=[], winner="", scores={}, cache_hit=True,
            )
            cached["cache_hit"] = True
            cached["elapsed_seconds"] = round(time.time() - start_time, 2)
            return cached

        # Stage 2: Intent classification
        task_type = classify_tts_task(text, prompt)

        # Stage 3: Tier determination
        if quality_tier == "auto":
            tier = determine_tts_tier(text, task_type)
        else:
            tier = quality_tier

        # Stage 4: Voice selection
        if voice is None:
            voice = get_default_voice(task_type)

        logger.info(f"TTS pipeline: task={task_type}, tier={tier}, voice={voice}, text_len={len(text)}")

        # Stage 5-7: Generate → Judge → Quality Gate
        gate_result = await self.quality_gate.run(
            text=text,
            tier=tier,
            task_type=task_type,
            voice=voice,
            response_format=response_format,
            speed=speed,
        )

        final_output = gate_result.get("final_output")
        final_score = gate_result.get("final_score", 0.0)
        iterations = gate_result.get("iterations", 1)
        passed_gate = gate_result.get("passed_gate", False)
        total_cost = gate_result.get("total_cost", 0.0)
        history = gate_result.get("history", [])

        final_url = final_output.get("url", "") if final_output else ""
        winning_model = final_output.get("model", "") if final_output else ""

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
            "voice": voice,
            "format": response_format,
            "text_length": len(text),
            "elapsed_seconds": round(elapsed, 2),
            "history": history,
        }

        # Cache the result
        self.cache.set_generation_result(
            cache_key_text, quality_tier, task_type, result,
            media_type="audio", size=response_format,
        )

        logger.info(
            f"TTS pipeline complete: score={final_score:.1f}, model={winning_model}, "
            f"iterations={iterations}, cost=${total_cost:.4f}, elapsed={elapsed:.1f}s"
        )

        return result

    def get_stats(self) -> dict:
        """Get pipeline statistics."""
        return {
            "cache": self.cache.stats(),
            "memory": self.memory.get_summary(),
        }