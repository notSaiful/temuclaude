"""
Screenshot Feedback Loop — Render code, screenshot, feed back to model.

From Builder.io's #1 tip: "You tell an AI tool to 'fix the layout' but it can't see
what you're looking at. It's working blind."

From Anthropic's Fable 5: "It can perform complex vision-based tasks like rebuilding
a web app's source code from screenshots alone."

This module:
1. Renders generated code in a headless browser (Playwright if available)
2. Takes a screenshot
3. Feeds the screenshot + quality report back to the model
4. Model can "see" what it made and fix visual issues

If Playwright is not installed, falls back to static analysis only.
"""
import os
import asyncio
import base64
from typing import Optional, Callable, Awaitable
from dataclasses import dataclass


@dataclass
class ScreenshotResult:
    """Result of screenshot capture."""
    captured: bool
    screenshot_path: Optional[str] = None
    screenshot_base64: Optional[str] = None  # For feeding to vision models
    console_errors: list = None
    render_errors: list = None
    viewport_tested: str = "desktop"  # desktop, mobile


class ScreenshotFeedback:
    """Renders code and captures screenshots for feedback loop."""

    def __init__(self, screenshots_dir: str = None):
        if screenshots_dir is None:
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            screenshots_dir = os.path.join(base, "config", "ui_ux_memory", "screenshots")
        self.screenshots_dir = screenshots_dir
        os.makedirs(screenshots_dir, exist_ok=True)

    def _check_playwright_available(self) -> bool:
        """Check if Playwright is installed."""
        try:
            import playwright
            return True
        except ImportError:
            return False

    async def capture_screenshot(
        self,
        generated_code: str,
        viewport: str = "desktop",
        session_id: str = None,
    ) -> ScreenshotResult:
        """Render code in headless browser and capture screenshot.

        Args:
            generated_code: HTML/CSS/JS code to render
            viewport: "desktop" (1280x720) or "mobile" (375x667)
            session_id: Unique ID for this screenshot (avoid collisions)

        Returns:
            ScreenshotResult with screenshot path/base64 and any errors
        """
        if not self._check_playwright_available():
            return ScreenshotResult(
                captured=False,
                console_errors=[],
                render_errors=["Playwright not installed — static analysis only"],
            )

        try:
            from playwright.async_api import async_playwright

            # Write code to temp file
            if session_id is None:
                import time
                session_id = str(int(time.time() * 1000))

            temp_path = os.path.join(self.screenshots_dir, f"_render_{session_id}.html")
            with open(temp_path, "w") as f:
                f.write(generated_code)

            # Viewport settings
            viewports = {
                "desktop": {"width": 1280, "height": 720},
                "mobile": {"width": 375, "height": 667},
                "tablet": {"width": 768, "height": 1024},
            }
            vp = viewports.get(viewport, viewports["desktop"])

            # Collect console errors
            console_errors = []

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(viewport=vp)

                # Capture console errors
                page.on("console", lambda msg: console_errors.append(f"{msg.type}: {msg.text}") if msg.type == "error" else None)
                page.on("pageerror", lambda err: console_errors.append(f"PAGE ERROR: {err}"))

                await page.goto(f"file://{temp_path}")
                await page.wait_for_load_state("networkidle", timeout=10000)

                # Take screenshot
                screenshot_path = os.path.join(self.screenshots_dir, f"{viewport}_{session_id}.png")
                await page.screenshot(path=screenshot_path, full_page=True)

                # Also get base64 for vision model feedback
                screenshot_b64 = await page.screenshot(full_page=True)
                screenshot_base64 = base64.b64encode(screenshot_b64).decode()

                await browser.close()

                return ScreenshotResult(
                    captured=True,
                    screenshot_path=screenshot_path,
                    screenshot_base64=screenshot_base64,
                    console_errors=console_errors,
                    render_errors=[],
                    viewport_tested=viewport,
                )

        except Exception as e:
            return ScreenshotResult(
                captured=False,
                console_errors=[],
                render_errors=[f"Screenshot capture failed: {e}"],
            )

    def build_feedback_prompt(
        self,
        screenshot_result: ScreenshotResult,
        quality_report,  # QualityReport from quality_gates
        generated_code: str,
    ) -> str:
        """Build a feedback prompt that includes screenshot + quality issues.

        This is what gets fed back to the model so it can "see" what it made.
        """
        lines = ["FEEDBACK ON YOUR GENERATED CODE:", ""]

        # Screenshot info
        if screenshot_result.captured:
            lines.append(f"SCREENSHOT CAPTURED: {screenshot_result.viewport_tested} viewport")
            lines.append("(See attached screenshot — this is what your code actually renders)")
            lines.append("")
        else:
            lines.append("SCREENSHOT: Could not capture (Playwright not installed)")
            for err in screenshot_result.render_errors:
                lines.append(f"  - {err}")
            lines.append("")

        # Console errors (JavaScript runtime errors)
        if screenshot_result.console_errors:
            lines.append("CONSOLE ERRORS (JavaScript runtime errors in browser):")
            for err in screenshot_result.console_errors[:5]:
                lines.append(f"  - {err}")
            lines.append("")

        # Quality gate results
        if quality_report:
            lines.append("QUALITY GATE RESULTS:")
            lines.append(f"  Overall Score: {quality_report.overall_score:.2f}/1.0")
            lines.append(f"  Overall Passed: {quality_report.overall_passed}")
            for gate in quality_report.gate_results:
                status = "PASS" if gate.passed else "FAIL"
                lines.append(f"  [{status}] {gate.gate_name}: {gate.details}")
                if not gate.passed and gate.fix_suggestion:
                    lines.append(f"    Fix: {gate.fix_suggestion}")
            lines.append("")

            if quality_report.blocking_issues:
                lines.append(f"BLOCKING ISSUES: {', '.join(quality_report.blocking_issues)}")
            if quality_report.warnings:
                lines.append(f"WARNINGS: {', '.join(quality_report.warnings)}")
            lines.append("")

        # Code preview (first 500 chars for context)
        lines.append("YOUR CODE (first 500 chars):")
        lines.append(generated_code[:500])
        lines.append("...")

        lines.append("")
        lines.append("INSTRUCTIONS:")
        lines.append("Based on the screenshot and quality report above, fix ALL issues.")
        lines.append("The screenshot shows what your code ACTUALLY renders — not what you intended.")
        lines.append("Fix both visual issues (from screenshot) and code issues (from quality gates).")
        lines.append("Return the complete fixed HTML code.")

        return "\n".join(lines)

    async def get_visual_feedback(
        self,
        generated_code: str,
        quality_report,
        call_model_fn: Callable[..., Awaitable[str]],
        model: str = "nemotron-3-ultra",
    ) -> str:
        """Full feedback loop: screenshot → build prompt → get critique from model.

        Returns the critique/feedback string from the model.
        """
        # Capture screenshot
        screenshot = await self.capture_screenshot(generated_code)

        # Build feedback prompt
        feedback_prompt = self.build_feedback_prompt(screenshot, quality_report, generated_code)

        # Get model critique
        messages = [
            {"role": "system", "content": "You are a UI/UX code reviewer. Analyze the screenshot and quality report. Give specific, actionable feedback on what to fix."},
            {"role": "user", "content": feedback_prompt},
        ]

        critique = await call_model_fn(model, messages, max_tokens=2000)
        return critique