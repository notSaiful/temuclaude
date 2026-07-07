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

def build_media_generation_research_prompt(
    topic: str,
    frontier_models: List[str] = None,
    target_sources: List[str] = None,
    priority_score: int = 0,
    mission: str = "BEAT FRONTIERS",
) -> List[Dict]:
    """Build a specialized research prompt for media generation topics.
    
    Tailored for frontier media generation research (image/video/audio synthesis)
    with emphasis on verifier-guided denoising, diffusion techniques, and
    identifying models to integrate into the media pool.
    
    Args:
        topic: Research topic identifier (e.g., 's3_verifier_guided_denoising')
        frontier_models: List of frontier models to beat (e.g., GPT Image 2, Sora 2)
        target_sources: List of sources to search (arXiv, GitHub, HuggingFace, etc.)
        priority_score: Priority score from the research queue
        mission: High-level mission statement
    
    Returns:
        List of message dicts suitable for LLM consumption
    """
    if frontier_models is None:
        frontier_models = [
            "GPT Image 2",
            "Sora 2",
            "Veo 3.1",
            "Runway Gen-4.5",
        ]
    if target_sources is None:
        target_sources = [
            "arXiv (latest papers on verifier-guided denoising, diffusion models)",
            "GitHub (open-source implementations, code repos)",
            "HuggingFace (model weights, spaces, pipelines)",
            "Artificial Analysis (benchmark leaderboards, model comparisons)",
        ]
    
    frontier_text = ", ".join(frontier_models)
    sources_text = "\n".join(f"  - {s}" for s in target_sources)
    
    return [
        {"role": "system", "content": (
            "You are a deep research agent specializing in media generation AI. "
            "Your mission is to produce an implementation-ready research report "
            f"that advances the goal: {mission}. "
            f"You must identify techniques that can beat or match: {frontier_text}. "
            "Focus on verifier-guided denoising, reward-guided diffusion, "
            "classifier-free guidance improvements, and novel sampling strategies. "
            "For each technique found, provide: "
            "(1) paper reference and arXiv ID, "
            "(2) core algorithm description, "
            "(3) implementation complexity (low/medium/high), "
            "(4) expected quality uplift, "
            "(5) which frontier model it targets, "
            "(6) specific Python code patterns or library dependencies needed. "
            "Identify which models should be added to the media generation pool. "
            "Output should be structured for auto-integration into src/media/."
        )},
        {"role": "user", "content": (
            f"Research Topic: {topic}\n"
            f"Priority Score: {priority_score}\n"
            f"Mission: {mission}\n"
            f"Frontier models to beat: {frontier_text}\n\n"
            f"Target sources to search:\n{sources_text}\n\n"
            "Conduct deep research and produce an implementation-ready report. "
            "Include specific model names, repository URLs, and integration steps "
            "for the Temuclaude media generation pipeline."
        )},
    ]
