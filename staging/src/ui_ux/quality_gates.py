"""
Quality Gates — Automated quality checks that beat "good enough".

Research finding (Section 5.5):
| Gate                | Tool                          | Threshold              |
|---------------------|-------------------------------|------------------------|
| Type Safety         | tsc --noEmit                  | Zero errors            |
| Lint/Format         | eslint + prettier             | Zero warnings          |
| Accessibility       | axe-core (playwright)         | Zero violations (AA)   |
| Performance         | Lighthouse CI                 | Perf >= 90, CLS < 0.1  |
| Visual Regression   | pixelmatch vs. screenshots    | <0.1% pixel diff       |
| Game Logic          | Custom Playwright tests       | All mechanics func     |
| Bundle Size         | webpack-bundle-analyzer       | < budget per route     |

This module provides gate definitions and validation logic.
The actual tools (Playwright, axe-core, Lighthouse) are invoked
by visual_validator.py.
"""
import os
import re
import json
from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class GateResult:
    """Result of a single quality gate check."""
    gate_name: str
    passed: bool
    score: float          # 0.0 - 1.0
    details: str          # Human-readable details
    errors: list          # List of specific errors/issues
    fix_suggestion: str   # What to fix if not passed


@dataclass
class QualityReport:
    """Aggregate quality report from all gates."""
    overall_passed: bool
    overall_score: float
    gate_results: list   # List of GateResult
    blocking_issues: list  # Issues that must be fixed
    warnings: list         # Issues that are non-blocking
    recommendations: list  # Suggestions for improvement


