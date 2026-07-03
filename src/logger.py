"""
Timuclaude Logger — Logs every query for self-improvement
"""
import json
import uuid
import time
import os
import threading
from datetime import datetime
from pathlib import Path


class QueryLogger:
    """Logs every query to JSONL file for analysis and self-improvement."""

    def __init__(self, log_dir: str = None) -> None:
        if log_dir is None:
            log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"queries_{datetime.now().strftime('%Y%m%d')}.jsonl"
        self._lock = threading.Lock()

    def log(
        self,
        user_query: str,
        task_type: str = None,
        routing_tier: str = None,
        models_used: list = None,
        strategy: str = None,
        responses: dict = None,
        final_answer: str = None,
        self_qa_score: int = None,
        confidence: float = None,
        latency_ms: int = None,
        cost_estimate: float = None,
        success: bool = True,
        error: str = None,
    ) -> str:
        """Log a query to the JSONL file."""
        entry = {
            "query_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "user_query": user_query,
            "task_type": task_type,
            "routing_tier": routing_tier,
            "models_used": models_used or [],
            "strategy": strategy,
            "responses": responses or {},
            "final_answer": final_answer,
            "self_qa_score": self_qa_score,
            "confidence": confidence,
            "latency_ms": latency_ms,
            "cost_estimate": cost_estimate,
            "success": success,
            "error": error,
        }
        with self._lock:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        return entry["query_id"]

    def get_recent(self, n: int = 100) -> list:
        """Get the N most recent queries."""
        if not self.log_file.exists():
            return []
        entries = []
        with open(self.log_file, "r") as f:
            for line in f:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return entries[-n:]