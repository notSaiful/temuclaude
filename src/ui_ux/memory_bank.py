"""
Memory Bank — Persists decisions, patterns, failures across sessions.

Research finding (Section 5.2):
- Memory bank = NOTES.md + vector DB for pattern reuse across sessions
- Structured note-taking: Agent writes NOTES.md / TODO.md; reads back on resume
- Pattern library from successful generations (vector DB)

This module implements file-based memory (NOTES.md pattern) with
pattern persistence for reuse across sessions.
"""
import os
import json
import hashlib
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Pattern:
    """A reusable pattern from a successful generation."""
    pattern_id: str          # Unique hash
    intent_category: str     # game_3d, physics_demo, etc.
    prompt_hash: str         # Hash of the original prompt
    spec_summary: str        # Brief spec summary
    generation_summary: str  # What was generated
    quality_score: float     # Quality gate score (0-1)
    iterations: int          # How many loop iterations were needed
    techniques_used: list    # Which quality gates passed
    timestamp: str           # When this was saved
    success: bool            # Whether the generation succeeded


class MemoryBank:
    """Persists generation patterns and notes across sessions."""

    def __init__(self, memory_dir: str = None):
        if memory_dir is None:
            memory_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "config", "ui_ux_memory"
            )
        self.memory_dir = memory_dir
        self.notes_path = os.path.join(memory_dir, "NOTES.md")
        self.patterns_path = os.path.join(memory_dir, "patterns.json")
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Ensure memory directory exists."""
        os.makedirs(self.memory_dir, exist_ok=True)

    def _hash_prompt(self, prompt: str) -> str:
        """Hash a prompt for deduplication and pattern matching."""
        return hashlib.sha256(prompt.encode()).hexdigest()[:16]

    def save_note(self, note: str, category: str = "general") -> None:
        """Save a note to NOTES.md.

        Args:
            note: The note content
            category: Note category (decision, failure, success, pattern)
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        entry = f"\n## [{category}] {timestamp}\n{note}\n"

        # Create file with header if it doesn't exist
        if not os.path.isfile(self.notes_path):
            with open(self.notes_path, "w") as f:
                f.write("# Temuclaude UI/UX Generation — Memory Bank\n")
                f.write("This file persists decisions, patterns, and lessons across sessions.\n")

        with open(self.notes_path, "a") as f:
            f.write(entry)

    def load_notes(self) -> str:
        """Load all notes from NOTES.md."""
        if not os.path.isfile(self.notes_path):
            return ""
        with open(self.notes_path, "r") as f:
            return f.read()

    def save_pattern(self, pattern: Pattern) -> None:
        """Save a successful generation pattern for future reuse.

        Args:
            pattern: Pattern object with generation details
        """
        patterns = self.load_patterns()
        patterns[pattern.pattern_id] = {
            "intent_category": pattern.intent_category,
            "prompt_hash": pattern.prompt_hash,
            "spec_summary": pattern.spec_summary,
            "generation_summary": pattern.generation_summary,
            "quality_score": pattern.quality_score,
            "iterations": pattern.iterations,
            "techniques_used": pattern.techniques_used,
            "timestamp": pattern.timestamp,
            "success": pattern.success,
        }

        with open(self.patterns_path, "w") as f:
            json.dump(patterns, f, indent=2)

        # Also save a note
        note = (
            f"Pattern saved: {pattern.intent_category} | "
            f"Quality: {pattern.quality_score:.2f} | "
            f"Iterations: {pattern.iterations} | "
            f"Techniques: {', '.join(pattern.techniques_used)}"
        )
        self.save_note(note, "pattern")

    def load_patterns(self) -> dict:
        """Load all saved patterns."""
        if not os.path.isfile(self.patterns_path):
            return {}
        try:
            with open(self.patterns_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def find_similar_patterns(self, intent_category: str, limit: int = 5) -> list:
        """Find patterns matching an intent category.

        Args:
            intent_category: The intent to match
            limit: Max patterns to return

        Returns:
            List of pattern dicts sorted by quality score
        """
        patterns = self.load_patterns()
        matching = [
            p for p in patterns.values()
            if p.get("intent_category") == intent_category and p.get("success", False)
        ]
        # Sort by quality score (highest first)
        matching.sort(key=lambda p: p.get("quality_score", 0), reverse=True)
        return matching[:limit]

    def find_pattern_by_prompt(self, prompt: str) -> Optional[dict]:
        """Find a pattern by exact prompt hash.

        Returns:
            Pattern dict if found, None otherwise
        """
        prompt_hash = self._hash_prompt(prompt)
        patterns = self.load_patterns()
        for p in patterns.values():
            if p.get("prompt_hash") == prompt_hash:
                return p
        return None

    def get_stats(self) -> dict:
        """Get memory bank statistics."""
        patterns = self.load_patterns()
        total = len(patterns)
        successful = sum(1 for p in patterns.values() if p.get("success", False))
        avg_quality = 0.0
        if successful > 0:
            avg_quality = sum(
                p.get("quality_score", 0) for p in patterns.values() if p.get("success", False)
            ) / successful

        # Count by category
        by_category = {}
        for p in patterns.values():
            cat = p.get("intent_category", "unknown")
            by_category[cat] = by_category.get(cat, 0) + 1

        return {
            "total_patterns": total,
            "successful_patterns": successful,
            "success_rate": round(successful / total * 100, 1) if total > 0 else 0,
            "avg_quality_score": round(avg_quality, 2),
            "patterns_by_category": by_category,
            "notes_exists": os.path.isfile(self.notes_path),
        }

    def create_pattern_from_result(self, intent, spec, result) -> Pattern:
        """Create a Pattern object from a generation result.

        Args:
            intent: Classified Intent
            spec: Generated Spec
            result: GenerationResult from loop_engine

        Returns:
            Pattern object ready to save
        """
        pattern_id = self._hash_prompt(intent.raw_prompt + intent.category)
        return Pattern(
            pattern_id=pattern_id,
            intent_category=intent.category,
            prompt_hash=self._hash_prompt(intent.raw_prompt),
            spec_summary=spec.markdown[:500],
            generation_summary=result.generated_code[:500] if hasattr(result, 'generated_code') else str(result)[:500],
            quality_score=result.quality_score if hasattr(result, 'quality_score') else 0.5,
            iterations=result.iterations if hasattr(result, 'iterations') else 1,
            techniques_used=result.techniques_passed if hasattr(result, 'techniques_passed') else [],
            timestamp=datetime.now(timezone.utc).isoformat(),
            success=result.success if hasattr(result, 'success') else True,
        )