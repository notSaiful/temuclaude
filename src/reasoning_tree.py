"""
MCTS Reasoning Tree Search — Step-Level Process Reward Tree (rStar-Math pattern)
Encodes intermediate thought steps as nodes and performs tree search (selection, expansion, rollout, backprop)
guided by step-level Process Reward Models (PRMs) to systematically eliminate logic errors.
"""
import math
import logging
import asyncio
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Callable, Awaitable

logger = logging.getLogger(__name__)


@dataclass
class PRMVerdict:
    """Structured process-reward judgment for a reasoning step."""
    score: float = 0.5
    label: str = "unknown"
    confidence: float = 0.0
    needs_escalation: bool = False
    source: str = "fallback"

    def as_dict(self) -> dict:
        return {
            "score": self.score,
            "label": self.label,
            "confidence": self.confidence,
            "needs_escalation": self.needs_escalation,
            "source": self.source,
        }


class ReasoningNode:
    """Represents a single intermediate reasoning step in the search tree."""

    def __init__(self, step_text: str, parent: Optional["ReasoningNode"] = None) -> None:
        self.step_text = step_text
        self.parent = parent
        self.children: List["ReasoningNode"] = []
        self.visits = 0
        self.value = 0.0  # Cumulative reward (Q-value)
        self.prm_score = 0.5  # Intermediate step correctness score from PRM
        self.prm_label = "unknown"
        self.prm_confidence = 0.0
        self.prm_needs_escalation = False

    @property
    def q_value(self) -> float:
        """Calculate average Q-value of the node."""
        if self.visits == 0:
            return self.prm_score
        return self.value / self.visits

    def get_full_thought_path(self) -> str:
        """Reconstruct the reasoning path from root to this node."""
        path = []
        curr = self
        while curr is not None:
            if curr.step_text:
                path.append(curr.step_text)
            curr = curr.parent
        return "\n\n".join(reversed(path))


