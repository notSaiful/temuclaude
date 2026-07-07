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

def build_quantization_research_prompt(topic: str, num_sections: int = 7) -> List[Dict]:
    """Build a specialized research outline prompt for LLM quantization and inference optimization topics.
    
    Tailored for researching techniques like AWQ, GPTQ, vLLM, and related
    model serving technologies. Ensures coverage of quantization methods,
    performance benchmarks, hardware compatibility, and deployment trade-offs.
    """
    return [
        {"role": "system", "content": (
            "You are a research planner specializing in LLM inference optimization "
            "and model quantization. Create a comprehensive research outline with "
            f"at least {num_sections} major sections. The outline must cover: "
            "(1) background on model quantization and activation-aware methods, "
            "(2) technical architecture of the target method (e.g., AWQ's salient "
            "weight detection and scaling), (3) comparison with competing inference "
            "engines (e.g., vLLM, TensorRT-LLM, llama.cpp), (4) performance "
            "benchmarks including throughput, latency, and memory footprint, "
            "(5) hardware compatibility (GPU types, CPU offloading, edge devices), "
            "(6) deployment considerations and integration patterns, "
            "(7) limitations, open problems, and future directions. "
            "Each section should have 3-5 subsections. Output as a numbered list."
        )},
        {"role": "user", "content": (
            f"Topic: {topic}\n\n"
            "Create a research outline focused on quantization and inference "
            "optimization. Ensure AWQ and vLLM are explicitly compared where relevant."
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


def build_awq_research_prompt(topic: str = "AWQ (Activation-aware Weight Quantization) vs vLLM") -> List[Dict]:
    """Build a specialized research prompt for AWQ quantization and vLLM comparison.
    
    Covers: quantization theory, AWQ algorithm details, vLLM architecture,
    performance benchmarks, memory efficiency, deployment considerations,
    and integration paths for the Temuclaude orchestration engine.
    """
    return [
        {"role": "system", "content": (
            "You are a deep research agent specializing in LLM inference optimization "
            "and quantization techniques. Produce a comprehensive, implementation-ready "
            "research report comparing AWQ (Activation-aware Weight Quantization) with "
            "vLLM as competing inference engines. Cover: (1) AWQ quantization algorithm "
            "and how it differs from GPTQ, SmoothQuant, and other methods; (2) vLLM's "
            "PagedAttention and continuous batching architecture; (3) memory footprint "
            "comparisons (AWQ 4-bit weight-only vs vLLM FP16/KV-cache management); "
            "(4) throughput and latency benchmarks across model sizes (7B, 13B, 70B); "
            "(5) hardware compatibility (GPU types, CPU offloading, Apple Silicon); "
            "(6) integration APIs and serving frameworks (how to load AWQ-quantized "
            "models, HuggingFace transformers support, AutoAWQ library); (7) practical "
            "deployment recommendations for an AI orchestration engine like Temuclaude "
            "that needs to serve multiple models efficiently. Include specific code "
            "examples for loading and serving AWQ models. Cite papers, benchmarks, "
            "and documentation where possible."
        )},
        {"role": "user", "content": (
            f"Research Topic: {topic}\n\n"
            "Sections to cover:\n"
            "1. Background: LLM quantization landscape and why weight-only quantization matters\n"
            "2. AWQ algorithm: activation-aware salient channel detection, scaling factor optimization\n"
            "3. vLLM architecture: PagedAttention, continuous batching, tensor parallelism\n"
            "4. Head-to-head comparison: throughput, latency, memory, accuracy degradation\n"
            "5. AutoAWQ and ecosystem: model conversion, supported architectures, HF integration\n"
            "6. Deployment in an orchestration engine: model loading, request routing, fallback strategies\n"
            "7. Future directions: fused kernels, multi-modal model support, edge deployment\n\n"
            "Write a complete, implementation-ready research report with code examples."
        )},
    ]
def build_quantization_comparison_prompt(topic: str, competitors: List[str], num_sections: int = 7) -> List[Dict]:
    """Build a specialized research outline prompt for quantization and inference engine comparisons.
    
    When the research topic involves model quantization techniques (e.g., AWQ, GPTQ, SmoothQuant)
    or inference engine comparisons (e.g., vLLM, TensorRT-LLM, TGI), this prompt ensures
    the outline covers technical dimensions critical to such evaluations: quantization
    methodology, kernel optimization, memory bandwidth, throughput/latency benchmarks,
    hardware compatibility, ease of deployment, and production readiness.
    
    Args:
        topic: The research topic (e.g., "AWQ vs vLLM for efficient LLM inference")
        competitors: List of competing technologies to compare (e.g., ["AWQ", "vLLM"])
        num_sections: Minimum number of sections in the outline
        
    Returns:
        List of message dicts suitable for an LLM chat completion call
    """
    competitor_text = ", ".join(competitors) if competitors else "the relevant technologies"
    return [
        {"role": "system", "content": (
            "You are a research planner specializing in LLM inference optimization and "
            "model quantization. Create a comprehensive research outline with at least "
            f"{num_sections} major sections. The outline must cover these technical "
            "dimensions for each technology being compared: "
            "(1) Quantization methodology and theoretical foundations, "
            "(2) Kernel implementation and CUDA/Triton optimization, "
            "(3) Memory footprint and bandwidth utilization, "
            "(4) Throughput and latency benchmarks across model sizes, "
            "(5) Hardware compatibility (GPU architectures, CPU, edge), "
            "(6) Deployment complexity and ecosystem integration, "
            "(7) Production readiness, community support, and maintenance. "
            "Each section should have 3-5 subsections. Include a section on "
            "benchmarking methodology to ensure fair comparisons. "
            "Output as a numbered list of sections with subsections."
        )},
        {"role": "user", "content": (
            f"Topic: {topic}\n"
            f"Technologies to compare: {competitor_text}\n\n"
            "Create a research outline that enables a rigorous technical comparison "
            "of these inference/quantization approaches."
        )},
    ]
def build_efficiency_evaluation_prompt(finding: str, topic: str) -> List[Dict]:
    """Build a prompt to evaluate an efficiency research finding for quality classification.
    
    Evaluates speedup, memory savings, and quality loss to classify as:
    LOSSLESS / QUALITY-PRESERVING / PARETO-OPTIMAL / REJECTED
    """
    return [
        {"role": "system", "content": (
            "You are an efficiency research evaluator. Analyze the finding for three metrics:\n"
            "1. Speedup factor (throughput increase, latency reduction)\n"
            "2. Memory/compute savings (VRAM reduction, FLOPs reduction)\n"
            "3. Quality loss (accuracy drop, perplexity increase, benchmark regression)\n\n"
            "Classify the finding into exactly one category:\n"
            "- LOSSLESS: Zero quality loss, any speedup/savings\n"
            "- QUALITY-PRESERVING: Negligible quality loss (<1% relative), significant speedup/savings\n"
            "- PARETO-OPTIMAL: Meaningful quality loss but optimal trade-off (best in class for given quality level)\n"
            "- REJECTED: Quality loss too high, or speedup/savings insufficient to justify loss\n\n"
            "Output format:\n"
            "CLASSIFICATION: <category>\n"
            "SPEEDUP: <factor or N/A>\n"
            "SAVINGS: <percentage or N/A>\n"
            "QUALITY_LOSS: <metric and value or N/A>\n"
            "JUSTIFICATION: <2-3 sentences>"
        )},
        {"role": "user", "content": (
            f"Research Topic: {topic}\n"
            f"Finding to Evaluate: {finding}\n\n"
            "Evaluate and classify this efficiency finding."
        )},
    ]

def build_awq_research_plan(topic: str = "AWQ (Activation-aware Weight Quantization) vs vLLM", num_sections: int = 6) -> List[Dict]:
    """Build a specialized research plan for AWQ quantization vs vLLM comparison."""
    return [
        {"role": "system", "content": (
            "You are a research planner specializing in LLM quantization techniques. "
            "Create a comprehensive research outline comparing AWQ (Activation-aware Weight Quantization) "
            "with vLLM's quantization approaches. Include at least 6 major sections with 3-5 subsections each. "
            "Cover: technical foundations, quantization algorithms, performance benchmarks, "
            "deployment considerations, integration with inference engines, and future directions. "
            "Output as a numbered list of sections with subsections."
        )},
        {"role": "user", "content": (
            f"Topic: {topic}\n\n"
            "Create a detailed research outline covering:\n"
            "1. AWQ algorithm fundamentals and activation-aware scaling\n"
            "2. vLLM quantization methods (AWQ, GPTQ, SmoothQuant, FP8)\n"
            "3. Comparative benchmarks: perplexity, latency, throughput, memory\n"
            "4. Hardware support: GPU (H100, A100, RTX 4090), CPU, Apple Silicon\n"
            "5. Integration patterns: vLLM AWQ backend, llama.cpp, TensorRT-LLM\n"
            "6. Production deployment: model serving, batching, KV cache quantization\n"
            "7. Temuclaude integration strategy for AWQ model orchestration\n\n"
            "Write as a numbered outline with subsections."
        )},
    ]


def build_awq_section_prompt(section_title: str, subsections: List[str], topic: str) -> List[Dict]:
    """Build a prompt to research one AWQ-specific section with technical depth."""
    sub_text = "\n".join(f"  - {s}" for s in subsections)
    return [
        {"role": "system", "content": (
            "You are a deep research agent specializing in LLM quantization. "
            "Write a comprehensive, technically rigorous section for a research report. "
            "Use prose with equations, pseudo-code, and architectural diagrams described in text. "
            "Include specific metrics: quantization error (L2), perplexity delta, "
            "tokens/sec, VRAM usage, kernel-level optimizations. "
            "Cite papers: AWQ (Lin et al. 2023), vLLM (Kwon et al. 2023), "
            "GPTQ (Frantar et al. 2022), SmoothQuant (Xiao et al. 2022). "
            "Write at least 2000 words for this section."
        )},
        {"role": "user", "content": (
            f"Research Topic: {topic}\n"
            f"Section: {section_title}\n"
            f"Subsections to cover:\n{sub_text}\n\n"
            "Write this section with full technical depth. Include:\n"
            "- Mathematical formulation of AWQ scaling factors\n"
            "- vLLM's PagedAttention interaction with quantized weights\n"
            "- Kernel fusion opportunities for INT4/FP8 GEMM\n"
            "- Calibration dataset requirements and sensitivity analysis\n"
            "- End-to-end latency breakdown (prefill vs decode)\n"
            "- Temuclaude orchestration implications"
        )},
    ]


def queue_awq_research_task(research_queue: asyncio.Queue, priority: int = 10) -> None:
    """Queue the AWQ research task with high priority for the deep research pipeline."""
    task = {
        "topic": "AWQ (Activation-aware Weight Quantization) implementation and vLLM competitive analysis",
        "priority": priority,
        "plan_prompt_builder": build_awq_research_plan_prompt,
        "min_words": 15000,
        "sections": 7,
        "metadata": {
            "source_finding": "swot_20260707T100738_missing_feature.json",
            "research_type": "implementation_ready",
            "target_module": "temuclaude.orchestration.quantization",
            "competitor": "vLLM",
        },
    }
    research_queue.put_nowait(task)

def build_efficiency_finding_prompt(finding: Dict) -> List[Dict]:
    """Build a deep research prompt for an efficiency finding (e.g., AWQ, vLLM).

    Instructs the LLM to research the specific technique, quantify speedup,
    cost savings, and quality loss, then classify under the quality guardrail.
    """
    title = finding.get("title", "Unknown Efficiency Finding")
    description = finding.get("description", finding.get("summary", ""))
    keywords = finding.get("keywords", [])
    keywords_str = ", ".join(keywords) if keywords else "N/A"
    return [
        {"role": "system", "content": (
            "You are a deep research agent specializing in LLM inference efficiency. "
            "Research the specified technique thoroughly. You MUST quantify ALL THREE "
            "of the following metrics where data is available:\n"
            "1. SPEEDUP — throughput or latency improvement (e.g., tokens/sec, % faster)\n"
            "2. SAVINGS — memory, VRAM, or cost reduction (e.g., GB saved, % less memory)\n"
            "3. QUALITY LOSS — any degradation in output quality (perplexity, accuracy, "
            "task benchmarks). If quality is preserved, state 'LOSSLESS'.\n\n"
            "After analysis, classify the finding into exactly one category:\n"
            "- LOSSLESS: no measurable quality loss, pure speed/memory gain\n"
            "- QUALITY-PRESERVING: negligible quality loss within noise threshold\n"
            "- PARETO-OPTIMAL: meaningful tradeoff (some quality loss for large gains)\n"
            "- REJECTED: quality loss outweighs efficiency gains or technique is "
            "inapplicable to this system\n\n"
            "Output a structured JSON object with keys: technique, speedup, savings, "
            "quality_loss, classification, evidence, recommendation, implementation_notes."
        )},
        {"role": "user", "content": (
            f"Efficiency Finding: {title}\n"
            f"Description: {description}\n"
            f"Keywords: {keywords_str}\n\n"
            "Conduct deep research on this technique. Compare against alternatives "
            "(e.g., vLLM, GPTQ, bitsandbytes). Provide concrete numbers from papers, "
            "benchmarks, or repos. End with your classification and a clear "
            "recommendation on whether to integrate into src/efficiency/."
        )},
    ]

def select_inference_backend(
    available_backends: List[str],
    require_low_latency: bool = True,
    latency_estimates: Optional[Dict[str, float]] = None,
) -> str:
    """
    Select the best inference backend for deep research workloads.

    Research findings indicate self-hosted vLLM incurs a significant latency
    penalty compared to managed API providers. When low latency is required
    (the default for interactive deep-research passes), deprioritize any
    backend whose name contains 'vllm' or 'self-hosted'.

    Args:
        available_backends: List of backend identifiers, e.g.
            ["anthropic", "openai", "vllm_self_hosted", "local_vllm"].
        require_low_latency: If True, avoid self-hosted vLLM backends.
        latency_estimates: Optional mapping of backend -> estimated latency
            in milliseconds. If provided, used to break ties / rank.

    Returns:
        The selected backend identifier.

    Raises:
        ValueError: If no backends are available.
    """
    if not available_backends:
        raise ValueError("No inference backends available for selection")

    latency_estimates = latency_estimates or {}

    def _is_self_hosted_vllm(name: str) -> bool:
        lowered = name.lower()
        return "vllm" in lowered and ("self" in lowered or "hosted" in lowered or "local" in lowered)

    def _latency(name: str) -> float:
        return latency_estimates.get(name, float("inf"))

    candidates = list(available_backends)

    if require_low_latency:
        filtered = [b for b in candidates if not _is_self_hosted_vllm(b)]
        if filtered:
            candidates = filtered

    candidates.sort(key=lambda b: (_is_self_hosted_vllm(b), _latency(b), b))

    return candidates[0]

def classify_awq_efficiency_finding(
    finding: Dict,
    speedup_estimate: float,
    memory_savings_pct: float,
    quality_loss_pct: float,
) -> Dict:
    """
    Classify an AWQ (Activation-aware Weight Quantization) efficiency finding
    according to Temuclaude quality guardrails.

    AWQ is a weight-only quantization technique that preserves activation
    precision while quantizing weights to 4-bit, achieving significant memory
    savings and inference speedup with minimal quality degradation. It is a
    direct competitor to vLLM's quantization strategies.

    Classification rules:
      - LOSSLESS: speedup >= 1.5x, memory savings >= 40%, quality loss == 0%
      - QUALITY-PRESERVING: speedup >= 1.5x, memory savings >= 40%, quality loss < 2%
      - PARETO-OPTIMAL: speedup >= 1.2x, memory savings >= 25%, quality loss < 5%
      - REJECTED: does not meet PARETO-OPTIMAL thresholds

    Args:
        finding: The research finding dict with keys like 'type', 'keywords'.
        speedup_estimate: Estimated inference speedup multiplier (e.g., 2.0 = 2x).
        memory_savings_pct: Estimated VRAM savings as a percentage (0-100).
        quality_loss_pct: Estimated quality degradation as a percentage (0-100).

    Returns:
        Dict with classification, metrics, and implementation recommendation.
    """
    classification = "REJECTED"
    rationale = "Does not meet minimum Pareto-optimal thresholds for adoption."

    thresholds = [
        ("LOSSLESS", 1.5, 40.0, 0.0),
        ("QUALITY-PRESERVING", 1.5, 40.0, 2.0),
        ("PARETO-OPTIMAL", 1.2, 25.0, 5.0),
    ]

    for label, min_speedup, min_savings, max_quality_loss in thresholds:
        if (
            speedup_estimate >= min_speedup
            and memory_savings_pct >= min_savings
            and quality_loss_pct <= max_quality_loss
        ):
            classification = label
            if label == "LOSSLESS":
                rationale = (
                    "AWQ achieves significant speedup and memory savings with "
                    "zero measurable quality loss — safe for production."
                )
            elif label == "QUALITY-PRESERVING":
                rationale = (
                    "AWQ achieves strong efficiency gains with negligible "
                    f"quality loss ({quality_loss_pct:.2f}%) — acceptable trade-off."
                )
            elif label == "PARETO-OPTIMAL":
                rationale = (
                    "AWQ offers a favorable speed/memory vs. quality trade-off "
                    "but quality loss is non-trivial — enable via config flag."
                )
            break

    implement = classification != "REJECTED"

    return {
        "finding_type": "EFFICIENCY",
        "technique": "AWQ",
        "competitor": "vLLM",
        "classification": classification,
        "rationale": rationale,
        "metrics": {
            "speedup_estimate": speedup_estimate,
            "memory_savings_pct": memory_savings_pct,
            "quality_loss_pct": quality_loss_pct,
        },
        "implement": implement,
        "target_path": "src/efficiency/awq_quantizer.py" if implement else None,
        "config_flag": "enable_awq_quantization" if implement else None,
        "default_enabled": classification in ("LOSSLESS", "QUALITY-PRESERVING"),
    }

def build_awq_vllm_comparison_prompt() -> List[Dict]:
    """Build a specialized research prompt for AWQ vs vLLM quantization comparison.
    
    AWQ (Activation-aware Weight Quantization) is a model quantization technique
    that competes with vLLM's quantization approaches. This prompt guides the
    research agent to produce an implementation-ready comparison covering
    architecture, performance, memory, accuracy, and deployment considerations.
    """
    return [
        {"role": "system", "content": (
            "You are a deep research agent specializing in LLM inference "
            "optimization and model quantization. Produce a comprehensive, "
            "implementation-ready comparison between AWQ (Activation-aware "
            "Weight Quantization) and vLLM's quantization and serving stack. "
            "Cover the following dimensions with concrete data, benchmarks, "
            "and code-level details: "
            "1) Quantization algorithm internals (how AWQ selects salient "
            "channels via activation magnitudes vs vLLM's supported methods "
            "such as GPTQ, AWQ integration, and bitsandbytes); "
            "2) Memory footprint and KV-cache handling; "
            "3) Throughput and latency benchmarks on common models "
            "(Llama-2 7B/13B/70B, Mistral 7B, Mixtral); "
            "4) Accuracy preservation (perplexity, MMLU, HumanEval) at "
            "4-bit and 8-bit configurations; "
            "5) Hardware compatibility (NVIDIA Ampere/Hopper, AMD, CPU); "
            "6) Deployment ergonomics: integration with Hugging Face "
            "Transformers, vLLM engine, TensorRT-LLM, and exllamav2; "
            "7) When to choose AWQ-native serving vs vLLM with AWQ weights; "
            "8) Known limitations, community support, and roadmap. "
            "Include code snippets for loading an AWQ-quantized model in "
            "both the AutoAWQ library and vLLM. Cite sources with URLs."
        )},
        {"role": "user", "content": (
            "Research and produce an implementation-ready report comparing "
            "AWQ quantization with vLLM as inference engines. Include "
            "practical guidance for integrating AWQ-quantized models into "
            "a Python-based AI orchestration engine, including pip "
            "dependencies, model loading code, and a benchmark harness "
            "snippet."
        )},
    ]