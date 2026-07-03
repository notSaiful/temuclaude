"""
Shared deduplication state for all scouts.
Persists seen IDs across runs to avoid re-fetching the same papers/repos/models.
"""
import json
import os
from datetime import datetime, timezone

STATE_DIR = os.path.join(os.path.dirname(__file__), "..", "raw")
STATE_FILE = os.path.join(STATE_DIR, "_seen_state.json")

def load_seen() -> dict:
    """Load the persistent seen-state across all scout types."""
    if not os.path.isfile(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_seen(state: dict) -> None:
    """Save the persistent seen-state."""
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def filter_new(items: list, scout_type: str, id_key: str = "id") -> list:
    """Filter out items that have already been seen by this scout type.
    
    Args:
        items: List of dicts with an id field
        scout_type: e.g. "arxiv", "github", "huggingface_papers", "huggingface_models"
        id_key: Key to use for deduplication (varies by scout type)
    
    Returns:
        Only items that haven't been seen before
    """
    state = load_seen()
    seen_set = set(state.get(scout_type, []))
    
    new_items = []
    new_ids = []
    for item in items:
        item_id = item.get(id_key, "")
        if not item_id:
            continue
        if item_id not in seen_set:
            new_items.append(item)
            new_ids.append(item_id)
            seen_set.add(item_id)
    
    # Update state with new IDs
    state[scout_type] = list(seen_set)
    
    # Prune: keep only last 5000 IDs per scout type to prevent unbounded growth
    if len(state[scout_type]) > 5000:
        state[scout_type] = state[scout_type][-5000:]
    
    # Add timestamp of last run
    state[f"{scout_type}_last_run"] = datetime.now(timezone.utc).isoformat()
    
    save_seen(state)
    
    return new_items

def get_seen_count(scout_type: str) -> int:
    """Get how many items this scout type has already seen."""
    state = load_seen()
    return len(state.get(scout_type, []))