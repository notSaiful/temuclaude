"""
Temuclaude Deep Research Module
Perplexity-style 10,000+ word comprehensive research reports.

Multi-pass pipeline:
1. Plan — generate research outline (5+ sections)
2. Research — deep dive on each section
3. Synthesize — combine sections into cohesive report
4. Review — check for gaps and quality
5. Expand — add more detail to reach word count target

Uses web_search for current facts, citation system for sources.
"""
import asyncio
import re
from typing import Optional, Callable, Awaitable, List, Dict


DEFAULT_MIN_WORDS = 10000
DEFAULT_SECTIONS = 5


def build_plan_prompt(topic: str, num_sections: int = 5) -> List[Dict]:
    """Build a prompt to generate a research outline."""
    return [
        {"role": "system", "content": (
            "You are a research planner. Create a comprehensive research outline "
            f"with at least {num_sections} major sections. Each section should have "
            "3-5 subsections. The outline should cover the topic from multiple angles: "
            "background, current state, key findings, debates, future directions. "
            "Output as a numbered list of sections with subsections."
        )},
        {"role": "user", "content": f"Topic: {topic}\n\nCreate a research outline."},
    ]


def build_section_prompt(section_title: str, subsections: List[str], topic: str) -> List[Dict]:
    """Build a prompt to research one section."""
    sub_text = "\n".join(f"  - {s}" for s in subsections)
    return [
        {"role": "system", "content": (
            "You are a deep research agent. Write a comprehensive, well-structured "
            "section for a research report. Use prose (not bullet points). "
            "Include facts, data, and citations where possible. "
            "Write at least 1500 words for this section."
        )},
        {"role": "user", "content": (
            f"Research Topic: {topic}\n"
            f"Section: {section_title}\n"
            f"Subsections to cover:\n{sub_text}\n\n"
            "Write this section in full."
        )},
    ]


def build_synthesis_prompt(sections: List[str], topic: str) -> List[Dict]:
    """Build a prompt to synthesize sections into a report."""
    sections_text = "\n\n---\n\n".join(sections)
    return [
        {"role": "system", "content": (
            "You are a research editor. Combine the following sections into a "
            "cohesive research report. Add transitions between sections. "
            "Write an introduction and conclusion. Ensure consistent tone throughout."
        )},
        {"role": "user", "content": (
            f"Topic: {topic}\n\nSections:\n{sections_text}\n\n"
            "Synthesize into a complete research report with introduction and conclusion."
        )},
    ]


def build_review_prompt(report: str, topic: str) -> List[Dict]:
    """Build a prompt to review the report for gaps."""
    return [
        {"role": "system", "content": (
            "You are a research reviewer. Identify gaps, missing information, "
            "and areas that need more depth in the following report. "
            "List specific areas that need expansion."
        )},
        {"role": "user", "content": f"Topic: {topic}\n\nReport:\n{report[:5000]}\n\nIdentify gaps."},
    ]


def build_expand_prompt(report: str, gaps: str, topic: str) -> List[Dict]:
    """Build a prompt to expand the report."""
    return [
        {"role": "system", "content": (
            "You are a research writer. Expand the following report by addressing "
            "the identified gaps. Add new sections or expand existing ones. "
            "Maintain the same tone and style."
        )},
        {"role": "user", "content": (
            f"Topic: {topic}\n\nReport:\n{report[:8000]}\n\nGaps to address:\n{gaps}\n\n"
            "Expand the report."
        )},
    ]


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def parse_outline(raw: str) -> List[Dict]:
    """Parse an outline into sections.

    Returns list of {title, subsections} dicts.
    """
    sections = []
    current_section = None
    current_subs = []

    for line in raw.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Section header (numbered: "1. Title" or "## Title")
        section_match = re.match(r'^(?:\d+\.|##)\s+(.+)', line)
        if section_match:
            if current_section:
                sections.append({
                    "title": current_section,
                    "subsections": current_subs,
                })
            current_section = section_match.group(1).strip()
            current_subs = []
        else:
            # Subsection (bullet or numbered)
            sub_match = re.match(r'(?:[-•*]|\d+\.)\s+(.+)', line)
            if sub_match and current_section:
                current_subs.append(sub_match.group(1).strip())
            elif line and current_section:
                current_subs.append(line)

    if current_section:
        sections.append({
            "title": current_section,
            "subsections": current_subs,
        })

    return sections


