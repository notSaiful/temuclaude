"""
Temuclaude Media Memory Bank

Stores which image/video models win for which prompt types.
Over time, learns: "For photoreal prompts, FLUX.2 Max wins 45% of the time."
Feeds back into adaptive routing to improve model selection.

Adapted from ui_ux/memory_bank.py.
"""

import json
import os
import time
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Default storage path
MEMORY_DIR = Path(__file__).parent.parent.parent / "data" / "media_memory"
MEMORY_FILE = MEMORY_DIR / "patterns.json"


class MediaMemoryBank:
    """Persistent memory of which models win for which task types.

    Stores:
      - Per task_type: model_id → {wins, total, avg_score, win_rate}
      - Per model: total generations, total wins, avg score
      - Overall stats: total generations, cache hits, avg iterations

    This data feeds back into adaptive routing:
      - If model A wins 60% of photoreal prompts, route more photoreal to A
      - If model B always fails on text_in_image, don't use B for text_in_image
    """

    def __init__(self, memory_file: Path = None):
        self.memory_file = memory_file or MEMORY_FILE
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)
        self._cache = None
        self._load()

    def _load(self):
        """Load patterns from disk."""
        try:
            if self.memory_file.exists():
                with open(self.memory_file, "r") as f:
                    self._cache = json.load(f)
            else:
                self._cache = self._default_structure()
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load media memory: {e}")
            self._cache = self._default_structure()

    def _default_structure(self) -> dict:
        """Return the default empty memory structure."""
        return {
            "task_types": {},  # task_type → {model_id → stats}
            "models": {},      # model_id → overall stats
            "overall": {
                "total_generations": 0,
                "total_wins": 0,
                "cache_hits": 0,
                "total_cost": 0.0,
                "avg_score": 0.0,
                "avg_iterations": 0.0,
                "last_updated": 0,
            },
        }

    def _save(self):
        """Save patterns to disk."""
        try:
            self._cache["overall"]["last_updated"] = time.time()
            with open(self.memory_file, "w") as f:
                json.dump(self._cache, f, indent=2)
        except IOError as e:
            logger.warning(f"Failed to save media memory: {e}")

    def record_generation(
        self,
        task_type: str,
        models_used: list,
        winner: str,
        scores: dict,
        cost: float = 0.0,
        iterations: int = 1,
        cache_hit: bool = False,
    ):
        """Record a generation result.

        Args:
            task_type: Classified task type (e.g., "photoreal")
            models_used: List of model IDs that were attempted
            winner: Model ID that won (highest score)
            scores: Dict of model_id → consensus_score
            cost: Total cost of this generation
            iterations: Number of refine iterations used
            cache_hit: Whether this was a cache hit (no generation needed)
        """
        if cache_hit:
            self._cache["overall"]["cache_hits"] += 1
            self._save()
            return

        # Update overall stats
        overall = self._cache["overall"]
        overall["total_generations"] += 1
        overall["total_cost"] += cost
        overall["avg_score"] = (
            (overall["avg_score"] * (overall["total_generations"] - 1) +
             max(scores.values()) if scores else 0.0
            ) / overall["total_generations"]
        )
        overall["avg_iterations"] = (
            (overall["avg_iterations"] * (overall["total_generations"] - 1) + iterations)
            / overall["total_generations"]
        )

        # Update per-task-type stats
        if task_type not in self._cache["task_types"]:
            self._cache["task_types"][task_type] = {}

        task_stats = self._cache["task_types"][task_type]

        for model_id in models_used:
            if model_id not in task_stats:
                task_stats[model_id] = {
                    "wins": 0,
                    "total": 0,
                    "avg_score": 0.0,
                    "win_rate": 0.0,
                }

            stats = task_stats[model_id]
            stats["total"] += 1
            if model_id == winner:
                stats["wins"] += 1

            # Update rolling average score
            model_score = scores.get(model_id, 0.0)
            stats["avg_score"] = (
                (stats["avg_score"] * (stats["total"] - 1) + model_score)
                / stats["total"]
            )
            stats["win_rate"] = stats["wins"] / stats["total"] if stats["total"] > 0 else 0.0

        # Update per-model overall stats
        for model_id in models_used:
            if model_id not in self._cache["models"]:
                self._cache["models"][model_id] = {
                    "wins": 0,
                    "total": 0,
                    "avg_score": 0.0,
                }

            model_stats = self._cache["models"][model_id]
            model_stats["total"] += 1
            if model_id == winner:
                model_stats["wins"] += 1
            model_score = scores.get(model_id, 0.0)
            model_stats["avg_score"] = (
                (model_stats["avg_score"] * (model_stats["total"] - 1) + model_score)
                / model_stats["total"]
            )

        self._save()

    def get_model_stats(self, task_type: str) -> dict:
        """Get win rate stats for all models for a task type.

        Returns:
            Dict of model_id → {wins, total, avg_score, win_rate}
        """
        return self._cache.get("task_types", {}).get(task_type, {})

    def get_best_models(self, task_type: str, top_n: int = 3) -> list:
        """Get the top-N best models for a task type, sorted by win rate.

        Args:
            task_type: Task type to query
            top_n: Number of top models to return

        Returns:
            List of (model_id, win_rate, avg_score) tuples, sorted by win_rate desc.
        """
        task_stats = self.get_model_stats(task_type)

        # Sort by win rate, then by avg_score
        sorted_models = sorted(
            task_stats.items(),
            key=lambda x: (x[1].get("win_rate", 0), x[1].get("avg_score", 0)),
            reverse=True,
        )

        return [
            (model_id, stats.get("win_rate", 0), stats.get("avg_score", 0))
            for model_id, stats in sorted_models[:top_n]
        ]

    def get_overall_stats(self) -> dict:
        """Get overall memory bank statistics."""
        return self._cache.get("overall", {})

    def get_model_overall_stats(self) -> dict:
        """Get per-model overall stats across all task types."""
        return self._cache.get("models", {})

    def get_routing_recommendation(self, task_type: str, available_models: list) -> list:
        """Get a routing recommendation — sort available models by historical performance.

        Args:
            task_type: Task type to route for
            available_models: List of model IDs available in the current pool

        Returns:
            List of model IDs, sorted by historical win rate (best first).
            Models with no history are placed at the end (unknown performance).
        """
        task_stats = self.get_model_stats(task_type)

        # Sort available models by win rate
        def sort_key(model_id):
            stats = task_stats.get(model_id, {})
            win_rate = stats.get("win_rate", -1)  # -1 for unknown models
            avg_score = stats.get("avg_score", 0)
            return (win_rate, avg_score)

        return sorted(available_models, key=sort_key, reverse=True)

    def reset(self):
        """Reset all memory (for testing/debugging)."""
        self._cache = self._default_structure()
        self._save()

    def get_summary(self) -> dict:
        """Get a human-readable summary of the memory bank."""
        overall = self.get_overall_stats()
        task_types = self._cache.get("task_types", {})

        summary = {
            "total_generations": overall.get("total_generations", 0),
            "cache_hits": overall.get("cache_hits", 0),
            "total_cost": round(overall.get("total_cost", 0), 4),
            "avg_score": round(overall.get("avg_score", 0), 2),
            "avg_iterations": round(overall.get("avg_iterations", 0), 2),
            "task_types_tracked": len(task_types),
            "models_tracked": len(self._cache.get("models", {})),
        }

        # Top models per task type
        top_models = {}
        for task_type in task_types:
            top = self.get_best_models(task_type, top_n=1)
            if top:
                top_models[task_type] = {
                    "model": top[0][0],
                    "win_rate": round(top[0][1], 2),
                    "avg_score": round(top[0][2], 2),
                }

        summary["top_models_per_task"] = top_models
        return summary


# Singleton instance
_memory_bank: Optional[MediaMemoryBank] = None


def get_memory_bank() -> MediaMemoryBank:
    """Get the singleton memory bank instance."""
    global _memory_bank
    if _memory_bank is None:
        _memory_bank = MediaMemoryBank()
    return _memory_bank