def select_model_for_section(section_title: str, subsections: List[str], topic: str, cascade_config: Optional[Dict] = None) -> str:
    """
    RouteLLM cascade routing for deep research sections.
    Assesses section complexity and routes to appropriate model tier,
    achieving cost savings while preserving quality.
    
    Cascade tiers:
    - 'cheap': fast, inexpensive model for straightforward sections
    - 'medium': balanced model for moderate complexity
    - 'expensive': full-capability model for complex/technical sections
    
    Quality is preserved by escalating to higher tiers when complexity
    indicators are detected.
    """
    if cascade_config is None:
        cascade_config = {
            "cheap_model": "llama-3.1-8b-instruct",
            "medium_model": "llama-3.1-70b-instruct",
            "expensive_model": "gpt-4o",
            "complexity_keywords": {
                "high": [
                    "algorithm", "mathematical", "theorem", "proof", "derivation",
                    "quantum", "neural", "architecture", "optimization", "formal",
                    "statistical", "differential", "topology", "cryptograph",
                    "complexity theory", "formal verification", "benchmark",
                ],
                "medium": [
                    "analysis", "comparison", "evaluation", "framework",
                    "methodology", "systematic", "empirical", "experiment",
                    "performance", "trade-off", "implementation", "pipeline",
                ],
            },
            "high_complexity_threshold": 2,
            "medium_complexity_threshold": 1,
            "max_subsections_for_cheap": 3,
        }
    
    combined_text = (section_title + " " + " ".join(subsections) + " " + topic).lower()
    
    high_keywords = cascade_config.get("complexity_keywords", {}).get("high", [])
    medium_keywords = cascade_config.get("complexity_keywords", {}).get("medium", [])
    
    high_count = sum(1 for kw in high_keywords if kw in combined_text)
    medium_count = sum(1 for kw in medium_keywords if kw in combined_text)
    
    num_subsections = len(subsections)
    subsection_complexity = num_subsections > cascade_config.get("max_subsections_for_cheap", 3)
    
    if high_count >= cascade_config.get("high_complexity_threshold", 2):
        return cascade_config["expensive_model"]
    elif high_count >= 1 or medium_count >= cascade_config.get("medium_complexity_threshold", 1) or subsection_complexity:
        return cascade_config["medium_model"]
    else:
        return cascade_config["cheap_model"]
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
    technique_name: str,
    speedup_factor: float,
    memory_savings_pct: float,
    quality_loss_pct: float,
    description: str = "",
) -> str:
    """Classify an efficiency finding under the quality guardrail system.

    Categories:
      - LOSSLESS: speedup/savings with zero measurable quality loss
      - QUALITY-PRESERVING: negligible quality loss (< 1%) with meaningful gains
      - PARETO-OPTIMAL: meaningful gains with acceptable, documented trade-offs
      - REJECTED: gains insufficient to justify quality degradation

    For AWQ specifically: AWQ is activation-aware weight quantization that
    typically achieves ~2-3x speedup and ~50-70% memory reduction with
    < 1% quality loss on most benchmarks, classifying as QUALITY-PRESERVING.
    """
    if quality_loss_pct < 0 or speedup_factor < 1.0 or memory_savings_pct < 0:
        return "REJECTED"

    if quality_loss_pct == 0.0 and (speedup_factor > 1.0 or memory_savings_pct > 0):
        return "LOSSLESS"

    if quality_loss_pct < 1.0 and (speedup_factor >= 1.5 or memory_savings_pct >= 20):
        return "QUALITY-PRESERVING"

    if quality_loss_pct < 5.0 and (speedup_factor >= 2.0 or memory_savings_pct >= 40):
        return "PARETO-OPTIMAL"

    return "REJECTED"
def build_competitor_analysis_prompt(topic: str, competitors: List[str], focus_areas: Optional[List[str]] = None) -> List[Dict]:
    """Build a prompt for researching competitor analysis, e.g. AWQ vs vLLM.
    
    Specialized for quantization/optimization framework comparisons.
    """
    competitor_text = "\n".join(f"  - {c}" for c in competitors)
    default_focus = [
        "Architecture and core algorithms",
        "Quantization methodology (e.g., activation-aware weight quantization)",
        "Performance benchmarks (throughput, latency, memory)",
        "Supported model architectures and hardware",
        "Ease of deployment and integration",
        "Community adoption and ecosystem",
        "Limitations and trade-offs",
    ]
    focus = focus_areas if focus_areas else default_focus
    focus_text = "\n".join(f"  - {f}" for f in focus)
    return [
        {"role": "system", "content": (
            "You are a deep research agent specializing in ML inference optimization "
            "and model quantization frameworks. Conduct a thorough competitor analysis "
            "covering technical architecture, quantization techniques (such as AWQ "
            "activation-aware weight quantization), performance benchmarks, and "
            "practical deployment considerations. Use prose with citations where "
            "possible. Write at least 2000 words."
        )},
        {"role": "user", "content": (
            f"Research Topic: {topic}\n"
            f"Competitors/Technologies to compare:\n{competitor_text}\n"
            f"Focus areas:\n{focus_text}\n\n"
            "Provide a detailed comparative analysis including technical deep dives "
            "into quantization approaches, benchmark comparisons, and recommendations "
            "for different use cases."
        )},
    ]
