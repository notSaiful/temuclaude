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

def cascade_route_research_call(
    messages: List[Dict],
    cheap_model_call: Callable[[List[Dict]], Awaitable[str]],
    expensive_model_call: Callable[[List[Dict]], Awaitable[str]],
    quality_check: Optional[Callable[[str], Awaitable[bool]]] = None,
    min_word_count: int = 0,
    max_retries: int = 1,
) -> Awaitable[str]:
    """
    RouteLLM-style cascade routing for deep research calls.

    Tries a cheap model first. If the output fails a quality gate
    (word count threshold and/or async quality checker), escalates
    to the expensive model. This preserves quality while cutting
    costs — cheap model handles easy sections, expensive model
    only invoked for hard ones.

    Args:
        messages: Chat messages to send.
        cheap_model_call: Async callable for the cheap/weak model.
        expensive_model_call: Async callable for the expensive/strong model.
        quality_check: Optional async predicate; returns True if output is acceptable.
        min_word_count: Minimum word count for the output to pass.
        max_retries: Times to retry the cheap model before escalating.

    Returns:
        The accepted output string.
    """
    async def _run() -> str:
        for attempt in range(max_retries + 1):
            output = await cheap_model_call(messages)
            word_count = len(output.split())
            if word_count >= min_word_count:
                if quality_check is None:
                    return output
                if await quality_check(output):
                    return output
        return await expensive_model_call(messages)

    return _run()

def build_media_generation_research_prompt(topic: str, frontier_models: List[str], priority_score: int = 0) -> List[Dict]:
    """Build a specialized research prompt for media generation topics.

    Tailored for topics like s3_verifier_guided_denoising, this prompt instructs
    the research agent to search arXiv, GitHub, HuggingFace, and Artificial Analysis,
    identify frontier models to beat, and produce an implementation-ready report
    suitable for auto-integration into src/media/.
    """
    frontier_text = ", ".join(frontier_models) if frontier_models else "current frontier media models"
    return [
        {"role": "system", "content": (
            "You are a deep research agent specializing in media generation "
            "(image, video, audio synthesis). Your mission is to produce an "
            "implementation-ready research report that identifies techniques, "
            "architectures, and models that can beat current frontier systems. "
            "Search arXiv for latest papers, GitHub for open-source implementations, "
            "HuggingFace for model checkpoints and spaces, and Artificial Analysis "
            "for benchmark scores. Focus on verifier-guided denoising, classifier-free "
            "guidance variants, reward-model-guided sampling, and any novel sampling "
            "strategies that improve fidelity, coherence, or prompt adherence. "
            "For each technique found, provide: (1) paper reference, (2) core algorithm "
            "description, (3) reported metrics vs frontier baselines, (4) open-source "
            "availability, (5) integration difficulty estimate, and (6) recommended "
            "placement within a media generation pipeline. Conclude with a ranked "
            "list of models and techniques to add to the model pool."
        )},
        {"role": "user", "content": (
            f"Research Topic: {topic}\n"
            f"Frontier models to beat: {frontier_text}\n"
            f"Priority Score: {priority_score}\n\n"
            "Conduct a comprehensive deep search and produce an implementation-ready "
            "media generation report. Identify which frontier models and techniques "
            "should be added to the pool for auto-integration into src/media/. "
            "Include specific architecture details, sampling parameters, and code "
            "snippets where available."
        )},
    ]

