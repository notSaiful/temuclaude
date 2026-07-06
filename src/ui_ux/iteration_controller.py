"""
Iteration Controller — Manages the generate/validate/critique/refine loop.

Research finding (Section 5.1):
SPEC -> GENERATE -> RENDER -> VALIDATE -> CRITIQUE -> REFINE (loop until quality gates pass)

The controller:
1. Starts with a spec
2. Generates code from spec
3. Validates against quality gates
4. If gates fail, critiques the output
5. Uses critique feedback to refine
6. Loops until quality threshold or max iterations
"""
from dataclasses import dataclass, field
from typing import Optional, Callable, Awaitable
import time


@dataclass
class IterationResult:
    """Result of a single iteration in the loop."""
    iteration_num: int
    generated_code: str
    quality_score: float
    gates_passed: bool
    critique_feedback: str
    techniques_passed: list
    time_taken_ms: int
    improvements_made: list  # What was fixed from previous iteration


@dataclass
class LoopSummary:
    """Final summary of the iteration loop."""
    total_iterations: int
    final_code: str
    final_quality_score: float
    all_gates_passed: bool
    iteration_history: list   # List of IterationResult
    total_time_ms: int
    success: bool             # True if quality threshold was met
    techniques_used: list     # All techniques applied across iterations
    stop_reason: str          # Why the loop stopped


