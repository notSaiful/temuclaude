"""
Adversarial Verifier — Subagent tries to break the code, another fixes it.

From Ethan Mollick's Fable 5 article:
"It launched yet more agents and tests to verify its code"
"It used adversarial groups of agents that did research and tested each others' results"

This module:
1. Spawns a "breaker" subagent (Nemotron) that tries to find bugs, edge cases,
   broken interactions, accessibility issues, performance problems
2. Spawns a "fixer" subagent (DeepSeek) that fixes all issues found
3. Loops until no critical bugs remain

This is the adversarial verification pattern Fable 5 uses.
"""
import asyncio
from dataclasses import dataclass
from typing import Callable, Awaitable, Optional


@dataclass
class BugReport:
    """A bug found by the breaker."""
    severity: str        # critical, major, minor
    category: str        # a11y, performance, logic, visual, security
    description: str
    location: str        # Where in the code (line/section)
    fix_suggestion: str


@dataclass
class AdversarialResult:
    """Result of adversarial verification cycle."""
    bugs_found: list     # List of BugReport
    bugs_fixed: list     # List of BugReport that were fixed
    unfixed_bugs: list   # List of BugReport that couldn't be fixed
    fixed_code: str      # Code after fixes
    iterations: int      # How many break-fix cycles ran
    all_critical_fixed: bool