def select_model_for_section(
    section_title: str,
    subsections: List[str],
    topic: str,
    complexity_threshold: float = 0.5,
    cheap_model: str = "gpt-4o-mini",
    expensive_model: str = "gpt-4o",
    fallback_model: str = "gpt-4o",
) -> Dict:
    """
    RouteLLM-style cascade routing for deep research sections.

    Estimates section complexity using lightweight heuristics and selects
    the appropriate model tier. Simple sections (background, definitions)
    go to the cheap model; complex sections (analysis, debates, synthesis)
    go to the expensive model. This preserves quality while cutting cost
    on the majority of sections that don't require frontier reasoning.

    Returns a dict with:
        - model: selected model name
        - complexity: estimated complexity score (0.0–1.0)
        - rationale: human-readable reason for the routing decision
    """
    # Heuristic complexity signals
    complexity_signals = {
        "background": 0.15,
        "introduction": 0.20,
        "overview": 0.20,
        "definition": 0.15,
        "history": 0.25,
        "current state": 0.35,
        "key findings": 0.55,
        "results": 0.55,
        "analysis": 0.75,
        "debates": 0.80,
        "controversy": 0.85,
        "future directions": 0.65,
        "implications": 0.70,
        "limitations": 0.60,
        "methodology": 0.65,
        "comparison": 0.60,
        "synthesis": 0.85,
        "conclusion": 0.40,
        "summary": 0.30,
    }

    title_lower = section_title.lower()
    combined_text = title_lower + " " + " ".join(s.lower() for s in subsections)

    # Base complexity from keyword matching
    matched_scores = []
    for keyword, score in complexity_signals.items():
        if keyword in combined_text:
            matched_scores.append(score)

    if matched_scores:
        complexity = sum(matched_scores) / len(matched_scores)
    else:
        complexity = 0.40  # default moderate

    # Boost complexity for sections with many subsections (more ground to cover)
    if len(subsections) >= 5:
        complexity = min(1.0, complexity + 0.10)

    # Boost complexity if the topic itself looks technical
    technical_markers = ["algorithm", "neural", "quantum", "optimization",
                         "theorem", "architecture", "protocol", "cryptograph"]
    topic_lower = topic.lower()
    if any(marker in topic_lower for marker in technical_markers):
        complexity = min(1.0, complexity + 0.10)

    # Routing decision
    if complexity >= complexity_threshold:
        model = expensive_model
        rationale = (
            f"High complexity ({complexity:.2f} >= {complexity_threshold}) — "
            f"using expensive model for quality preservation."
        )
    else:
        model = cheap_model
        rationale = (
            f"Low complexity ({complexity:.2f} < {complexity_threshold}) — "
            f"routing to cheap model for cost savings."
        )

    return {
        "model": model,
        "complexity": round(complexity, 3),
        "rationale": rationale,
        "fallback_model": fallback_model,
    }

def build_efficiency_research_prompt(finding: Dict, topic: str) -> List[Dict]:
    """Build a prompt to deep-research an efficiency finding (e.g., AWQ, vLLM)
    and classify it under the quality guardrail system.

    The prompt instructs the LLM to:
    1. Research the specific technique, paper, or repo
    2. Quantify speedup, memory/compute savings, and quality impact
    3. Classify as LOSSLESS / QUALITY-PRESERVING / PARETO-OPTIMAL / REJECTED
    """
    technique = finding.get("title", topic)
    finding_type = finding.get("type", "unknown")
    keywords = finding.get("keywords", [])
    keywords_str = ", ".join(keywords) if keywords else "N/A"

    return [
        {"role": "system", "content": (
            "You are a deep research agent specializing in LLM inference efficiency. "
            "Your task is to research a specific efficiency technique and produce a "
            "rigorous analysis covering ALL THREE impact dimensions:\n"
            "1. SPEEDUP — measured or estimated inference speed improvement (e.g., tokens/sec, latency reduction)\n"
            "2. SAVINGS — memory footprint reduction, compute cost savings, or hardware requirements lowered\n"
            "3. QUALITY LOSS — any degradation in output quality (perplexity increase, accuracy drop, etc.)\n\n"
            "After analysis, you MUST classify the technique into exactly one category:\n"
            "  - LOSSLESS: No measurable quality degradation; pure speed/efficiency gain\n"
            "  - QUALITY-PRESERVING: Negligible quality loss (<1% accuracy/perplexity delta) with significant speedup\n"
            "  - PARETO-OPTIMAL: Meaningful quality loss but proportional or greater efficiency gain; acceptable tradeoff\n"
            "  - REJECTED: Quality loss outweighs efficiency benefits; not worth adopting\n\n"
            "Cite specific papers, benchmarks, and repository data where available. "
            "Write at least 1500 words. Structure your response as:\n"
            "## Technique Overview\n## Speedup Analysis\n## Savings Analysis\n## Quality Impact Analysis\n## Benchmark Comparison\n## Classification: <CATEGORY>\n## Implementation Recommendations"
        )},
        {"role": "user", "content": (
            f"Research Topic: {technique}\n"
            f"Finding Type: {finding_type}\n"
            f"Keywords: {keywords_str}\n"
            f"Topic Context: {topic}\n\n"
            "Conduct a comprehensive efficiency analysis of this technique. "
            "Compare against known alternatives (e.g., if researching AWQ, compare "
            "against GPTQ, bitsandbytes, and unquantized baselines). "
            "Provide concrete numbers wherever possible and conclude with the classification."
        )},
    ]

