"""
Timuclaude Fusion Module
Calls multiple models in parallel, then a dynamic aggregator synthesizes the best answer.

This is the core of Timuclaude's power — the "invisible orchestration" that makes
5 models act as one. The user sees one response. Internally, 5 models answered
in parallel, an aggregator analyzed their responses, and synthesized the best answer.

Based on:
- OpenRouter Fusion Router (panel + judge pattern)
- Sakana Fugu (dynamic aggregator selection per question)
- MGH hypothesis (better management of existing model capabilities)
"""
import asyncio
from typing import Optional, Callable, Awaitable

from .models import (
    MODEL_POOL,
    FUSION_PANEL,
    AGGREGATOR_MAP,
    OLLAMA_API_BASE,
)


# Configurable panel size (3 for Ollama Pro, 5 for Ollama Max)
DEFAULT_PANEL_SIZE = 3


def get_panel(task_type: str, panel_size: int = DEFAULT_PANEL_SIZE) -> list:
    """Get the panel of models for a given task type.
    
    For math: prioritize DeepSeek (math specialist)
    For coding: prioritize DeepSeek + Kimi K2.7 Code
    For knowledge: prioritize GLM-5.2
    For reasoning: prioritize DeepSeek
    For creative: prioritize MiniMax
    For agentic: prioritize GLM-5.2
    """
    priority_map = {
        "math": ["deepseek-v4-pro", "glm-5.2", "kimi-k2.6", "minimax-m3", "nemotron-3-ultra"],
        "coding": ["deepseek-v4-pro", "kimi-k2.6", "glm-5.2", "minimax-m3", "nemotron-3-ultra"],
        "knowledge": ["glm-5.2", "deepseek-v4-pro", "kimi-k2.6", "minimax-m3", "nemotron-3-ultra"],
        "reasoning": ["deepseek-v4-pro", "glm-5.2", "kimi-k2.6", "minimax-m3", "nemotron-3-ultra"],
        "creative": ["minimax-m3", "glm-5.2", "deepseek-v4-pro", "kimi-k2.6", "nemotron-3-ultra"],
        "agentic": ["glm-5.2", "deepseek-v4-pro", "kimi-k2.6", "minimax-m3", "nemotron-3-ultra"],
    }
    
    panel = priority_map.get(task_type, FUSION_PANEL)
    return panel[:panel_size]


def get_aggregator(task_type: str) -> str:
    """Get the aggregator model for a given task type (Fugu pattern).
    
    The aggregator is chosen based on which model is strongest for that task type.
    This is the key innovation Fugu uses — dynamic aggregator selection.
    """
    return AGGREGATOR_MAP.get(task_type, AGGREGATOR_MAP["default"])


def build_fusion_prompt(question: str, responses: dict, panel_models: list) -> list:
    """Build the synthesis prompt for the aggregator model.
    
    The aggregator receives:
    1. The original question
    2. All model responses labeled with model names
    3. Instructions to identify consensus, contradictions, and synthesize
    """
    model_labels = {
        "glm-5.2": "Model A (GLM-5.2)",
        "deepseek-v4-pro": "Model B (DeepSeek V4 Pro)",
        "kimi-k2.6": "Model C (Kimi K2.6)",
        "minimax-m3": "Model D (MiniMax M3)",
        "nemotron-3-ultra": "Model E (Nemotron 3 Ultra)",
        "gpt-oss-120b": "Model F (GPT-OSS 120B)",
    }

    response_text = ""
    for i, model in enumerate(panel_models):
        label = model_labels.get(model, f"Model {i+1}")
        response = responses.get(model, "[No response]")
        # Truncate very long responses to keep the prompt manageable
        if len(response) > 2000:
            response = response[:2000] + "... [truncated]"
        response_text += f"\n\n{label}:\n{response}"

    system_prompt = (
        "You are Timuclaude, an AI synthesis engine. You are reviewing answers "
        "from multiple AI models that attempted the same question. Your job is to:\n"
        "1. Identify where the models AGREE (consensus) — this is high confidence.\n"
        "2. Identify where the models DISAGREE (contradictions) — analyze which is correct.\n"
        "3. Synthesize the best possible answer using the strengths of each model.\n"
        "4. If most models agree on the same answer, use that answer.\n"
        "5. If models disagree, use your expertise to determine the correct answer.\n"
        "Provide a single, clear, final answer. Do not mention which model said what."
    )

    user_prompt = f"Here is the question:\n{question}\n\nHere are the responses from {len(panel_models)} models:{response_text}\n\nProvide the best synthesized answer:"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


async def fuse(
    question: str,
    task_type: str,
    call_model_func: Callable[..., Awaitable[str]],
    panel_size: int = DEFAULT_PANEL_SIZE,
    max_tokens: int = 8192,
) -> dict:
    """
    Run the Fusion pattern: call N models in parallel, synthesize with aggregator.
    
    Args:
        question: The user's question
        task_type: The classified task type (math, coding, knowledge, etc.)
        call_model_func: Async function to call a model (from orchestrator)
        panel_size: Number of models in the panel (3 for Pro, 5 for Max)
        max_tokens: Max tokens for each model response
    
    Returns:
        Dict with:
        - 'answer': The synthesized final answer
        - 'aggregator': Which model was the aggregator
        - 'panel': Which models were in the panel
        - 'responses': All individual model responses
    """
    # Get the panel and aggregator
    panel = get_panel(task_type, panel_size)
    aggregator = get_aggregator(task_type)

    # Build messages for each panel model
    messages = [
        {"role": "system", "content": f"You are Timuclaude, a helpful AI assistant. Answer the following question thoroughly and accurately."},
        {"role": "user", "content": question},
    ]

    # Call all panel models in parallel
    tasks = [call_model_func(model, messages, max_tokens=max_tokens) for model in panel]
    responses_list = await asyncio.gather(*tasks)

    # Map responses to model names
    responses = {}
    for i, model in enumerate(panel):
        responses[model] = responses_list[i]

    # Build synthesis prompt
    synthesis_messages = build_fusion_prompt(question, responses, panel)

    # Aggregator synthesizes
    final_answer = await call_model_func(aggregator, synthesis_messages, max_tokens=max_tokens)

    return {
        "answer": final_answer,
        "aggregator": aggregator,
        "panel": panel,
        "responses": responses,
    }