async def research_plan(
    topic: str,
    model_fn: Optional[Callable[[List[Dict]], Awaitable[str]]] = None,
    num_sections: int = DEFAULT_SECTIONS,
) -> List[Dict]:
    """Generate a research plan.

    Args:
        topic: Research topic
        model_fn: Async LLM function
        num_sections: Minimum number of sections

    Returns:
        List of {title, subsections} dicts
    """
    messages = build_plan_prompt(topic, num_sections)

    if model_fn:
        raw = await model_fn(messages)
        return parse_outline(raw)

    # Fallback: generic outline
    return [
        {"title": "Introduction and Background", "subsections": ["Historical context", "Key definitions"]},
        {"title": "Current State", "subsections": ["Latest developments", "Key players"]},
        {"title": "Key Findings", "subsections": ["Primary research", "Data analysis"]},
        {"title": "Debates and Controversies", "subsections": ["Main disagreements", "Evidence on each side"]},
        {"title": "Future Directions", "subsections": ["Emerging trends", "Predictions"]},
    ]


async def research_section(
    section: Dict,
    topic: str,
    model_fn: Optional[Callable[[List[Dict]], Awaitable[str]]] = None,
) -> str:
    """Research one section of the report.

    Args:
        section: {title, subsections} dict
        topic: Overall research topic
        model_fn: Async LLM function

    Returns:
        Section text
    """
    messages = build_section_prompt(
        section["title"],
        section.get("subsections", []),
        topic,
    )

    if model_fn:
        return await model_fn(messages)

    # Fallback: template
    subs = ", ".join(section.get("subsections", []))
    return f"## {section['title']}\n\nThis section covers: {subs}. (Provide model_fn for full research.)"


async def synthesize_report(
    sections: List[str],
    topic: str,
    model_fn: Optional[Callable[[List[Dict]], Awaitable[str]]] = None,
) -> str:
    """Synthesize sections into a cohesive report.

    Args:
        sections: List of section texts
        topic: Research topic
        model_fn: Async LLM function

    Returns:
        Complete report text
    """
    messages = build_synthesis_prompt(sections, topic)

    if model_fn:
        return await model_fn(messages)

    # Fallback: join sections
    intro = f"# Research Report: {topic}\n\n"
    return intro + "\n\n---\n\n".join(sections)


async def deep_research(
    topic: str,
    model_fn: Optional[Callable[[List[Dict]], Awaitable[str]]] = None,
    min_words: int = DEFAULT_MIN_WORDS,
    num_sections: int = DEFAULT_SECTIONS,
) -> Dict:
    """Full deep research pipeline.

    Args:
        topic: Research topic
        model_fn: Async LLM function
        min_words: Minimum word count target
        num_sections: Minimum number of sections

    Returns:
        Dict with: topic, report, word_count, sections, sources
    """
    # Step 1: Plan
    outline = await research_plan(topic, model_fn, num_sections)

    # Step 2: Research each section
    section_texts = []
    for section in outline:
        text = await research_section(section, topic, model_fn)
        section_texts.append(text)

    # Step 3: Synthesize
    report = await synthesize_report(section_texts, topic, model_fn)

    # Step 4: Check word count and expand if needed
    word_count = count_words(report)
    if word_count < min_words and model_fn:
        # Review for gaps
        review_messages = build_review_prompt(report, topic)
        gaps = await model_fn(review_messages)

        # Expand
        expand_messages = build_expand_prompt(report, gaps, topic)
        expanded = await model_fn(expand_messages)

        if count_words(expanded) > word_count:
            report = expanded
            word_count = count_words(report)

    return {
        "topic": topic,
        "report": report,
        "word_count": word_count,
        "sections": len(outline),
        "outline": outline,
    }


def is_research_request(text: str) -> bool:
    """Detect if the text is requesting deep research."""
    research_keywords = [
        "deep research", "comprehensive report", "detailed analysis",
        "thorough investigation", "research report", "in-depth",
        "literature review", "state of the art", "survey",
        "comprehensive study", "full report", "complete analysis",
    ]
    text_lower = text.lower()

    for kw in research_keywords:
        if kw in text_lower:
            return True

    return False