class AdversarialVerifier:
    """Adversarial verification: breaker finds bugs, fixer fixes them."""

    def __init__(self, call_model_fn: Callable[..., Awaitable[str]]):
        self.call_model_fn = call_model_fn

    async def break_code(self, generated_code: str, intent_category: str) -> list:
        """Spawn a breaker subagent to find bugs in the code.

        Returns list of BugReport.
        """
        breaker_prompt = f"""You are a hostile code reviewer. Your job is to find EVERY bug, issue, and problem in this {intent_category} code.

Look for:
1. CRITICAL: Broken functionality (buttons that don't work, broken layout, JavaScript errors)
2. CRITICAL: Accessibility violations (missing alt text, no keyboard nav, poor contrast)
3. MAJOR: Performance issues (large DOM, sync scripts, memory leaks)
4. MAJOR: Visual bugs (overlapping elements, broken responsive, missing states)
5. MAJOR: Logic errors (incorrect calculations, wrong physics, broken interactions)
6. MINOR: Code quality issues (inconsistent styling, missing comments)
7. MINOR: Missing features from spec

Be thorough. Find EVERYTHING. Report each bug with:
- SEVERITY: critical, major, or minor
- CATEGORY: a11y, performance, logic, visual, or security
- DESCRIPTION: What's wrong
- LOCATION: Where in the code
- FIX: How to fix it

Code to review:
{generated_code[:8000]}

Report ALL bugs found:"""

        messages = [
            {"role": "system", "content": "You are a hostile code reviewer. Find every bug."},
            {"role": "user", "content": breaker_prompt},
        ]

        response = await self.call_model_fn("nemotron-3-ultra", messages, max_tokens=3000)

        # Parse the response into BugReport objects
        bugs = self._parse_bug_reports(response)
        return bugs

    def _parse_bug_reports(self, response: str) -> list:
        """Parse model response into BugReport objects."""
        bugs = []
        lines = response.split("\n")
        current_bug = {}

        for line in lines:
            line = line.strip()
            if not line:
                if current_bug.get("description"):
                    bugs.append(BugReport(
                        severity=current_bug.get("severity", "minor"),
                        category=current_bug.get("category", "logic"),
                        description=current_bug.get("description", ""),
                        location=current_bug.get("location", ""),
                        fix_suggestion=current_bug.get("fix", ""),
                    ))
                    current_bug = {}
                continue

            # Parse severity
            lower = line.lower()
            if "critical" in lower and "severity" not in current_bug:
                current_bug["severity"] = "critical"
            elif "major" in lower and "severity" not in current_bug:
                current_bug["severity"] = "major"
            elif "minor" in lower and "severity" not in current_bug:
                current_bug["severity"] = "minor"

            # Parse category
            for cat in ["a11y", "accessibility", "performance", "logic", "visual", "security"]:
                if cat in lower and "category" not in current_bug:
                    current_bug["category"] = "a11y" if cat == "accessibility" else cat
                    break

            # Parse description
            if "description" in lower or "issue" in lower or "problem" in lower:
                if ":" in line:
                    current_bug["description"] = line.split(":", 1)[1].strip()
                else:
                    current_bug["description"] = line
            elif "fix" in lower and ":" in line:
                current_bug["fix"] = line.split(":", 1)[1].strip()
            elif "location" in lower and ":" in line:
                current_bug["location"] = line.split(":", 1)[1].strip()
            elif line and not line.startswith("#") and "description" not in current_bug:
                current_bug["description"] = line

        # Don't forget the last bug
        if current_bug.get("description"):
            bugs.append(BugReport(
                severity=current_bug.get("severity", "minor"),
                category=current_bug.get("category", "logic"),
                description=current_bug.get("description", ""),
                location=current_bug.get("location", ""),
                fix_suggestion=current_bug.get("fix", ""),
            ))

        return bugs

    async def fix_bugs(self, generated_code: str, bugs: list, spec_markdown: str) -> str:
        """Spawn a fixer subagent to fix all bugs found by the breaker.

        Returns the fixed code.
        """
        # Format bugs for the fixer
        bug_list = []
        for i, bug in enumerate(bugs, 1):
            bug_list.append(
                f"{i}. [{bug.severity.upper()}] {bug.category}: {bug.description}\n"
                f"   Location: {bug.location}\n"
                f"   Fix: {bug.fix_suggestion}"
            )

        fixer_prompt = f"""You are a code fixer. The breaker found these bugs in the code:

BUGS TO FIX:
{chr(10).join(bug_list)}

Fix ALL bugs, prioritizing CRITICAL first, then MAJOR, then MINOR.
Keep what works. Fix what's broken. Return the complete fixed code.

ORIGINAL CODE:
{generated_code[:8000]}

SPEC (for reference):
{spec_markdown[:1000]}

Return the complete fixed code:"""

        messages = [
            {"role": "system", "content": "You are a code fixer. Fix all bugs found by the breaker. Return complete code."},
            {"role": "user", "content": fixer_prompt},
        ]

        fixed_code = await self.call_model_fn("deepseek-v4-pro", messages, max_tokens=12000)
        return fixed_code

    async def verify(self, generated_code: str, intent_category: str, spec_markdown: str,
                     max_cycles: int = 2) -> AdversarialResult:
        """Full adversarial verification cycle: break → fix → verify.

        Runs up to max_cycles break-fix loops until no critical bugs remain.

        Returns AdversarialResult with all bugs found and fixed code.
        """
        all_bugs_found = []
        all_bugs_fixed = []
        current_code = generated_code

        for cycle in range(max_cycles):
            # Step 1: Break the code
            bugs = await self.break_code(current_code, intent_category)
            all_bugs_found.extend(bugs)

            # Check if there are critical bugs
            critical_bugs = [b for b in bugs if b.severity == "critical"]
            if not critical_bugs and cycle > 0:
                # No critical bugs and we've done at least one cycle — done
                break

            if not bugs:
                # No bugs at all — done
                break

            # Step 2: Fix the bugs
            fixed_code = await self.fix_bugs(current_code, bugs, spec_markdown)
            if fixed_code and not fixed_code.startswith("[ERROR"):
                all_bugs_fixed.extend(bugs)
                current_code = fixed_code
            else:
                # Fixer failed — keep current code
                break

        # Check if all critical bugs are fixed
        unfixed = [b for b in all_bugs_found if b not in all_bugs_fixed]
        critical_unfixed = [b for b in unfixed if b.severity == "critical"]

        return AdversarialResult(
            bugs_found=all_bugs_found,
            bugs_fixed=all_bugs_fixed,
            unfixed_bugs=unfixed,
            fixed_code=current_code,
            iterations=max_cycles,
            all_critical_fixed=len(critical_unfixed) == 0,
        )

    def get_summary(self, result: AdversarialResult) -> str:
        """Get human-readable summary of adversarial verification."""
        lines = [
            "Adversarial Verification Summary:",
            f"  Total bugs found: {len(result.bugs_found)}",
            f"  Bugs fixed: {len(result.bugs_fixed)}",
            f"  Unfixed bugs: {len(result.unfixed_bugs)}",
            f"  All critical fixed: {result.all_critical_fixed}",
            f"  Iterations: {result.iterations}",
            "",
        ]

        # Bug breakdown by severity
        critical = [b for b in result.bugs_found if b.severity == "critical"]
        major = [b for b in result.bugs_found if b.severity == "major"]
        minor = [b for b in result.bugs_found if b.severity == "minor"]
        lines.append(f"  By severity: {len(critical)} critical, {len(major)} major, {len(minor)} minor")

        if result.unfixed_bugs:
            lines.append("\n  UNFIXED BUGS:")
            for bug in result.unfixed_bugs[:5]:
                lines.append(f"    [{bug.severity}] {bug.description}")

        return "\n".join(lines)