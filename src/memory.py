"""
Temuclaude Persistent Memory Module
Cross-query memory — remember user preferences, context, facts across conversations.

Categories:
- user_profile: Who the user is (name, role, preferences)
- preferences: User's stated preferences
- context: Conversation context and background
- facts: Stable facts about the environment
- corrections: User corrections to previous responses

SQLite-backed for persistence. Keyword + LLM similarity for recall.
"""
import sqlite3
import os
import re
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional


DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "memory.db"
)


def _get_db_path() -> str:
    """Get the database path, creating config dir if needed."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return DB_PATH


def _init_db(conn: sqlite3.Connection) -> None:
    """Initialize the database schema."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            keywords TEXT,
            created_at TEXT NOT NULL,
            access_count INTEGER DEFAULT 0,
            last_accessed TEXT
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_category ON memories(category)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_keywords ON memories(keywords)
    """)
    conn.commit()


def _extract_keywords(text: str) -> List[str]:
    """Extract keywords from text for search indexing."""
    # Remove common stop words
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "must", "can",
        "to", "of", "in", "on", "at", "by", "for", "with", "about",
        "as", "from", "up", "down", "into", "through", "during",
        "and", "or", "but", "if", "then", "else", "when", "where",
        "why", "how", "all", "each", "every", "both", "few", "more",
        "most", "other", "some", "such", "no", "nor", "not", "only",
        "own", "same", "so", "than", "too", "very", "s", "t", "just",
    }
    words = re.findall(r'\b[a-z]{2,}\b', text.lower())
    keywords = [w for w in words if w not in stop_words]
    return keywords


class MemoryStore:
    """Persistent memory store backed by SQLite."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or _get_db_path()
        self._conn: Optional[sqlite3.Connection] = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            _init_db(self._conn)
        return self._conn

    def save(self, category: str, content: str) -> int:
        """Save a memory entry.

        Args:
            category: One of user_profile, preferences, context, facts, corrections
            content: The memory content

        Returns:
            The ID of the saved entry
        """
        keywords = json.dumps(_extract_keywords(content))
        now = datetime.now(timezone.utc).isoformat()

        cursor = self.conn.execute(
            "INSERT INTO memories (category, content, keywords, created_at, access_count, last_accessed) "
            "VALUES (?, ?, ?, ?, 0, ?)",
            (category, content, keywords, now, now)
        )
        self.conn.commit()
        return cursor.lastrowid

    def recall(self, query: str, limit: int = 5) -> List[Dict]:
        """Recall memories relevant to a query.

        Uses keyword overlap for matching.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of memory dicts: {id, category, content, score}
        """
        query_keywords = set(_extract_keywords(query))
        if not query_keywords:
            return []

        rows = self.conn.execute(
            "SELECT id, category, content, keywords FROM memories"
        ).fetchall()

        scored = []
        for row in rows:
            mem_id, category, content, keywords_json = row
            mem_keywords = set(json.loads(keywords_json)) if keywords_json else set()

            # Score = keyword overlap
            overlap = len(query_keywords & mem_keywords)
            if overlap > 0:
                score = overlap / max(len(query_keywords), 1)
                scored.append({
                    "id": mem_id,
                    "category": category,
                    "content": content,
                    "score": score,
                })

        scored.sort(key=lambda x: x["score"], reverse=True)

        # Update access count for recalled memories
        for mem in scored[:limit]:
            self.conn.execute(
                "UPDATE memories SET access_count = access_count + 1, "
                "last_accessed = ? WHERE id = ?",
                (datetime.now(timezone.utc).isoformat(), mem["id"])
            )
        self.conn.commit()

        return scored[:limit]

    def forget(self, content: str) -> int:
        """Remove memories matching the given content.

        Returns number of entries removed.
        """
        cursor = self.conn.execute(
            "DELETE FROM memories WHERE content LIKE ?",
            (f"%{content}%",)
        )
        self.conn.commit()
        return cursor.rowcount

    def forget_by_id(self, mem_id: int) -> bool:
        """Remove a memory by ID."""
        cursor = self.conn.execute("DELETE FROM memories WHERE id = ?", (mem_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def list_memories(self, category: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """List all memories, optionally filtered by category.

        Returns list of memory dicts.
        """
        if category:
            rows = self.conn.execute(
                "SELECT id, category, content, created_at, access_count "
                "FROM memories WHERE category = ? ORDER BY created_at DESC LIMIT ?",
                (category, limit)
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT id, category, content, created_at, access_count "
                "FROM memories ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()

        return [
            {
                "id": r[0],
                "category": r[1],
                "content": r[2],
                "created_at": r[3],
                "access_count": r[4],
            }
            for r in rows
        ]

    def clear_all(self) -> int:
        """Clear all memories. Returns count removed."""
        cursor = self.conn.execute("DELETE FROM memories")
        self.conn.commit()
        return cursor.rowcount

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None


def extract_memories_prompt(text: str) -> List[dict]:
    """Build a prompt to extract memories from a conversation.

    Args:
        text: Conversation text

    Returns:
        Messages for LLM
    """
    return [
        {"role": "system", "content": (
            "Extract durable facts from the conversation that should be remembered. "
            "For each fact, output a JSON array of objects with 'category' and 'content'. "
            "Categories: user_profile, preferences, context, facts, corrections. "
            "Only extract stable, reusable facts — not temporary details. "
            "Output ONLY the JSON array, no other text."
        )},
        {"role": "user", "content": text},
    ]


def parse_extracted_memories(raw: str) -> List[Dict]:
    """Parse LLM response into memory entries.

    Args:
        raw: LLM response text (JSON array)

    Returns:
        List of {category, content} dicts
    """
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [
                {"category": item.get("category", "context"),
                 "content": item.get("content", "")}
                for item in data if item.get("content")
            ]
    except (json.JSONDecodeError, TypeError):
        pass
    return []


# Module-level convenience functions
_store: Optional[MemoryStore] = None


def get_store() -> MemoryStore:
    """Get the singleton MemoryStore instance."""
    global _store
    if _store is None:
        _store = MemoryStore()
    return _store