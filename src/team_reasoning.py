"""
Temuclaude Multi-Agent Team Reasoning Module
Grok-style multi-agent team collaboration with chatroom.

Team: Leader, Researcher, Analyst, Critic
- Leader: plans and breaks down the question
- Researcher: investigates sub-questions
- Analyst: analyzes findings
- Critic: reviews before synthesis
- Synthesizer: combines into final answer

Based on:
- Grok multi-agent reasoning (xAI)
- Multi-Agent Collaboration (arXiv:2406.04692)
- Chain-of-Verification (arXiv:2305.03474)
"""
import asyncio
from typing import Optional, Callable, Awaitable, List, Dict
from dataclasses import dataclass, field


@dataclass
class AgentMessage:
    """A message in the team chatroom."""
    agent: str
    content: str
    timestamp: int = 0


@dataclass
class TeamResult:
    """Result of team reasoning."""
    plan: str
    research: List[str]
    analysis: str
    critique: str
    final_answer: str
    messages: List[AgentMessage] = field(default_factory=list)


def build_leader_prompt(question: str) -> List[Dict]:
    """Build prompt for the Leader agent to plan the approach."""
    return [
        {"role": "system", "content": (
            "You are the Team Leader. Break down the user's question into 2-4 "
            "sub-questions that the team can research. Assign each sub-question "
            "to the Researcher. Be strategic — focus on the most important aspects."
        )},
        {"role": "user", "content": f"Question: {question}\n\nBreak this down into sub-questions."},
    ]


def build_researcher_prompt(sub_question: str, context: str = "") -> List[Dict]:
    """Build prompt for the Researcher agent."""
    return [
        {"role": "system", "content": (
            "You are the Researcher. Investigate the assigned sub-question thoroughly. "
            "Provide facts, data, and evidence. Be concise but comprehensive."
        )},
        {"role": "user", "content": (
            f"Sub-question: {sub_question}\n"
            f"Context: {context}\n\n"
            "Research this sub-question and provide your findings."
        )},
    ]


def build_analyst_prompt(research_findings: List[str], question: str) -> List[Dict]:
    """Build prompt for the Analyst agent."""
    findings_text = "\n\n".join(f"Finding {i+1}: {f}" for i, f in enumerate(research_findings))
    return [
        {"role": "system", "content": (
            "You are the Analyst. Analyze the research findings. Identify patterns, "
            "synthesize insights, and resolve any contradictions. Prepare the analysis "
            "for the Critic to review."
        )},
        {"role": "user", "content": (
            f"Original question: {question}\n\n"
            f"Research findings:\n{findings_text}\n\n"
            "Analyze these findings."
        )},
    ]


def build_critic_prompt(analysis: str, question: str) -> List[Dict]:
    """Build prompt for the Critic agent."""
    return [
        {"role": "system", "content": (
            "You are the Critic. Review the analysis for: logical errors, "
            "unsupported claims, missing perspectives, and quality issues. "
            "Be rigorous but constructive. If the analysis is solid, say so."
        )},
        {"role": "user", "content": (
            f"Original question: {question}\n\n"
            f"Analysis to review:\n{analysis}\n\n"
            "Review this analysis."
        )},
    ]


def build_synthesis_prompt(
    question: str,
    plan: str,
    research: List[str],
    analysis: str,
    critique: str,
) -> List[Dict]:
    """Build prompt for final synthesis."""
    research_text = "\n".join(f"- {r[:200]}" for r in research)
    return [
        {"role": "system", "content": (
            "You are the Synthesizer. Combine all the team's work into a single, "
            "coherent, high-quality answer. Incorporate the analysis and address "
            "any issues the Critic raised. Be comprehensive but clear."
        )},
        {"role": "user", "content": (
            f"Question: {question}\n\n"
            f"Plan: {plan}\n\n"
            f"Research findings:\n{research_text}\n\n"
            f"Analysis: {analysis}\n\n"
            f"Critic's review: {critique}\n\n"
            "Synthesize the final answer."
        )},
    ]


async def leader_plan(
    question: str,
    model_fn: Optional[Callable[[List[Dict]], Awaitable[str]]] = None,
) -> str:
    """Leader plans the approach."""
    messages = build_leader_prompt(question)
    if model_fn:
        return await model_fn(messages)
    return f"Plan: Investigate key aspects of: {question}"


