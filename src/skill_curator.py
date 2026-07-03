"""
Timuclaude Skill Curator
Background maintenance for the skill library — prevents skill bloat.

Based on Hermes Agent's Curator pattern:
- Usage tracking: which skills are actually used
- Staleness detection: skills that haven't been used in N days
- Archival: move stale skills to archive
- LLM-driven review: periodically review skills for quality
- Size limits: skills ≤15KB (Hermes pattern)

This module is called periodically (not on every query) to maintain the skill library.
"""
import json
import os
import time
from typing import Optional
from datetime import datetime, timezone


SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "skills")
USAGE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "skill_usage.json")
ARCHIVE_DIR = os.path.join(SKILLS_DIR, "archive")

# Skills not used in 30 days get archived
STALENESS_THRESHOLD_DAYS = 30

# Skills larger than 15KB get flagged for review (Hermes pattern)
SIZE_LIMIT_KB = 15


def load_usage_data() -> dict:
    """Load skill usage tracking data."""
    if not os.path.isfile(USAGE_FILE):
        return {}
    try:
        with open(USAGE_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_usage_data(data: dict) -> None:
    """Save skill usage tracking data."""
    os.makedirs(os.path.dirname(USAGE_FILE), exist_ok=True)
    with open(USAGE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def track_skill_usage(skill_name: str) -> None:
    """Record that a skill was used (called by orchestrator when loading a skill)."""
    data = load_usage_data()
    if skill_name not in data:
        data[skill_name] = {
            "use_count": 0,
            "first_used": datetime.now(timezone.utc).isoformat(),
            "last_used": datetime.now(timezone.utc).isoformat(),
        }
    data[skill_name]["use_count"] += 1
    data[skill_name]["last_used"] = datetime.now(timezone.utc).isoformat()
    save_usage_data(data)


def get_stale_skills() -> list:
    """Find skills that haven't been used in STALENESS_THRESHOLD_DAYS days."""
    data = load_usage_data()
    now = datetime.now(timezone.utc)
    stale = []
    
    for skill_name, usage in data.items():
        last_used_str = usage.get("last_used", "")
        if not last_used_str:
            continue
        try:
            last_used = datetime.fromisoformat(last_used_str)
            days_since = (now - last_used).days
            if days_since >= STALENESS_THRESHOLD_DAYS:
                stale.append({
                    "name": skill_name,
                    "days_since_use": days_since,
                    "use_count": usage.get("use_count", 0),
                })
        except (ValueError, TypeError):
            continue
    
    return stale


def get_oversized_skills() -> list:
    """Find skills that exceed the size limit."""
    if not os.path.isdir(SKILLS_DIR):
        return []
    
    oversized = []
    for item in os.listdir(SKILLS_DIR):
        skill_path = os.path.join(SKILLS_DIR, item, "SKILL.md")
        if os.path.isfile(skill_path):
            size_bytes = os.path.getsize(skill_path)
            size_kb = size_bytes / 1024
            if size_kb > SIZE_LIMIT_KB:
                oversized.append({
                    "name": item,
                    "size_kb": round(size_kb, 1),
                    "limit_kb": SIZE_LIMIT_KB,
                })
    
    return oversized


def archive_stale_skills() -> dict:
    """Move stale skills to archive directory."""
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    stale = get_stale_skills()
    
    archived = []
    for skill in stale:
        skill_name = skill["name"]
        skill_dir = os.path.join(SKILLS_DIR, skill_name)
        archive_dest = os.path.join(ARCHIVE_DIR, skill_name)
        
        if os.path.isdir(skill_dir) and not os.path.isdir(archive_dest):
            try:
                import shutil
                shutil.move(skill_dir, archive_dest)
                archived.append(skill_name)
            except (IOError, OSError) as e:
                print(f"Warning: Could not archive {skill_name}: {e}")
    
    return {
        "archived": archived,
        "count": len(archived),
        "stale_found": len(stale),
    }


def run_curation() -> dict:
    """Run full curation cycle: check staleness, check sizes, archive stale."""
    stale = get_stale_skills()
    oversized = get_oversized_skills()
    archive_result = archive_stale_skills()
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stale_skills": stale,
        "oversized_skills": oversized,
        "archived": archive_result,
        "recommendations": [
            f"Review {len(oversized)} oversized skills (>{SIZE_LIMIT_KB}KB)" if oversized else "",
            f"Archived {archive_result['count']} stale skills" if archive_result["count"] > 0 else "",
        ],
    }


if __name__ == "__main__":
    result = run_curation()
    print(json.dumps(result, indent=2))