"""
Temuclaude Prompt Engineering Module
Apply prompt engineering best practices to system prompt generation.

Features:
- Optimize prompts with best practices
- Add few-shot examples
- Add chain-of-thought instructions
- Add self-consistency instructions
- Build modular prompts from sections
- A/B test prompt quality
"""
import re
from typing import Optional, Callable, Awaitable, List, Dict


def optimize_prompt(base_prompt: str) -> str:
    """Apply prompt engineering best practices to a system prompt.

    Rules:
    - Clear role definition
    - Positive instructions (what TO do, not what NOT to do)
    - Step-by-step guidance
    - Structured output format
    - Be specific and concrete
    """
    optimized = base_prompt

    # Ensure role definition
    if not re.search(r'^You\s+are\s+', optimized, re.IGNORECASE):
        optimized = f"You are an expert assistant. {optimized}"

    # Add step-by-step for complex prompts
    if len(optimized) > 200 and "step" not in optimized.lower():
        optimized += "\n\nThink through this step by step."

    # Add output format guidance
    if "format" not in optimized.lower() and "output" not in optimized.lower():
        optimized += "\n\nProvide a clear, well-structured response."

    return optimized.strip()


def add_few_shot(prompt: str, examples: List[Dict[str, str]]) -> str:
    """Add few-shot examples to a prompt.

    Args:
        prompt: Base system prompt
        examples: List of {input, output} dicts

    Returns:
        Prompt with examples appended
    """
    if not examples:
        return prompt

    examples_text = "\n\nExamples:\n"
    for i, ex in enumerate(examples, 1):
        examples_text += f"\nExample {i}:\n"
        examples_text += f"Input: {ex.get('input', '')}\n"
        examples_text += f"Output: {ex.get('output', '')}\n"

    return f"{prompt}\n{examples_text}"


def add_chain_of_thought(prompt: str) -> str:
    """Add chain-of-thought instructions to a prompt."""
    cot_addition = (
        "\n\nReasoning approach:\n"
        "1. Understand what is being asked\n"
        "2. Identify the key information needed\n"
        "3. Work through the problem step by step\n"
        "4. Verify your reasoning\n"
        "5. Provide the final answer\n\n"
        "Show your reasoning process before giving the answer."
    )
    return f"{prompt}{cot_addition}"


def add_self_consistency(prompt: str, n: int = 5) -> str:
    """Add self-consistency instructions.

    Self-consistency: generate N independent solutions and take the majority answer.
    """
    sc_addition = (
        f"\n\nApproach: Generate {n} independent solutions to this problem. "
        f"Then select the most consistent answer (majority vote). "
        "If answers differ, analyze the disagreements and choose the most "
        "well-reasoned answer."
    )
    return f"{prompt}{sc_addition}"


def modular_prompt(sections: Dict[str, str]) -> str:
    """Build a prompt from modular sections.

    Args:
        sections: Dict of section_name → content

    Returns:
        Complete prompt string
    """
    parts = []
    for name, content in sections.items():
        parts.append(f"## {name.replace('_', ' ').title()}\n{content}")
    return "\n\n".join(parts)


def build_optimization_prompt(base_prompt: str) -> List[Dict]:
    """Build a prompt to optimize a system prompt via LLM."""
    return [
        {"role": "system", "content": (
            "You are a prompt engineering expert. Optimize the given system prompt "
            "by applying best practices: clear role definition, positive instructions, "
            "step-by-step guidance, structured output, and specificity. "
            "Return only the optimized prompt."
        )},
        {"role": "user", "content": f"Prompt to optimize:\n{base_prompt}"},
    ]


async def optimize_prompt_with_llm(
    base_prompt: str,
    model_fn: Optional[Callable[[List[Dict]], Awaitable[str]]] = None,
) -> str:
    """Optimize a prompt using an LLM.

    Falls back to rule-based optimization if no model_fn.
    """
    if model_fn:
        messages = build_optimization_prompt(base_prompt)
        return await model_fn(messages)
    return optimize_prompt(base_prompt)


async def a_b_test(
    prompt_a: str,
    prompt_b: str,
    test_cases: List[str],
    model_fn: Optional[Callable[[List[Dict]], Awaitable[str]]] = None,
) -> Dict:
    """A/B test two prompts on a set of test cases.

    Args:
        prompt_a: First prompt
        prompt_b: Second prompt
        test_cases: List of test inputs
        model_fn: Async LLM function

    Returns:
        Dict with: prompt_a_avg_length, prompt_b_avg_length, recommendation
    """
    if not model_fn:
        # Fallback: compare prompt structure
        a_score = len(prompt_a.split()) + (10 if "step" in prompt_a.lower() else 0)
        b_score = len(prompt_b.split()) + (10 if "step" in prompt_b.lower() else 0)
        return {
            "prompt_a_score": a_score,
            "prompt_b_score": b_score,
            "recommendation": "A" if a_score >= b_score else "B",
        }

    # Run both prompts on all test cases
    results_a = []
    results_b = []

    for case in test_cases:
        msgs_a = [{"role": "system", "content": prompt_a}, {"role": "user", "content": case}]
        msgs_b = [{"role": "system", "content": prompt_b}, {"role": "user", "content": case}]

        resp_a = await model_fn(msgs_a)
        resp_b = await model_fn(msgs_b)

        results_a.append(resp_a)
        results_b.append(resp_b)

    # Compare average response length (proxy for quality)
    avg_a = sum(len(r.split()) for r in results_a) / max(len(results_a), 1)
    avg_b = sum(len(r.split()) for r in results_b) / max(len(results_b), 1)

    return {
        "prompt_a_avg_length": avg_a,
        "prompt_b_avg_length": avg_b,
        "results_a": results_a,
        "results_b": results_b,
        "recommendation": "A" if avg_a >= avg_b else "B",
    }


def add_structured_output(prompt: str, schema: str) -> str:
    """Add structured output format instructions to a prompt.

    Args:
        prompt: Base prompt
        schema: Expected output format description

    Returns:
        Prompt with output format instructions
    """
    return f"{prompt}\n\nOutput format:\n{schema}"


def add_role(prompt: str, role: str) -> str:
    """Add or prepend a role definition to a prompt."""
    role_text = f"You are {role}. "
    if prompt.lower().startswith("you are"):
        return prompt  # Already has a role
    return role_text + prompt