class MCTSReasoningSearch:
    """Performs Monte Carlo Tree Search over reasoning paths."""

    def __init__(
        self,
        call_model_func: Callable[[str, list, int], Awaitable[str]],
        prm_model: str = "gemini-2.5-flash",
        policy_model: str = "deepseek-v4-pro",
        exploration_constant: float = 1.0,
        branch_factor: int = 3,
        max_depth: int = 5,
        iterations: int = 6
    ) -> None:
        self.call_model_func = call_model_func
        self.prm_model = prm_model
        self.policy_model = policy_model
        self.c = exploration_constant  # UCT exploration weight
        self.branch_factor = branch_factor
        self.max_depth = max_depth
        self.iterations = iterations

    def _uct_score(self, parent: ReasoningNode, child: ReasoningNode) -> float:
        """Calculate UCT (Upper Confidence bound for Trees) score for selection."""
        if child.visits == 0:
            # Encourage exploring unvisited nodes, weighted by their PRM estimate
            return child.q_value + self.c * math.sqrt(math.log(parent.visits + 1) / 0.1)
        return child.q_value + self.c * math.sqrt(math.log(parent.visits) / child.visits)

    def _select(self, node: ReasoningNode) -> ReasoningNode:
        """Select node using UCT score until we reach a leaf node."""
        curr = node
        while curr.children:
            # If any child has 0 visits, select it immediately to explore
            unvisited = [c for c in curr.children if c.visits == 0]
            if unvisited:
                return unvisited[0]
            # Otherwise, pick based on max UCT score
            curr = max(curr.children, key=lambda c: self._uct_score(curr, c))
        return curr

    async def _expand(self, node: ReasoningNode, query: str) -> None:
        """Expand leaf node by generating potential next steps."""
        context = node.get_full_thought_path()
        prompt = (
            f"Original Question: '{query}'\n\n"
            f"Previous Reasoning Steps:\n{context}\n\n"
            f"Propose a next single step of reasoning. The step must be logical, "
            f"complete, and focus on moving towards the final answer. "
            f"Output ONLY the single next step of reasoning. Do not output anything else."
        )

        tasks = []
        for _ in range(self.branch_factor):
            messages = [
                {"role": "system", "content": "You are a logical thinker generating one next step of reasoning."},
                {"role": "user", "content": prompt}
            ]
            tasks.append(self.call_model_func(self.policy_model, messages, 256))

        completions = await asyncio.gather(*tasks, return_exceptions=True)
        
        for comp in completions:
            if isinstance(comp, str) and not comp.startswith("[ERROR") and comp.strip():
                child = ReasoningNode(comp.strip(), parent=node)
                # Score the step with PRM
                verdict = await self._score_step_structured(query, context, child.step_text)
                child.prm_score = verdict.score
                child.prm_label = verdict.label
                child.prm_confidence = verdict.confidence
                child.prm_needs_escalation = verdict.needs_escalation
                node.children.append(child)

        # Apply MARRP (Rollout Pruning via Semantic Divergence)
        if len(node.children) >= 2:
            embeddings = []
            for child in node.children:
                emb = self._get_embedding(child.step_text)
                if emb is not None:
                    embeddings.append(emb)
            if len(embeddings) >= 2:
                similarities = []
                for i in range(len(embeddings)):
                    for j in range(i + 1, len(embeddings)):
                        similarities.append(self._calculate_cosine_similarity(embeddings[i], embeddings[j]))
                avg_sim = sum(similarities) / len(similarities)
                if avg_sim < 0.75:
                    logger.info(f"MCTS MARRP: Semantic divergence detected (avg_sim={avg_sim:.3f}). Lowering node step values.")
                    for child in node.children:
                        child.prm_score *= 0.5  # Penalize high divergence paths

    async def _score_step(self, query: str, context: str, step: str) -> float:
        """Score the intermediate step correctness, preserving legacy float API."""
        verdict = await self._score_step_structured(query, context, step)
        return verdict.score

    async def _score_step_structured(self, query: str, context: str, step: str) -> PRMVerdict:
        """Score a reasoning step with label, confidence, and escalation signal."""
        prompt = (
            f"Determine if the next reasoning step is correct and logical given the question and context.\n\n"
            f"Question: '{query}'\n"
            f"Context:\n{context}\n"
            f"Next Reasoning Step to Verify:\n{step}\n\n"
            f"Score the correctness and logical validity from 0 to 10 (10 is perfectly correct, 0 is logically contradictory).\n"
            f"Reply with ONLY a single digit score: e.g. '9' or '3'."
        )
        messages = [
            {"role": "system", "content": "You are a Process Reward Model. Reply ONLY with a single score digit from 0 to 10."},
            {"role": "user", "content": prompt}
        ]
        
        # Peer models for DPRM-P2P consensus
        peers = ["llama-3.3-70b-instruct", "mistral-large-3", "glm-5.2"]
        tasks = []
        for peer in peers:
            tasks.append(self.call_model_func(peer, messages, 5))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        scores = []
        import re
        for res in results:
            if isinstance(res, str) and not res.startswith("[ERROR"):
                digits = re.findall(r'\d+', res)
                if digits:
                    scores.append(min(max(int(digits[0]) / 10.0, 0.0), 1.0))
                    
        if len(scores) >= 2:
            avg_score = sum(scores) / len(scores)
            # Calculate variance for consensus confidence
            variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
            if variance > 0.08:
                # Split consensus: escalate to primary model
                logger.info(f"DPRM-P2P: Low consensus (variance={variance:.3f}). Escalating to primary PRM: {self.prm_model}.")
                primary = await self._score_step_primary_structured(query, context, step)
                primary.needs_escalation = True
                primary.source = "primary_after_peer_disagreement"
                return primary
            confidence = round(max(0.0, min(1.0, 1.0 - variance * 4)), 4)
            return PRMVerdict(
                score=avg_score,
                label=self._label_from_score(avg_score),
                confidence=confidence,
                needs_escalation=avg_score < 0.5 or confidence < 0.6,
                source="peer_consensus",
            )
            
        primary = await self._score_step_primary_structured(query, context, step)
        primary.needs_escalation = True
        return primary

    async def _score_step_primary(self, query: str, context: str, step: str) -> float:
        """Fallback to the primary PRM, preserving legacy float API."""
        verdict = await self._score_step_primary_structured(query, context, step)
        return verdict.score

    async def _score_step_primary_structured(self, query: str, context: str, step: str) -> PRMVerdict:
        """Fallback to the primary, high-capability Process Reward Model."""
        prompt = (
            f"Determine if the next reasoning step is correct and logical given the question and context.\n\n"
            f"Question: '{query}'\n"
            f"Context:\n{context}\n"
            f"Next Reasoning Step to Verify:\n{step}\n\n"
            f"Score correctness from 0 to 10 and classify the step as one label from: "
            f"correct, unsupported, arithmetic_error, logic_gap, contradiction, needs_tool, unsafe, unclear.\n"
            f"Reply compactly as: score=<0-10>; label=<label>."
        )
        messages = [
            {"role": "system", "content": "You are a Process Reward Model. Reply with score=<0-10>; label=<label>."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            verdict = await self.call_model_func(self.prm_model, messages, 5)
            return self._parse_prm_verdict(verdict, source="primary")
        except Exception:
            pass
        return PRMVerdict(score=0.5, label="unknown", confidence=0.0, needs_escalation=True, source="fallback")

    def _parse_prm_verdict(self, text: str, source: str = "primary") -> PRMVerdict:
        """Parse score/label output from a PRM response."""
        import re
        raw = text or ""
        lower = raw.lower()
        score = 0.5

        score_match = re.search(r"score\s*[:=]\s*(\d+(?:\.\d+)?)", lower)
        if score_match:
            score = float(score_match.group(1))
        else:
            digits = re.findall(r"\d+(?:\.\d+)?", lower)
            if digits:
                score = float(digits[0])
        if score > 1.0:
            score = score / 10.0
        score = max(0.0, min(1.0, score))

        labels = [
            "arithmetic_error", "logic_gap", "needs_tool", "unsupported",
            "contradiction", "unsafe", "unclear", "correct",
        ]
        normalized = lower.replace("-", "_").replace(" ", "_")
        label = next((candidate for candidate in labels if candidate in normalized), "")
        if not label:
            label = self._label_from_score(score)

        confidence = 0.75 if "label" in lower or any(label in normalized for label in labels) else 0.55
        if label == "correct" and score >= 0.8:
            confidence = max(confidence, 0.85)

        return PRMVerdict(
            score=score,
            label=label,
            confidence=round(confidence, 4),
            needs_escalation=label != "correct" or score < 0.5,
            source=source,
        )

    def _label_from_score(self, score: float) -> str:
        """Coarse fallback label when only scalar PRM scores are available."""
        if score >= 0.8:
            return "correct"
        if score >= 0.55:
            return "unclear"
        if score >= 0.3:
            return "logic_gap"
        return "contradiction"

    def _get_embedding(self, text: str):
        """Retrieve local embedding using SentenceTransformer (MARRP helper)."""
        try:
            from sentence_transformers import SentenceTransformer
            if not hasattr(self, "_embed_model"):
                self._embed_model = SentenceTransformer("all-MiniLM-L6-v2")
            return self._embed_model.encode(text)
        except Exception:
            return None

    def _calculate_cosine_similarity(self, vec1, vec2) -> float:
        """Calculate cosine similarity between two vector embeddings."""
        if vec1 is None or vec2 is None:
            return 1.0
        try:
            import numpy as np
            dot = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return float(dot / (norm1 * norm2))
        except Exception:
            # Pure-python fallback
            dot = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = sum(a * a for a in vec1) ** 0.5
            norm2 = sum(b * b for b in vec2) ** 0.5
            if norm1 == 0 or norm2 == 0:
                return 0.0
            return float(dot / (norm1 * norm2))

    async def _rollout(self, node: ReasoningNode, query: str) -> float:
        """Perform a fast complete rollout to the final answer and score it."""
        context = node.get_full_thought_path()
        prompt = (
            f"Question: '{query}'\n\n"
            f"Previous Reasoning Steps:\n{context}\n\n"
            f"Complete the remaining steps of reasoning quickly and output the final answer."
        )
        messages = [
            {"role": "system", "content": "Complete the logic and state the final answer concisely."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            # Fast rollout using worker model
            rollout_ans = await self.call_model_func(self.prm_model, messages, 512)
            if rollout_ans.startswith("[ERROR"):
                return 0.2
            
            # Score outcome correctness (ORM simulation)
            orm_prompt = (
                f"Question: '{query}'\n"
                f"Solution Attempt:\n{context}\n{rollout_ans}\n\n"
                f"Is the final answer correct? Reply ONLY 'YES' or 'NO'."
            )
            orm_messages = [
                {"role": "system", "content": "Reply ONLY YES or NO."},
                {"role": "user", "content": orm_prompt}
            ]
            orm_verdict = await self.call_model_func(self.prm_model, orm_messages, 5)
            if "YES" in orm_verdict.upper():
                return 1.0
        except Exception:
            pass
        return 0.3  # Rollout failed or completed with low confidence

    def _backpropagate(self, node: ReasoningNode, reward: float) -> None:
        """Backpropagate execution reward back to ancestors."""
        curr = node
        while curr is not None:
            curr.visits += 1
            curr.value += reward
            curr = curr.parent

    async def search(self, query: str, initial_thought: str = "") -> Dict[str, Any]:
        """Execute the MCTS loop and return the best reasoning path."""
        root = ReasoningNode(initial_thought.strip())
        
        # Initial expansion
        await self._expand(root, query)
        if not root.children:
            return {"path": initial_thought, "confidence": 0.3}

        for _ in range(self.iterations):
            # 1. Selection
            leaf = self._select(root)
            
            # Calculate leaf depth
            depth = 0
            curr = leaf
            while curr.parent is not None:
                depth += 1
                curr = curr.parent

            # 2. Expansion (if depth limit not reached)
            if depth < self.max_depth and leaf.visits > 0:
                await self._expand(leaf, query)
                if leaf.children:
                    leaf = leaf.children[0]

            # 3. Rollout
            reward = await self._rollout(leaf, query)

            # 4. Backpropagation
            self._backpropagate(leaf, reward)

        # Retrieve the best leaf (highest average value / visited node)
        best_path = root
        while best_path.children:
            best_path = max(best_path.children, key=lambda c: c.visits)

        return {
            "path": best_path.get_full_thought_path(),
            "confidence": best_path.q_value
        }

    async def search_decoupled(
        self, 
        query: str, 
        verifier_func: Callable[[str], Awaitable[bool]], 
        initial_thought: str = ""
    ) -> Dict[str, Any]:
        """
        D-MCTS: Run reasoning tree search decoupled from the generator.
        Verify the best path logical assertions; if Z3/SymPy verifications pass,
        mark as verified and return the trace.
        """
        search_res = await self.search(query, initial_thought)
        best_path_str = search_res["path"]
        
        is_logical = False
        try:
            is_logical = await verifier_func(best_path_str)
        except Exception as e:
            logger.warning(f"D-MCTS logical verification failed with error: {str(e)}")
            
        return {
            "path": best_path_str,
            "confidence": search_res["confidence"],
            "verified": is_logical
        }
