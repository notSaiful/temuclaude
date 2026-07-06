"""Tests for memory module."""
import sys
import os
import tempfile
sys.path.insert(0, "/Users/saiful/temuclaude")
from src.memory import MemoryStore, _extract_keywords, parse_extracted_memories


def test_memory_store_save_recall():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        store = MemoryStore(db_path=db_path)
        mem_id = store.save("user_profile", "User likes Python programming")
        assert mem_id > 0

        results = store.recall("Python coding preferences")
        assert len(results) > 0
        assert "Python" in results[0]["content"]
        store.close()
    finally:
        os.unlink(db_path)


def test_memory_store_categories():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        store = MemoryStore(db_path=db_path)
        store.save("user_profile", "Name is John")
        store.save("preferences", "Prefers dark mode")
        store.save("facts", "Uses Python 3.11")

        all_mems = store.list_memories()
        assert len(all_mems) == 3

        prefs = store.list_memories(category="preferences")
        assert len(prefs) == 1
        assert "dark mode" in prefs[0]["content"]
        store.close()
    finally:
        os.unlink(db_path)


def test_memory_store_forget():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        store = MemoryStore(db_path=db_path)
        store.save("context", "Temporary note")
        count = store.forget("Temporary note")
        assert count >= 1
        store.close()
    finally:
        os.unlink(db_path)


def test_memory_store_forget_by_id():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        store = MemoryStore(db_path=db_path)
        mem_id = store.save("context", "A test note")
        assert store.forget_by_id(mem_id) == True
        assert store.forget_by_id(9999) == False
        store.close()
    finally:
        os.unlink(db_path)


def test_extract_keywords():
    keywords = _extract_keywords("The user likes Python programming language")
    assert "python" in keywords
    assert "programming" in keywords
    assert "language" in keywords
    assert "the" not in keywords  # stop word


def test_parse_extracted_memories():
    raw = '[{"category": "user_profile", "content": "Likes Python"}]'
    result = parse_extracted_memories(raw)
    assert len(result) == 1
    assert result[0]["category"] == "user_profile"
    assert result[0]["content"] == "Likes Python"


def test_parse_extracted_memories_invalid():
    result = parse_extracted_memories("not json")
    assert result == []


def test_memory_store_clear():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        store = MemoryStore(db_path=db_path)
        store.save("context", "Note 1")
        store.save("context", "Note 2")
        count = store.clear_all()
        assert count == 2
        assert len(store.list_memories()) == 0
        store.close()
    finally:
        os.unlink(db_path)