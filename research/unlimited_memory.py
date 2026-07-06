#!/usr/bin/env python3
"""
Unlimited Memory — permanent searchable knowledge base.
Everything that ever happens is stored here, forever. Never deleted.
"""

import json, os, sqlite3
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, List

STORE_DIR = Path(os.environ.get("MEMORY_STORE_DIR",
    f"{os.environ.get('TEMUCLAUDE_DIR', '/Users/saiful/temuclaude')}/research/memory_store"))
STORE_DIR.mkdir(exist_ok=True)
DB_FILE = STORE_DIR / "swarm_memory.db"
ARCHIVE_DIR = STORE_DIR / "archives"
ARCHIVE_DIR.mkdir(exist_ok=True)

def _get_db():
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = _get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            category TEXT NOT NULL,
            daemon TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT,
            importance INTEGER DEFAULT 5,
            search_text TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_category ON memories(category);
        CREATE INDEX IF NOT EXISTS idx_daemon ON memories(daemon);
        CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp);
        CREATE INDEX IF NOT EXISTS idx_search ON memories(search_text);
    """)
    conn.commit()
    conn.close()

def remember(category, daemon, title, content, tags=None, importance=5):
    init_db()
    conn = _get_db()
    tags_str = ",".join(tags or [])
    search_text = f"{title} {json.dumps(content)} {tags_str}".lower()
    conn.execute("""INSERT INTO memories (timestamp, category, daemon, title, content, tags, importance, search_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (datetime.now(timezone.utc).isoformat(), category, daemon, title, json.dumps(content), tags_str, importance, search_text))
    conn.commit()
    conn.close()

def recall(query=None, category=None, daemon=None, tags=None, limit=20, since=None):
    init_db()
    conn = _get_db()
    sql = "SELECT * FROM memories WHERE 1=1"
    params = []
    if query:
        sql += " AND search_text LIKE ?"
        params.append(f"%{query.lower()}%")
    if category:
        sql += " AND category = ?"
        params.append(category)
    if daemon:
        sql += " AND daemon = ?"
        params.append(daemon)
    if since:
        sql += " AND timestamp >= ?"
        params.append(since)
    sql += " ORDER BY importance DESC, timestamp DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [{"id": r["id"], "timestamp": r["timestamp"], "category": r["category"],
             "daemon": r["daemon"], "title": r["title"], "content": json.loads(r["content"]),
             "tags": r["tags"].split(",") if r["tags"] else [], "importance": r["importance"]} for r in rows]

def recall_one(query, category=None):
    results = recall(query=query, category=category, limit=1)
    return results[0] if results else None

def get_stats():
    init_db()
    conn = _get_db()
    total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    by_cat = {}
    for row in conn.execute("SELECT category, COUNT(*) as c FROM memories GROUP BY category"):
        by_cat[row["category"]] = row["c"]
    conn.close()
    return {"total_memories": total, "by_category": by_cat}

def get_context_for_decision(decision_type, topic):
    return {"similar_past": recall(query=topic, category=decision_type, limit=5),
            "related": recall(query=topic, limit=10), "stats": get_stats()}

if __name__ == "__main__":
    init_db()
    print(json.dumps(get_stats(), indent=2))
