"""
Persistent Notes — NOTES.md that survives across iterations.

From Anthropic's context engineering article:
"Structured note-taking, or agentic memory, is a technique where the agent regularly
writes notes persisted to memory outside of the context window."

From Fable 5's capabilities:
"giving it access to persistent file-based memory improved its performance three times
more than for Opus 4.8"

This module maintains a NOTES.md file across iterations of the generation loop.
Each iteration:
1. Reads notes from previous iterations
2. Uses them to avoid repeating mistakes
3. Writes new notes about what was tried and what happened

This is what makes the loop get BETTER with each iteration, not just repeat.
"""
import os
from datetime import datetime
from dataclasses import dataclass, field


@dataclass
class IterationNote:
    """A single note from one iteration."""
    iteration: int
    timestamp: str
    what_was_tried: str       # What approach was used
    what_worked: str          # What succeeded
    what_failed: str          # What didn't work
    bugs_found: list          # Bugs/issues found
    quality_score: float     # Quality score achieved
    key_decisions: list       # Important decisions made
    lessons_learned: str      # What to do differently next time


class PersistentNotes:
    """Maintains NOTES.md across iterations of the generation loop."""

    def __init__(self, notes_dir: str = None, session_id: str = None):
        if notes_dir is None:
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            notes_dir = os.path.join(base, "config", "ui_ux_memory", "iteration_notes")
        self.notes_dir = notes_dir
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.notes_path = os.path.join(notes_dir, f"NOTES_{self.session_id}.md")
        os.makedirs(notes_dir, exist_ok=True)

        # Initialize notes file
        if not os.path.isfile(self.notes_path):
            self._init_notes_file()

    def _init_notes_file(self):
        """Initialize the NOTES.md file with header."""
        header = f"""# Temuclaude UI/UX Generation — Iteration Notes
## Session: {self.session_id}

This file persists across iterations of the generation loop.
Each iteration reads previous notes to avoid repeating mistakes and builds on successes.

---
"""
        with open(self.notes_path, "w") as f:
            f.write(header)

    def read_notes(self) -> str:
        """Read all notes from previous iterations."""
        if not os.path.isfile(self.notes_path):
            return ""
        with open(self.notes_path, "r") as f:
            return f.read()

    def get_previous_lessons(self) -> str:
        """Get lessons learned from previous iterations.

        Returns a summary string of what to do differently, based on past notes.
        """
        content = self.read_notes()
        if not content or "## Iteration" not in content:
            return ""

        # Extract lessons from all iterations
        lessons = []
        sections = content.split("## Iteration")
        for section in sections[1:]:  # Skip header
            # Find lessons learned section
            if "Lessons:" in section:
                lesson_start = section.find("Lessons:") + len("Lessons:")
                lesson_end = section.find("---", lesson_start)
                if lesson_end == -1:
                    lesson_text = section[lesson_start:].strip()
                else:
                    lesson_text = section[lesson_start:lesson_end].strip()
                if lesson_text:
                    lessons.append(lesson_text)

        if not lessons:
            return ""

        return "PREVIOUS ITERATION LESSONS:\n" + "\n---\n".join(lessons[-3:])  # Last 3 iterations

    def get_previous_failures(self) -> list:
        """Get list of things that failed in previous iterations."""
        content = self.read_notes()
        if not content:
            return []

        failures = []
        sections = content.split("## Iteration")
        for section in sections[1:]:
            if "Failed:" in section:
                fail_start = section.find("Failed:") + len("Failed:")
                fail_end = section.find("\n", fail_start)
                if fail_end == -1:
                    fail_text = section[fail_start:].strip()
                else:
                    fail_text = section[fail_start:fail_end].strip()
                if fail_text and fail_text != "N/A":
                    failures.append(fail_text)

        return failures

    def write_iteration_note(self, note: IterationNote) -> None:
        """Write a note for the current iteration."""
        entry = f"""
## Iteration {note.iteration}
**Time:** {note.timestamp}
**Quality Score:** {note.quality_score:.2f}/1.0

### What Was Tried
{note.what_was_tried}

### What Worked
{note.what_worked}

### What Failed
{note.what_failed}

### Bugs Found
"""
        for bug in note.bugs_found:
            entry += f"- {bug}\n"

        if not note.bugs_found:
            entry += "(none)\n"

        entry += f"""
### Key Decisions
"""
        for decision in note.key_decisions:
            entry += f"- {decision}\n"

        if not note.key_decisions:
            entry += "(none)\n"

        entry += f"""
### Lessons: What to Do Differently Next Time
{note.lessons_learned}

---
"""
        with open(self.notes_path, "a") as f:
            f.write(entry)

    def build_context_for_iteration(self, iteration: int) -> str:
        """Build context string from previous notes for the current iteration.

        This is injected into the generation prompt so the model knows
        what was tried before and what to avoid.
        """
        if iteration == 1:
            return "This is the first iteration — no previous notes."

        lessons = self.get_previous_lessons()
        failures = self.get_previous_failures()

        if not lessons and not failures:
            return f"No specific lessons from previous {iteration - 1} iterations."

        lines = [f"CONTEXT FROM PREVIOUS {iteration - 1} ITERATION(S):", ""]

        if lessons:
            lines.append(lessons)
            lines.append("")

        if failures:
            lines.append("THINGS THAT FAILED (avoid repeating):")
            for f in failures[-5:]:  # Last 5 failures
                lines.append(f"  - {f}")
            lines.append("")

        lines.append("Use this context to avoid repeating mistakes and build on what worked.")
        return "\n".join(lines)

    def create_note_from_result(
        self,
        iteration: int,
        what_was_tried: str,
        quality_score: float,
        what_worked: str = "",
        what_failed: str = "",
        bugs_found: list = None,
        key_decisions: list = None,
        lessons_learned: str = "",
    ) -> IterationNote:
        """Create and save an IterationNote from loop results."""
        note = IterationNote(
            iteration=iteration,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            what_was_tried=what_was_tried,
            what_worked=what_worked or "N/A",
            what_failed=what_failed or "N/A",
            bugs_found=bugs_found or [],
            quality_score=quality_score,
            key_decisions=key_decisions or [],
            lessons_learned=lessons_learned or "N/A",
        )
        self.write_iteration_note(note)
        return note