def classify_efficiency_finding(
    speedup_factor: float,
    memory_savings_pct: float,
    quality_loss_pct: float,
    technique_name: str = "",
) -> str:
    """
    Classify an efficiency finding into one of four quality guardrail buckets.

    Used to gate whether a technique (e.g. AWQ quantization, vLLM-style
    paged attention) is safe to auto-integrate into src/efficiency/.

    Classification rules:
      - LOSSLESS          : zero measurable quality loss
      - QUALITY-PRESERVING: quality loss < 1% (imperceptible)
      - PARETO-OPTIMAL    : quality loss >= 1% but speedup or savings
                            justify the trade-off (speedup >= 1.5x OR
                            memory savings >= 30%)
      - REJECTED          : quality loss too high for the gains offered

    Args:
        speedup_factor:    Inference speedup as a multiplier (1.0 = no change).
        memory_savings_pct: Percentage of memory saved (0-100).
        quality_loss_pct:  Percentage of quality degradation (0-100).
        technique_name:    Optional name for logging/debugging.

    Returns:
        One of: "LOSSLESS", "QUALITY-PRESERVING",
                "PARETO-OPTIMAL", "REJECTED".
    """
    if quality_loss_pct <= 0.0:
        return "LOSSLESS"

    if quality_loss_pct < 1.0:
        return "QUALITY-PRESERVING"

    meaningful_speedup = speedup_factor >= 1.5
    meaningful_savings = memory_savings_pct >= 30.0

    if meaningful_speedup or meaningful_savings:
        return "PARETO-OPTIMAL"

    return "REJECTED"
def build_competitor_analysis_prompt(topic: str, competitors: List[str], focus_areas: Optional[List[str]] = None) -> List[Dict]:
    """Build a specialized prompt for competitor analysis research (e.g., AWQ vs vLLM).
    
    Generates a structured research plan tailored to comparing ML inference/quantization
    technologies, covering architecture, performance benchmarks, deployment, and ecosystem.
    """
    if focus_areas is None:
        focus_areas = [
            "Architecture & Core Design",
            "Quantization Methodology",
            "Performance Benchmarks (throughput, latency, memory)",
            "Hardware Compatibility & Deployment",
            "Ease of Integration & API Design",
            "Community & Ecosystem Maturity",
            "Limitations & Trade-offs",
            "Future Roadmap & Industry Adoption",
        ]
    competitors_text = ", ".join(competitors)
    focus_text = "\n".join(f"  {i+1}. {area}" for i, area in enumerate(focus_areas))
    return [
        {"role": "system", "content": (
            "You are a competitive intelligence research planner specializing in "
            "ML inference and model quantization technologies. Create a detailed "
            "research outline that systematically compares the specified technologies. "
            "For each focus area, define 3-5 subsections with specific metrics, "
            "benchmarks, or qualitative criteria to evaluate. Prioritize verifiable "
            "data: published benchmarks, GitHub metrics, paper citations, and "
            "production deployment reports. Flag areas where public data is scarce "
            "so the research agent can search deeper."
        )},
        {"role": "user", "content": (
            f"Topic: {topic}\n"
            f"Technologies to compare: {competitors_text}\n\n"
            f"Suggested focus areas:\n{focus_text}\n\n"
            "Create a comprehensive competitor analysis research outline. "
            "Include a section on quantitative benchmark comparison and a "
            "section on practical deployment recommendations."
        )},
    ]

