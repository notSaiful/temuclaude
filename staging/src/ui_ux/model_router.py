"""
Model Router — Routes to the right model based on intent and task.

Research finding (Section 5.3):
| Task Tier                         | Model         | Rationale                              |
|-----------------------------------|---------------|----------------------------------------|
| Spec generation / intent clarif  | Fable 5       | Best reasoning, understands builders   |
| Complex game/app implementation   | Fable 5       | ViBench #1, vision-native, one-shot    |
| Precision refactoring / bug fixes| Opus / GPT-5.5| SWE-Bench leadership                    |
| Computer-use automation (testing)| GPT-5.5       | OSWorld 78.7%, Codex integration        |
| Cost-sensitive / high-volume      | Kimi K2.6     | 80% SWE-Verified, free                 |
| Design token / component extract  | GPT-5.5       | Vision + structure understanding        |

Since we use OpenRouter with Temuclaude's 8-model pool, we map:
- Fable 5 -> claude-sonnet-5 (frontier fallback, highest quality)
- GPT-5.5 -> deepseek-v4-pro (precision coding)
- Kimi K2.6 -> kimi-k2.6 (cost-sensitive, free-ish)
- Default generation -> glm-5.2 (orchestrator, best general)
- Creative/landing -> minimax-m3 (generation specialist)
- Verification -> nemotron-3-ultra (verifier role)
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelChoice:
    """Model routing decision."""
    model: str              # Model key in Temuclaude pool
    role: str               # What role this model plays
    max_tokens: int         # Token budget
    temperature: float      # Generation temperature
    rationale: str          # Why this model was chosen


# Model routing strategy — mapped from research to Temuclaude's pool
ROUTING_STRATEGY = {
    # Generation tasks — need creativity and quality
    "game_3d": {
        "model": "claude-sonnet-5",  # Closest to Fable 5 (frontier)
        "role": "generation",
        "max_tokens": 16000,
        "temperature": 0.7,
        "rationale": "Frontier model for complex game generation (Fable 5 equivalent)",
    },
    "physics_demo": {
        "model": "claude-sonnet-5",  # Frontier for physics sims
        "role": "generation",
        "max_tokens": 12000,
        "temperature": 0.7,
        "rationale": "Frontier model for physics/WebGL demos (Fable 5 equivalent)",
    },
    "dashboard_saas": {
        "model": "deepseek-v4-pro",  # Precision coding
        "role": "implementation",
        "max_tokens": 8000,
        "temperature": 0.2,
        "rationale": "Precision coding for production dashboard (GPT-5.5 equivalent)",
    },
    "landing_page": {
        "model": "minimax-m3",  # Creative/generation
        "role": "generation",
        "max_tokens": 6000,
        "temperature": 0.8,
        "rationale": "Creative generation for marketing page (vision + creative specialist)",
    },
    "mobile_app": {
        "model": "deepseek-v4-pro",
        "role": "implementation",
        "max_tokens": 10000,
        "temperature": 0.3,
        "rationale": "Precision coding for mobile app (GPT-5.5 equivalent)",
    },
    # Special routing for loop phases
    "spec_generation": {
        "model": "glm-5.2",  # Best reasoning in pool (IQ 51)
        "role": "spec",
        "max_tokens": 2000,
        "temperature": 0.3,
        "rationale": "Best orchestrator for spec generation (high reasoning, low cost)",
    },
    "critique": {
        "model": "nemotron-3-ultra",  # Verifier
        "role": "critique",
        "max_tokens": 2000,
        "temperature": 0.1,
        "rationale": "Verifier model for critique phase",
    },
    "refine": {
        "model": "deepseek-v4-pro",  # Precision for fixes
        "role": "refine",
        "max_tokens": 8000,
        "temperature": 0.2,
        "rationale": "Precision coding for refinement (SWE-Bench leader)",
    },
}


class ModelRouter:
    """Routes intents to appropriate models."""

    def __init__(self):
        self.strategy = ROUTING_STRATEGY

    def route(self, intent, phase: str = "generation") -> ModelChoice:
        """Route an intent to a model for a specific phase.

        Args:
            intent: Classified Intent
            phase: Which phase of the loop:
                - "spec_generation" — creating the spec
                - "generation" — initial code generation
                - "critique" — reviewing the output
                - "refine" — fixing issues found in critique

        Returns:
            ModelChoice with model, role, token budget, temperature
        """
        if phase == "spec_generation":
            config = self.strategy["spec_generation"]
        elif phase == "critique":
            config = self.strategy["critique"]
        elif phase == "refine":
            config = self.strategy["refine"]
        else:
            # Generation phase — route by intent category
            config = self.strategy.get(intent.category, self.strategy["dashboard_saas"])

        return ModelChoice(
            model=config["model"],
            role=config["role"],
            max_tokens=config["max_tokens"],
            temperature=config["temperature"],
            rationale=config["rationale"],
        )

    def get_model_for_intent(self, intent_category: str) -> str:
        """Get just the model name for an intent category."""
        config = self.strategy.get(intent_category, self.strategy["dashboard_saas"])
        return config["model"]

    def get_all_strategies(self) -> dict:
        """Return all routing strategies."""
        return dict(self.strategy)