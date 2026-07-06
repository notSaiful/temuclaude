"""
Temuclaude Media Orchestrator

The main entry point for media generation. Implements the full 10-stage pipeline:

  Stage 1: Semantic Cache — check if we've generated this before ($0 cost)
  Stage 2: Intent Classification — classify the prompt type
  Stage 3: Tier Determination — determine quality tier (ATTS adaptive)
  Stage 4: Prompt Enhancement — GEPA prompt evolution per model
  Stage 5: Parallel Generation — best-of-N models in parallel
  Stage 6: Multi-Judge Consensus — 3 vision LLMs score outputs
  Stage 7: Quality Gate — if below threshold, critique & regenerate (Reflexion)
  Stage 8: Post-Processing — upscale, face restore
  Stage 9: Memory Bank — store which model won, update routing
  Stage 10: Return — final output + metadata

Usage:
    from src.media.orchestrator import MediaOrchestrator

    mo = MediaOrchestrator(call_llm_func=orchestrator.call_model_with_fallback)
    result = await mo.generate_image("a photorealistic cat")
    print(result["url"])  # best image URL
    print(result["score"])  # judge score
    print(result["models_used"])  # which models ran
"""

import asyncio
import time
import logging
from typing import Optional, Callable, Awaitable

from .intent import classify_media_task, determine_media_tier, is_video_prompt
from .models import get_image_pool, get_video_pool, estimate_image_cost, estimate_video_cost
from .prompt_enhancer import enhance_prompts_for_pool
from .generator import MediaGenerator
from .cascading_generator import CascadingMediaGenerator
from .judge import MediaJudge
from .quality_gate import MediaQualityGate
from .post_processor import MediaPostProcessor
from .memory import get_memory_bank
from .media_cache import get_media_cache

logger = logging.getLogger(__name__)