def build_quantization_research_prompt(topic: str, competitor: str = "vLLM") -> List[Dict]:
    """Build a specialized research prompt for LLM quantization and inference optimization topics
    such as AWQ, GPTQ, SmoothQuant, and their competitors like vLLM, TGI, or TensorRT-LLM.
    
    Pre-populates subsections with domain-relevant areas to ensure comprehensive coverage
    of quantization techniques, performance benchmarks, and deployment considerations.
    """
    quantization_subsections = [
        "Background and motivation: why LLM quantization matters (memory, cost, latency)",
        "Core algorithm: activation-aware weight quantization methodology and key innovations",
        "Comparison with alternative quantization methods (GPTQ, SmoothQuant, bitsandbytes, GGUF)",
        f"Competitor analysis: {competitor} and other inference engines (TGI, TensorRT-LLM, llama.cpp)",
        "Performance benchmarks: throughput, latency, memory footprint, accuracy retention",
        "Hardware compatibility: GPU types, CPU offloading, edge deployment scenarios",
        "Integration and deployment: supported model architectures, serving frameworks, APIs",
        "Limitations, open issues, and future research directions",
    ]
    sub_text = "\n".join(f"  - {s}" for s in quantization_subsections)
    return [
        {"role": "system", "content": (
            "You are a deep research agent specializing in LLM inference optimization and "
            "model quantization. Write a comprehensive, technically accurate research section. "
            "Include specific numbers, benchmark results, and citations where possible. "
            "Compare methodologies rigorously. Write at least 2000 words for this section."
        )},
        {"role": "user", "content": (
            f"Research Topic: {topic}\n"
            f"Competitor / Comparison Target: {competitor}\n"
            f"Subsections to cover:\n{sub_text}\n\n"
            "Write this section in full with technical depth, including any known "
            "benchmark numbers, model compatibility tables, and deployment trade-offs."
        )},
    ]

def build_media_research_prompt(topic: str, mission: str = "BEAT FRONTIERS", 
                                frontier_models: Optional[List[str]] = None,
                                target_dir: str = "src/media/") -> List[Dict]:
    """Build a research prompt specialized for media generation topics.
    
    Tailored for verifier-guided denoising and similar media generation
    research, incorporating frontier model benchmarks and implementation
    readiness requirements.
    """
    if frontier_models is None:
        frontier_models = [
            "GPT Image 2", "Sora 2", "Veo 3.1", "Runway Gen-4.5"
        ]
    frontiers_text = ", ".join(frontier_models)
    return [
        {"role": "system", "content": (
            "You are a deep research agent specializing in media generation "
            "AI (image, video, audio synthesis). Your mission is to produce "
            f"implementation-ready reports that help BEAT frontier models "
            f"({frontiers_text}).\n\n"
            "Conduct deep search across:\n"
            "1. arXiv — latest papers on diffusion, verifier-guided denoising, "
            "classifier-free guidance, reward-guided sampling, DPO for diffusion\n"
            "2. GitHub — reference implementations, code snippets, repos\n"
            "3. HuggingFace — model checkpoints, pipelines, diffusers integrations\n"
            "4. Artificial Analysis — benchmark scores and leaderboards\n\n"
            "Your report must include:\n"
            "- Technical architecture of the proposed approach\n"
            "- Verifier model design (what guides the denoising)\n"
            "- Training and inference pipeline details\n"
            "- Quantitative comparison vs frontier models\n"
            "- Concrete Python implementation plan for "
            f"{target_dir}\n"
            "- Which frontier models to add to the model pool\n"
            "- Risks, limitations, and fallback strategies\n\n"
            "Write at least 10000 words. Use prose with code blocks where helpful."
        )},
        {"role": "user", "content": (
            f"Research Topic: {topic}\n"
            f"Mission: {mission}\n"
            f"Frontier targets to beat: {frontiers_text}\n"
            f"Implementation target: {target_dir}\n\n"
            "Produce a comprehensive, implementation-ready media generation "
            "research report covering verifier-guided denoising and related "
            "techniques. Include specific algorithmic details, pseudocode, "
            "and a step-by-step integration plan."
        )},
    ]

