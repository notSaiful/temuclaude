"""
Temuclaude Fusion Module
Calls multiple models in parallel, then a dynamic aggregator synthesizes the best answer.

This is the core of Temuclaude's power — the "invisible orchestration" that makes
5 models act as one. The user sees one response. Internally, 5 models answered
in parallel, an aggregator analyzed their responses, and synthesized the best answer.

Based on:
- OpenRouter Fusion Router (panel + judge pattern)
- Sakana Fugu (dynamic aggregator selection per question)
- MGH hypothesis (better management of existing model capabilities)
- Mixture-of-Agents (arXiv:2406.04692): Layered aggregation — each layer takes
  ALL outputs from previous layer as auxiliary info. 3-layer MoA achieves 65.1%
  on AlpacaEval 2.0 vs GPT-4o's 57.5%. Layer scaling: 1L=44%, 2L=61%, 3L=65%.
- Self-MoA (arXiv:2502.00674): Sampling one top model N times can outperform
  heterogeneous panel by +6.6%. Use when one model clearly dominates task type.
"""
import asyncio
from typing import Optional, Callable, Awaitable

from .models import (
    MODEL_POOL,
    FUSION_PANEL,
    AGGREGATOR_MAP,
    OLLAMA_API_BASE,
    get_runtime_model,
)


# Configurable panel size (3 for Ollama Pro, 5 for Ollama Max)
DEFAULT_PANEL_SIZE = 3

# A third cross-review layer doubles panel calls. Keep the default at two
# layers; callers can explicitly request three only for a benchmarked premium
# path where the measured quality gain justifies its cost and latency.
DEFAULT_MOA_LAYERS = 2


def get_panel(task_type: str, panel_size: int = DEFAULT_PANEL_SIZE) -> list:
    """Get the panel of models for a given task type.
    
    For math: prioritize DeepSeek (math specialist)
    For coding: prioritize DeepSeek + Kimi K2.7 Code
    For knowledge: prioritize GLM-5.2
    For reasoning: prioritize DeepSeek
    For creative: prioritize MiniMax
    For agentic: prioritize GLM-5.2
    """
    # Keep ordinary fusion to diverse, proven open routes.  Premium models are
    # deliberately absent here: Grok is a conditional repair model and Gemini
    # is a visual-review model.  Adding either to every hard request whenever a
    # key is present quietly defeats the cost-aware cascade.
    priority_map = {
        "math": ["deepseek-v4-pro", "glm-5.2", "nemotron-3-ultra"],
        "coding": ["deepseek-v4-pro", "glm-5.2", "nemotron-3-ultra"],
        "knowledge": ["glm-5.2", "deepseek-v4-pro", "deepseek-v4-flash"],
        "reasoning": ["deepseek-v4-pro", "glm-5.2", "nemotron-3-ultra"],
        "creative": ["minimax-m3", "glm-5.2", "deepseek-v4-pro"],
        "agentic": ["glm-5.2", "deepseek-v4-pro", "nemotron-3-ultra"],
        "vision": ["minimax-m3", "glm-5.2", "deepseek-v4-pro"],
        "ui_ux": ["minimax-m3", "glm-5.2", "deepseek-v4-pro"],
    }

    resolved = []
    for candidate in priority_map.get(task_type, FUSION_PANEL):
        model = get_runtime_model(candidate)
        if model not in resolved:
            resolved.append(model)
        if len(resolved) >= panel_size:
            break
    return resolved


def get_aggregator(task_type: str) -> str:
    """Get the aggregator model for a given task type (Fugu pattern).
    
    The aggregator is chosen based on which model is strongest for that task type.
    This is the key innovation Fugu uses — dynamic aggregator selection.
    """
    return AGGREGATOR_MAP.get(task_type, AGGREGATOR_MAP["default"])


