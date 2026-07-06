"""
Spec Generator — Produces detailed markdown spec from intent.

Based on v0 / Bolt / Lovable spec-driven generation pattern:
1. User gives high-level prompt
2. Model generates detailed SPEC (markdown) — UI, components, data models, flows
3. Human reviews/edits spec (critical checkpoint)
4. Model implements from spec — deterministic, reviewable
5. Iterate on spec, not code

Research finding: Viral demos work because prompts are hyper-specific specs:
- Exact tech stack (raw WebGL2, single HTML, no deps)
- Named algorithms (Verlet, mass-spring physics)
- Explicit quality bar ("impressive enough to share publicly")
- Full visual/layout/control specifications
"""
import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Spec:
    """Generated specification for UI/UX generation."""
    markdown: str            # Full spec as markdown
    template_used: str       # Which template was used
    fields_filled: dict      # Template fields that were filled
    estimated_complexity: str  # simple, medium, complex
    target_tokens: int       # Estimated tokens for generation


class SpecGenerator:
    """Generates detailed specs from classified intents."""

    def __init__(self, templates_dir: str = None):
        if templates_dir is None:
            templates_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "config", "spec_templates"
            )
        self.templates_dir = templates_dir

    def _load_template(self, template_name: str) -> str:
        """Load a spec template by name."""
        path = os.path.join(self.templates_dir, template_name)
        if not os.path.isfile(path):
            # Fall back to landing_spec if template missing
            path = os.path.join(self.templates_dir, "landing_spec.md")
        with open(path, "r") as f:
            return f.read()

    def _extract_project_name(self, prompt: str) -> str:
        """Extract a project name from the prompt."""
        # Try to find "called X" or "named X"
        import re
        match = re.search(r'(?:called|named)\s+["\']?([A-Za-z0-9\s]+?)["\']?(?:[.,]|$)', prompt, re.I)
        if match:
            return match.group(1).strip().title()

        # Try first significant words
        words = [w for w in prompt.split() if len(w) > 3 and w.lower() not in
                 {"create", "build", "make", "generate", "design", "develop", "please", "a", "an", "the"}]
        if words:
            return " ".join(words[:2]).title()
        return "Untitled Project"

    def _extract_colors(self, prompt: str) -> str:
        """Extract color preferences from prompt."""
        prompt_lower = prompt.lower()
        color_map = {
            "dark": "#0a0a0a, #1a1a2e, #16213e",
            "light": "#ffffff, #f8f9fa, #e9ecef",
            "blue": "#0066ff, #0033cc, #e6f0ff",
            "green": "#00cc66, #009944, #e6f9ee",
            "purple": "#7b2ff7, #6633cc, #f0e6ff",
            "red": "#ff3344, #cc1122, #ffe6e9",
            "cinematic": "#0a0a0a, #1a1a2e, #e94560",
            "glassmorphism": "#1a1a2e, #16213e, rgba(255,255,255,0.1)",
            "neon": "#0a0a0a, #ff00ff, #00ffff",
            "pastel": "#fce4ec, #e8f5e9, #fff3e0",
        }
        for key, colors in color_map.items():
            if key in prompt_lower:
                return colors
        return ""  # Empty = template default

    def _estimate_complexity(self, prompt: str, intent_category: str) -> str:
        """Estimate complexity of the generation task."""
        word_count = len(prompt.split())
        # Games and physics demos are always complex
        if intent_category in ("game_3d", "physics_demo"):
            return "complex"
        if word_count > 50:
            return "complex"
        if word_count > 20:
            return "medium"
        return "simple"

    def _estimate_tokens(self, complexity: str, intent_category: str) -> int:
        """Estimate tokens needed for generation."""
        base = {
            "simple": 4000,
            "medium": 8000,
            "complex": 16000,
        }
        # Games and physics need more tokens
        if intent_category in ("game_3d", "physics_demo"):
            return base.get(complexity, 8000) * 2
        return base.get(complexity, 8000)

    def generate(self, intent, user_context: dict = None) -> Spec:
        """Generate a detailed spec from an intent.

        Args:
            intent: Classified Intent from IntentClassifier
            user_context: Optional dict with keys like:
                - colors: Preferred color scheme
                - fonts: Font preferences
                - reference_url: URL of design reference
                - target_audience: Who this is for
                - brand: Brand name/guidelines

        Returns:
            Spec object with markdown and metadata
        """
        if user_context is None:
            user_context = {}

        template = self._load_template(intent.spec_template)
        project_name = self._extract_project_name(intent.raw_prompt)
        colors = user_context.get("colors") or self._extract_colors(intent.raw_prompt)
        complexity = self._estimate_complexity(intent.raw_prompt, intent.category)
        target_tokens = self._estimate_tokens(complexity, intent.category)

        # Fill template placeholders
        fields_filled = {
            "PROJECT_NAME": project_name,
            "RAW_PROMPT": intent.raw_prompt,
            "QUALITY_BAR": intent.quality_bar,
            "COLORS": colors or "[Specify 3-5 colors with roles]",
            "FONTS": user_context.get("fonts", "Inter (sans) + JetBrains Mono (mono)"),
            "TARGET_AUDIENCE": user_context.get("target_audience", "General users"),
            "BRAND": user_context.get("brand", project_name),
            "REFERENCE_URL": user_context.get("reference_url", ""),
            "KEYWORDS_MATCHED": ", ".join(intent.keywords_matched) if intent.keywords_matched else "auto-detected",
        }

        # Replace placeholders in template
        markdown = template
        for key, value in fields_filled.items():
            markdown = markdown.replace(f"{{{{ {key} }}}}", str(value))
            markdown = markdown.replace(f"{{{{{key}}}}}", str(value))

        return Spec(
            markdown=markdown,
            template_used=intent.spec_template,
            fields_filled=fields_filled,
            estimated_complexity=complexity,
            target_tokens=target_tokens,
        )

    def generate_from_prompt(self, prompt: str, intent, user_context: dict = None) -> Spec:
        """Convenience: generate spec directly from prompt + intent."""
        return self.generate(intent, user_context)