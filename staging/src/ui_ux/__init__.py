"""
Temuclaude UI/UX Generation Module — Loop Engineering System

Architecture: SPEC -> GENERATE -> RENDER -> VALIDATE -> CRITIQUE -> REFINE (loop)

Three-layer stack (MindStudio framework):
1. Intent Engineering — success criteria, user context, trade-offs
2. Context Engineering — just-in-time retrieval, design tokens, compaction
3. Prompt Engineering — format, examples, constraints (smallest layer)

Components:
- intent_classifier: Routes vague prompts to structured spec templates
- spec_generator: Produces detailed markdown spec from intent
- model_router: Picks right model (Fable 5 for gen, GPT-5.5 for precision, Kimi for volume)
- memory_bank: NOTES.md + pattern persistence across sessions
- visual_validator: Playwright + screenshot diff + axe-core + Lighthouse CI
- quality_gates: TypeScript strict, a11y AA, performance >= 90, visual regression < 0.1%
- iteration_controller: Manages loop, compiles feedback, decides next action
- loop_engine: Main entry point — orchestrates the full loop
"""

from .intent_classifier import IntentClassifier, Intent
from .spec_generator import SpecGenerator, Spec
from .model_router import ModelRouter, ModelChoice
from .memory_bank import MemoryBank, Pattern
from .quality_gates import QualityGates, QualityReport, GateResult
from .visual_validator import VisualValidator, VisualValidationResult
from .iteration_controller import IterationController, LoopSummary, IterationResult
from .subagent_orchestrator import SubagentOrchestrator, Subtask, SubtaskResult
from .screenshot_feedback import ScreenshotFeedback, ScreenshotResult
from .adversarial_verifier import AdversarialVerifier, BugReport, AdversarialResult
from .persistent_notes import PersistentNotes, IterationNote
from .design_enforcer import DesignEnforcer, DesignRules
from .loop_engine import LoopEngine, GenerationResult

__all__ = [
    "IntentClassifier", "Intent",
    "SpecGenerator", "Spec",
    "ModelRouter", "ModelChoice",
    "MemoryBank", "Pattern",
    "QualityGates", "QualityReport", "GateResult",
    "VisualValidator", "VisualValidationResult",
    "IterationController", "LoopSummary", "IterationResult",
    "SubagentOrchestrator", "Subtask", "SubtaskResult",
    "ScreenshotFeedback", "ScreenshotResult",
    "AdversarialVerifier", "BugReport", "AdversarialResult",
    "PersistentNotes", "IterationNote",
    "DesignEnforcer", "DesignRules",
    "LoopEngine", "GenerationResult",
]