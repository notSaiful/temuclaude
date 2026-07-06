"""
Temuclaude Media Quality Gate

USVA-adapted verification + Reflexion memory for media generation.

If the best output's consensus score is below a task-specific threshold:
  1. Generate a critique (LLM identifies what's wrong)
  2. Enhance the prompt with critique feedback
  3. Regenerate with the enhanced prompt
  4. Re-judge the new outputs
  5. Repeat up to MAX_REFINE_ITERATIONS (3)

Adapted from self_qa.py's self_qa_gate + reflexion pattern.
"""

import asyncio
import logging
from typing import Optional

from .models import QUALITY_THRESHOLDS, MAX_REFINE_ITERATIONS
from .judge import MediaJudge
from .generator import MediaGenerator

logger = logging.getLogger(__name__)


def build_critique_prompt(
    prompt: str,
    task_type: str,
    best_output: dict,
    threshold: float,
    media_type: str = "image",
) -> list:
    """Build the LLM prompt to generate a critique of the best output.

    The LLM sees the original prompt, the output's scores, and identifies
    what's wrong — this becomes the feedback for the next iteration.
    """
    judge_scores = best_output.get("judge_scores", [])
    score_summary = "\n".join(
        f"  - {js.get('judge', 'unknown')}: overall={js.get('overall', 0)}, "
        f"dimensions={{{', '.join(f'{k}: {v}' for k, v in js.items() if k not in ('judge', 'weight', 'overall', 'error'))}}}"
        for js in judge_scores
    )

    media_word = "video" if media_type == "video" else "image"

    system_prompt = f"""You are an expert {media_word} quality critic. Given a generated {media_word}'s scores, you identify specific, actionable improvements.

Focus on the WEAKEST dimensions. Be specific about what to fix.
Return ONLY a brief, actionable improvement instruction (1-2 sentences)."""

    user_prompt = f"""Original prompt: {prompt}
Task type: {task_type}
Quality threshold: {threshold}/10
Actual best score: {best_output.get('consensus_score', 0)}/10

Judge scores:
{score_summary}

What specific improvement should be made to the prompt to increase the score above {threshold}/10?

Improvement instruction:"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_refined_prompt(original_prompt: str, critique: str, task_type: str) -> str:
    """Build a refined prompt that incorporates the critique feedback.

    This is the Reflexion pattern: the LLM's critique is fed back into the
    prompt to improve the next generation.
    """
    return f"""{original_prompt}

Quality improvement notes: {critique}

