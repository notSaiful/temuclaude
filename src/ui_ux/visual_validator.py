"""
Visual Validator — Playwright + screenshot diff + axe-core + Lighthouse CI.

Research finding (Section 5.2):
- Visual validator = Playwright + screenshot diff + axe-core + Lighthouse CI

This module provides the interface for visual validation. In production
it would launch a headless browser, render the generated code, capture
screenshots, run axe-core for accessibility, and run Lighthouse for
performance.

For now, we implement:
1. Static analysis of generated code (no browser needed)
2. Optional Playwright integration (if playwright is installed)
3. Screenshot comparison (if reference screenshots exist)
"""
import os
import asyncio
from typing import Optional
from dataclasses import dataclass


@dataclass
class VisualValidationResult:
    """Result of visual validation."""
    screenshots_captured: int
    accessibility_violations: int
    performance_score: Optional[float]  # Lighthouse score 0-100
    cls_score: Optional[float]          # Cumulative Layout Shift
    lcp_score: Optional[float]          # Largest Contentful Paint (seconds)
    pixel_diff: Optional[float]         # Visual regression diff (0-1)
    rendered_correctly: bool
    errors: list
    warnings: list


class VisualValidator:
    """Validates generated UI/UX using browser-based tools."""

    def __init__(self, screenshots_dir: str = None, reference_dir: str = None):
        if screenshots_dir is None:
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            screenshots_dir = os.path.join(base, "config", "ui_ux_memory", "screenshots")
        if reference_dir is None:
            reference_dir = os.path.join(os.path.dirname(screenshots_dir), "references")
        self.screenshots_dir = screenshots_dir
        self.reference_dir = reference_dir
        os.makedirs(screenshots_dir, exist_ok=True)
        os.makedirs(reference_dir, exist_ok=True)

    def _check_playwright_available(self) -> bool:
        """Check if Playwright is installed."""
        try:
            import playwright
            return True
        except ImportError:
            return False

    async def validate(
        self,
        generated_code: str,
        intent_category: str = None,
        capture_screenshots: bool = True,
    ) -> VisualValidationResult:
        """Validate generated code visually.

        Args:
            generated_code: HTML/CSS/JS code to validate
            intent_category: Intent category for context
            capture_screenshots: Whether to capture screenshots

        Returns:
            VisualValidationResult with validation metrics
        """
        errors = []
        warnings = []

        # Static checks (always available)
        rendered_correctly = self._static_render_check(generated_code, errors, warnings)
        screenshots_captured = 0
        accessibility_violations = self._static_a11y_check(generated_code, warnings)
        performance_score = self._estimate_performance(generated_code, warnings)
        cls_score = self._estimate_cls(generated_code)
        lcp_score = self._estimate_lcp(generated_code)
        pixel_diff = None

        # Playwright-based checks (if available)
        if self._check_playwright_available() and capture_screenshots:
            try:
                screenshots_captured = await self._capture_screenshots(generated_code)
                if screenshots_captured > 0:
                    pixel_diff = self._compare_with_reference(intent_category)
            except Exception as e:
                warnings.append(f"Playwright validation failed: {e}")
        else:
            warnings.append("Playwright not installed — static validation only")

        return VisualValidationResult(
            screenshots_captured=screenshots_captured,
            accessibility_violations=accessibility_violations,
            performance_score=performance_score,
            cls_score=cls_score,
            lcp_score=lcp_score,
            pixel_diff=pixel_diff,
            rendered_correctly=rendered_correctly,
            errors=errors,
            warnings=warnings,
        )

    def _static_render_check(self, code: str, errors: list, warnings: list) -> bool:
        """Static analysis to check if code will render correctly."""
        # Check for basic HTML structure
        has_html = "<html" in code.lower() or "<!doctype" in code.lower()
        has_body = "<body" in code.lower()
        has_head = "<head" in code.lower() if has_html else True

        if not has_html and not code.strip().startswith("<"):
            errors.append("Missing HTML structure")
        if not has_body and has_html:
            warnings.append("Missing <body> tag")

        # Check for unclosed script tags
        import re
        script_opens = len(re.findall(r"<script", code, re.I))
        script_closes = len(re.findall(r"</script>", code, re.I))
        if script_opens != script_closes:
            errors.append(f"Unbalanced script tags: {script_opens} open, {script_closes} close")

        return len(errors) == 0

    def _static_a11y_check(self, code: str, warnings: list) -> int:
        """Static accessibility check (heuristic)."""
        import re
        violations = 0

        # Check for alt text on images
        imgs = re.findall(r"<img\s[^>]*>", code, re.I)
        for img in imgs:
            if "alt=" not in img.lower():
                violations += 1

        # Check for labels on form inputs
        inputs = re.findall(r"<input\s[^>]*>", code, re.I)
        for inp in inputs:
            if "aria-label" not in inp.lower() and "id=" not in inp.lower():
                violations += 1

        # Check for button text
        button_matches = re.findall(r"<button[^>]*>.*?</button>", code, re.I | re.DOTALL)
        for btn in button_matches:
            # Check if button has text content or aria-label
            has_text = bool(re.search(r">[^<]+<", btn))
            has_aria = "aria-label" in btn.lower()
            if not has_text and not has_aria:
                violations += 1

        if violations > 0:
            warnings.append(f"Found {violations} potential accessibility issues")

        return violations

    def _estimate_performance(self, code: str, warnings: list) -> Optional[float]:
        """Estimate performance score based on code patterns."""
        score = 100.0

        # Penalty for large inline CSS
        import re
        styles = re.findall(r"<style[^>]*>(.*?)</style>", code, re.I | re.DOTALL)
        for style in styles:
            if len(style) > 20000:
                score -= 15
                warnings.append(f"Large inline CSS ({len(style)} chars)")

        # Penalty for large inline JS
        scripts = re.findall(r"<script[^>]*>(.*?)</script>", code, re.I | re.DOTALL)
        for script in scripts:
            if len(script) > 50000:
                score -= 20
                warnings.append(f"Large inline JS ({len(script)} chars)")

        # Penalty for too many DOM elements (heuristic)
        dom_elements = len(re.findall(r"<[a-z][^>]*>", code, re.I))
        if dom_elements > 1000:
            score -= 10
            warnings.append(f"Large DOM ({dom_elements} elements)")

        # Penalty for synchronous scripts
        sync_scripts = len(re.findall(r"<script\s+src=[^>]*(?<!async)(?<!defer)>", code, re.I))
        score -= sync_scripts * 5

        return max(0, min(100, score))

    def _estimate_cls(self, code: str) -> Optional[float]:
        """Estimate Cumulative Layout Shift score."""
        # Heuristic: check for elements that might cause layout shift
        import re
        cls_risk = 0.0

        # Images without dimensions
        imgs = re.findall(r"<img\s[^>]*>", code, re.I)
        for img in imgs:
            if "width=" not in img.lower() and "height=" not in img.lower():
                cls_risk += 0.05

        # Dynamic content placeholders
        if "loading=" in code.lower():
            cls_risk += 0.02

        return min(0.1, cls_risk)  # Target: < 0.1

    def _estimate_lcp(self, code: str) -> Optional[float]:
        """Estimate Largest Contentful Paint (seconds)."""
        # Heuristic: estimate based on code size and complexity
        code_size = len(code)
        if code_size < 10000:
            return 1.5  # Small = fast
        if code_size < 50000:
            return 2.5
        if code_size < 100000:
            return 4.0
        return 6.0  # Large = slow

    async def _capture_screenshots(self, code: str) -> int:
        """Capture screenshots using Playwright (if available)."""
        try:
            from playwright.async_api import async_playwright

            # Write code to temp HTML file
            temp_path = os.path.join(self.screenshots_dir, "_temp_render.html")
            with open(temp_path, "w") as f:
                f.write(code)

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page(viewport={"width": 1280, "height": 720})
                await page.goto(f"file://{temp_path}")
                await page.wait_for_load_state("networkidle")

                # Capture desktop screenshot
                desktop_path = os.path.join(self.screenshots_dir, "desktop.png")
                await page.screenshot(path=desktop_path, full_page=True)

                # Capture mobile viewport
                await page.set_viewport_size({"width": 375, "height": 667})
                mobile_path = os.path.join(self.screenshots_dir, "mobile.png")
                await page.screenshot(path=mobile_path, full_page=True)

                await browser.close()
                return 2  # 2 screenshots captured
        except Exception:
            return 0

    def _compare_with_reference(self, intent_category: str) -> Optional[float]:
        """Compare current screenshot with reference (if exists)."""
        if not intent_category:
            return None

        ref_path = os.path.join(self.reference_dir, f"{intent_category}_ref.png")
        current_path = os.path.join(self.screenshots_dir, "desktop.png")

        if not os.path.isfile(ref_path) or not os.path.isfile(current_path):
            return None

        try:
            # Try pixelmatch if available
            from PIL import Image
            import numpy as np

            ref = np.array(Image.open(ref_path))
            current = np.array(Image.open(current_path))

            if ref.shape != current.shape:
                return 1.0  # Completely different

            diff = np.abs(ref.astype(int) - current.astype(int))
            pixel_diff = (diff.sum(axis=2) > 10).sum() / (ref.shape[0] * ref.shape[1])
            return float(pixel_diff)
        except ImportError:
            return None