class IterationController:
    """Controls the generate-validate-critique-refine loop."""

    def __init__(
        self,
        max_iterations: int = 3,
        quality_threshold: float = 0.85,
        single_file_mode: bool = False,
    ):
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        self.single_file_mode = single_file_mode

    async def run_loop(
        self,
        spec_markdown: str,
        generate_fn: Callable[..., Awaitable[str]],
        validate_fn: Callable[..., Awaitable[tuple]],
        critique_fn: Optional[Callable[..., Awaitable[str]]] = None,
        refine_fn: Optional[Callable[..., Awaitable[str]]] = None,
        intent_category: str = None,
    ) -> LoopSummary:
        """Run the full iteration loop.

        Args:
            spec_markdown: The spec to generate from
            generate_fn: Async function(spec_markdown, iteration, feedback) -> generated_code
            validate_fn: Async function(generated_code, intent_category) -> (QualityReport, VisualValidationResult)
            critique_fn: Optional async function(generated_code, quality_report) -> feedback_str
            refine_fn: Optional async function(generated_code, feedback, spec_markdown) -> refined_code
                       If None, uses generate_fn with feedback appended to spec
            intent_category: The intent category for context

        Returns:
            LoopSummary with final code and iteration history
        """
        start_time = time.time()
        iterations = []
        all_techniques = []

        current_code = None
        current_feedback = None
        best_code = None
        best_score = 0.0
        gates_passed = False
        quality_report = None  # Will be set during iteration
        stop_reason = "max_iterations_reached"

        for i in range(1, self.max_iterations + 1):
            iter_start = time.time()

            # Step 1: Generate (or refine if we have feedback)
            if i == 1:
                # First iteration — generate from spec
                current_code = await generate_fn(spec_markdown, i, None)
            else:
                # Subsequent iterations — refine with feedback
                if refine_fn:
                    current_code = await refine_fn(current_code, current_feedback, spec_markdown)
                else:
                    # Use generate_fn with feedback
                    current_code = await generate_fn(spec_markdown, i, current_feedback)

            # Step 2: Validate
            quality_report, visual_result = await validate_fn(current_code, intent_category)

            # Track techniques
            techniques = [g.gate_name for g in quality_report.gate_results if g.passed]
            all_techniques.extend(techniques)

            # Track best result
            if quality_report.overall_score > best_score:
                best_code = current_code
                best_score = quality_report.overall_score

            # Step 3: Check if quality threshold met
            gates_passed = quality_report.overall_passed and quality_report.overall_score >= self.quality_threshold

            improvements = []
            if current_feedback and i > 1:
                # Check what was fixed from previous feedback
                improvements = [fb for fb in current_feedback.split("\n") if fb.strip()][:5]

            iter_result = IterationResult(
                iteration_num=i,
                generated_code=current_code,
                quality_score=quality_report.overall_score,
                gates_passed=gates_passed,
                critique_feedback="",
                techniques_passed=techniques,
                time_taken_ms=int((time.time() - iter_start) * 1000),
                improvements_made=improvements,
            )

            # Step 4: If gates passed, we're done
            if gates_passed:
                iter_result.critique_feedback = "Quality threshold met — no critique needed"
                iterations.append(iter_result)
                stop_reason = "quality_threshold_met"
                break

            # Step 5: Critique
            if critique_fn:
                critique_feedback = await critique_fn(current_code, quality_report)
            else:
                # Generate critique from quality report
                critique_feedback = self._generate_default_critique(quality_report, visual_result)

            iter_result.critique_feedback = critique_feedback
            iterations.append(iter_result)

            # Update feedback for next iteration
            current_feedback = critique_feedback

        else:
            # Loop exhausted without meeting threshold
            stop_reason = "max_iterations_reached"

        total_time = int((time.time() - start_time) * 1000)

        # Use best code if we never met threshold
        final_code = current_code if gates_passed else (best_code or current_code or "")
        final_score = best_score if not gates_passed else (quality_report.overall_score if quality_report else best_score)

        success = gates_passed

        return LoopSummary(
            total_iterations=len(iterations),
            final_code=final_code,
            final_quality_score=round(final_score, 2),
            all_gates_passed=success,
            iteration_history=iterations,
            total_time_ms=total_time,
            success=success,
            techniques_used=list(set(all_techniques)),
            stop_reason=stop_reason,
        )

    def _generate_default_critique(self, quality_report, visual_result) -> str:
        """Generate critique feedback from quality report."""
        lines = ["ISSUES TO FIX:"]

        # Blocking issues
        for gate_name in quality_report.blocking_issues:
            gate_result = next((g for g in quality_report.gate_results if g.gate_name == gate_name), None)
            if gate_result:
                lines.append(f"- [BLOCKING] {gate_result.details}")
                if gate_result.fix_suggestion:
                    lines.append(f"  Fix: {gate_result.fix_suggestion}")

        # Warnings
        for gate_name in quality_report.warnings:
            gate_result = next((g for g in quality_report.gate_results if g.gate_name == gate_name), None)
            if gate_result:
                lines.append(f"- [WARNING] {gate_result.details}")

        # Visual validation issues
        if hasattr(visual_result, 'errors') and visual_result.errors:
            for err in visual_result.errors[:3]:
                lines.append(f"- [RENDER] {err}")

        if hasattr(visual_result, 'accessibility_violations') and visual_result.accessibility_violations > 0:
            lines.append(f"- [A11Y] {visual_result.accessibility_violations} accessibility violations")

        if hasattr(visual_result, 'performance_score') and visual_result.performance_score is not None:
            if visual_result.performance_score < 90:
                lines.append(f"- [PERF] Performance score {visual_result.performance_score:.0f} < 90")

        lines.append(f"\nOverall quality: {quality_report.overall_score:.2f}/1.0 (target: {self.quality_threshold})")
        lines.append("Fix ALL blocking issues and as many warnings as possible.")

        return "\n".join(lines)

    def get_summary_text(self, summary: LoopSummary) -> str:
        """Get human-readable summary of the loop."""
        lines = [
            f"Loop Summary:",
            f"  Iterations: {summary.total_iterations}/{self.max_iterations}",
            f"  Final Quality: {summary.final_quality_score:.2f}/1.0 (threshold: {self.quality_threshold})",
            f"  All Gates Passed: {summary.all_gates_passed}",
            f"  Success: {summary.success}",
            f"  Stop Reason: {summary.stop_reason}",
            f"  Total Time: {summary.total_time_ms}ms",
            f"  Techniques Used: {', '.join(summary.techniques_used)}",
            "",
        ]

        for iter_result in summary.iteration_history:
            status = "PASS" if iter_result.gates_passed else "FAIL"
            lines.append(f"  Iteration {iter_result.iteration_num}: [{status}] "
                        f"score={iter_result.quality_score:.2f} "
                        f"techniques={len(iter_result.techniques_passed)} "
                        f"time={iter_result.time_taken_ms}ms")

        return "\n".join(lines)