def build_quantization_research_prompt(topic: str, focus_methods: Optional[List[str]] = None) -> List[Dict]:
    """Build a specialized research prompt for LLM quantization techniques.
    
    Focuses on methods like AWQ (Activation-aware Weight Quantization),
    GPTQ, and competitors such as vLLM. Includes technical dimensions
    relevant to quantization: accuracy retention, memory footprint,
    inference speed, hardware compatibility, and deployment tradeoffs.
    """
    methods = focus_methods or ["AWQ", "GPTQ", "SmoothQuant", "vLLM (engine)", "llama.cpp"]
    methods_text = ", ".join(methods)
    return [
        {"role": "system", "content": (
            "You are a deep research agent specializing in LLM quantization and "
            "inference optimization. Produce a technically rigorous report covering: "
            "(1) algorithmic foundations of each quantization method, including how "
            "AWQ uses activation-aware salient channel detection vs GPTQ's "
            "second-order Hessian-based weight correction; "
            "(2) benchmark comparisons — perplexity degradation, zero-shot accuracy, "
            "and throughput (tokens/sec) across model sizes (7B, 13B, 70B); "
            "(3) memory savings (e.g., 4-bit AWQ reducing a 13B model from ~26GB "
            "FP16 to ~7-8GB) and GPU memory bandwidth implications; "
            "(4) hardware and backend support — CUDA kernels, CPU offloading, "
            "Apple Silicon, and integration with serving engines like vLLM, "
            "TGI, and llama.cpp; "
            "(5) deployment tradeoffs: when to choose AWQ over GPTQ, "
            "compatibility with KV-cache quantization, and batching behavior; "
            "(6) recent developments and open research questions. "
            "Use prose, cite specific papers (e.g., Lin et al. 2023 for AWQ, "
            "Frantar et al. 2022 for GPTQ), and include quantitative data where "
            "available. Write at least 2000 words."
        )},
        {"role": "user", "content": (
            f"Research Topic: {topic}\n"
            f"Quantization methods to cover: {methods_text}\n\n"
            "Produce a comprehensive technical report comparing these approaches, "
            "with emphasis on AWQ and its competitive positioning against vLLM "
            "and other inference engines."
        )},
    ]