async def researcher_investigate(
    sub_question: str,
    context: str = "",
    model_fn: Optional[Callable[[List[Dict]], Awaitable[str]]] = None,
) -> str:
    """Researcher investigates a sub-question."""
    messages = build_researcher_prompt(sub_question, context)
    if model_fn:
        return await model_fn(messages)
    return f"Research on: {sub_question}"


async def analyst_analyze(
    findings: List[str],
    question: str,
    model_fn: Optional[Callable[[List[Dict]], Awaitable[str]]] = None,
) -> str:
    """Analyst analyzes findings."""
    messages = build_analyst_prompt(findings, question)
    if model_fn:
        return await model_fn(messages)
    return f"Analysis of {len(findings)} findings for: {question}"


async def critic_review(
    analysis: str,
    question: str,
    model_fn: Optional[Callable[[List[Dict]], Awaitable[str]]] = None,
) -> str:
    """Critic reviews the analysis."""
    messages = build_critic_prompt(analysis, question)
    if model_fn:
        return await model_fn(messages)
    return "Review: Analysis appears sound. No major issues found."


async def synthesize(
    question: str,
    plan: str,
    research: List[str],
    analysis: str,
    critique: str,
    model_fn: Optional[Callable[[List[Dict]], Awaitable[str]]] = None,
) -> str:
    """Synthesize the final answer from all team outputs."""
    messages = build_synthesis_prompt(question, plan, research, analysis, critique)
    if model_fn:
        return await model_fn(messages)
    # Fallback: simple combination
    return f"{analysis}\n\n(Critic review: {critique})"


async def team_solve(
    question: str,
    model_fn: Optional[Callable[[List[Dict]], Awaitable[str]]] = None,
) -> TeamResult:
    """Full team reasoning pipeline.

    1. Leader plans → breaks question into sub-questions
    2. Researcher investigates each sub-question (parallel)
    3. Analyst analyzes findings
    4. Critic reviews analysis
    5. Synthesizer combines into final answer

    Args:
        question: The question to solve
        model_fn: Async LLM function

    Returns:
        TeamResult with all intermediate steps and final answer
    """
    chatroom: List[AgentMessage] = []
    tick = 0

    # Step 1: Leader plans
    plan = await leader_plan(question, model_fn)
    chatroom.append(AgentMessage(agent="Leader", content=plan, timestamp=tick))
    tick += 1

    # Parse sub-questions from plan (simple: split by numbered lines)
    import re
    sub_questions = re.findall(r'(?:\d+\.|[-•])\s+(.+)', plan)
    if not sub_questions:
        sub_questions = [question]

    # Step 2: Researcher investigates (sequential to maintain context)
    research_findings = []
    context = ""
    for sq in sub_questions[:4]:  # Max 4 sub-questions
        finding = await researcher_investigate(sq, context, model_fn)
        research_findings.append(finding)
        context += f"\n{finding[:200]}"
        chatroom.append(AgentMessage(agent="Researcher", content=finding, timestamp=tick))
        tick += 1

    # Step 3: Analyst analyzes
    analysis = await analyst_analyze(research_findings, question, model_fn)
    chatroom.append(AgentMessage(agent="Analyst", content=analysis, timestamp=tick))
    tick += 1

    # Step 4: Critic reviews
    critique = await critic_review(analysis, question, model_fn)
    chatroom.append(AgentMessage(agent="Critic", content=critique, timestamp=tick))
    tick += 1

    # Step 5: Synthesize
    final = await synthesize(question, plan, research_findings, analysis, critique, model_fn)
    chatroom.append(AgentMessage(agent="Synthesizer", content=final, timestamp=tick))

    return TeamResult(
        plan=plan,
        research=research_findings,
        analysis=analysis,
        critique=critique,
        final_answer=final,
        messages=chatroom,
    )


def format_chatroom(messages: List[AgentMessage]) -> str:
    """Format chatroom messages for display."""
    lines = []
    for msg in messages:
        lines.append(f"[{msg.agent}]: {msg.content[:200]}")
    return "\n\n".join(lines)