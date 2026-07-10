"""
Subagent Orchestrator — Decomposes spec into parallel subtasks for different models.

Based on Anthropic's multi-agent research system (90.2% improvement over single agent):
- Lead agent (GLM-5.2) decomposes spec into subtasks
- Each subtask assigned to the best specialized model
- Subagents run in PARALLEL (asyncio.gather)
- Each returns condensed summary + code
- Lead agent synthesizes all outputs

This is the KEY advantage over Fable 5:
- Fable 5 spawns homogeneous Claude Sonnet subagents
- We spawn HETEROGENEOUS specialized models:
  - DeepSeek V4 Pro for physics/reasoning code
  - MiniMax M3 for visual/creative code
  - DeepSeek V4 Flash for low-cost research and implementation support
  - Nemotron for verification
  - GLM-5.2 synthesizes as orchestrator
"""
import asyncio
from dataclasses import dataclass
from typing import Callable, Awaitable, Optional


@dataclass
class Subtask:
    """A subtask for a specialized subagent."""
    name: str                # Task name (physics, ui, research, etc.)
    model: str               # Which model to use
    role: str                # What this subagent does
    prompt: str              # The task prompt
    max_tokens: int          # Token budget
    temperature: float       # Generation temperature


@dataclass
class SubtaskResult:
    """Result from a subagent."""
    task_name: str
    model: str
    code: str                # Generated code or research findings
    summary: str             # Condensed summary (1000-2000 tokens)
    success: bool
    error: Optional[str] = None


