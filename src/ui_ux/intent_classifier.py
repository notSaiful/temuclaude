"""
Intent Classifier — Routes vague prompts to structured spec templates.

Based on v0 system prompt approach: keyword-based intent detection with
confidence scoring. Maps to spec_template + stack + model.

Research finding: "Single-prompt Minecraft" works because prompts are
hyper-specific specs, not vague wishes. This classifier bridges that gap.
"""
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Intent:
    """Classified intent for UI/UX generation."""
    category: str           # game_3d, physics_demo, dashboard_saas, landing_page, mobile_app
    confidence: float        # 0.0 - 1.0
    keywords_matched: list   # Which keywords triggered this
    spec_template: str       # Which template file to use
    stack: str               # Technology stack
    model: str               # Which model to use
    is_vague: bool           # True if prompt is too vague (needs clarification)
    quality_bar: str         # Explicit quality target
    raw_prompt: str          # Original user prompt


# Intent detection patterns — from research report Section 5.4
INTENT_PATTERNS = {
    "game_3d": {
        "keywords": ["minecraft", "voxel", "3d game", "first person", "three.js",
                     "webgl", "physics", "game", "playable", "fps", "rpg",
                     "platformer", "open world", "sandbox"],
        "spec_template": "game_3d_spec.md",
        "stack": "three.js + cannon/es + vite",
        "model": "glm-5.2",  # Best available via OpenRouter
        "quality_bar": "Playable at 60fps, impressive enough to share publicly",
    },
    "physics_demo": {
        "keywords": ["cloth", "fluid", "particle", "verlet", "spring",
                     "simulation", "webgl", "shader", "canvas", "physics lab",
                     "smoke", "fire", "water", "wave", "gravity"],
        "spec_template": "physics_demo_spec.md",
        "stack": "raw webgl2, single html",
        "model": "glm-5.2",
        "quality_bar": "Smooth 60fps simulation, interactive controls, visually impressive",
    },
    "dashboard_saas": {
        "keywords": ["dashboard", "admin", "analytics", "saas", "b2b", "charts",
                     "tables", "crm", "erp", "metrics", "kpi", "reports",
                     "data visualization", "admin panel"],
        "spec_template": "dashboard_spec.md",
        "stack": "nextjs + shadcn + recharts + supabase",
        "model": "deepseek-v4-pro",
        "quality_bar": "WCAG AA, responsive, loading/error/empty states, production-grade",
    },
    "landing_page": {
        "keywords": ["landing", "hero", "pricing", "testimonial", "marketing",
                     "conversion", "cta", "signup", "waitlist", "launch page",
                     "product page", "startup website"],
        "spec_template": "landing_spec.md",
        "stack": "nextjs + tailwind + framer-motion",
        "model": "minimax-m3",  # Creative/generation specialist
        "quality_bar": "Mobile-first, fast load, high conversion design, SEO-optimized",
    },
    "mobile_app": {
        "keywords": ["mobile", "ios", "android", "react native", "expo",
                     "pwa", "app store", "play store", "mobile-first app",
                     "swift", "kotlin"],
        "spec_template": "mobile_spec.md",
        "stack": "expo + nativewind + expo-router",
        "model": "deepseek-v4-pro",
        "quality_bar": "Native feel, smooth gestures, offline-capable, app-store ready",
    },
}

# Vagueness indicators — prompts that need clarification
VAGUE_INDICATORS = [
    "something cool", "a nice", "make a good", "build an app",
    "a website for", "a tool that", "something like",
]


class IntentClassifier:
    """Classifies user prompts into UI/UX generation intents."""

    def __init__(self):
        self.patterns = INTENT_PATTERNS

    def classify(self, prompt: str) -> Intent:
        """Classify a prompt into an intent category.

        Returns Intent with category, confidence, matched keywords,
        spec template, stack, model, and vagueness flag.
        """
        prompt_lower = prompt.lower()
        best_category = None
        best_score = 0
        best_keywords = []

        # Score each category by keyword matches
        for category, config in self.patterns.items():
            matched = [kw for kw in config["keywords"] if kw in prompt_lower]
            score = len(matched)

            # Weighted scoring: exact matches score higher
            for kw in matched:
                # Phrase matches (multi-word) get higher weight
                if " " in kw:
                    score += 0.5

            if score > best_score:
                best_score = score
                best_category = category
                best_keywords = matched

        # If no matches, default to landing_page (most general web UI)
        if best_category is None or best_score == 0:
            best_category = "landing_page"
            best_keywords = []
            confidence = 0.3  # Low confidence — needs clarification
        else:
            # Confidence based on score (more matches = higher confidence)
            confidence = min(1.0, best_score / 5.0)
            if confidence < 0.4:
                confidence = 0.4  # Minimum confidence if we matched something

        # Check vagueness
        is_vague = any(vague in prompt_lower for vague in VAGUE_INDICATORS)
        # Also vague if very short and no keywords matched
        if len(prompt.split()) < 5 and best_score <= 1:
            is_vague = True

        config = self.patterns[best_category]

        return Intent(
            category=best_category,
            confidence=round(confidence, 2),
            keywords_matched=best_keywords,
            spec_template=config["spec_template"],
            stack=config["stack"],
            model=config["model"],
            is_vague=is_vague,
            quality_bar=config["quality_bar"],
            raw_prompt=prompt,
        )

    def get_all_categories(self) -> list:
        """Return all supported intent categories."""
        return list(self.patterns.keys())

    def needs_clarification(self, intent: Intent) -> Optional[str]:
        """If intent is vague, return a clarification question.

        Returns None if no clarification needed.
        """
        if not intent.is_vague:
            return None

        if intent.confidence < 0.4:
            return (
                f"I can help you build a {intent.category.replace('_', ' ')}. "
                f"To get the best result, please tell me:\n"
                f"1. What specific features do you want?\n"
                f"2. What's the target audience/use case?\n"
                f"3. Any design preferences (colors, style, references)?"
            )

        return None