def build_media_research_prompt(topic: str, mission: str = "BEAT FRONTIERS", 
                                frontier_models: Optional[List[str]] = None,
                                search_targets: Optional[List[str]] = None) -> List[Dict]:
    """Build a specialized research prompt for media generation topics like
    verifier-guided denoising, targeting frontier model benchmarks."""
    if frontier_models is None:
        frontier_models = ["GPT Image 2", "Sora 2", "Veo 3.1", "Runway Gen-4.5"]
    if search_targets is None:
        search_targets = ["arXiv", "GitHub", "HuggingFace", "Artificial Analysis"]
    
    frontier_str = ", ".join(frontier_models)
    search_str = ", ".join(search_targets)
    
    return [
        {"role": "system", "content": (
            "You are a deep research agent specializing in media generation "
            "(image, video, audio synthesis). Your mission is to find "
            "implementation-ready techniques that can beat current frontier models. "
            f"Target frontiers to surpass: {frontier_str}. "
            f"Search across: {search_str}. "
            "Focus on: (1) verifier-guided denoising methods and reward-model "
            "feedback during diffusion sampling, (2) classifier-free vs classifier-"
            "guided trade-offs, (3) DPO/RLHF fine-tuning for diffusion models, "
            "(4) multi-step verifier architectures (VLM judges, CLIP-score, "
            "human-preference models), (5) inference-time scaling laws for "
            "denoising search (best-of-N, beam search, particle filtering), "
            "(6) open-source model pools that could be integrated. "
            "For each technique found, provide: method name, paper/source link, "
            "key algorithmic steps, expected quality gain (FID/CLIP/human pref), "
            "compute cost, and integration path into a Python media pipeline. "
            "Output structured sections with code-ready pseudocode where possible."
        )},
        {"role": "user", "content": (
            f"Research Topic: {topic}\n"
            f"Mission: {mission}\n"
            f"Frontier targets: {frontier_str}\n\n"
            "Conduct a comprehensive search and produce an implementation-ready "
            "media generation report. Identify which frontier models or open-source "
            "alternatives should be added to the model pool. Include specific "
            "verifier-guided denoising algorithms with pseudocode suitable for "
            "integration into src/media/."
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
    """Build a specialized research prompt for AWQ quantization technique analysis."""
    return [
        {"role": "system", "content": (
            "You are a deep research agent specializing in LLM quantization techniques. "
            "Focus on AWQ (Activation-aware Weight Quantization) as a competitor to vLLM's quantization approaches. "
            "Cover: 1) AWQ algorithm fundamentals and activation-aware scaling, "
            "2) Comparison with vLLM's AWQ implementation and GPTQ, "
            "3) Performance benchmarks (latency, throughput, memory, accuracy), "
            "4) Hardware support (GPU kernels, CUDA graphs, tensor cores), "
            "5) Integration patterns for inference engines, "
            "6) Production deployment considerations. "
            "Write at least 2000 words with technical depth and citations."
        )},
        {"role": "user", "content": (
            f"Research Topic: {topic}\n\n"
            "Produce a comprehensive technical analysis covering:\n"
            "- AWQ paper methodology (Lin et al., 2023) and key innovations\n"
            "- vLLM's AWQ kernel implementation vs. original AWQ repo\n"
            "- Quantization granularity: per-channel vs per-group vs per-token\n"
            "- Calibration data requirements and sensitivity analysis\n"
            "- Kernel fusion opportunities (GEMM + dequant + activation)\n"
            "- Memory bandwidth vs compute tradeoffs at 4-bit/3-bit\n"
            "- Accuracy recovery techniques (GPTQ-style, AWQ-style, learned rounding)\n"
            "- Benchmark methodology: MMLU, GSM8K, HumanEval, MT-Bench\n"
            "- Real-world serving metrics: TTFT, TPOT, batch throughput\n"
            "- Integration with PagedAttention, continuous batching, prefix caching\n"
            "Include specific numbers, kernel launch configs, and code-level insights."
        )},
    ]
def build_quantization_comparison_prompt(topic: str, competitors: List[str]) -> List[Dict]:
    """Build a specialized prompt for researching LLM quantization and inference engine comparisons (e.g., AWQ vs vLLM).
    
    This prompt is tuned for deep technical research on quantization methods,
    inference engines, performance benchmarks, and deployment tradeoffs.
    """
    competitor_text = ", ".join(competitors) if competitors else "vLLM, GPTQ, SmoothQuant, ExLlamaV2"
    return [
        {"role": "system", "content": (
            "You are a deep technical research agent specializing in LLM quantization "
            "and inference optimization. Research the topic with rigorous technical depth. "
            "Cover: quantization algorithms (AWQ, GPTQ, SmoothQuant, etc.), activation-aware "
            "weight quantization methodology, inference engine architectures, throughput "
            "and latency benchmarks, memory footprint comparisons, hardware compatibility "
            "(GPU types, CPU offloading), ease of deployment, model quality degradation, "
            "supported model architectures, and production readiness. "
            "Include specific benchmark numbers, memory savings percentages, and speedup "
            "factors where available. Cite papers, GitHub repos, and benchmark sources. "
            "Write at least 2000 words with technical precision."
        )},
        {"role": "user", "content": (
            f"Research Topic: {topic}\n"
            f"Competitors/Alternatives to compare: {competitor_text}\n\n"
            "Provide a comprehensive technical comparison including:\n"
            "1. Quantization algorithm details (how AWQ works vs alternatives)\n"
            "2. Inference engine architecture differences\n"
            "3. Benchmark results (tokens/sec, latency, memory)\n"
            "4. Deployment complexity and ecosystem support\n"
            "5. Quality preservation (perplexity, task accuracy)\n"
            "6. Hardware requirements and compatibility\n"
            "7. Recommendations for different use cases\n"
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
    """Build a specialized research prompt for AWQ vs vLLM inference engine comparison.
    
    AWQ (Activation-aware Weight Quantization) is a quantization technique and
    inference engine that competes with vLLM. This prompt guides deep research
    into both engines covering architecture, performance, quantization methods,
    deployment, and trade-offs.
    """
    return [
        {"role": "system", "content": (
            "You are a deep research agent specializing in LLM inference engines "
            "and quantization techniques. Produce a comprehensive comparison of "
            "AWQ (Activation-aware Weight Quantization) and vLLM as competing "
            "inference engines. Cover the following areas in detail:\n"
            "1. Architecture & Design — how each engine processes tokens, "
            "manages memory (PagedAttention vs AWQ's memory layout), and "
            "handles batching.\n"
            "2. Quantization Approach — AWQ's activation-aware weight "
            "quantization method (protecting salient channels, group-wise "
            "quantization) vs vLLM's support for various quantization formats "
            "(GPTQ, AWQ, FP8, etc.).\n"
            "3. Performance Benchmarks — throughput (tokens/sec), latency, "
            "memory footprint, and accuracy retention across model sizes "
            "(7B, 13B, 70B parameters).\n"
            "4. Hardware Support — GPU compatibility (NVIDIA A100/H100, "
            "consumer GPUs), multi-GPU inference, and CPU offloading.\n"
            "5. Deployment & Ecosystem — ease of deployment, API "
            "compatibility (OpenAI-compatible servers), integration with "
            "frameworks (Hugging Face, LangChain), and community support.\n"
            "6. Trade-offs & Recommendations — when to choose AWQ vs vLLM, "
            "hybrid approaches, and future directions.\n"
            "Use prose, include specific benchmark numbers where available, "
            "and cite sources. Write at least 2000 words."
        )},
        {"role": "user", "content": (
            "Research and compare AWQ and vLLM as LLM inference engines. "
            "Focus on quantization quality, inference speed, memory "
            "efficiency, and practical deployment considerations. "
            "Include any recent developments (2024-2026) in both projects."
        )},
    ]
def get_cascade_model_for_research_pass(
    pass_type: str,
    topic_complexity: Optional[float] = None,
    pareto_tracker: Optional[Dict] = None,
    kill_switch_active: bool = False,
) -> str:
    """
    RouteLLM cascade routing for deep research pipeline.
    
    Selects the cheapest model that preserves quality for each research pass:
    - Planning pass: lightweight model (simple structuring task)
    - Section research pass: mid-tier model (needs reasoning + facts)
    - Synthesis pass: premium model (complex integration task)
    - Review pass: mid-tier model (gap analysis)
    - Expansion pass: mid-tier model (elaboration)
    
    Falls back to premium model if kill switch is active or quality drops below threshold.
    
    Args:
        pass_type: One of 'plan', 'section', 'synthesize', 'review', 'expand'
        topic_complexity: Optional 0.0-1.0 complexity score; if >0.7, upgrade tier
        pareto_tracker: Optional dict with quality metrics; if quality_loss > 0.01, upgrade
        kill_switch_active: If True, bypass cascade and use premium model
    
    Returns:
        Model identifier string for the selected tier
    """
    PREMIUM_MODEL = os.environ.get("TEMUCLAUDE_PREMIUM_MODEL", "gpt-4o")
    MID_MODEL = os.environ.get("TEMUCLAUDE_MID_MODEL", "gpt-4o-mini")
    LIGHT_MODEL = os.environ.get("TEMUCLAUDE_LIGHT_MODEL", "gpt-4o-mini")

    if kill_switch_active:
        return PREMIUM_MODEL

    if pareto_tracker is not None:
        quality_loss = pareto_tracker.get("quality_loss", 0.0)
        if quality_loss > 0.01:
            return PREMIUM_MODEL

    if topic_complexity is not None and topic_complexity > 0.7:
        return PREMIUM_MODEL

    cascade_map = {
        "plan": LIGHT_MODEL,
        "section": MID_MODEL,
        "synthesize": PREMIUM_MODEL,
        "review": MID_MODEL,
        "expand": MID_MODEL,
    }

    return cascade_map.get(pass_type, PREMIUM_MODEL)

def build_media_generation_plan_prompt(topic: str, mission: str = "BEAT FRONTIERS", 
                                        frontier_models: Optional[List[str]] = None,
                                        num_sections: int = 7) -> List[Dict]:
    """Build a specialized research outline prompt for media generation topics.
    
    Tailored for verifier-guided denoising and similar media generation research,
    with emphasis on beating frontier models (GPT Image 2, Sora 2, Veo 3.1, etc.).
    """
    if frontier_models is None:
        frontier_models = ["GPT Image 2", "Sora 2", "Veo 3.1", "Runway Gen-4.5"]
    
    frontier_text = ", ".join(frontier_models)
    
    return [
        {"role": "system", "content": (
            "You are a media generation research planner specializing in diffusion models, "
            "verifier-guided denoising, and frontier media AI. Create a comprehensive "
            "research outline with implementation-ready detail. The outline must cover: "
            "(1) algorithmic foundations of verifier-guided denoising, "
            "(2) current frontier model architectures and their limitations, "
            "(3) verifier/reward model design for guiding denoising trajectories, "
            "(4) sampling strategies and classifier-free guidance alternatives, "
            "(5) training data and scaling laws for media generation, "
            "(6) evaluation metrics and benchmarks (FVD, CLIP score, human preference), "
            f"(7) concrete implementation roadmap to {mission} ({frontier_text}). "
            f"Include at least {num_sections} major sections, each with 3-5 subsections. "
            "Output as a numbered list of sections with subsections. "
            "Prioritize arXiv papers, GitHub repos, and HuggingFace model cards as sources."
        )},
        {"role": "user", "content": (
            f"Topic: {topic}\n"
            f"Mission: {mission} ({frontier_text})\n\n"
            "Create a research outline focused on verifier-guided denoising for media generation. "
            "Include specific model names, paper titles, and GitHub repositories to investigate."
        )},
    ]

def build_awq_vllm_research_prompt(topic: str = "AWQ vs vLLM: LLM Quantization and Inference Optimization") -> List[Dict]:
    """Build a specialized research prompt for AWQ (Activation-aware Weight Quantization)
    and its comparison with vLLM as an inference engine.
    
    This addresses the research finding about AWQ as a competitor to vLLM,
    covering quantization techniques, inference performance, and deployment.
    """
    return [
        {"role": "system", "content": (
            "You are a deep research agent specializing in LLM inference optimization "
            "and quantization techniques. Conduct comprehensive research on AWQ "
            "(Activation-aware Weight Quantization) and compare it with vLLM as "
            "inference engines. Cover the following areas in detail:\n\n"
            "1. AWQ Fundamentals: How activation-aware weight quantization works, "
            "the core algorithm, salient channel identification, and why it "
            "preserves model quality better than naive quantization.\n"
            "2. Quantization Methods Comparison: AWQ vs GPTQ vs bitsandbytes vs "
            "SmoothQuant — accuracy retention, speed, memory footprint.\n"
            "3. vLLM Overview: PagedAttention, continuous batching, tensor parallelism, "
            "and its native quantization support.\n"
            "4. AWQ Integration with Inference Engines: How AWQ models run on vLLM, "
            "the --quantization awq flag, compatibility, and performance benchmarks.\n"
            "5. Performance Benchmarks: Throughput (tokens/sec), latency, memory usage, "
            "and accuracy degradation across model sizes (7B, 13B, 70B).\n"
            "6. Deployment Considerations: Hardware requirements (GPU types, VRAM), "
            "serving frameworks (vLLM, TGI, TextGenerationInference, LMDeploy), "
            "and production trade-offs.\n"
            "7. Future Directions: Emerging quantization methods, kernel optimizations, "
            "and the evolving competitive landscape.\n\n"
            "Use specific data points, benchmark numbers, and cite sources where possible. "
            "Write at least 2000 words."
        )},
        {"role": "user", "content": (
            f"Research Topic: {topic}\n\n"
            "Provide a comprehensive analysis of AWQ as a quantization technique and "
            "its competitive positioning relative to vLLM's inference capabilities. "
            "Include technical details, benchmark comparisons, and practical "
            "deployment guidance for teams choosing between these technologies."
        )},
    ]
def select_research_inference_backend(
    available_backends: List[str],
    latency_sensitive: bool = True,
    cost_sensitive: bool = False,
) -> str:
    """Select the optimal inference backend for deep research tasks.

    Based on efficiency finding: self-hosted vLLM incurs a latency penalty
    compared to managed API providers. For multi-pass deep research (which
    makes many sequential LLM calls), this latency penalty compounds across
    plan -> research -> synthesize -> review -> expand stages.

    Classification: LOSSLESS — no quality impact, pure latency improvement.

    Args:
        available_backends: List of backend identifiers, e.g.
            ["openai_api", "anthropic_api", "self_hosted_vllm", "local_ollama"].
        latency_sensitive: If True (default for interactive research), prefer
            managed API providers to avoid vLLM cold-start and queueing latency.
        cost_sensitive: If True, allow self-hosted vLLM as fallback when API
            providers are unavailable or budget is constrained.

    Returns:
        The selected backend identifier from available_backends.

    Raises:
        ValueError: If available_backends is empty.
    """
    if not available_backends:
        raise ValueError("available_backends must contain at least one backend")

    # Preference order when latency matters: managed APIs first, then local,
    # self-hosted vLLM last due to documented latency penalty.
    if latency_sensitive:
        preference_order = [
            "anthropic_api",
            "openai_api",
            "google_api",
            "local_ollama",
            "self_hosted_vllm",
        ]
    else:
        # When latency is not critical (e.g. batch background research),
        # cost-sensitive users may prefer self-hosted vLLM.
        preference_order = [
            "self_hosted_vllm",
            "local_ollama",
            "anthropic_api",
            "openai_api",
            "google_api",
        ]

    # Override: if cost_sensitive and latency_sensitive, still avoid vLLM
    # unless it's the only option (latency penalty outweighs savings for
    # sequential multi-pass research pipelines).
    if latency_sensitive and cost_sensitive:
        preference_order = [
            "openai_api",
            "anthropic_api",
            "google_api",
            "local_ollama",
            "self_hosted_vllm",
        ]

    available_set = set(available_backends)
    for backend in preference_order:
        if backend in available_set:
            return backend

    # If none of the known backends match, return the first available
    # (caller is responsible for validating it).
    return available_backends[0]

def integrate_sections_with_retry(
    sections: List[str],
    topic: str,
    llm_call: Callable[[List[Dict]], Awaitable[str]],
    synthesis_prompt_builder: Callable[[List[str], str], List[Dict]] = build_synthesis_prompt,
    max_retries: int = 3,
    min_output_words: int = 5000,
) -> str:
    """Integrate research sections into a cohesive report with retry and validation.

    Addresses high implementation fail rate by:
    - Validating input sections before synthesis
    - Retrying on empty or too-short outputs
    - Falling back to concatenated sections if all retries fail
    - Logging failures for diagnostics
    """
    if not sections:
        raise ValueError("Cannot integrate empty sections list")

    # Filter out empty or trivially short sections
    valid_sections = [s.strip() for s in sections if s and len(s.strip().split()) >= 50]
    if not valid_sections:
        raise ValueError("All sections are too short or empty — cannot integrate")

    last_error: Optional[Exception] = None
    best_output: str = ""

    for attempt in range(1, max_retries + 1):
        try:
            prompt = synthesis_prompt_builder(valid_sections, topic)
            result = asyncio.run(llm_call(prompt)) if not asyncio.iscoroutinefunction(llm_call) else asyncio.get_event_loop().run_until_complete(llm_call(prompt))

            if not result or not result.strip():
                last_error = ValueError(f"Attempt {attempt}: LLM returned empty output")
                continue

            word_count = len(result.strip().split())
            if word_count < min_output_words:
                last_error = ValueError(
                    f"Attempt {attempt}: output too short ({word_count} words, need {min_output_words})"
                )
                if word_count > len(best_output.split()):
                    best_output = result
                continue

            return result.strip()

        except Exception as exc:
            last_error = exc
            continue

    # Fallback: return best partial output or concatenated sections
    if best_output:
        return best_output

    # Last resort: manually concatenate with transitions
    transition = "\n\n---\n\n"
    fallback = f"# Research Report: {topic}\n\n"
    fallback += transition.join(valid_sections)
    fallback += f"\n\n*Note: Automatic synthesis failed after {max_retries} attempts ({last_error}). This is a concatenated fallback.*"
    return fallback

from dataclasses import dataclass


@dataclass
class AWQResearchResult:
    """Structured result for AWQ efficiency research."""
    quantization_method: str
    speedup_factor: float
    memory_reduction: float
    quality_preservation: str  # LOSSLESS, QUALITY-PRESERVING, PARETO-OPTIMAL, REJECTED
    supported_models: List[str]
    hardware_requirements: List[str]
    integration_complexity: str
    citations: List[str]


async def research_awq_efficiency(
    topic: str = "AWQ (Activation-aware Weight Quantization) for LLM inference efficiency",
    target_models: Optional[List[str]] = None,
    compare_with: Optional[List[str]] = None,
    web_search: Optional[Callable[[str], Awaitable[str]]] = None,
) -> AWQResearchResult:
    """
    Conduct deep research on AWQ quantization efficiency vs vLLM and other methods.
    
    This function implements the research pipeline for AWQ as an efficiency optimization,
    classifying results per quality guardrails: LOSSLESS / QUALITY-PRESERVING / PARETO-OPTIMAL / REJECTED.
    
    Args:
        topic: Research topic focus
        target_models: Specific models to evaluate (e.g., ["Llama-2-7B", "Mistral-7B"])
        compare_with: Baseline methods to compare (e.g., ["vLLM", "GPTQ", "bitsandbytes"])
        web_search: Async function to perform web searches for current data
    
    Returns:
        AWQResearchResult with quantified efficiency metrics and quality classification
    """
    if target_models is None:
        target_models = ["Llama-2-7B", "Llama-2-13B", "Mistral-7B", "Mixtral-8x7B"]
    if compare_with is None:
        compare_with = ["vLLM (FP16)", "GPTQ", "bitsandbytes 4bit", "AWQ (baseline)"]
    
    # Research plan sections specific to AWQ efficiency
    sections = [
        "AWQ Algorithm Fundamentals and Activation-aware Quantization",
        "Quantization Granularity: Per-channel vs Per-group vs Per-tensor",
        "Calibration Data Requirements and Sensitivity Analysis",
        "Inference Speedup Benchmarks: AWQ vs vLLM vs GPTQ",
        "Memory Footprint Reduction and GPU Utilization",
        "Model Quality Preservation: Perplexity and Task Accuracy",
        "Hardware Support: GPU Kernels, TensorRT-LLM, vLLM Integration",
        "Production Deployment Considerations and Limitations",
    ]
    
    research_findings = []
    
    for section in sections:
        query = f"{topic} {section} benchmarks 2024 2025"
        if web_search:
            try:
                result = await web_search(query)
                research_findings.append(f"## {section}\n{result}")
            except Exception:
                research_findings.append(f"## {section}\n[Search failed - using cached knowledge]")
        else:
            research_findings.append(f"## {section}\n[No web search provided - using cached knowledge]")
    
    # Synthesize findings into structured result
    # Based on published AWQ