def build_technical_comparison_prompt(topic: str, competitors: List[str], num_sections: int = 6) -> List[Dict]:
    """Build a research outline prompt specialized for technical feature comparisons
    such as AWQ vs vLLM quantization/inference engines.
    
    Produces sections covering: architecture, quantization methods, performance
    benchmarks, memory efficiency, deployment ergonomics, and ecosystem support.
    """
    competitor_text = " vs ".join(competitors) if competitors else "competing solutions"
    return [
        {"role": "system", "content": (
            "You are a technical research planner specializing in ML infrastructure "
            "and LLM inference optimization. Create a comprehensive research outline "
            f"with at least {num_sections} major sections comparing {competitor_text}. "
            "Each section should have 3-5 subsections. Cover these dimensions: "
            "(1) Architecture & design philosophy, (2) Quantization techniques "
            "(e.g., AWQ, GPTQ, SmoothQuant, FP8) and their mathematical foundations, "
            "(3) Throughput and latency benchmarks on common hardware (A100, H100, "
            "consumer GPUs), (4) Memory footprint and KV-cache management, "
            "(5) Deployment, API compatibility, and ease of integration, "
            "(6) Community ecosystem, supported models, and roadmap. "
            "Output as a numbered list of sections with subsections."
        )},
        {"role": "user", "content": (
            f"Topic: {topic}\n"
            f"Competitors to compare: {competitor_text}\n\n"
            "Create a detailed technical comparison research outline."
        )},
    ]

def build_technical_comparison_plan_prompt(topic: str, competitors: List[str], num_sections: int = 7) -> List[Dict]:
    """Build a specialized research outline prompt for technical competitive analysis
    (e.g., AWQ vs vLLM quantization/inference engine comparison).
    
    Produces a more structured outline than the generic planner, with sections
    tailored to benchmarking, architecture, and deployment tradeoffs.
    """
    competitor_text = ", ".join(competitors) if competitors else "relevant alternatives"
    return [
        {"role": "system", "content": (
            "You are a technical research planner specializing in ML infrastructure "
            "and LLM inference systems. Create a comprehensive research outline "
            f"with at least {num_sections} major sections for a technical comparison. "
            "Include these mandatory sections when applicable: "
            "(1) Background & Problem Statement, "
            "(2) Architecture & Core Algorithms, "
            "(3) Quantization / Optimization Techniques, "
            "(4) Performance Benchmarks & Throughput Metrics, "
            "(5) Memory & Hardware Requirements, "
            "(6) Deployment & Ecosystem Comparison, "
            "(7) Tradeoffs, Limitations, and Future Directions. "
            "Each section should have 3-5 subsections with specific technical focus. "
            "Output as a numbered list of sections with subsections."
        )},
        {"role": "user", "content": (
            f"Topic: {topic}\n"
            f"Technologies to compare: {competitor_text}\n\n"
            "Create a technical research outline suitable for engineers and "
            "researchers evaluating these systems for production deployment."
        )},
    ]

from typing import Optional, Callable, Awaitable, List, Dict


def build_awq_research_prompt(topic: str = "AWQ (Activation-aware Weight Quantization) vs vLLM quantization") -> List[Dict]:
    """Build a specialized deep research prompt for AWQ quantization vs vLLM.
    
    AWQ is a weight-only quantization method that protects salient weights
    by observing activation magnitudes, achieving better accuracy than
    GPTQ at 4-bit/3-bit. vLLM uses AWQ kernels for fast inference.
    This prompt covers technical details, benchmarks, and integration.
    """
    return [
        {"role": "system", "content": (
            "You are a deep research agent specializing in LLM quantization. "
            "Write a comprehensive technical section comparing AWQ (Activation-aware "
            "Weight Quantization) with vLLM's quantization stack. Cover: "
            "1) AWQ algorithm (salient weight detection via activation scaling), "
            "2) vLLM's AWQ kernel implementation (fused kernels, Marlin, GEMM), "
            "3) Benchmark comparisons (perplexity, latency, throughput at 4-bit/3-bit), "
            "4) Integration patterns (AutoAWQ, llm-compressor, vLLM AWQ backend), "
            "5) Limitations and future directions (W4A8, W4A4, kernel fusion). "
            "Include specific numbers from papers (AWQ: arXiv:2306.00978, "
            "vLLM AWQ benchmarks). Write at least 2000 words with citations."
        )},
        {"role": "user", "content": (
            f"Research Topic: {topic}\n\n"
            "Produce a detailed technical comparison suitable for engineers "
            "evaluating quantization backends for production LLM serving."
        )},
    ]
