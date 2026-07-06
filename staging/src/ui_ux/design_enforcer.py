"""
Design Enforcer — Bakes v0's production rules into generation prompts.

From the v0 system prompt (46KB, reverse-engineered):
- 3-5 colors max (1 primary, 2-3 neutrals, 1-2 accents)
- 2 fonts max (1 heading, 1 body)
- Semantic design tokens (bg-background, text-foreground), no raw colors
- Mobile-first responsive
- WCAG AA accessibility
- No placeholder text, no TODOs, no lorem ipsum
- Specific component library (shadcn/ui new-york)
- Flexbox first, CSS Grid only for complex 2D
- Tailwind spacing scale (p-4, not p-[16px])
- gap classes for spacing, never mix margin/padding with gap
- NEVER use emojis as icons
- NEVER use purple/violet prominently unless asked

This module enforces these rules in every generation prompt.
"""
from dataclasses import dataclass


@dataclass
class DesignRules:
    """Production-grade design rules from v0's system prompt."""
    max_colors: int = 5
    max_fonts: int = 2
    require_semantic_tokens: bool = True
    require_responsive: bool = True
    require_accessibility: bool = True
    no_placeholders: bool = True
    no_emojis_as_icons: bool = True
    flexbox_first: bool = True
    tailwind_scale_only: bool = True
    no_purple_default: bool = True
    component_library: str = "shadcn/ui (new-york style)"
    chart_library: str = "Recharts"


