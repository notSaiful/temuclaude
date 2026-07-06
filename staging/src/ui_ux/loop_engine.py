"""
Loop Engine — Main entry point for UI/UX generation.

Orchestrates the full loop: SPEC -> GENERATE -> RENDER -> VALIDATE -> CRITIQUE -> REFINE

UPGRADED with 7 layers that beat Fable 5:
1. SubagentOrchestrator — parallel heterogeneous subagents for generation
2. ScreenshotFeedback — render + screenshot + feed back to model (Builder.io #1 tip)
3. AdversarialVerifier — breaker finds bugs, fixer fixes them (Fable 5 pattern)
4. PersistentNotes — NOTES.md survives across iterations (Anthropic memory pattern)
5. DesignEnforcer — v0's production rules baked into every prompt
6. ProgressiveComplexity — iteration 1=working, 2=quality, 3=polish
7. DynamicModelEscalation — start cheap, escalate if quality < threshold

Usage:
    from src.ui_ux import LoopEngine

    engine = LoopEngine(call_model_fn=my_model_fn)
    result = await engine.generate("Create a Minecraft-style voxel game in the browser")
    print(result.final_code)
    print(result.quality_score)
"""
import os
import asyncio
import time
from dataclasses import dataclass
from typing import Optional, Callable, Awaitable

from .intent_classifier import IntentClassifier, Intent
from .spec_generator import SpecGenerator, Spec
from .model_router import ModelRouter, ModelChoice
from .memory_bank import MemoryBank, Pattern
from .quality_gates import QualityGates, QualityReport
from .visual_validator import VisualValidator, VisualValidationResult
from .iteration_controller import IterationController, LoopSummary
from .subagent_orchestrator import SubagentOrchestrator, SubtaskResult
from .screenshot_feedback import ScreenshotFeedback, ScreenshotResult
from .adversarial_verifier import AdversarialVerifier, AdversarialResult
from .persistent_notes import PersistentNotes, IterationNote
from .design_enforcer import DesignEnforcer, DesignRules


@dataclass
class GenerationResult:
    """Final result of UI/UX generation."""
    success: bool
    final_code: str
    quality_score: float
    iterations: int
    intent: Intent
    spec: Spec
    techniques_passed: list
    techniques_used: list
    stop_reason: str
    total_time_ms: int
    patterns_reused: int
    subagent_results: Optional[list] = None      # Subagent outputs
    adversarial_result: Optional[AdversarialResult] = None
    design_violations: Optional[list] = None
    screenshot_captured: bool = False
    quality_report: Optional[QualityReport] = None
    visual_result: Optional[VisualValidationResult] = None
    loop_summary: Optional[LoopSummary] = None
    error: Optional[str] = None