class QualityGates:
    """Defines and evaluates quality gates for generated UI/UX."""

    # Gate definitions — from research report
    GATES = {
        "html_valid": {
            "description": "HTML is well-formed and valid",
            "threshold": 1.0,
            "blocking": True,
        },
        "no_placeholder": {
            "description": "No placeholder text (lorem ipsum, TODO, FIXME)",
            "threshold": 1.0,
            "blocking": True,
        },
        "responsive_meta": {
            "description": "Has responsive viewport meta tag",
            "threshold": 1.0,
            "blocking": True,
        },
        "semantic_html": {
            "description": "Uses semantic HTML5 elements (header, nav, main, section, footer)",
            "threshold": 0.8,
            "blocking": False,
        },
        "accessibility_attrs": {
            "description": "Images have alt text, buttons have aria-labels",
            "threshold": 0.9,
            "blocking": True,
        },
        "color_contrast": {
            "description": "Color contrast meets WCAG AA standards",
            "threshold": 0.9,
            "blocking": False,
        },
        "performance_hints": {
            "description": "No render-blocking patterns (sync scripts, huge inline CSS)",
            "threshold": 0.8,
            "blocking": False,
        },
        "no_external_deps": {
            "description": "For single-file demos: no external dependencies",
            "threshold": 1.0,
            "blocking": False,  # Only for single-file mode
        },
        "code_quality": {
            "description": "Code is clean, indented, no obvious errors",
            "threshold": 0.8,
            "blocking": False,
        },
        "interactive_elements": {
            "description": "Has interactive elements (buttons, inputs, links)",
            "threshold": 0.8,
            "blocking": False,
        },
    }

    def __init__(self, single_file_mode: bool = False):
        self.single_file_mode = single_file_mode

    def evaluate(self, generated_code: str, intent_category: str = None) -> QualityReport:
        """Run all quality gates on generated code.

        Args:
            generated_code: The generated HTML/CSS/JS code
            intent_category: The intent category (affects which gates apply)

        Returns:
            QualityReport with all gate results
        """
        results = []

        # HTML validity
        results.append(self._check_html_valid(generated_code))

        # No placeholders
        results.append(self._check_no_placeholder(generated_code))

        # Responsive viewport
        results.append(self._check_responsive_meta(generated_code))

        # Semantic HTML
        results.append(self._check_semantic_html(generated_code))

        # Accessibility attributes
        results.append(self._check_accessibility(generated_code))

        # Color contrast (basic check)
        results.append(self._check_color_contrast(generated_code))

        # Performance hints
        results.append(self._check_performance_hints(generated_code))

        # No external deps (only for single-file mode)
        if self.single_file_mode:
            results.append(self._check_no_external_deps(generated_code))

        # Code quality
        results.append(self._check_code_quality(generated_code))

        # Interactive elements
        results.append(self._check_interactive_elements(generated_code))

        # Compute overall
        blocking = [r for r in results if not r.passed and self.GATES.get(r.gate_name, {}).get("blocking", False)]
        warnings = [r for r in results if not r.passed and not self.GATES.get(r.gate_name, {}).get("blocking", False)]
        recommendations = [r.fix_suggestion for r in results if not r.passed and r.fix_suggestion]

        # Overall score = weighted average
        total_weight = len(results)
        score_sum = sum(r.score for r in results)
        overall_score = score_sum / total_weight if total_weight > 0 else 0.0
        overall_passed = len(blocking) == 0

        return QualityReport(
            overall_passed=overall_passed,
            overall_score=round(overall_score, 2),
            gate_results=results,
            blocking_issues=[r.gate_name for r in blocking],
            warnings=[r.gate_name for r in warnings],
            recommendations=recommendations,
        )

    def _check_html_valid(self, code: str) -> GateResult:
        """Check if HTML is well-formed."""
        # Basic check: balanced tags for common elements
        issues = []
        for tag in ["html", "head", "body", "div", "section", "header", "footer", "main", "nav"]:
            opens = len(re.findall(rf"<{tag}[\s>]", code, re.I))
            closes = len(re.findall(rf"</{tag}>", code, re.I))
            if opens != closes:
                issues.append(f"Unbalanced <{tag}>: {opens} open, {closes} close")

        # Check for DOCTYPE
        has_doctype = "<!DOCTYPE html>" in code.upper() or "<!doctype html>" in code.lower()
        if not has_doctype:
            issues.append("Missing DOCTYPE declaration")

        passed = len(issues) == 0
        return GateResult(
            gate_name="html_valid",
            passed=passed,
            score=1.0 if passed else 0.5,
            details="HTML is well-formed" if passed else f"{len(issues)} issues: {'; '.join(issues[:3])}",
            errors=issues,
            fix_suggestion="Fix unbalanced HTML tags and add DOCTYPE" if not passed else "",
        )

    def _check_no_placeholder(self, code: str) -> GateResult:
        """Check for placeholder text."""
        placeholders = ["lorem ipsum", "TODO", "FIXME", "placeholder text",
                        "your content here", "sample text", "xxx"]
        found = []
        code_lower = code.lower()
        for ph in placeholders:
            if ph.lower() in code_lower:
                found.append(ph)

        passed = len(found) == 0
        return GateResult(
            gate_name="no_placeholder",
            passed=passed,
            score=1.0 if passed else 0.0,
            details="No placeholder text found" if passed else f"Found: {', '.join(found)}",
            errors=found,
            fix_suggestion="Replace all placeholder text with real content" if not passed else "",
        )

    def _check_responsive_meta(self, code: str) -> GateResult:
        """Check for responsive viewport meta tag."""
        has_viewport = "viewport" in code.lower() and "width=device-width" in code.lower()
        return GateResult(
            gate_name="responsive_meta",
            passed=has_viewport,
            score=1.0 if has_viewport else 0.0,
            details="Has responsive viewport meta" if has_viewport else "Missing viewport meta tag",
            errors=[] if has_viewport else ["Missing <meta name='viewport' content='width=device-width'>"],
            fix_suggestion="" if has_viewport else "Add viewport meta tag in <head>",
        )

    def _check_semantic_html(self, code: str) -> GateResult:
        """Check for semantic HTML5 elements."""
        semantic_tags = ["<header", "<nav", "<main", "<section", "<article", "<footer", "<aside"]
        found = [tag for tag in semantic_tags if tag in code.lower()]
        score = len(found) / len(semantic_tags)
        passed = score >= 0.8
        return GateResult(
            gate_name="semantic_html",
            passed=passed,
            score=round(score, 2),
            details=f"Found {len(found)}/{len(semantic_tags)} semantic elements",
            errors=[] if passed else [f"Missing semantic elements: {set(semantic_tags) - set(found)}"],
            fix_suggestion="Use more semantic HTML5 elements (header, nav, main, section)" if not passed else "",
        )

    def _check_accessibility(self, code: str) -> GateResult:
        """Check accessibility attributes."""
        issues = []

        # Check images for alt text
        img_matches = re.findall(r"<img\s[^>]*>", code, re.I)
        for img in img_matches:
            if "alt=" not in img.lower():
                issues.append(f"Image missing alt: {img[:50]}...")

        # Check buttons for aria-label or text content
        button_matches = re.findall(r"<button\s[^>]*>.*?</button>", code, re.I | re.DOTALL)
        for btn in button_matches:
            # Check if button has text or aria-label
            has_text = bool(re.search(r">[^<]+<", btn))
            has_aria = "aria-label" in btn.lower()
            if not has_text and not has_aria:
                issues.append("Button missing text or aria-label")

        # Check for role attributes on interactive elements
        has_role = "role=" in code.lower()

        score = 1.0 - min(len(issues) / 10, 0.5)  # Reduce score per issue
        passed = len(issues) == 0
        return GateResult(
            gate_name="accessibility_attrs",
            passed=passed,
            score=round(score, 2),
            details=f"{len(issues)} accessibility issues found" if issues else "All accessibility checks passed",
            errors=[str(i) for i in issues[:5]],
            fix_suggestion="Add alt text to images, aria-labels to icon buttons" if not passed else "",
        )

    def _check_color_contrast(self, code: str) -> GateResult:
        """Basic color contrast check (heuristic)."""
        # Extract color pairs from inline styles
        style_matches = re.findall(r"(?:color|background-color|background)\s*:\s*([^;]+)", code, re.I)
        if len(style_matches) < 2:
            return GateResult(
                gate_name="color_contrast",
                passed=True,
                score=0.8,
                details="Not enough color definitions to check contrast",
                errors=[],
                fix_suggestion="",
            )

        # Simple heuristic: check if dark and light colors are both present
        has_dark = any(self._is_dark_color(c.strip()) for c in style_matches)
        has_light = any(not self._is_dark_color(c.strip()) for c in style_matches)

        passed = has_dark and has_light
        return GateResult(
            gate_name="color_contrast",
            passed=passed,
            score=0.9 if passed else 0.5,
            details="Color contrast looks adequate" if passed else "May have poor contrast (all dark or all light)",
            errors=[] if passed else ["Consider adding both dark and light colors for contrast"],
            fix_suggestion="Ensure text and background have sufficient contrast (WCAG AA)" if not passed else "",
        )

    def _is_dark_color(self, color_str: str) -> bool:
        """Heuristic: is this a dark color?"""
        color_str = color_str.strip().lower()
        if color_str.startswith("#"):
            try:
                r = int(color_str[1:3], 16)
                g = int(color_str[3:5], 16) if len(color_str) > 4 else r
                b = int(color_str[5:7], 16) if len(color_str) > 6 else r
                luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                return luminance < 0.5
            except (ValueError, IndexError):
                return False
        dark_keywords = ["black", "dark", "navy", "#000", "#111", "#222", "#333"]
        return any(k in color_str for k in dark_keywords)

    def _check_performance_hints(self, code: str) -> GateResult:
        """Check for performance anti-patterns."""
        issues = []

        # Check for synchronous scripts (not async/defer)
        script_matches = re.findall(r"<script\s[^>]*>", code, re.I)
        for script in script_matches:
            if "src=" in script and "async" not in script.lower() and "defer" not in script.lower():
                issues.append("Synchronous script tag (add async or defer)")

        # Check for large inline styles
        style_matches = re.findall(r"<style[^>]*>(.*?)</style>", code, re.I | re.DOTALL)
        for style in style_matches:
            if len(style) > 10000:  # >10KB inline CSS
                issues.append(f"Large inline CSS: {len(style)} chars")

        score = 1.0 - min(len(issues) / 5, 0.3)
        passed = len(issues) <= 1
        return GateResult(
            gate_name="performance_hints",
            passed=passed,
            score=round(score, 2),
            details=f"{len(issues)} performance hints" if issues else "No performance issues detected",
            errors=[str(i) for i in issues[:3]],
            fix_suggestion="Add async/defer to script tags, extract large CSS" if not passed else "",
        )

    def _check_no_external_deps(self, code: str) -> GateResult:
        """For single-file mode: check no external dependencies."""
        external_patterns = [
            r'<script\s+src=["\']https?://',  # External scripts
            r'<link\s+.*href=["\']https?://.*\.css',  # External CSS
            r'@import\s+url\(.*https?://',  # CSS @import
        ]
        issues = []
        for pattern in external_patterns:
            matches = re.findall(pattern, code, re.I)
            issues.extend(matches)

        # CDN references are OK for frameworks but note them
        passed = len(issues) == 0
        return GateResult(
            gate_name="no_external_deps",
            passed=passed,
            score=1.0 if passed else 0.3,
            details=f"{len(issues)} external dependencies" if issues else "No external dependencies",
            errors=[str(i) for i in issues[:3]],
            fix_suggestion="Remove external dependencies for single-file mode" if not passed else "",
        )

    def _check_code_quality(self, code: str) -> GateResult:
        """Check basic code quality indicators."""
        issues = []

        # Check for obvious syntax errors (unclosed tags, brackets)
        open_braces = code.count("{")
        close_braces = code.count("}")
        if open_braces != close_braces:
            issues.append(f"Unbalanced braces: {open_braces} open, {close_braces} close")

        # Check for very long lines (hard to maintain)
        lines = code.split("\n")
        long_lines = sum(1 for line in lines if len(line) > 500)
        if long_lines > 5:
            issues.append(f"{long_lines} very long lines (>500 chars)")

        # Check for consistent indentation (basic)
        inconsistent = 0
        for line in lines:
            if line.strip() and line[0] == " " and not line.startswith("    ") and not line.startswith("  "):
                inconsistent += 1
        if inconsistent > 10:
            issues.append("Inconsistent indentation")

        score = 1.0 - min(len(issues) / 5, 0.3)
        passed = len(issues) <= 1
        return GateResult(
            gate_name="code_quality",
            passed=passed,
            score=round(score, 2),
            details=f"{len(issues)} code quality issues" if issues else "Code quality is good",
            errors=[str(i) for i in issues[:3]],
            fix_suggestion="Fix syntax issues, consistent indentation, break long lines" if not passed else "",
        )

    def _check_interactive_elements(self, code: str) -> GateResult:
        """Check for interactive elements."""
        interactive = 0
        interactive += len(re.findall(r"<button", code, re.I))
        interactive += len(re.findall(r"<input", code, re.I))
        interactive += len(re.findall(r"<a\s+href", code, re.I))
        interactive += len(re.findall(r"onclick|addEventListener|onchange", code, re.I))

        score = min(interactive / 5, 1.0)  # 5+ interactive elements = full score
        passed = interactive >= 3
        return GateResult(
            gate_name="interactive_elements",
            passed=passed,
            score=round(score, 2),
            details=f"{interactive} interactive elements found",
            errors=[] if passed else ["Not enough interactive elements"],
            fix_suggestion="Add more interactive elements (buttons, inputs, event handlers)" if not passed else "",
        )

    def get_gate_summary(self, report: QualityReport) -> str:
        """Get a human-readable summary of quality gate results."""
        lines = [f"Quality Score: {report.overall_score:.2f}/1.0", ""]
        for result in report.gate_results:
            status = "PASS" if result.passed else "FAIL"
            lines.append(f"  [{status}] {result.gate_name}: {result.details}")

        if report.blocking_issues:
            lines.append(f"\nBlocking: {', '.join(report.blocking_issues)}")
        if report.warnings:
            lines.append(f"Warnings: {', '.join(report.warnings)}")

        return "\n".join(lines)