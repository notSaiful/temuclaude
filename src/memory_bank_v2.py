"""
Temuclaude Voyager-style Skill Memory Bank (v2)

Provides persistent vector-indexed and keyword-indexed storage for verified skills,
reusable code snippets, formulas, and domain recipes.
If a query matches a previously solved skill semantically, the orchestrator
can fetch and inject this skill directly into the context prompt.
"""
import os
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

SKILLS_LIBRARY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "skills_library.json"
)


class VoyagerMemoryBank:
    """Voyager-style persistent memory bank for verified skills."""

    def __init__(self, storage_path: str = SKILLS_LIBRARY_FILE) -> None:
        self.storage_path = storage_path
        self.skills: List[Dict[str, Any]] = []
        
        # Embeddings lazy loading
        self._embed_fn = None
        self._embed_fn_loaded = False
        
        self.load()

    def _get_embed_fn(self):
        """Lazy-load sentence-transformers for embeddings lookup."""
        if self._embed_fn_loaded:
            return self._embed_fn
        self._embed_fn_loaded = True
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2")
            self._embed_fn = model.encode
            logger.info("VoyagerMemoryBank: loaded all-MiniLM-L6-v2 for semantic skill lookup")
        except ImportError:
            logger.info("VoyagerMemoryBank: sentence-transformers not installed, using keyword fallback.")
            self._embed_fn = None
        return self._embed_fn

    def load(self) -> None:
        """Load skills from JSON storage."""
        if not os.path.isfile(self.storage_path):
            self.skills = []
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.skills = data.get("skills", [])
                logger.info(f"VoyagerMemoryBank: loaded {len(self.skills)} skills.")
        except Exception as e:
            logger.error(f"VoyagerMemoryBank: Failed to load skills: {e}")
            self.skills = []

    def persist(self) -> None:
        """Persist skills to JSON storage."""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({"skills": self.skills}, f, indent=2, default=str)
                logger.info(f"VoyagerMemoryBank: Saved {len(self.skills)} skills.")
        except Exception as e:
            logger.error(f"VoyagerMemoryBank: Failed to persist skills: {e}")

    def add_skill(
        self,
        query: str,
        skill_code: str,
        task_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a new verified skill to the library."""
        embed_fn = self._get_embed_fn()
        embedding = None
        if embed_fn:
            try:
                embedding = embed_fn(query).tolist()
            except Exception as e:
                logger.error(f"VoyagerMemoryBank: Embedding generation failed: {e}")

        # Check if the skill already exists to prevent duplicate blow-up
        for skill in self.skills:
            if skill.get("query") == query or skill.get("skill_code") == skill_code:
                return

        new_skill = {
            "query": query,
            "skill_code": skill_code,
            "task_type": task_type,
            "metadata": metadata or {},
            "embedding": embedding
        }
        self.skills.append(new_skill)
        self.persist()

    def find_skills(self, query: str, task_type: str, limit: int = 2) -> List[Dict[str, Any]]:
        """Find relevant skills semantically or via keyword matching."""
        if not self.skills:
            return []

        embed_fn = self._get_embed_fn()
        
        # Filter skills by task_type first
        filtered_skills = [s for s in self.skills if s.get("task_type") == task_type]
        if not filtered_skills:
            return []

        # 1. Try semantic cosine similarity if embeddings are available
        if embed_fn:
            try:
                import numpy as np
                query_vector = embed_fn(query)
                scored_skills = []
                for skill in filtered_skills:
                    if skill.get("embedding") is not None:
                        skill_vector = np.array(skill["embedding"])
                        # Cosine similarity
                        dot_product = np.dot(query_vector, skill_vector)
                        norm_q = np.linalg.norm(query_vector)
                        norm_s = np.linalg.norm(skill_vector)
                        similarity = dot_product / (norm_q * norm_s) if norm_q > 0 and norm_s > 0 else 0.0
                        scored_skills.append((skill, similarity))
                
                # Sort and return skills above 0.70 threshold
                scored_skills.sort(key=lambda x: x[1], reverse=True)
                results = [item[0] for item in scored_skills if item[1] >= 0.70]
                return results[:limit]
            except Exception as e:
                logger.error(f"VoyagerMemoryBank: Semantic search failed: {e}")

        # 2. Keyword fallback matching
        query_words = set(query.lower().split())
        scored_skills = []
        for skill in filtered_skills:
            skill_words = set(skill.get("query", "").lower().split())
            intersection = query_words.intersection(skill_words)
            score = len(intersection) / len(query_words) if query_words else 0.0
            scored_skills.append((skill, score))
            
        scored_skills.sort(key=lambda x: x[1], reverse=True)
        results = [item[0] for item in scored_skills if item[1] > 0.10]
        return results[:limit]