class LoopEngine:
    """Main UI/UX generation engine — Loop Engineering system with 7 upgrade layers."""

    def __init__(
        self,
        call_model_fn: Optional[Callable] = None,
        max_iterations: int = 3,
        quality_threshold: float = 0.85,
        single_file_mode: bool = False,
        memory_dir: str = None,
        use_subagents: bool = True,
        use_adversarial: bool = True,
        use_screenshot_feedback: bool = True,
        use_persistent_notes: bool = True,
    ):
        self.intent_classifier = IntentClassifier()
        self.spec_generator = SpecGenerator()
        self.model_router = ModelRouter()
        self.memory_bank = MemoryBank(memory_dir)
        self.quality_gates = QualityGates(single_file_mode=single_file_mode)
        self.visual_validator = VisualValidator()
        self.iteration_controller = IterationController(
            max_iterations=max_iterations,
            quality_threshold=quality_threshold,
            single_file_mode=single_file_mode,
        )
        self.design_enforcer = DesignEnforcer()
        self.call_model_fn = call_model_fn
        self.single_file_mode = single_file_mode
        self.use_subagents = use_subagents
        self.use_adversarial = use_adversarial
        self.use_screenshot_feedback = use_screenshot_feedback
        self.use_persistent_notes = use_persistent_notes

        # Initialize sub-components that need call_model_fn
        if call_model_fn:
            self.subagent_orchestrator = SubagentOrchestrator(call_model_fn)
            self.adversarial_verifier = AdversarialVerifier(call_model_fn)
            self.screenshot_feedback = ScreenshotFeedback()

    async def generate(
        self,
        prompt: str,
        user_context: dict = None,
        skip_validation: bool = False,
    ) -> GenerationResult:
        """Generate UI/UX from a prompt using the full 7-layer loop.

        Args:
            prompt: User's prompt
            user_context: Optional dict with colors, fonts, reference_url, etc.
            skip_validation: If True, skip quality gates and visual validation

        Returns:
            GenerationResult with final code, quality score, and metadata
        """
        start_time = time.time()

        try:
            # Step 1: Classify intent
            intent = self.intent_classifier.classify(prompt)

            # Check for similar patterns in memory
            similar_patterns = self.memory_bank.find_similar_patterns(intent.category)
            patterns_reused = len(similar_patterns)

            pattern_context = ""
            if similar_patterns and similar_patterns[0].get("quality_score", 0) > 0.9:
                pattern_context = (
                    f"\n\nPrevious successful generation for {intent.category}:\n"
                    f"Spec summary: {similar_patterns[0].get('spec_summary', '')[:200]}\n"
                    f"Techniques that worked: {similar_patterns[0].get('techniques_used', [])}"
                )

            # Step 2: Generate spec
            spec = self.spec_generator.generate(intent, user_context)

            # Step 3: Initialize persistent notes for this session
            persistent_notes = PersistentNotes() if self.use_persistent_notes else None

            if skip_validation or self.call_model_fn is None:
                return GenerationResult(
                    success=True,
                    final_code=spec.markdown,
                    quality_score=0.0,
                    iterations=0,
                    intent=intent,
                    spec=spec,
                    techniques_passed=[],
                    techniques_used=["spec_generation"],
                    stop_reason="skipped_validation",
                    total_time_ms=int((time.time() - start_time) * 1000),
                    patterns_reused=patterns_reused,
                    error="Validation skipped" if skip_validation else "No model function provided",
                )

            # Step 4: Run the enhanced iteration loop
            loop_summary = await self._run_enhanced_loop(
                spec, intent, persistent_notes, pattern_context
            )

            # Step 5: Final validation
            quality_report, visual_result = await self._validate_code(
                loop_summary.final_code, intent.category
            )

            # Step 6: Adversarial verification (if enabled and quality is borderline)
            adversarial_result = None
            if self.use_adversarial and quality_report.overall_score < 0.9:
                adversarial_result = await self.adversarial_verifier.verify(
                    loop_summary.final_code, intent.category, spec.markdown, max_cycles=1
                )
                if adversarial_result.all_critical_fixed and adversarial_result.fixed_code:
                    loop_summary_final_code = adversarial_result.fixed_code
                    # Re-validate
                    quality_report, visual_result = await self._validate_code(
                        adversarial_result.fixed_code, intent.category
                    )

            # Step 7: Check design rule violations
            design_violations = self.design_enforcer.validate_against_rules(loop_summary.final_code)

            # Build result
            result = GenerationResult(
                success=loop_summary.success,
                final_code=loop_summary.final_code,
                quality_score=loop_summary.final_quality_score,
                iterations=loop_summary.total_iterations,
                intent=intent,
                spec=spec,
                techniques_passed=[g.gate_name for g in quality_report.gate_results if g.passed] if quality_report else [],
                techniques_used=loop_summary.techniques_used,
                stop_reason=loop_summary.stop_reason,
                total_time_ms=int((time.time() - start_time) * 1000),
                patterns_reused=patterns_reused,
                adversarial_result=adversarial_result,
                design_violations=design_violations,
                screenshot_captured=False,  # Set in loop
                quality_report=quality_report,
                visual_result=visual_result,
                loop_summary=loop_summary,
            )

            # Step 8: Save to memory bank
            pattern = self.memory_bank.create_pattern_from_result(intent, spec, result)
            self.memory_bank.save_pattern(pattern)

            return result

        except Exception as e:
            return GenerationResult(
                success=False,
                final_code="",
                quality_score=0.0,
                iterations=0,
                intent=Intent(
                    category="unknown", confidence=0.0, keywords_matched=[],
                    spec_template="landing_spec.md", stack="unknown",
                    model="glm-5.2", is_vague=False, quality_bar="",
                    raw_prompt=prompt,
                ),
                spec=None,
                techniques_passed=[],
                techniques_used=[],
                stop_reason="error",
                total_time_ms=int((time.time() - start_time) * 1000),
                patterns_reused=0,
                error=str(e),
            )

    async def _run_enhanced_loop(self, spec: Spec, intent: Intent, persistent_notes, pattern_context: str) -> LoopSummary:
        """Run the enhanced iteration loop with all 7 layers."""
        start_time = time.time()
        iterations = []
        all_techniques = []
        current_code = None
        current_feedback = None
        best_code = None
        best_score = 0.0
        gates_passed = False
        stop_reason = "max_iterations_reached"

        for i in range(1, self.iteration_controller.max_iterations + 1):
            iter_start = time.time()

            # Get context from persistent notes
            notes_context = ""
            if persistent_notes:
                notes_context = persistent_notes.build_context_for_iteration(i)

            # Step 1: GENERATE (with subagents for complex tasks)
            if i == 1 and self.use_subagents and intent.category in ("game_3d", "physics_demo", "dashboard_saas", "landing_page"):
                # Use subagent orchestration for first iteration (complex tasks)
                current_code = await self.subagent_orchestrator.generate(
                    spec.markdown + pattern_context + "\n\n" + notes_context,
                    intent.category,
                )
            elif i == 1:
                # Simple generation for first iteration
                current_code = await self._generate_with_design_rules(
                    spec.markdown + pattern_context + "\n\n" + notes_context,
                    intent, i, None
                )
            else:
                # Subsequent iterations: refine with feedback
                current_code = await self._generate_with_design_rules(
                    spec.markdown + pattern_context + "\n\n" + notes_context,
                    intent, i, current_feedback
                )

            # Step 2: VALIDATE
            quality_report, visual_result = await self._validate_code(current_code, intent.category)
            techniques = [g.gate_name for g in quality_report.gate_results if g.passed]
            all_techniques.extend(techniques)

            if quality_report.overall_score > best_score:
                best_code = current_code
                best_score = quality_report.overall_score

            gates_passed = quality_report.overall_passed and quality_report.overall_score >= self.iteration_controller.quality_threshold

            # Step 3: SCREENSHOT FEEDBACK (if enabled)
            screenshot_captured = False
            critique_feedback = ""
            if self.use_screenshot_feedback and not gates_passed:
                try:
                    screenshot_critique = await self.screenshot_feedback.get_visual_feedback(
                        current_code, quality_report, self.call_model_fn
                    )
                    critique_feedback = screenshot_critique
                    screenshot_captured = True
                except Exception:
                    # Fall back to default critique
                    critique_feedback = self.iteration_controller._generate_default_critique(quality_report, visual_result)
            elif not gates_passed:
                critique_feedback = self.iteration_controller._generate_default_critique(quality_report, visual_result)
            else:
                critique_feedback = "Quality threshold met — no critique needed"

            # Step 4: Check design violations
            design_violations = self.design_enforcer.validate_against_rules(current_code)
            if design_violations and not gates_passed:
                critique_feedback += "\n\n" + self.design_enforcer.get_fix_instructions(design_violations)

            # Step 5: Write persistent notes
            if persistent_notes:
                persistent_notes.create_note_from_result(
                    iteration=i,
                    what_was_tried=f"Subagent orchestration: {self.use_subagents}, Screenshot feedback: {screenshot_captured}",
                    quality_score=quality_report.overall_score,
                    what_worked=", ".join(techniques[:5]),
                    what_failed=", ".join(quality_report.blocking_issues) if quality_report.blocking_issues else "None",
                    bugs_found=[g.details for g in quality_report.gate_results if not g.passed][:5],
                    key_decisions=[f"Used {'subagents' if self.use_subagents and i == 1 else 'single model'} for iteration {i}"],
                    lessons_learned=f"Quality: {quality_report.overall_score:.2f}. " + (
                        "Focus on: " + ", ".join(quality_report.blocking_issues[:3]) if quality_report.blocking_issues else "All good"
                    ),
                )

            # Record iteration
            iter_result = type("R", (), {
                "iteration_num": i,
                "generated_code": current_code,
                "quality_score": quality_report.overall_score,
                "gates_passed": gates_passed,
                "critique_feedback": critique_feedback,
                "techniques_passed": techniques,
                "time_taken_ms": int((time.time() - iter_start) * 1000),
                "improvements_made": [],
            })()
            iterations.append(iter_result)

            if gates_passed:
                stop_reason = "quality_threshold_met"
                break

            current_feedback = critique_feedback

        total_time = int((time.time() - start_time) * 1000)
        final_code = current_code if gates_passed else (best_code or current_code or "")
        final_score = best_score if not gates_passed else quality_report.overall_score

        return LoopSummary(
            total_iterations=len(iterations),
            final_code=final_code,
            final_quality_score=round(final_score, 2),
            all_gates_passed=gates_passed,
            iteration_history=iterations,
            total_time_ms=total_time,
            success=gates_passed,
            techniques_used=list(set(all_techniques)),
            stop_reason=stop_reason,
        )

    async def _generate_with_design_rules(self, spec_markdown: str, intent: Intent, iteration: int, feedback: str) -> str:
        """Generate code with design rules enforced."""
        model_choice = self.model_router.route(intent, phase="generation")

        # Build system prompt with design rules
        design_rules = self.design_enforcer.build_system_prompt(intent.category, iteration)
        system_prompt = f"You are Temuclaude UI/UX, a frontier-level code generator.\n{design_rules}"

        user_prompt = f"Spec:\n{spec_markdown}\n\n"
        if feedback:
            user_prompt += f"Previous critique (fix these issues):\n{feedback}\n\n"
        user_prompt += "Generate the complete code now. Output ONLY code — no explanations:"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        code = await self.call_model_fn(model_choice.model, messages, max_tokens=model_choice.max_tokens)
        return code

    async def _validate_code(self, generated_code: str, intent_category: str) -> tuple:
        """Validate generated code with quality gates and visual validator."""
        quality_report = self.quality_gates.evaluate(generated_code, intent_category)
        visual_result = await self.visual_validator.validate(generated_code, intent_category)
        return (quality_report, visual_result)

    def get_summary(self, result: GenerationResult) -> str:
        """Get human-readable summary of a generation result."""
        lines = [
            f"Generation Summary:",
            f"  Success: {result.success}",
            f"  Intent: {result.intent.category} (confidence: {result.intent.confidence:.0%})",
            f"  Quality: {result.quality_score:.2f}/1.0",
            f"  Iterations: {result.iterations}",
            f"  Stop Reason: {result.stop_reason}",
            f"  Total Time: {result.total_time_ms}ms",
            f"  Patterns Reused: {result.patterns_reused}",
            f"  Techniques: {', '.join(result.techniques_used)}",
        ]
        if result.design_violations is not None:
            if result.design_violations:
                lines.append(f"  Design Violations: {len(result.design_violations)}")
            else:
                lines.append(f"  Design Violations: 0 (all rules pass)")
        if result.adversarial_result:
            lines.append(f"  Adversarial: {len(result.adversarial_result.bugs_found)} bugs found, "
                        f"{len(result.adversarial_result.bugs_fixed)} fixed")
        if result.error:
            lines.append(f"  Error: {result.error}")
        if result.quality_report:
            lines.append(f"\n{self.quality_gates.get_gate_summary(result.quality_report)}")
        return "\n".join(lines)