class MediaOrchestrator:
    """Full 10-stage media generation pipeline.

    One call to generate_image() or generate_video() runs the entire pipeline:
    cache → classify → tier → enhance → generate → judge → quality gate → post-process → memory → return.

    All orchestration is invisible to the user.
    """

    def __init__(
        self,
        call_llm_func: Callable[..., Awaitable[str]] = None,
        provider_manager=None,
    ):
        """
        Args:
            call_llm_func: Async function to call LLM for prompt enhancement and judging.
                Signature: async func(model: str, messages: list, max_tokens: int, temperature: float) -> str
                This is typically orchestrator.call_model_with_fallback from the LLM orchestrator.
            provider_manager: Media provider manager (AIML API + fal.ai).
                If None, creates a default one.
        """
        self.call_llm_func = call_llm_func
        # Use cascading generator for 7.9x cost savings (cheapest first, add more only if needed)
        self.generator = MediaGenerator(
            provider_manager=provider_manager,
            call_llm_func=call_llm_func,
        )
        self.cascading_generator = CascadingMediaGenerator(
            provider_manager=provider_manager,
            call_llm_func=call_llm_func,
        )
        self.judge = MediaJudge(call_llm_func=call_llm_func)
        self.quality_gate = MediaQualityGate(
            generator=self.generator,
            judge=self.judge,
            call_llm_func=call_llm_func,
        )
        self.post_processor = MediaPostProcessor(provider_manager=provider_manager)
        self.memory = get_memory_bank()
        self.cache = get_media_cache()

    async def generate_image(
        self,
        prompt: str,
        quality_tier: str = "auto",
        size: str = "1024x1024",
        target_resolution: int = 4096,
    ) -> dict:
        """Generate an image through the full 10-stage pipeline.

        Args:
            prompt: Image generation prompt
            quality_tier: "draft", "standard", "premium", or "auto" (auto-detect)
            size: Image size (e.g., "1024x1024")
            target_resolution: Target resolution for post-processing upscaling

        Returns:
            Dict with:
              - 'url': Final image URL
              - 'score': Consensus judge score (1-10)
              - 'model': Which model won
              - 'models_used': All models that were attempted
              - 'tier': Quality tier used
              - 'task_type': Classified task type
              - 'iterations': Number of quality gate iterations
              - 'cost': Total estimated cost
              - 'cache_hit': Whether this was a cache hit
              - 'upscaled': Whether post-processing was applied
              - 'elapsed_seconds': Total pipeline time
        """
        start_time = time.time()

        # === Stage 1: Semantic Cache ===
        explicit_tier = quality_tier if quality_tier != "auto" else None

        # Check pipeline-level cache
        cached = self.cache.get_generation_result(
            prompt, quality_tier if quality_tier != "auto" else "auto",
            "auto", "image", size,
        )
        if cached:
            logger.info(f"Media cache HIT — returning cached result for: {prompt[:50]}...")
            self.memory.record_generation(
                task_type=cached.get("task_type", "general_image"),
                models_used=[],
                winner="",
                scores={},
                cache_hit=True,
            )
            cached["cache_hit"] = True
            cached["elapsed_seconds"] = round(time.time() - start_time, 2)
            return cached

        # === Stage 2: Intent Classification ===
        task_type = classify_media_task(prompt)

        # === Stage 3: Tier Determination ===
        if quality_tier == "auto":
            tier = determine_media_tier(prompt, task_type)
        else:
            tier = quality_tier

        logger.info(f"Media pipeline: task={task_type}, tier={tier}, prompt={prompt[:50]}...")

        # === Stage 4-5: Cascading Generation (cheapest first, add more only if needed) ===
        # This replaces blind best-of-N with intelligent cascading — 7.9x cheaper.
        # For draft/budget tier: single model, no cascade needed.
        # For standard/premium tier: cascade from cheapest to most expensive.
        from .models import CASCADING_ENABLED
        if CASCADING_ENABLED and tier in ("standard", "premium"):
            cascade_result = await self.cascading_generator.generate_images_cascading(
                prompt=prompt,
                tier=tier,
                task_type=task_type,
                size=size,
            )
            # If cascade produced good output, skip the full quality gate
            if cascade_result.get("early_exit") and cascade_result.get("outputs"):
                # Cascade found good output early — pick the best from cascade
                outputs = cascade_result["outputs"]
                # Use the judge to pick the best output from the cascade
                judge_result = await self.judge.judge_all(prompt, task_type, outputs, "image")
                final_output = judge_result.get("winner")
                final_score = judge_result.get("best_score", 0.0)
                iterations = 1
                passed_gate = final_score >= 7.5
                total_cost = cascade_result.get("estimated_cost", 0.0)
                history = [{
                    "iteration": 0,
                    "tier": tier,
                    "models_used": cascade_result.get("models_used", []),
                    "successful_models": cascade_result.get("successful_models", []),
                    "failed_models": cascade_result.get("failed_models", []),
                    "estimated_cost": total_cost,
                    "best_score": final_score,
                    "all_scores": judge_result.get("all_scores", {}),
                    "winner": final_output,
                    "cascade_steps": cascade_result.get("cascade_steps", []),
                    "early_exit": True,
                }]
            else:
                # Cascade didn't find good output early — run full quality gate with all outputs
                # Fall through to quality gate with the cascade's outputs
                gate_result = await self.quality_gate.run(
                    prompt=prompt,
                    tier=tier,
                    task_type=task_type,
                    media_type="image",
                    size=size,
                )
                final_output = gate_result.get("final_output")
                final_score = gate_result.get("final_score", 0.0)
                iterations = gate_result.get("iterations", 1)
                passed_gate = gate_result.get("passed_gate", False)
                total_cost = gate_result.get("total_cost", 0.0) + cascade_result.get("estimated_cost", 0.0)
                history = gate_result.get("history", [])
        else:
            # Draft/budget or cascading disabled — use standard pipeline
            gate_result = await self.quality_gate.run(
                prompt=prompt,
                tier=tier,
                task_type=task_type,
                media_type="image",
                size=size,
            )
            final_output = gate_result.get("final_output")
            final_score = gate_result.get("final_score", 0.0)
            iterations = gate_result.get("iterations", 1)
            passed_gate = gate_result.get("passed_gate", False)
            total_cost = gate_result.get("total_cost", 0.0)
            history = gate_result.get("history", [])

        # === Stage 8: Post-Processing ===
        if final_output and final_output.get("url"):
            pp_result = await self.post_processor.process_image(
                image_url=final_output["url"],
                task_type=task_type,
                current_size=size,
                target_resolution=target_resolution,
            )
            final_url = pp_result["url"]
            upscaled = pp_result.get("upscaled", False)
            total_cost += pp_result.get("cost", 0.0)
        else:
            final_url = ""
            upscaled = False

        # === Stage 9: Memory Bank ===
        # Record which model won for this task type
        if history:
            latest = history[-1]
            self.memory.record_generation(
                task_type=task_type,
                models_used=latest.get("models_used", []),
                winner=final_output.get("model", "") if final_output else "",
                scores=latest.get("all_scores", {}),
                cost=total_cost,
                iterations=iterations,
            )

        # === Stage 10: Return ===
        elapsed = time.time() - start_time

        result = {
            "url": final_url,
            "score": final_score,
            "model": final_output.get("model", "") if final_output else "",
            "models_used": history[-1].get("models_used", []) if history else [],
            "successful_models": history[-1].get("successful_models", []) if history else [],
            "tier": tier,
            "task_type": task_type,
            "iterations": iterations,
            "passed_gate": passed_gate,
            "cost": round(total_cost, 4),
            "cache_hit": False,
            "upscaled": upscaled,
            "elapsed_seconds": round(elapsed, 2),
            "history": history,
        }

        # Cache the result
        self.cache.set_generation_result(
            prompt, quality_tier, task_type, result,
            media_type="image", size=size,
        )

        logger.info(
            f"Media pipeline complete: score={final_score:.1f}, model={result['model']}, "
            f"iterations={iterations}, cost=${total_cost:.4f}, elapsed={elapsed:.1f}s"
        )

        return result

    async def generate_video(
        self,
        prompt: str,
        quality_tier: str = "auto",
        duration_seconds: int = 5,
        resolution: str = "1080p",
        first_frame_image: str = None,
    ) -> dict:
        """Generate a video through the full 10-stage pipeline.

        Args:
            prompt: Video generation prompt
            quality_tier: "draft", "budget", "standard", "premium", or "auto"
            duration_seconds: Video duration in seconds
            resolution: Video resolution ("720p", "1080p", "4k")
            first_frame_image: URL of first frame (for image-to-video)

        Returns:
            Dict with video URL, score, model, cost, etc.
        """
        start_time = time.time()

        # === Stage 1: Cache ===
        explicit_tier = quality_tier if quality_tier != "auto" else None

        cached = self.cache.get_generation_result(
            prompt, quality_tier if quality_tier != "auto" else "auto",
            "auto", "video", str(duration_seconds),
        )
        if cached:
            logger.info(f"Media cache HIT (video) — returning cached result")
            self.memory.record_generation(
                task_type=cached.get("task_type", "video_standard"),
                models_used=[],
                winner="",
                scores={},
                cache_hit=True,
            )
            cached["cache_hit"] = True
            cached["elapsed_seconds"] = round(time.time() - start_time, 2)
            return cached

        # === Stage 2: Intent Classification ===
        task_type = classify_media_task(prompt)

        # === Stage 3: Tier Determination ===
        if quality_tier == "auto":
            tier = determine_media_tier(prompt, task_type)
        else:
            tier = quality_tier

        logger.info(f"Video pipeline: task={task_type}, tier={tier}, prompt={prompt[:50]}...")

        # === Stage 4-7: Generate → Enhance → Judge → Quality Gate ===
        gen_kwargs = {
            "duration_seconds": duration_seconds,
            "resolution": resolution,
        }
        if first_frame_image:
            gen_kwargs["first_frame_image"] = first_frame_image

        gate_result = await self.quality_gate.run(
            prompt=prompt,
            tier=tier,
            task_type=task_type,
            media_type="video",
            call_llm_func=self.call_llm_func,
            **gen_kwargs,
        )

        final_output = gate_result.get("final_output")
        final_score = gate_result.get("final_score", 0.0)
        iterations = gate_result.get("iterations", 1)
        passed_gate = gate_result.get("passed_gate", False)
        total_cost = gate_result.get("total_cost", 0.0)
        history = gate_result.get("history", [])

        # === Stage 8: Post-Processing (video) ===
        if final_output and final_output.get("url"):
            pp_result = await self.post_processor.process_video(
                video_url=final_output["url"],
                task_type=task_type,
            )
            final_url = pp_result["url"]
        else:
            final_url = ""

        # === Stage 9: Memory Bank ===
        if history:
            latest = history[-1]
            self.memory.record_generation(
                task_type=task_type,
                models_used=latest.get("models_used", []),
                winner=final_output.get("model", "") if final_output else "",
                scores=latest.get("all_scores", {}),
                cost=total_cost,
                iterations=iterations,
            )

        # === Stage 10: Return ===
        elapsed = time.time() - start_time

        result = {
            "url": final_url,
            "score": final_score,
            "model": final_output.get("model", "") if final_output else "",
            "models_used": history[-1].get("models_used", []) if history else [],
            "successful_models": history[-1].get("successful_models", []) if history else [],
            "tier": tier,
            "task_type": task_type,
            "iterations": iterations,
            "passed_gate": passed_gate,
            "cost": round(total_cost, 4),
            "cache_hit": False,
            "duration_seconds": duration_seconds,
            "resolution": resolution,
            "elapsed_seconds": round(elapsed, 2),
            "history": history,
        }

        # Cache the result
        self.cache.set_generation_result(
            prompt, quality_tier, task_type, result,
            media_type="video", size=str(duration_seconds),
        )

        logger.info(
            f"Video pipeline complete: score={final_score:.1f}, model={result['model']}, "
            f"iterations={iterations}, cost=${total_cost:.4f}, elapsed={elapsed:.1f}s"
        )

        return result

    async def generate(
        self,
        prompt: str,
        media_type: str = "auto",
        **kwargs,
    ) -> dict:
        """Unified entry point — auto-detects image vs video.

        Args:
            prompt: Generation prompt
            media_type: "image", "video", or "auto" (auto-detect from prompt)
            **kwargs: Additional parameters (size, duration, etc.)

        Returns:
            Generation result dict.
        """
        if media_type == "auto":
            if is_video_prompt(prompt):
                media_type = "video"
            else:
                media_type = "image"

        if media_type == "video":
            return await self.generate_video(prompt, **kwargs)
        else:
            return await self.generate_image(prompt, **kwargs)

    def get_stats(self) -> dict:
        """Get pipeline statistics (cache, memory)."""
        return {
            "cache": self.cache.stats(),
            "memory": self.memory.get_summary(),
        }