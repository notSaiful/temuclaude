#!/usr/bin/env python3
"""
Website Updater — scans codebase, extracts current state, updates website.
"""

import json, os, sys, subprocess, re
from pathlib import Path
from datetime import datetime, timezone

TEMUCLAUDE = Path(os.environ.get("TEMUCLAUDE_DIR", "/Users/saiful/temuclaude"))
WEBSITE_DIR = TEMUCLAUDE / "website"
LANDING_PAGE = TEMUCLAUDE / "landing_page.html"
DB_FILE = WEBSITE_DIR / "temuclaude-db.json"

def get_current_features() -> list:
    features = []
    src_dir = TEMUCLAUDE / "src"
    if src_dir.exists():
        for pyfile in sorted(src_dir.glob("*.py")):
            if pyfile.stem.startswith("_"):
                continue
            features.append({
                "name": pyfile.stem.replace("_", " ").title(),
                "module": pyfile.stem,
                "description": f"{pyfile.stem} module"
            })
    return features

def get_test_count() -> dict:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "--co", "-q"],
            capture_output=True, text=True, timeout=60, cwd=TEMUCLAUDE
        )
        for line in result.stdout.split("\n"):
            if "test" in line.lower() and ("collected" in line.lower() or "passed" in line.lower()):
                return {"raw": line.strip()}
    except Exception:
        pass
    return {"raw": "unknown"}

def get_git_stats() -> dict:
    try:
        count = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            capture_output=True, text=True, cwd=TEMUCLAUDE
        ).stdout.strip()
        last = subprocess.run(
            ["git", "log", "-1", "--oneline"],
            capture_output=True, text=True, cwd=TEMUCLAUDE
        ).stdout.strip()
        return {"total_commits": count, "last_commit": last}
    except Exception:
        return {"total_commits": "0", "last_commit": ""}

def get_model_pool() -> list:
    config_file = TEMUCLAUDE / "config" / "litellm.yaml"
    if not config_file.exists():
        return []
    content = config_file.read_text()
    models = re.findall(r"model:\s*(.+)", content)
    return [m.strip().strip("'\"") for m in models]

def update_db_file(features, tests, git_stats, models):
    db = {
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "feature_count": len(features),
        "features": features,
        "test_stats": tests,
        "git_stats": git_stats,
        "model_pool": models,
        "model_count": len(models),
    }
    if DB_FILE.exists():
        try:
            with open(DB_FILE) as f:
                existing = json.load(f)
            existing.update(db)
            db = existing
        except Exception:
            pass
    with open(DB_FILE, 'w') as f:
        json.dump(db, f, indent=2)
    return db

def update_landing_page(db):
    if not LANDING_PAGE.exists():
        return False
    content = LANDING_PAGE.read_text()
    changed = False
    if "features" in content.lower():
        new_count = str(db["feature_count"])
        new_content = re.sub(r'\d+\s+(features|modules|components)', f'{new_count} \\1', content, count=5)
        if new_content != content:
            content = new_content
            changed = True
    if "model" in content.lower():
        new_models = str(db["model_count"])
        new_content = re.sub(r'\d+\s+(models|model pool)', f'{new_models} \\1', content, count=5)
        if new_content != content:
            content = new_content
            changed = True
    if changed:
        LANDING_PAGE.write_text(content)
    return changed

def deploy_to_vercel() -> bool:
    try:
        result = subprocess.run(
            ["npx", "vercel", "--prod", "--yes"],
            capture_output=True, text=True, timeout=300, cwd=WEBSITE_DIR
        )
        return result.returncode == 0
    except Exception:
        return False

if __name__ == "__main__":
    features = get_current_features()
    tests = get_test_count()
    git_stats = get_git_stats()
    models = get_model_pool()
    db = update_db_file(features, tests, git_stats, models)
    landing_changed = update_landing_page(db)
    print(f"Features: {len(features)}, Models: {len(models)}, Tests: {tests}")
    print(f"Landing page updated: {landing_changed}")
