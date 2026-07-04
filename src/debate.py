"""
Temuclaude Multi-Agent Debate Module
Selective debate: only triggers when self-QA fails after retry.

Based on:
- Du et al. (ICML 2024): Multiagent Debate — +14.8% accuracy on reasoning
- iMAD (arXiv:2511.11306): Adaptive debate — only for queries that need it
- Debate Limitations (arXiv:2511.07784): 65% of failures are "Collective Delusion"
  → Use debate SELECTIVELY, not as default. Limit rounds. Use model diversity.

Key design decisions:
1. Only trigger after self-QA fails (not default path)
2. Limit to 2-3 rounds to control cost
3. Use temuclaude's model diversity as anti-echo-chamber advantage
4. Final answer via weighted consensus, not unanimous agreement
"""
import asyncio
import re
from typing import Callable, Awaitable, Optional, List
from collections import defaultdict


DEFAULT_DEBATE_ROUNDS = 2
DEFAULT_PANEL = ["glm-5.2", "deepseek-v4-pro", "kimi-k2.6"]


def build_debate_prompt(question: str, model_name: str, other_responses: dict, round_num: int) -> list:
    """Build a debate prompt for a model to argue its position.
    
    Each model sees the other models' arguments and is asked to either
    defend its position or concede if another model has a better argument.
    """
    model_labels = {
        "glm-5.2": "GLM-5.2",
        "deepseek-v4-pro": "DeepSeek V4 Pro",
        "kimi-k2.6": "Kimi K2.6",
        "minimax-m3": "MiniMax M3",
        "nemotron-3-ultra": "Nemotron 3 Ultra",
    }
    
    other_text = ""
    for m, resp in other_responses.items():
        if m == model_name:
            continue
        label = model_labels.get(m, m)
        if len(resp) > 1000:
            resp = resp[:1000] + "... [truncated]"
        other_text += f"\n\n{label}'s argument:\n{resp}"
    
    my_label = model_labels.get(model_name, model_name)
    
    if round_num == 0:
        system_prompt = (
            f"You are {my_label}, an AI reasoning expert. A question has been posed "
            f"and multiple AI models will debate their answers. Provide your initial "
            f"answer with clear reasoning. Be precise and logical."
        )
        user_prompt = f"Question: {question}\n\nProvide your answer with reasoning:"
    else:
        system_prompt = (
            f"You are {my_label}, an AI reasoning expert in round {round_num + 1} of a debate. "
            f"Other models have presented their arguments. Review them critically.\n"
            f"- If another model has a better argument, concede and adopt their reasoning.\n"
            f"- If your answer is correct, defend it with stronger evidence.\n"
            f"- Be objective — the goal is to find the CORRECT answer, not to win.\n"
            f"Provide your revised answer with reasoning."
        )
        user_prompt = f"Question: {question}\n\nOther models' arguments:{other_text}\n\nYour revised answer:"
    
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_consensus_prompt(question: str, final_responses: dict) -> list:
    """Build a consensus prompt for the aggregator to synthesize the debate outcome."""
    model_labels = {
        "glm-5.2": "GLM-5.2",
        "deepseek-v4-pro": "DeepSeek V4 Pro",
        "kimi-k2.6": "Kimi K2.6",
        "minimax-m3": "MiniMax M3",
        "nemotron-3-ultra": "Nemotron 3 Ultra",
    }
    
    responses_text = ""
    for m, resp in final_responses.items():
        label = model_labels.get(m, m)
        if len(resp) > 1500:
            resp = resp[:1500] + "... [truncated]"
        responses_text += f"\n\n{label}'s final argument:\n{resp}"
    
    system_prompt = (
        "You are a debate moderator. Multiple AI models have debated a question "
        "across multiple rounds. Synthesize the final answer based on:\n"
        "1. Which answer most models converged on (consensus)\n"
        "2. Which model had the strongest reasoning\n"
        "3. Any remaining disagreements and which side is correct\n"
        "Provide a single, clear final answer."
    )
    
    user_prompt = f"Question: {question}\n\nFinal arguments from all models:{responses_text}\n\nFinal synthesized answer:"
    
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


async def multi_agent_debate(
    question: str,
    call_model_func: Callable[..., Awaitable[str]],
    panel: list = None,
    rounds: int = DEFAULT_DEBATE_ROUNDS,
    aggregator: str = "nemotron-3-ultra",
    max_tokens: int = 4096,
) -> dict:
    """
    Run a multi-agent debate to resolve a difficult question.
    
    Should ONLY be called as an escalation mechanism when self-QA fails.
    The debate allows models to argue, concede, and converge on the correct answer.
    
    Args:
        question: The question to debate
        call_model_func: Async function to call models
        panel: List of model names to participate in the debate
        rounds: Number of debate rounds (2-3 recommended, more = echo chamber risk)
        aggregator: Which model synthesizes the final consensus
        max_tokens: Max tokens per model call
    
    Returns:
        Dict with:
        - 'answer': The synthesized final answer
        - 'rounds': Number of rounds completed
        - 'participants': Which models debated
        - 'final_responses': Each model's final argument
    """
    if panel is None:
        panel = DEFAULT_PANEL
    
    current_responses = {}
    
    for round_num in range(rounds):
        # Each model generates/revises its answer
        debate_tasks = []
        debate_models = []
        for model in panel:
            debate_messages = build_debate_prompt(question, model, current_responses, round_num)
            debate_tasks.append(call_model_func(model, debate_messages, max_tokens=max_tokens))
            debate_models.append(model)
        
        debate_results = await asyncio.gather(*debate_tasks)
        
        # Update responses
        for i, model in enumerate(debate_models):
            current_responses[model] = debate_results[i]
    
    # Synthesize consensus
    consensus_messages = build_consensus_prompt(question, current_responses)
    final_answer = await call_model_func(aggregator, consensus_messages, max_tokens=max_tokens)
    
    return {
        "answer": final_answer,
        "rounds": rounds,
        "participants": panel,
        "final_responses": current_responses,
        "aggregator": aggregator,
    }