class SubagentOrchestrator:
    """Orchestrates parallel subagents for complex generation."""

    def __init__(self, call_model_fn: Callable[..., Awaitable[str]]):
        self.call_model_fn = call_model_fn

    def decompose_spec(self, spec_markdown: str, intent_category: str) -> list:
        """Decompose a spec into parallel subtasks.

        Returns list of Subtask objects assigned to specialized models.
        """
        subtasks = []

        if intent_category in ("game_3d", "physics_demo"):
            # Games/physics: decompose into engine + UI + research
            subtasks.append(Subtask(
                name="engine",
                model="deepseek-v4-pro",
                role="Generate the physics/rendering engine code",
                prompt=self._build_engine_prompt(spec_markdown, intent_category),
                max_tokens=8000,
                temperature=0.3,
            ))
            subtasks.append(Subtask(
                name="ui",
                model="minimax-m3",
                role="Generate the UI/controls/visual layer",
                prompt=self._build_ui_prompt(spec_markdown, intent_category),
                max_tokens=6000,
                temperature=0.7,
            ))
            subtasks.append(Subtask(
                name="research",
                model="deepseek-v4-flash",
                role="Research best practices and provide reference code snippets",
                prompt=self._build_research_prompt(spec_markdown, intent_category),
                max_tokens=3000,
                temperature=0.2,
            ))

        elif intent_category == "dashboard_saas":
            # Dashboard: decompose into layout + charts + data layer
            subtasks.append(Subtask(
                name="layout",
                model="deepseek-v4-pro",
                role="Generate the dashboard layout and navigation",
                prompt=self._build_layout_prompt(spec_markdown),
                max_tokens=6000,
                temperature=0.2,
            ))
            subtasks.append(Subtask(
                name="charts",
                model="minimax-m3",
                role="Generate the chart components with Recharts",
                prompt=self._build_charts_prompt(spec_markdown),
                max_tokens=5000,
                temperature=0.5,
            ))
            subtasks.append(Subtask(
                name="data",
                model="deepseek-v4-flash",
                role="Generate the data layer (mock data, API routes, types)",
                prompt=self._build_data_prompt(spec_markdown),
                max_tokens=4000,
                temperature=0.2,
            ))

        elif intent_category == "landing_page":
            # Landing page: decompose into hero + sections + animations
            subtasks.append(Subtask(
                name="hero",
                model="minimax-m3",
                role="Generate the hero section with animations",
                prompt=self._build_hero_prompt(spec_markdown),
                max_tokens=4000,
                temperature=0.8,
            ))
            subtasks.append(Subtask(
                name="sections",
                model="deepseek-v4-pro",
                role="Generate the content sections (features, pricing, FAQ, testimonial)",
                prompt=self._build_sections_prompt(spec_markdown),
                max_tokens=6000,
                temperature=0.4,
            ))

        else:
            # Default: single generation task
            subtasks.append(Subtask(
                name="generate",
                model="glm-5.2",
                role="Generate the complete code from spec",
                prompt=spec_markdown,
                max_tokens=10000,
                temperature=0.5,
            ))

        return subtasks

    async def execute_parallel(self, subtasks: list) -> list:
        """Execute all subtasks in parallel.

        Returns list of SubtaskResult.
        """
        async def run_subtask(task: Subtask) -> SubtaskResult:
            try:
                messages = [
                    {"role": "system", "content": f"You are a specialist. {task.role}. Output ONLY code, no explanations."},
                    {"role": "user", "content": task.prompt},
                ]
                code = await self.call_model_fn(
                    task.model, messages,
                    max_tokens=task.max_tokens,
                )
                return SubtaskResult(
                    task_name=task.name,
                    model=task.model,
                    code=code,
                    summary=code[:2000],  # Condensed summary
                    success=not code.startswith("[ERROR"),
                )
            except Exception as e:
                return SubtaskResult(
                    task_name=task.name,
                    model=task.model,
                    code="",
                    summary=f"Failed: {e}",
                    success=False,
                    error=str(e),
                )

        # Run all subtasks in parallel
        results = await asyncio.gather(*[run_subtask(task) for task in subtasks])
        return list(results)

    async def synthesize(self, results: list, intent_category: str, spec_markdown: str) -> str:
        """Synthesize subagent outputs into final code.

        The orchestrator (GLM-5.2) takes all subagent outputs and
        combines them into a single coherent codebase.
        """
        # Build synthesis prompt with all subagent outputs
        parts = []
        for r in results:
            if r.success and r.code:
                parts.append(f"### {r.task_name.upper()} (by {r.model})\n{r.code[:5000]}")
            else:
                parts.append(f"### {r.task_name.upper()} (FAILED)\nError: {r.error}")

        synthesis_prompt = f"""You are Temuclaude's master synthesizer. Multiple specialized subagents have generated different parts of a {intent_category} project. Your job is to combine them into a SINGLE, COMPLETE, WORKING HTML file.

SPEC:
{spec_markdown[:2000]}

SUBAGENT OUTPUTS:
{chr(10).join(parts)}

INSTRUCTIONS:
1. Combine all subagent outputs into ONE complete, working HTML file
2. Resolve any conflicts between subagents (e.g., variable names, styles)
3. Ensure all parts work together (engine + UI + data)
4. Add any missing glue code needed to make parts work together
5. Remove duplicates and redundant code
6. Ensure the output is a SINGLE self-contained HTML file
7. Output ONLY the final HTML code — no explanations

Output the complete, synthesized HTML:"""

        messages = [
            {"role": "system", "content": "You are Temuclaude's master code synthesizer. Combine subagent outputs into one working file."},
            {"role": "user", "content": synthesis_prompt},
        ]

        synthesized = await self.call_model_fn("glm-5.2", messages, max_tokens=16000)
        return synthesized

    async def generate(self, spec_markdown: str, intent_category: str) -> str:
        """Full pipeline: decompose → parallel execution → synthesize.

        Returns the synthesized final code.
        """
        # Step 1: Decompose spec into subtasks
        subtasks = self.decompose_spec(spec_markdown, intent_category)

        # Step 2: Execute all subtasks in parallel
        results = await self.execute_parallel(subtasks)

        # Step 3: Synthesize outputs
        final_code = await self.synthesize(results, intent_category, spec_markdown)

        return final_code

    # === PROMPT BUILDERS ===

    def _build_engine_prompt(self, spec: str, category: str) -> str:
        if category == "game_3d":
            return f"""Generate ONLY the physics/rendering engine for a 3D voxel game.
Include: Three.js scene setup, Cannon-ES physics, chunk loading, block placement/destruction,
player movement (WASD + mouse), gravity, collision detection.
Do NOT include UI, controls panel, or HTML structure — just the JavaScript engine code.

Spec:
{spec[:2000]}

Output the engine JavaScript code:"""
        else:  # physics_demo
            return f"""Generate ONLY the physics simulation engine.
Include: WebGL2 setup, Verlet integration, mass-spring system, wind/turbulence forces,
constraint solving, particle updates, custom shaders.
Do NOT include UI, controls panel, or HTML structure — just the JavaScript simulation code.

Spec:
{spec[:2000]}

Output the engine JavaScript code:"""

    def _build_ui_prompt(self, spec: str, category: str) -> str:
        return f"""Generate ONLY the UI/visual layer for a {category}.
Include: HTML structure, CSS styling, control panels, stats display, instructions,
crosshair, inventory hotbar, all visual elements.
Do NOT include physics/rendering engine — just the UI layer.

Spec:
{spec[:2000]}

Output the UI HTML/CSS code:"""

    def _build_research_prompt(self, spec: str, category: str) -> str:
        return f"""Research best practices for building a {category}.
Provide: optimal algorithms, performance tips, common pitfalls, code snippets
that the engine and UI subagents should incorporate.
Be specific and technical. Include code examples.

Spec:
{spec[:1500]}

Output research findings and code snippets:"""

    def _build_layout_prompt(self, spec: str) -> str:
        return f"""Generate ONLY the dashboard layout and navigation structure.
Include: sidebar, top bar, page layout, responsive grid, routing structure.
Use shadcn/ui components. Do NOT include chart or data code.

Spec:
{spec[:2000]}

Output the layout code:"""

    def _build_charts_prompt(self, spec: str) -> str:
        return f"""Generate ONLY the chart components using Recharts.
Include: area chart, bar chart, line chart, KPI cards with sparklines.
Do NOT include layout or data fetching code.

Spec:
{spec[:2000]}

Output the chart components:"""

    def _build_data_prompt(self, spec: str) -> str:
        return f"""Generate ONLY the data layer: mock data, API route handlers, TypeScript types.
Include: realistic mock data for dashboard, API endpoints, data types/interfaces.
Do NOT include layout or chart code.

Spec:
{spec[:2000]}

Output the data layer code:"""

    def _build_hero_prompt(self, spec: str) -> str:
        return f"""Generate ONLY the hero section for a landing page.
Include: headline, subheadline, CTA button, hero visual/animation, Framer Motion.
Make it visually stunning. Do NOT include other sections.

Spec:
{spec[:2000]}

Output the hero section code:"""

    def _build_sections_prompt(self, spec: str) -> str:
        return f"""Generate ONLY the content sections for a landing page.
Include: Features grid, How It Works, Testimonial, Pricing cards, FAQ accordion, CTA footer.
Do NOT include the hero section.

Spec:
{spec[:2000]}

Output the content sections code:"""
