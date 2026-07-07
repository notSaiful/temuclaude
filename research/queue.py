#!/usr/bin/env python3
"""
Queue wrapper — re-exports from queue_utils.py for backward compatibility.
Many daemon scripts import 'from queue import pop_implementation, ...'
but the actual implementation is in queue_utils.py.
"""
import json
from queue_utils import (
    QueueManager,
    push_raw_file,
    pop_raw_file,
    push_findings,
    pop_findings,
    push_implementation,
    pop_implementation,
    mark_implementation_complete,
)

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