class DesignEnforcer:
    """Enforces production-grade design rules in generation prompts."""

    def __init__(self, rules: DesignRules = None):
        self.rules = rules or DesignRules()

    def build_system_prompt(self, intent_category: str, iteration: int) -> str:
        """Build a system prompt with design rules enforced.

        Args:
            intent_category: game_3d, physics_demo, dashboard_saas, etc.
            iteration: Which iteration (1=working, 2=quality, 3=polish)

        Returns:
            System prompt string with all design rules
        """
        # Base rules for ALL categories
        rules_text = f"""## Design System Rules (MANDATORY — follow ALL)

### Color System
- Use exactly {self.rules.max_colors} colors total: 1 primary, 2-3 neutrals, 1-2 accents
- NEVER exceed {self.rules.max_colors} colors without explicit permission
- NEVER use purple or violet prominently, unless explicitly asked
- If you override a component's background color, you MUST override its text color for contrast
- Use semantic design tokens: bg-background, text-foreground, bg-primary, text-primary-foreground
- DO NOT use direct colors like bg-white, text-black, bg-blue-500 — use tokens

### Typography
- Maximum {self.rules.max_fonts} font families total
- One font for headings, one for body text
- Use line-height between 1.4-1.6 for body text (leading-relaxed or leading-6)
- NEVER use decorative fonts for body text or fonts smaller than 14px

### Layout
- Design mobile-first, then enhance for larger screens
- Use Flexbox for most layouts: flex items-center justify-between
- Use CSS Grid only for complex 2D layouts: grid grid-cols-3 gap-4
- NEVER use floats or absolute positioning unless absolutely necessary
- Use Tailwind spacing scale: p-4, mx-2, py-6 — NEVER p-[16px], mx-[8px]
- Use gap classes for spacing: gap-4, gap-x-2, gap-y-6
- NEVER mix margin/padding with gap on the same element
- NEVER use space-* classes for spacing

### Components
- Use {self.rules.component_library} components by default
- Use {self.rules.chart_library} for all charts
- Use semantic HTML: header, nav, main, section, article, footer, aside
- Add alt text for ALL images
- Use sr-only Tailwind class for screen reader only text
- NEVER use emojis as icons — use proper icon components

### States
- Include loading states (skeleton screens)
- Include error states (error boundary + retry)
- Include empty states (illustration + helpful text + CTA)
- Include responsive viewport meta tag

### Code Quality
- No placeholder text (no "lorem ipsum", "TODO", "FIXME", "placeholder")
- No TODO comments
- No FIXME comments
- All features must be functional — no stub implementations
- Clean, consistent indentation
- Split code into logical components/sections

### Accessibility (WCAG AA)
- All images have alt text
- All buttons have text or aria-label
- All form inputs have labels
- Color contrast meets WCAG AA
- Keyboard navigation works
- Focus states are visible"""

        # Category-specific rules
        category_rules = self._get_category_rules(intent_category)
        rules_text += f"\n\n### Category-Specific Rules ({intent_category})\n{category_rules}"

        # Iteration-specific goals (progressive complexity)
        iteration_rules = self._get_iteration_rules(iteration)
        rules_text += f"\n\n### Iteration {iteration} Goals\n{iteration_rules}"

        # Quality bar
        rules_text += """

### Quality Bar
The output must be impressive enough to share publicly.
Ship something interesting rather than boring, but never ugly.
Every feature must work. Every button must do something.
No half-implemented features. No "coming soon" placeholders."""

        return rules_text

    def _get_category_rules(self, category: str) -> str:
        """Get design rules specific to the intent category."""
        rules = {
            "game_3d": """- Use Three.js + Cannon-ES for physics
- First-person camera with pointer lock
- WASD + mouse controls
- Block placement/destruction (left/right click)
- Inventory hotbar (1-9 keys)
- Chunk loading for performance
- 60fps target on 5-year-old laptop
- Procedural textures (no external assets unless asked)
- Dark cinematic theme with glowing accents
- Crosshair in center for FPS mode
- Performance: <100KB gzipped (excluding Three.js CDN)""",

            "physics_demo": """- Use raw WebGL2 (no Three.js, no libraries, no imports)
- Custom physics: Verlet integration + mass-spring system
- Procedural texture generation via offscreen canvas
- Custom vertex/fragment shaders
- Full-screen simulation canvas
- Control panel with exposed physics parameters
- Mouse interaction (grab/drag particles)
- 60fps target with 5000+ particles
- Dark cinematic theme
- No external dependencies (single HTML file)""",

            "dashboard_saas": """- Use Next.js 16 App Router + React 19 + Tailwind v4 + TypeScript
- shadcn/ui components (Card, Table, Button, Input, Select, Dialog, Tabs, Badge, Avatar)
- Recharts for all charts (area, bar, line, pie)
- SWR for data fetching (no useEffect fetch)
- Server Components by default, Client Components only when needed
- Supabase for auth + database
- KPI cards (4), activity feed, recent table, chart
- Dark mode support required
- Responsive: mobile single column, tablet 2-col, desktop full sidebar
- Loading: skeleton screens, Error: error boundary + retry, Empty: illustration + CTA""",

            "landing_page": """- Use Next.js 16 + React 19 + Tailwind v4 + Framer Motion
- Sections: Hero, Social Proof, Features, How It Works, Testimonial, Pricing, FAQ, CTA, Footer
- Modern, clean, lots of whitespace
- Subtle gradients and glows (no heavy gradients)
- Glassmorphism on cards
- Smooth hover transitions
- Fade-in on scroll (Framer Motion whileInView)
- Stagger children in feature grid
- Hover scale on cards and buttons
- Mobile-first: single column on mobile, multi-column desktop
- SEO: meta tags, OpenGraph, structured data
- Performance: LCP < 2s, CLS < 0.1""",

            "mobile_app": """- Use Expo + React Native + NativeWind + Expo Router
- TypeScript strict
- Bottom tab bar + stack navigation
- Safe area insets (iOS notch, Android status bar)
- Offline support: AsyncStorage + sync on reconnect
- Push notifications: Expo Notifications
- Gestures: swipe right=back, swipe down=refresh, long press=context menu
- iOS dynamic type / Android font scale support
- Shimmer loading placeholders
- Error: retry with icon + message
- Empty: illustration + helpful text + CTA
- Offline banner + cached content""",
        }
        return rules.get(category, rules["landing_page"])

    def _get_iteration_rule(self, iteration: int) -> str:
        """Get progressive complexity goals for each iteration."""
        if iteration == 1:
            return """Iteration 1 — WORKING VERSION:
- Get a fully functional, working version
- All core features must work (even if basic)
- Correct HTML structure, viewport meta, responsive layout
- No placeholder text
- All interactive elements functional
- This is the foundation — it must WORK, not just look good"""

        elif iteration == 2:
            return """Iteration 2 — QUALITY IMPROVEMENT:
- Improve visual design (colors, typography, spacing)
- Add loading/error/empty states
- Improve accessibility (alt text, aria-labels, contrast)
- Optimize performance (remove sync scripts, reduce DOM size)
- Add animations/transitions where appropriate
- Fix any blocking issues from iteration 1"""

        else:
            return f"""Iteration {iteration} — POLISH:
- Add polish: hover effects, transitions, micro-interactions
- Ensure all quality gates pass (target: {0.85:.0%})
- Optimize for 60fps performance
- Add any missing features from spec
- Final accessibility audit
- Final visual regression check
- This is the final iteration — make it impressive"""

    def _get_iteration_rules(self, iteration: int) -> str:
        """Alias for _get_iteration_rule to match the method call."""
        return self._get_iteration_rule(iteration)

    def validate_against_rules(self, generated_code: str) -> list:
        """Validate generated code against design rules.

        Returns list of violations (empty if all rules pass).
        """
        violations = []
        code_lower = generated_code.lower()

        # Check color count (extract unique colors)
        import re
        colors = set(re.findall(r'#([0-9a-f]{3,6})', code_lower))
        if len(colors) > self.rules.max_colors:
            violations.append(f"Too many colors: {len(colors)} (max {self.rules.max_colors})")

        # Check for raw color usage (should use tokens)
        raw_colors = re.findall(r'(?:bg|text|border)-(?:white|black|red|blue|green|yellow|purple|pink|gray)\b', code_lower)
        # Filter out semantic ones
        raw_color_violations = [c for c in raw_colors if c not in ['bg-background', 'text-foreground']]
        if raw_color_violations and self.rules.require_semantic_tokens:
            violations.append(f"Using raw colors instead of semantic tokens: {raw_color_violations[:3]}")

        # Check font count
        font_matches = re.findall(r'font-(?:sans|serif|mono)', code_lower)
        if len(set(font_matches)) > self.rules.max_fonts:
            violations.append(f"Too many font families: {len(set(font_matches))} (max {self.rules.max_fonts})")

        # Check for emojis as icons (heuristic)
        emoji_ranges = [
            r'[\U0001F600-\U0001F64F]',  # emoticons
            r'[\U0001F300-\U0001F5FF]',  # symbols & pictographs
            r'[\U0001F680-\U0001F6FF]',  # transport & map
        ]
        for pattern in emoji_ranges:
            if re.search(pattern, generated_code) and self.rules.no_emojis_as_icons:
                violations.append("Using emojis as icons — use proper icon components")
                break

        # Check for placeholders
        placeholders = ['lorem ipsum', 'todo', 'fixme', 'placeholder text', 'coming soon']
        for ph in placeholders:
            if ph in code_lower and self.rules.no_placeholders:
                violations.append(f"Contains placeholder text: '{ph}'")

        # Check for purple/violet without permission
        if self.rules.no_purple_default:
            purple_usage = re.findall(r'(?:bg|text|border)-(?:purple|violet)-\d+', code_lower)
            if purple_usage:
                violations.append(f"Using purple/violet without explicit permission: {purple_usage[:2]}")

        # Check viewport meta
        if self.rules.require_responsive:
            if 'viewport' not in code_lower or 'width=device-width' not in code_lower:
                violations.append("Missing responsive viewport meta tag")

        return violations

    def get_fix_instructions(self, violations: list) -> str:
        """Convert violations into actionable fix instructions."""
        if not violations:
            return "No design rule violations found."

        lines = ["DESIGN RULE VIOLATIONS TO FIX:"]
        for v in violations:
            lines.append(f"- {v}")

        lines.append("")
        lines.append("Fix ALL violations. Use semantic design tokens (bg-background, text-foreground),")
        lines.append(f"limit to {self.rules.max_colors} colors and {self.rules.max_fonts} fonts,")
        lines.append("remove all placeholder text, and ensure accessibility.")

        return "\n".join(lines)