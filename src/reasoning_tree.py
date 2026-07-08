"""
MCTS Reasoning Tree Search — Step-Level Process Reward Tree (rStar-Math pattern)
Encodes intermediate thought steps as nodes and performs tree search (selection, expansion, rollout, backprop)
guided by step-level Process Reward Models (PRMs) to systematically eliminate logic errors.
"""
import math
import logging
import asyncio
from typing import List, Dict, Any, Optional, Callable, Awaitable

logger = logging.getLogger(__name__)


class ReasoningNode:
    """Represents a single intermediate reasoning step in the search tree."""

    def __init__(self, step_text: str, parent: Optional["ReasoningNode"] = None) -> None:
        self.step_text = step_text
        self.parent = parent
        self.children: List["ReasoningNode"] = []
        self.visits = 0
        self.value = 0.0  # Cumulative reward (Q-value)
        self.prm_score = 0.5  # Intermediate step correctness score from PRM

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
        prm_model: str = "gemini-2.0-flash",
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
                child.prm_score = await self._score_step(query, context, child.step_text)
                node.children.append(child)

    async def _score_step(self, query: str, context: str, step: str) -> float:
        """Use the PRM model to score the intermediate step correctness."""
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
        
        try:
            verdict = await self.call_model_func(self.prm_model, messages, 5)
            # Find digits in response
            import re
            digits = re.findall(r'\d+', verdict)
            if digits:
                score = int(digits[0])
                return min(max(score / 10.0, 0.0), 1.0)
        except Exception:
            pass
        return 0.5  # Fallback neutral score

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
