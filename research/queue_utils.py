#!/usr/bin/env python3
"""
Queue management for Temuclaude Research Swarm.
Inter-daemon communication via filesystem queue.
"""

import json
import os
import fcntl
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

QUEUE_FILE = Path("/Users/saiful/temuclaude/research/queue.json")
QUEUE_LOCK_FILE = Path("/Users/saiful/temuclaude/research/queue.lock")


class QueueManager:
    """Thread/process-safe queue for daemon coordination."""
    
    def __init__(self):
        self.queue_file = QUEUE_FILE
        self.lock_file = QUEUE_LOCK_FILE
        self._ensure_queue()
    
    def _ensure_queue(self):
        """Initialize queue file if not exists."""
        if not self.queue_file.exists():
            self._write_queue({
                "new_raw": [],
                "new_findings": [],
                "research_requests": [],
                "research_complete": [],
                "implementation_queue": [],
                "implementation_complete": [],
                "implementation_failed": [],
                "priority_updates": [],
                "last_updated": datetime.now(timezone.utc).isoformat()
            })
    
    def _acquire_lock(self):
        """Acquire file lock."""
        self.lock_fd = open(self.lock_file, 'w')
        fcntl.flock(self.lock_fd, fcntl.LOCK_EX)
    
    def _release_lock(self):
        """Release file lock."""
        fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
        self.lock_fd.close()
    
    def _read_queue(self) -> Dict:
        """Read queue (with lock)."""
        self._acquire_lock()
        try:
            with open(self.queue_file) as f:
                return json.load(f)
        finally:
            self._release_lock()
    
    def _write_queue(self, data: Dict):
        """Write queue (with lock)."""
        self._acquire_lock()
        try:
            data["last_updated"] = datetime.now(timezone.utc).isoformat()
            with open(self.queue_file, 'w') as f:
                json.dump(data, f, indent=2)
        finally:
            self._release_lock()
    
    def push(self, queue_name: str, items: List[Any]):
        """Add items to a queue."""
        q = self._read_queue()
        if queue_name not in q:
            q[queue_name] = []
        q[queue_name].extend(items)
        self._write_queue(q)
    
    def pop(self, queue_name: str, max_items: int = 1) -> List[Any]:
        """Pop items from a queue."""
        q = self._read_queue()
        items = q.get(queue_name, [])
        if not items:
            return []
        popped = items[:max_items]
        q[queue_name] = items[max_items:]
        self._write_queue(q)
        return popped
    
    def peek(self, queue_name: str) -> List[Any]:
        """View queue without removing."""
        q = self._read_queue()
        return q.get(queue_name, [])
    
    def clear(self, queue_name: str):
        """Clear a queue."""
        q = self._read_queue()
        q[queue_name] = []
        self._write_queue(q)
    
    def size(self, queue_name: str) -> int:
        """Get queue size."""
        q = self._read_queue()
        return len(q.get(queue_name, []))
    
    def get_all(self) -> Dict:
        """Get entire queue state."""
        return self._read_queue()
    
    def update_priorities(self, priorities: Dict):
        """Update priority queue."""
        self.push("priority_updates", [priorities])


# Convenience functions
def push_raw_file(filename: str):
    """Notify distiller of new raw file."""
    QueueManager().push("new_raw", [filename])

def pop_raw_file() -> Optional[str]:
    """Get next raw file to process."""
    items = QueueManager().pop("new_raw", 1)
    return items[0] if items else None

def push_findings(filenames: List[str]):
    """Notify research daemons of new findings."""
    QueueManager().push("new_findings", filenames)

def pop_findings(max_items: int = 1) -> List[str]:
    """Get findings to research."""
    return QueueManager().pop("new_findings", max_items)

def push_implementation(finding_files: List[str]):
    """Queue findings for implementation."""
    QueueManager().push("implementation_queue", finding_files)

def pop_implementation() -> Optional[str]:
    """Get next implementation task."""
    items = QueueManager().pop("implementation_queue", 1)
    return items[0] if items else None

def mark_implementation_complete(filename: str, success: bool):
    """Mark implementation done."""
    qm = QueueManager()
    if success:
        qm.push("implementation_complete", [filename])
    else:
        qm.push("implementation_failed", [filename])


if __name__ == "__main__":
    import sys
    qm = QueueManager()
    if len(sys.argv) > 1:
        if sys.argv[1] == "status":
            print(json.dumps(qm.get_all(), indent=2))
        elif sys.argv[1] == "clear" and len(sys.argv) > 2:
            qm.clear(sys.argv[2])
            print(f"Cleared {sys.argv[2]}")
    else:
        print(json.dumps(qm.get_all(), indent=2))