def build_fusion_prompt(question: str, responses: dict, panel_models: list, task_type: str = "default") -> list:
    """Build the synthesis prompt for the aggregator model.
    
    The aggregator receives:
    1. The original question
    2. All model responses labeled with model names
    3. Instructions to identify consensus, contradictions, and synthesize
    """
    model_labels = {
        "glm-5.2": "Model A (GLM-5.2)",
        "deepseek-v4-pro": "Model B (DeepSeek V4 Pro)",
        "deepseek-v4-flash": "Model C (DeepSeek V4 Flash)",
        "minimax-m3": "Model D (MiniMax M3)",
        "gemini-3.5-flash": "Model E (Gemini 3.5 Flash)",
        "grok-4.5": "Model F (Grok 4.5)",
        "nemotron-3-ultra": "Model G (Nemotron 3 Ultra)",
    }

    response_text = ""
    for i, model in enumerate(panel_models):
        label = model_labels.get(model, f"Model {i+1}")
        response = responses.get(model, "[No response]")
        # Truncate very long responses to keep the prompt manageable
        if len(response) > 2000:
            response = response[:2000] + "... [truncated]"
        response_text += f"\n\n{label}:\n{response}"

    priority_notes = {
        "math": "Model B (DeepSeek V4 Pro) is our prime math reasoning specialist and should be given 1.5x weight in your synthesis.",
        "coding": "DeepSeek V4 Pro is the prime reasoning specialist. Prefer independently verified details over ungrounded consensus.",
        "knowledge": "Model A (GLM-5.2) is our prime general knowledge specialist and should be given 1.5x weight in your synthesis.",
        "reasoning": "Model B (DeepSeek V4 Pro) is our prime logical reasoning specialist and should be given 1.5x weight in your synthesis.",
    }
    priority_note = priority_notes.get(task_type, "")

    system_prompt = (
        "You are Temuclaude, an AI synthesis engine. You are reviewing answers "
        "from multiple AI models that attempted the same question. Your job is to:\n"
        "1. Identify where the models AGREE (consensus) — this is high confidence.\n"
        "2. Identify where the models DISAGREE (contradictions) — analyze which is correct.\n"
        "3. Synthesize the best possible answer using the strengths of each model.\n"
        "4. If most models agree on the same answer, use that answer.\n"
        "5. If models disagree, use your expertise to determine the correct answer.\n"
        "Provide a single, clear, final answer. Do not mention which model said what."
    )
    if priority_note:
        system_prompt += f"\n\n[CS-DVW WEIGHTING]: {priority_note}"

    user_prompt = f"Here is the question:\n{question}\n\nHere are the responses from {len(panel_models)} models:{response_text}\n\nProvide the best synthesized answer:"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_cross_review_prompt(question: str, model_name: str, all_responses: dict, panel_models: list) -> list:
    """Build a cross-review prompt for the MoA 3rd layer.
    
    Each model sees ALL other models' responses and is asked to improve its own
    answer by incorporating insights from the others. This is the key MoA innovation
    that adds +4% quality over 2-layer panel+judge (65.1% vs 61% on AlpacaEval).
    """
    model_labels = {
        "glm-5.2": "GLM-5.2",
        "deepseek-v4-pro": "DeepSeek V4 Pro",
        "deepseek-v4-flash": "DeepSeek V4 Flash",
        "minimax-m3": "MiniMax M3",
        "gemini-3.5-flash": "Gemini 3.5 Flash",
        "grok-4.5": "Grok 4.5",
        "nemotron-3-ultra": "Nemotron 3 Ultra",
    }
    
    other_responses = ""
    for m in panel_models:
        if m == model_name:
            continue
        label = model_labels.get(m, m)
        resp = all_responses.get(m, "[No response]")
        if len(resp) > 1500:
            resp = resp[:1500] + "... [truncated]"
        other_responses += f"\n\n{label}'s answer:\n{resp}"
    
    my_label = model_labels.get(model_name, model_name)
    
    system_prompt = (
        f"You are {my_label}, part of a panel of AI models answering the same question. "
        f"You now see the other models' answers. Review them and provide an IMPROVED answer "
        f"that incorporates the best insights from the other models while maintaining your own expertise.\n"
        f"If other models have better reasoning or facts, adopt them.\n"
        f"If your original answer was correct, refine and strengthen it.\n"
        f"Provide a single, clear, final answer."
    )
    
    user_prompt = (
        f"Question: {question}\n\n"
        f"Other models' answers:{other_responses}\n\n"
        f"Your improved answer:"
    )
    
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
    moa_layers: int = DEFAULT_MOA_LAYERS,
) -> dict:
    """
    Run the Fusion pattern: call N models in parallel, synthesize with aggregator.
    
    Supports 2-layer (original panel+judge) and 3-layer MoA (panel+cross-review+judge).
    3-layer MoA adds +4% quality on average (65.1% vs 61% AlpacaEval 2.0).
    
    Args:
        question: The user's question
        task_type: The classified task type (math, coding, knowledge, etc.)
        call_model_func: Async function to call a model (from orchestrator)
        panel_size: Number of models in the panel (3 for Pro, 5 for Max)
        max_tokens: Max tokens for each model response
        moa_layers: 2 = panel+judge, 3 = panel+cross-review+judge (MoA upgrade)
    
    Returns:
        Dict with:
        - 'answer': The synthesized final answer
        - 'aggregator': Which model was the aggregator
        - 'panel': Which models were in the panel
        - 'responses': All individual model responses (final layer)
        - 'layer1_responses': Original responses (if 3-layer MoA)
        - 'moa_layers': How many layers were used
    """
    # Get the panel and aggregator
    panel = get_panel(task_type, panel_size)
    aggregator = get_aggregator(task_type)

    # Build messages for each panel model
    messages = [
        {"role": "system", "content": f"You are Temuclaude, a helpful AI assistant. Answer the following question thoroughly and accurately."},
        {"role": "user", "content": question},
    ]

    # Layer 1: Call all panel models in parallel
    tasks = [call_model_func(model, messages, max_tokens=max_tokens) for model in panel]
    responses_list = await asyncio.gather(*tasks)

    # Map responses to model names
    responses = {}
    for i, model in enumerate(panel):
        responses[model] = responses_list[i]
    
    layer1_responses = dict(responses)  # Keep copy of original responses

    # Layer 2 (if 3-layer MoA): Cross-review — each model sees others' responses
    if moa_layers >= 3 and len(panel) > 1:
        cross_review_tasks = []
        cross_review_models = []
        for model in panel:
            review_messages = build_cross_review_prompt(question, model, responses, panel)
            cross_review_tasks.append(call_model_func(model, review_messages, max_tokens=max_tokens))
            cross_review_models.append(model)
        
        cross_review_responses = await asyncio.gather(*cross_review_tasks)
        
        # Update responses with cross-reviewed versions
        for i, model in enumerate(cross_review_models):
            responses[model] = cross_review_responses[i]

    # Final Layer: Aggregator synthesizes
    synthesis_messages = build_fusion_prompt(question, responses, panel, task_type=task_type)
    final_answer = await call_model_func(aggregator, synthesis_messages, max_tokens=max_tokens)

    return {
        "answer": final_answer,
        "aggregator": aggregator,
        "panel": panel,
        "responses": responses,
        "layer1_responses": layer1_responses if moa_layers >= 3 else None,
        "moa_layers": moa_layers,
    }