Please generate with these improvements in mind."""


class MediaQualityGate:
    """Quality gate with Reflexion loop for media generation.

    Flow:
      1. Judge the best output
      2. If score ≥ threshold → return (quality is good enough)
      3. If score < threshold:
         a. Generate critique (LLM identifies what's wrong)
         b. Refine prompt with critique
         c. Regenerate
         d. Re-judge
         e. Repeat up to MAX_REFINE_ITERATIONS
    """

    def __init__(
        self,
        generator: MediaGenerator = None,
        judge: MediaJudge = None,
        call_llm_func=None,
    ):
        self.generator = generator or MediaGenerator(call_llm_func=call_llm_func)
        self.judge = judge or MediaJudge(call_llm_func=call_llm_func)
        self.call_llm_func = call_llm_func

    def get_threshold(self, task_type: str) -> float:
        """Get the quality threshold for a task type.

        If no specific threshold, use the default (7.5).
        """
        return QUALITY_THRESHOLDS.get(task_type, 7.5)

    async def generate_critique(
        self,
        prompt: str,
        task_type: str,
        best_output: dict,
        threshold: float,
        media_type: str = "image",
    ) -> str:
        """Generate a critique of the best output using LLM.

        This is the Reflexion step — the LLM identifies what's wrong
        and suggests improvements.
        """
        if not self.call_llm_func:
            # Fallback: generic critique based on weakest dimension
            judge_scores = best_output.get("judge_scores", [])
            if not judge_scores:
                return "Improve overall quality and prompt adherence."

            # Find weakest dimension
            all_dims = {}
            for js in judge_scores:
                for key, val in js.items():
                    if key not in ("judge", "weight", "overall", "error") and isinstance(val, (int, float)):
                        if key not in all_dims:
                            all_dims[key] = []
                        all_dims[key].append(val)

            weakest = min(all_dims.items(), key=lambda x: sum(x[1]) / len(x[1]))
            return f"Improve {weakest[0]} — current average is {sum(weakest[1])/len(weakest[1]):.1f}/10."

        try:
            messages = build_critique_prompt(prompt, task_type, best_output, threshold, media_type)

            critique = await self.call_llm_func(
                "z-ai/glm-5.2",  # cheapest model for critique
                messages,
                max_tokens=200,
                temperature=0.3,
            )

            return critique.strip()

        except Exception as e:
            logger.warning(f"Critique generation failed: {e}")
            return "Improve overall quality and prompt adherence."

    async def evaluate_and_refine(
        self,
        prompt: str,
        tier: str,
        task_type: str,
        generation_result: dict,
        media_type: str = "image",
        iteration: int = 0,
        max_iterations: int = None,
        **gen_kwargs,
    ) -> dict:
        """Evaluate the generation result and refine if below threshold.

        This is the main quality gate loop. It:
        1. Judges all outputs from the generation result
        2. Checks if the best score meets the threshold
        3. If not, generates critique, refines prompt, regenerates
        4. Returns the final result with full history

        Args:
            prompt: Original user prompt
            tier: Quality tier used
            task_type: Classified task type
            generation_result: Result from MediaGenerator.generate_images/videos
            media_type: "image" or "video"
            iteration: Current iteration (0 = first pass)
            max_iterations: Max refine iterations (default from models.py)
            **gen_kwargs: Additional generation kwargs (size, duration, etc.)

        Returns:
            Dict with:
              - 'final_output': The best output (dict with model, url, score)
              - 'final_score': Consensus score of the final output
              - 'iterations': Number of iterations used
              - 'passed_gate': Whether the final score met the threshold
              - 'history': List of all iterations' results
              - 'total_cost': Total estimated cost across all iterations
        """
        if max_iterations is None:
            max_iterations = MAX_REFINE_ITERATIONS

        threshold = self.get_threshold(task_type)
        outputs = generation_result.get("outputs", [])

        # Judge all outputs
        judge_result = await self.judge.judge_all(prompt, task_type, outputs, media_type)
        best_score = judge_result.get("best_score", 0.0)
        winner = judge_result.get("winner")

        # Record this iteration
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

        # Check if quality is good enough
        if best_score >= threshold or iteration >= max_iterations:
            passed = best_score >= threshold
            return {
                "final_output": winner,
                "final_score": best_score,
                "iterations": iteration + 1,
                "passed_gate": passed,
                "threshold": threshold,
                "history": [iteration_record],
                "total_cost": generation_result.get("estimated_cost", 0.0),
            }

        # Quality is below threshold — generate critique and refine
        logger.info(
            f"Quality gate: score {best_score:.1f} < threshold {threshold:.1f} "
            f"for task {task_type}. Generating critique (iteration {iteration + 1}/{max_iterations})..."
        )

        critique = await self.generate_critique(
            prompt, task_type, winner or {}, threshold, media_type
        )

        refined_prompt = build_refined_prompt(prompt, critique, task_type)

        # Regenerate with the refined prompt
        if media_type == "video":
            new_generation = await self.generator.generate_videos(
                refined_prompt, tier, task_type, **gen_kwargs
            )
        else:
            new_generation = await self.generator.generate_images(
                refined_prompt, tier, task_type, **gen_kwargs
            )

        # Recursive call with the new generation
        next_result = await self.evaluate_and_refine(
            prompt,  # keep the ORIGINAL prompt for judging (not the refined one)
            tier,
            task_type,
            new_generation,
            media_type,
            iteration + 1,
            max_iterations,
            **gen_kwargs,
        )

        # Merge history and costs
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
        task_type: str = "general_image",
        media_type: str = "image",
        call_llm_func=None,
        **gen_kwargs,
    ) -> dict:
        """Full quality gate pipeline: generate → judge → refine if needed.

        This is the main entry point. It:
        1. Generates with best-of-N models
        2. Judges all outputs
        3. If below threshold, refines and regenerates (up to 3 times)
        4. Returns the best output

        Returns:
            Dict with final output, score, iterations, cost, and history.
        """
        # Step 1: Generate
        if media_type == "video":
            generation = await self.generator.generate_videos(
                prompt, tier, task_type, **gen_kwargs
            )
        else:
            generation = await self.generator.generate_images(
                prompt, tier, task_type, **gen_kwargs
            )

        # Step 2: Evaluate and refine
        result = await self.evaluate_and_refine(
            prompt, tier, task_type, generation, media_type, **gen_kwargs
        )

        return result